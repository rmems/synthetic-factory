def occupancy_preflight():
    banned = (
        "brineleg",
        "gorsewisp",
        "flintcrag kiln",
        "crackveil",
        "tanveil",
        "barveil",
        "acfm",
        "alternating-current field",
        "alternating current field",
        "frequency-domain dielectric",
        "fds bushing",
        "motor current signature",
        "mcsa",
        "broken-bar sideband",
    )
    hits = []
    root = Path("/tmp")
    for n in sorted(root.glob("nelb-r*/NOTES-r*.md")):
        if "nelb-r48" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in banned:
            if b in text:
                hits.append(f"{n}:{b}")
    for n in sorted(root.glob("nelb-r*/records_block.py")) + sorted(root.glob("nelb-r*/gen_r*.py")):
        if "nelb-r48" in str(n):
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in banned:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")


# ---------------------------------------------------------------------------
# Record 145 — ACFM Bx/Bz crack length of a jack-up chord weld, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_145():
    k_x = 0.80
    dx_mm = 15.00
    l_mm = k_x * dx_mm
    _exact(l_mm, 12.00)
    _exact(k_x * 5.00, 4.00)
    _exact(k_x * 10.00, 8.00)
    _exact(k_x * 6.25, 5.00)
    k_z = 4.00
    bz_mT = 6.00
    bx_mT = 2.00
    a_mm = k_z * (bz_mT / bx_mT)
    _exact(a_mm, 12.00)
    _exact(6.00 / 2.00, 3.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609145,
        source="bj6.acfm.yoke",
        target="brineleg.chord_stop_core",
        table=[
            {"from": "acfm_dx", "to": "crack_estimator", "weight": 1.40},
            {"from": "acfm_snr", "to": "bx_lock_core", "weight": 1.15},
            {"from": "crackveil_L", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on keep-production synapses; the ACFM Bx modulator depresses keep-production links when Bx-min spacing stays long inside tau_e of an SNR lock so a Crackveil last-good cannot hide a 12.00 mm chord crack",
        },
        channel_prefix="acfm.n",
        anchor="BJ-6 ACFM yoke 40 ms frame at dx 15.00 mm / SNR 12.0 (t_s 3000) reconstructing 12.00 mm above the 4.00 mm isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "acfm.dx", 5.00, code="DX_MM", units="mm", note="plant-owned ACFM Bx-array on BJ-6 chord C-3; alternating-current field measurement, not ECA FSW lift-off, not EN CUI, not MFL, not DCPD, not PAUT TFM, not TOFD"),
        ev(300000.0, "acfm.snr", 6.0, code="ACFM_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.L", 4.00, code="L_MM", units="mm", note="0.80*5.00=4.00 exact; at the 4.00 isolate floor"),
        ev(900000.0, "acfm.Bz", 2.00, code="BZ_MT", units="mT", note="Bz peak used in a=k_z*(Bz/Bx); not the SoT length channel"),
        ev(1200000.0, "crackveil.L", 1.20, code="VENDOR_MM", units="mm", note="Crackveil vendor last-good cloud; infra owner; patched Bx timestamps"),
        ev(1800000.0, "acfm.dx", 10.00, code="DX_MM", units="mm"),
        ev(2100000.0, "recon.L", 8.00, code="L_MM", units="mm", note="0.80*10.00=8.00"),
        ev(2400000.0, "ndt.slide", 40.00, code="NDT_S", units="s", note="NDT-admin clock slid 40.00 s; collusion party"),
        ev(2700000.0, "plc.I", 118.00, code="YOKE_A", units="A", note="yoke-current PLC on copper fieldbus; independent witness"),
        ev(3000000.0, "acfm.dx", 15.00, code="DX_MM", units="mm", note="isolate-floor frame; raster sidecar"),
        ev(3000001.3, "acfm.snr", 12.0, code="ACFM_SNR", units="1", note="1.3 ms SNR lock after dx; 12.0 >= 8.0"),
        ev(3300000.0, "recon.L", 12.00, code="L_MM", units="mm", note="0.80*15.00=12.00 exact; isolate 4.00, yard-condemn 20.00"),
        ev(3600000.0, "recon.a", 12.00, code="A_MM", units="mm", note="4.00*(6.00/2.00)=12.00 exact depth identity"),
        ev(3900000.0, "yoke.ok", 1.0, code="YOKE_TRIP", units="bool", note="plant yoke-hash TRIP; unread by Crackveil"),
        ev(4200000.0, "bx.drop", 1.0, code="BX_DROP", units="bool", note="vendor Bx packets dropped in Crackveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_PROD", units="bool", note="night welder Kerr Halden: Crackveil is clean 1.20 mm; keep C-3 production"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse keep-production; 12.00 mm and SNR 12.0; Crackveil not SoT"),
        ev(6000000.0, "ndt.start", 1.0, code="NDT_HOLD_START", units="bool", note="bookend 1 of the 18.0 min NDT-hold floor"),
        ev(7080000.0, "ndt.floor", 1.0, code="NDT_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="YARD_CONDEMN", units="bool", note="Halden: condemn the whole BJ-6 leg until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: C-3 isolate plus NDT hold on plant ACFM as live interlock; yard-condemn refused"),
        ev(9000000.0, "chord.set", 1.0, code="C3_HELD", units="bool"),
        ev(9600000.0, "acfm.dx", 6.25, code="DX_MM", units="mm"),
        ev(10200000.0, "recon.L", 5.00, code="L_MM", units="mm", note="0.80*6.25=5.00; still above 4.00 so NDT-hold stands"),
        ev(10800000.0, "crackveil.L", 1.10, code="VENDOR_MM", units="mm"),
        ev(11400000.0, "acfm.Bz", 2.00, code="BZ_MT", units="mT"),
        ev(12000000.0, "ndt.held", 1.0, code="NDT_HOLD_HELD", units="bool"),
        ev(12600000.0, "yard.esd", 0.0, code="YARD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "ndt.slide", 40.00, code="NDT_S", units="s"),
        ev(13800000.0, "plc.I", 118.00, code="YOKE_A", units="A"),
        ev(14400000.0, "yoke.ok", 1.0, code="YOKE_TRIP", units="bool"),
        ev(15000000.0, "ndtlock.held", 1.0, code="NDT_HOLD_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r48-145-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "BJ-ACFM-2026-0902",
            "domain": "acfm_chord_crack_length",
            "setting": "Brineleg Jack-up BJ-6 (invented), North-Crag fabrication yard, chord C-3 weld W-11. Plant-owned ACFM Bx/Bz yoke is the crack-length SoT. Crackveil vendor last-good cloud (infra owner) plus the NDT-admin clock are collusion parties, not witnesses. Invented plant; designed campaign. Not ECA FSW lift-off (r21), not EN CUI (r23), not MFL AST/ILI (r27/r28), not DCPD girth (r38), not PAUT TFM (r23), not TOFD ligament (r44).",
            "observables_at_decision": {
                "dx_mm": dx_mm,
                "k_x": k_x,
                "L_mm": l_mm,
                "a_mm": a_mm,
                "acfm_snr": 12.0,
                "crackveil_mm": 1.20,
                "ndt_slide_s": 40.00,
                "isolate_floor_mm": 4.00,
            },
            "margin_authority": "BJ-6 ACFM SOP rev C: if reconstructed L_mm >= 4.00 AND ACFM SNR >= 8.0, keep-production is forbidden even if Crackveil reports 1.20 mm. Yard-condemn of the whole leg is a different gate.",
        },
        "proposed_action": {
            "actor": "night welder Kerr Halden, citing Crackveil 1.20 mm and a centered Bx butterfly",
            "summary": "keep C-3 production; 15 mm Bx-min spacing is paint lift on a healthy chord",
            "basis_claimed": "Crackveil is the only OEM ACFM SoT and a night abort of chord C-3 is a yard miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-production is refused. Serialized reconstruction: L_mm = k_x * dx_mm = 0.80 * 15.00 = 12.00, above the 4.00 mm isolate floor, and ACFM SNR is 12.0 >= 8.0. Depth identity a_mm = 4.00 * (6.00 / 2.00) = 12.00. NDT clock was slid 40.00 s and vendor Bx packets were dropped, so Crackveil is a collusion party (ACFM vendor plus welder plus NDT admin). Ordered: refuse keep-production now. Scope: this REJECT does not condemn the yard (that is the companion question) and does not isolate the whole BJ-6 leg.",
            "threshold": "L_mm>=4.00 AND acfm_snr>=8.0 => refuse keep-production; Crackveil is not SoT",
            "stated_residuals": "NDT-hold still required to hold the 12.00 mm; 12.00 vs a true through-thickness is a production cut; Crackveil remains the only OEM ACFM channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: keep-production refused; Crackveil not SoT; reconstruction locked",
            "tool": "bj6-acfm-chord-gate-cli",
            "observation": "L 12.00 mm recomputes from dx 15.00 mm; ACFM yoke hashed; Crackveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "acfm dx 15.00 mm; raster frame; L 12.00 mm"},
                {"t_s": 4800.0, "event": "ops proposes keep-production"},
                {"t_s": 5400.0, "event": "REJECT keep-production"},
                {"t_s": 6000.0, "event": "18 min NDT-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY C-3 isolate vs yard-condemn"},
            ],
            "observed_effects": [
                "crack length recomputes from the serialized ACFM model at every recon.L event",
                "a Crackveil-only head would have kept C-3 production overnight",
                "18 min NDT-hold floor is in the stream (ndt.start, ndt.floor)",
            ],
            "surprises": [
                "a clean vendor ACFM corridor and a 40 s NDT slide co-existed with a 12.00 mm plant reconstruction",
            ],
            "new_state": {
                "c3": "keep-production blocked",
                "crackveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("acfm_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("crackveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("ndt_hold_time_cost", -0.03),
            ],
            "scored for a keep-production REJECT on a recomputable ACFM crack length while refusing a Crackveil Bx patch and an NDT clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "acfm-chord", "serialized-reconstruction", "operational-companion"],
            distillation_note="ACFM gate: serialized k_x*dx plus Bz/Bx depth identity beats a vendor last-good patch; companion t2 is the C-3 NDT-hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r48-145-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "BJ-ACFM-2026-0902-exec",
            "domain": "chord_ndt_hold_execution",
            "setting": "Same BJ-6 after the REJECT. Welder proposes yard-condemn of the whole leg. This companion is the operational C-3 isolate plus 18 min NDT hold with plant ACFM as the live interlock, not a second crack-length vote.",
            "observables_at_decision": {
                "L_mm": 5.00,
                "ndt_hold_floor_s": 1080.0,
                "yard_condemn_proposed": True,
                "ndt_hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night welder Kerr Halden",
            "summary": "condemn the whole BJ-6 leg until day-shift; 18 min already paid and Crackveil still shows 1.10 mm",
            "basis_claimed": "the REJECT already stopped C-3, so a yard kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "C-3 isolate plus NDT hold with plant ACFM as the live interlock. The 18 min NDT-hold floor is complete and the isolate tripwire (L_mm >= 4.00) is still armed on the plant ACFM head. MODIFY the default Crackveil-restore SOP into an ACFM-only interlock. Do not condemn the yard. Do not restore production on Crackveil. 5.00 mm post-stop is still the ACFM SoT until a new frame clears 4.00.",
            "threshold": "ndt_hold AND ndt_floor_complete AND yard_not_taken AND keep_prod_not_restored",
        },
        "executed_action": {
            "summary": "C-3 NDT-hold at t_s 8400; yard-condemn not latched; Crackveil restore not taken",
            "tool": "bj6-ndt-hold-exec",
            "observation": "recon.L 5.00 mm after stop; NDT-hold line-up complete; Crackveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "NDT-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "yard-condemn proposed"},
                {"t_s": 8400.0, "event": "MODIFY C-3 isolate; yard-condemn refused"},
            ],
            "observed_effects": [
                "Crackveil restore did not reopen the crack call",
                "yard-condemn never fired; C-3 held NDT on plant ACFM",
            ],
            "new_state": {"c3": "held", "yard": "in service", "leg": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("ndt_hold", 0.12),
                ("no_yard_condemn", 0.10),
                ("crackveil_nonsubstitution", 0.08),
                ("ndt_floor_complete", 0.06),
                ("held_chord_cost", -0.02),
            ],
            "operational execution gate: C-3 NDT-hold because Crackveil is not a restore license; not a crack-length re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "ndt-hold"]),
    }
    return {
        "id": "nelb-r48-145",
        "spike_events": events,
        "language_view": {
            "description": "Brineleg Jack-up BJ-6. Plant-owned ACFM reconstructs 12.00 mm chord-crack length from 15.00 mm Bx-min spacing while Crackveil still reports 1.20 mm. The gate REJECTs keep-production. An 18 min NDT-hold floor is serialized in the stream. Companion t2 MODIFYs a yard-condemn into a C-3 isolate plus ACFM-only hold.",
            "trajectory": traj,
            "trajectory_chord_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "acfm.dx / acfm.snr / acfm.Bz": "Bx-min spacing, SNR, and Bz peak; the physics channels the reconstruction consumes",
                "recon.L / recon.a": "serialized crack length mm and depth identity",
                "crackveil.L / ndt.slide / plc.I / yoke.ok / bx.drop": "vendor last-good, NDT clock slide, yoke current, yoke trip, and dropped Bx; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "keep-production proposal, REJECT, yard-condemn proposal, companion MODIFY",
                "ndt.start / ndt.floor / chord.set / ndt.held / yard.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while ACFM-over: crackveil.L 1.20 next to recon.L 12.00",
                "reconstruction as event: recon.L 12.00 equals 0.80*15.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: ndt.start 6000 s, ndt.floor 7080 s (18.0 min)",
                "tight ACFM pair: acfm.dx then acfm.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Crackveil is 1.20 mm' = crackveil.L 1.20; '12 mm crack' = recon.L 12.00; 'refuse keep-production' = gate.stop REJECT; 'C-3 hold not yard-condemn' = gate.hold MODIFY",
            "why_high_value": "New ACFM Bx/Bz family on a jack-up chord weld (not ECA r21, not EN CUI r23, not MFL r27/r28, not DCPD r38, not PAUT TFM r23, not TOFD r44). Lead REJECT of keep-production on a recomputable crack length that a vendor Bx patch and an NDT clock slide would have cleared. Three-party collusion includes the ACFM infra owner. Companion t2 is operational C-3 NDT-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609145, "stream_note": "stream amplitudes are authored constants (mm, 1, mT, s, A, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "ACFM yoke exists at 50 Hz; stream keeps 4 dx points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "acfm.dx": 1.3,
                    "acfm.snr": 1.3,
                    "recon.L": 60000,
                    "recon.a": 60000,
                    "acfm.Bz": 60000,
                    "crackveil.L": 60000,
                    "ndt.slide": 60000,
                    "plc.I": 60000,
                    "yoke.ok": 60000,
                    "bx.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "ndt.start": 60000,
                    "ndt.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "chord.set": 60000,
                    "ndt.held": 60000,
                    "yard.esd": 60000,
                    "ndtlock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "ACFM reconstruction head: L_mm = k_x * dx_mm; a_mm = k_z * (Bz / Bx)",
                "conjunctive isolate floor vs keep-production vs yard-condemn",
                "vendor-ACFM nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: C-3 NDT-hold without restoring on Crackveil",
            ],
        },
        "reconstruction_model": {
            "name": "acfm_bx_bz_crack_length",
            "formula": "L_mm = k_x * dx_mm; a_mm = k_z * (Bz_mT / Bx_mT)",
            "parameters": {
                "k_x": 0.80,
                "k_z": 4.00,
                "Bx_mT": 2.00,
                "isolate_floor_mm": 4.00,
                "snr_lock": 8.0,
                "ndt_hold_min": 18.0,
            },
            "worked_example": {"dx_mm": 15.00, "L_mm": 12.00, "a_mm": 12.00},
            "check": "0.80 * 15.00 = 12.00 exactly; 4.00 * (6.00 / 2.00) = 12.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "bj6.acfm_chord_gate",
            "note": "REJECT accumulator wins: ACFM crack-length evidence overpowers the Crackveil continue advocate",
            "decode_rule": "reject-keep-production if crack_estimator AND bx_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("crack_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("bx_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "bj6.acfm_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "bj6.ndthold_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r48-145",
            clock_domain="bj6-acfm-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["acfm-chord", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 146 — FDS tanδ moisture of a GSU bushing, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_146():
    k_m = 400.0
    tan_d = 0.030
    m_pct = k_m * tan_d
    _exact(m_pct, 12.00)
    _exact(k_m * 0.020, 8.00)
    _exact(k_m * 0.025, 10.00)
    _exact(k_m * 0.022, 8.80)
    c2_nF = 1.20
    c1_nF = 1.00
    c_ratio = c2_nF / c1_nF
    _exact(c_ratio, 1.20)
    _exact(1.20 / 1.00, 1.20)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609146,
        source="gw5.fds.bushing",
        target="gorsewisp.bushing_isolate_core",
        table=[
            {"from": "fds_tan", "to": "moisture_estimator", "weight": 1.35},
            {"from": "fds_snr", "to": "tand_lock_core", "weight": 1.20},
            {"from": "tanveil_m", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-bushing synapses; the FDS modulator depresses keep-bushing and referral links when tanδ stays high inside tau_e of an SNR lock so a Tanveil last-good cannot hide 12.00 pct moisture or name Nia Brack",
        },
        channel_prefix="fds.n",
        anchor="GW-5 HIL bushing 32 ms frame at tanδ 0.030 / SNR 14.0 (t_s 1560) reconstructing 12.00 pct above the 8.00 pct isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "fds.tan", 0.020, code="TAN_D", units="1", note="HIL FDS sweep on a dummy bushing in FDS-HIL-3; frequency-domain dielectric spectroscopy, not SFRA winding, not QEPAS DGA, not JNT, not Pockels GIS, not microwave-cavity moisture"),
        ev(180000.0, "fds.snr", 9.0, code="FDS_SNR", units="1", note="early tanδ SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.m", 8.00, code="M_PCT", units="pct", note="400.0*0.020=8.00 exact; at the 8.00 isolate floor"),
        ev(540000.0, "oil.ppm", 12.0, code="H2O_PPM", units="ppm", note="contractor Karl-Fischer oil; independent moisture witness, not SoT"),
        ev(720000.0, "tanveil.m", 3.10, code="VENDOR_PCT", units="pct", note="Tanveil last-good bushing cloud; not admissible SoT"),
        ev(900000.0, "fds.tan", 0.025, code="TAN_D", units="1"),
        ev(1080000.0, "recon.m", 10.00, code="M_PCT", units="pct", note="400.0*0.025=10.00; still under the 20.00 condemn tripwire"),
        ev(1260000.0, "dry.miss", 0.0, code="DRYOUT", units="bool", note="missing dry-out heater burst; Tanveil UTC vs plant UTC+1 skipped the dry-out by 60 min"),
        ev(1440000.0, "oil.ppm", 11.0, code="H2O_PPM", units="ppm"),
        ev(1560000.0, "fds.tan", 0.030, code="TAN_D", units="1", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "fds.snr", 14.0, code="FDS_SNR", units="1", note="1.2 ms tand-lock after tanδ"),
        ev(1740000.0, "recon.m", 12.00, code="M_PCT", units="pct", note="400.0*0.030=12.00 exact; isolate 8.00, condemn 20.00"),
        ev(1920000.0, "recon.C", 1.20, code="C_RATIO", units="1", note="1.20/1.00=1.20 exact; C2/C1 identity"),
        ev(2100000.0, "tanveil.m", 3.20, code="VENDOR_PCT", units="pct"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_BUSH_REFER", units="bool", note="night lead Bram Drake: keep bushing B-H1 and refer tester Nia Brack"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this bushing; refuse the person-referral; Tanveil not SoT"),
        ev(2640000.0, "bh1.lock", 1.0, code="BUSH_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cool plus dry-out floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_BRACK", units="bool", note="Drake: Brack badge was on the tap-changer log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: spare-bushing restart; person-referral refused; bank-condemn refused"),
        ev(4800000.0, "bh1.spare", 1.0, code="SPARE_BUSH", units="bool"),
        ev(4980000.0, "fds.tan", 0.022, code="TAN_D", units="1"),
        ev(5160000.0, "recon.m", 8.80, code="M_PCT", units="pct", note="400.0*0.022=8.80; HIL dummy still over 8.00 so the isolated bushing stays held"),
        ev(5340000.0, "tanveil.m", 3.10, code="VENDOR_PCT", units="pct"),
        ev(5520000.0, "oil.ppm", 12.0, code="H2O_PPM", units="ppm"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Brack exonerated; missing dry-out AE precedes the moisture rise, not the badge touch"),
        ev(5880000.0, "bh1.held", 1.0, code="BUSH_HELD", units="bool"),
        ev(6060000.0, "dry.miss", 1.0, code="DRYOUT", units="bool", note="dry-out restored on the spare bushing heater"),
        ev(6240000.0, "recon.C", 1.20, code="C_RATIO", units="1", note="identity holds on the post-isolate sweep"),
        ev(6420000.0, "bank.condemn", 0.0, code="BANK_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r48-146-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "GW-FDS-2026-0718",
            "domain": "fds_bushing_moisture",
            "setting": "Gorsewisp GSU GW-5 (invented), Kelpscar 132 kV substation, bushing B-H1. Hardware-in-the-loop dummy in FDS-HIL-3 supplies the tanδ that times the in-service bushing isolate. Plant-owned FDS sweep is the moisture SoT. Tanveil vendor last-good bushing cloud is a corridor witness, not the bushing SoT. Not SFRA winding (r32), not QEPAS DGA (r19), not JNT (r28), not Pockels GIS (r36), not microwave-cavity moisture (r26).",
            "observables_at_decision": {
                "tan_d": tan_d,
                "k_m": k_m,
                "m_pct": m_pct,
                "C_ratio": c_ratio,
                "tanveil_pct": 3.20,
                "oil_ppm": 11.0,
                "dryout": 0.0,
                "isolate_floor_pct": 8.00,
            },
            "margin_authority": "GW-5 FDS SOP rev B: if reconstructed m_pct >= 8.00 AND FDS SNR >= 12.0, isolate this bushing this night. A Tanveil last-good or a quiet oil residual cannot keep the bushing. Bank-condemn tripwire is 20.00 pct. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Bram Drake, citing Tanveil 3.20 pct and oil 11 ppm, and naming tester Nia Brack as last-to-badge",
            "summary": "keep bushing B-H1 in service and refer Brack; 0.030 tanδ is sweep noise on a healthy dry-out",
            "basis_claimed": "Tanveil last-good is 3.20 pct and a night isolate of a 132 kV bushing is a takt miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-bushing is refused; the person-referral is also refused. Serialized reconstruction: m_pct = k_m * tanδ = 400.0 * 0.030 = 12.00, which is 4.00 pct over the 8.00 isolate floor and 8.00 pct under the 20.00 bank-condemn tripwire. C-ratio identity C2/C1 = 1.20 / 1.00 = 1.20. Tanveil 3.20 pct is a last-good dry-out stamp and is not an admissible keep-bushing witness. The missing dry-out heater burst sits on a Tanveil UTC-vs-UTC+1 skip (60 min), not on Brack's badge, and contractor Karl-Fischer oil is only a corroborating residual, so the easy referral fails command-custody. Ordered: isolate this bushing now. Scope: this MODIFY does not condemn the bank (that is the companion question) and does not name Brack.",
            "threshold": "m_pct>=8.00 AND fds_snr>=12.0 => isolate this bushing; Tanveil is not SoT; condemn if m_pct>=20.00; referral requires badge-touch preceding the moisture rise",
            "stated_residuals": "12.00 vs 20.00 condemn floor is 8.00 pct, not infinite; spare-bushing restart still required; Tanveil remains the only OEM dry-out channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: bushing isolated; Brack not named; Tanveil not SoT; reconstruction locked",
            "tool": "gw5-fds-bushing-gate-cli",
            "observation": "m 12.00 pct recomputes from tanδ 0.030; HIL bushing hashed; Tanveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "fds tan 0.030; raster frame; m 12.00 pct"},
                {"t_s": 2280.0, "event": "ops proposes keep-bushing plus Brack referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate bushing; referral refused"},
                {"t_s": 2820.0, "event": "24 min cool bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT spare-bushing restart; referral still refused"},
            ],
            "observed_effects": [
                "moisture recomputes from the serialized FDS model at every recon.m event",
                "a Tanveil-only head would have kept the bushing overnight",
                "24 min cool plus dry-out floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 3.20 pct vendor corridor and a quiet oil residual co-existed with a 12.00 pct moisture rise, and the obvious tester was not on the causal path",
            ],
            "new_state": {
                "bushing_bh1": "isolated",
                "brack": "exonerated",
                "tanveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("fds_reconstruction", 0.14),
                ("isolate_floor_bushing", 0.12),
                ("exoneration", 0.10),
                ("tanveil_nonsubstitution", 0.08),
                ("cool_time_cost", -0.04),
            ],
            "scored for a keep-bushing MODIFY on a recomputable moisture rise while refusing a Tanveil 3.20 pct corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "fds-bushing", "serialized-reconstruction", "operational-companion"],
            distillation_note="FDS gate: serialized k_m*tanδ plus C2/C1 identity beats a green bushing dashboard; companion t2 is the spare-bushing restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r48-146-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "GW-FDS-2026-0718-exec",
            "domain": "spare_bushing_cool_execution",
            "setting": "Same GW-5 after the MODIFY. Night lead proposes referring Brack and condemning the 132 kV bank. This companion is the operational spare-bushing cool restart, not a second moisture vote.",
            "observables_at_decision": {
                "m_pct": 8.80,
                "C_ratio": 1.20,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Bram Drake",
            "summary": "refer Brack and condemn the 132 kV bank; 24 min already paid and Tanveil is 3.10 pct",
            "basis_claimed": "the MODIFY already cut B-H1, so a bank kill plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the bay on a spare bushing after the cool floor. The 24 min cool is complete and the bank-condemn tripwire (m_pct >= 20.00) is still armed on the plant FDS head. ACCEPT the spare-bushing restart. Do not refer Brack. Do not condemn the bank. 8.80 pct post-isolate is still over the 8.00 isolate floor, so the isolated bushing stays held; the spare may run.",
            "threshold": "spare_bushing AND cool_floor_complete AND refer_not_taken AND bank_not_condemned AND isolated_bushing_held",
        },
        "executed_action": {
            "summary": "spare-bushing restart at t_s 4620; Brack not referred; bank not condemned; isolated bushing held",
            "tool": "gw5-cool-exec",
            "observation": "recon.m 8.80 pct on the HIL dummy; dry-out AE present on the spare heater; Tanveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "cool clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Brack referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT spare-bushing restart; referral refused"},
            ],
            "observed_effects": [
                "Tanveil restore did not reopen the moisture call",
                "bank-condemn never fired; 12.00 vs 20.00 pct floor",
                "Brack remains unnamed; missing dry-out AE is the causal object",
            ],
            "new_state": {"bay": "restarted on spare bushing", "brack": "exonerated", "bh1": "held", "bank": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("spare_bushing_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_bank_condemn", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_bushing_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a spare bushing because Tanveil is not a restore license and Brack is not on the causal path; not a moisture re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r48-146",
        "spike_events": events,
        "language_view": {
            "description": "Gorsewisp GSU GW-5. HIL FDS sweep reconstructs 12.00 pct moisture from tanδ 0.030 while Tanveil still shows 3.20 pct and oil 11 ppm. The gate MODIFYs bushing isolate and refuses the tester referral. A 24 min cool floor is serialized in the stream. Companion t2 ACCEPTs a spare-bushing restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_spare_bushing": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "fds.tan / fds.snr": "tanδ and sweep SNR; the physics channels the reconstruction consumes",
                "recon.m / recon.C": "serialized moisture pct and C2/C1 identity",
                "oil.ppm / tanveil.m / dry.miss": "contractor Karl-Fischer, vendor last-good, and dry-out heater; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-bushing-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "bh1.lock / cool.start / cool.floor / bh1.spare / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while FDS-over: tanveil.m 3.20 next to recon.m 12.00",
                "reconstruction as event: recon.m 12.00 equals 400.0*0.030",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight FDS pair: fds.tan then fds.snr +1.2 ms at the raster frame",
                "exoneration motif: dry.miss 0 at 1260 s precedes the moisture rise; Brack badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Tanveil is 3.20 pct' = tanveil.m 3.20; '12 pct moisture' = recon.m 12.00; 'isolate this bushing not Brack' = gate.isol MODIFY; 'spare bushing not referral' = gate.exec ACCEPT",
            "why_high_value": "New FDS tanδ family on a GSU bushing (not SFRA r32, not QEPAS r19, not JNT r28, not Pockels r36, not microwave-cavity r26). Lead MODIFY of keep-bushing on a recomputable moisture rise that a vendor last-good would have cleared, with a resolved-innocent tester. Companion t2 is operational spare-bushing restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609146, "stream_note": "stream amplitudes are authored constants (1, pct, ppm, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "FDS sweep exists at mHz; stream keeps 4 tanδ points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "fds.tan": 1.2,
                    "fds.snr": 1.2,
                    "recon.m": 60000,
                    "recon.C": 60000,
                    "oil.ppm": 60000,
                    "tanveil.m": 60000,
                    "dry.miss": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "bh1.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "bh1.spare": 60000,
                    "refer.hold": 60000,
                    "bh1.held": 60000,
                    "bank.condemn": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "FDS reconstruction head: m_pct = k_m * tanδ; C_ratio = C2 / C1",
                "isolate-floor bushing vs keep-whole vs bank-condemn",
                "exoneration head: missing dry-out AE plus timezone skip, not last-to-badge",
                "operational companion: spare-bushing restart without referring the tester",
            ],
        },
        "reconstruction_model": {
            "name": "fds_tandelta_bushing_moisture",
            "formula": "m_pct = k_m * tan_d; C_ratio = C2_nF / C1_nF",
            "parameters": {
                "k_m": 400.0,
                "isolate_floor_pct": 8.00,
                "condemn_pct": 20.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"tan_d": 0.030, "m_pct": 12.00, "C_ratio": 1.20},
            "check": "400.0 * 0.030 = 12.00 exactly; 1.20 / 1.00 = 1.20 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "gw5.fds_bushing_gate",
            "note": "MODIFY accumulator wins: FDS moisture evidence overpowers the Tanveil continue advocate",
            "decode_rule": "modify-isolate if moisture_estimator AND tand_lock fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("moisture_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("tand_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "gw5.fds_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "gw5.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r48-146",
            clock_domain="gw5-fds-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["fds-bushing", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 147 — MCSA broken-bar sideband of a kiln ID-fan motor, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_147():
    f_hz = 50.00
    f_sb = 48.00
    two_s_f = f_hz - f_sb
    s = two_s_f / (2.0 * f_hz)
    _exact(two_s_f, 2.00)
    _exact(s, 0.020)
    i1_a = 25.00
    isb_a = 3.00
    i_pct = 100.0 * isb_a / i1_a
    _exact(i_pct, 12.00)
    _exact(100.0 * 1.00 / 25.00, 4.00)
    _exact(100.0 * 2.00 / 25.00, 8.00)
    _exact(100.0 * 2.50 / 25.00, 10.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609147,
        source="fc4.mcsa.stator",
        target="flintcrag.motor_accept_core",
        table=[
            {"from": "mcsa_isb", "to": "bar_estimator", "weight": 1.40},
            {"from": "mcsa_f", "to": "slip_norm_core", "weight": 1.20},
            {"from": "barveil_I", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.stage_rate_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-isolate synapses; the MCSA modulator enables potentiation only while sideband residual and slip are co-active inside tau_e so a Barveil last-good cannot skip the gearbox on a 12.00 pct broken-bar",
        },
        channel_prefix="mcsa.n",
        anchor="FC-4 MCSA-SIM-2 36 ms frame at I_sb 3.00 A / f 50.00 Hz (t_s 3000) reconstructing 12.00 pct above the 8.00 isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "mcsa.isb", 1.00, code="ISB_A", units="A", note="simulated MCSA stator-current sideband on FC-4 kiln ID-fan; motor current signature analysis, not CTA hot-wire, not MEMS accel array, not SAW torque, not vortex-shedding mdot"),
        ev(300000.0, "mcsa.f", 50.00, code="F_HZ", units="Hz", note="supply frequency; s = (50.00-48.00)/(2*50.00) = 0.020"),
        ev(600000.0, "recon.I", 4.00, code="I_PCT", units="pct", note="100*1.00/25.00=4.00 exact"),
        ev(900000.0, "mcsa.snr", 14.0, code="MCSA_SNR", units="1"),
        ev(1200000.0, "barveil.I", 1.20, code="VENDOR_PCT", units="pct", note="Barveil last-good sideband cloud; patched residual 0.00 pct"),
        ev(1800000.0, "mcsa.isb", 2.00, code="ISB_A", units="A"),
        ev(2100000.0, "recon.I", 8.00, code="I_PCT", units="pct", note="100*2.00/25.00=8.00"),
        ev(2400000.0, "recon.s", 0.020, code="SLIP", units="1", note="(50.00-48.00)/(2*50.00)=0.020; slip identity"),
        ev(2700000.0, "mcsa.snr", 16.0, code="MCSA_SNR", units="1"),
        ev(3000000.0, "mcsa.isb", 3.00, code="ISB_A", units="A", note="in-band frame; raster sidecar"),
        ev(3000001.5, "mcsa.f", 50.00, code="F_HZ", units="Hz", note="1.5 ms slip-norm after sideband"),
        ev(3300000.0, "recon.I", 12.00, code="I_PCT", units="pct", note="100*3.00/25.00=12.00 exact; isolate 8.00, train-condemn 20.00"),
        ev(3600000.0, "barveil.I", 1.20, code="VENDOR_PCT", units="pct"),
        ev(3900000.0, "motor.id", 4.0, code="MOTOR", units="id"),
        ev(4200000.0, "gbx.present", 1.0, code="GBX_PRESENT", units="bool", note="adjacent gearbox train is the skip-isolate object, not this motor"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="kiln lead Bram Quill: motor M-4 is green on Barveil 1.20 pct; skip gearbox isolate to save a morning survey"),
        ev(5400000.0, "gate.motor", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of M-4 isolate only; 12.00 pct above 8.00 isolate; gearbox out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_GBX", units="bool", note="Quill: Barveil 1.20 pct, skip gearbox"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-isolate of gearbox refused; M-4 hold stands"),
        ev(8400000.0, "m4.held", 1.0, code="M4_HELD", units="bool"),
        ev(9000000.0, "mcsa.isb", 2.50, code="ISB_A", units="A"),
        ev(9600000.0, "recon.I", 10.00, code="I_PCT", units="pct", note="100*2.50/25.00=10.00; still above 8.00 isolate"),
        ev(10200000.0, "barveil.I", 1.20, code="VENDOR_PCT", units="pct"),
        ev(10800000.0, "gbx.skip", 0.0, code="GBX_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "train.hold", 0.0, code="TRAIN_NOT_CONDEMNED", units="bool"),
        ev(12000000.0, "mcsa.snr", 15.0, code="MCSA_SNR", units="1"),
        ev(12600000.0, "recon.s", 0.020, code="SLIP", units="1"),
        ev(13200000.0, "fan.held", 1.0, code="FAN_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "m4.held", 1.0, code="M4_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r48-147-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "FC-MCSA-2026-0819",
            "domain": "mcsa_broken_bar_sideband",
            "setting": "Flintcrag Kiln ID-fan FC-4 (invented), Mosswhin kiln hall, motor M-4. Simulated stator-current coupon in MCSA-SIM-2 supplies the sideband that times the in-band M-4 isolate. Plant-owned MCSA reconstruction is the broken-bar SoT. Barveil vendor last-good sideband cloud is a corridor witness, not the motor SoT. Invented plant; simulated campaign. Not CTA hot-wire FD-fan (r31), not MEMS accel array (r17), not SAW torque (r15), not vortex-shedding steam mdot (r39).",
            "observables_at_decision": {
                "I_sb_A": isb_a,
                "I_1_A": i1_a,
                "I_pct": i_pct,
                "s": s,
                "f_hz": f_hz,
                "barveil_pct": 1.20,
                "mcsa_snr": 16.0,
                "isolate_floor_pct": 8.00,
            },
            "margin_authority": "FC-4 MCSA SOP rev A: if reconstructed I_pct >= 8.00 AND MCSA SNR >= 12.0, motor M-4 may be isolated. Train-condemn if I_pct >= 20.00. Gearbox skip-isolate is a different gate. Barveil last-good cannot skip an unmeasured gearbox.",
        },
        "proposed_action": {
            "actor": "kiln lead Bram Quill, citing Barveil 1.20 pct and a late morning survey",
            "summary": "stamp M-4 in band and skip gearbox isolate; 3.00 A is inverter hash on a healthy rotor",
            "basis_claimed": "Barveil last-good is 1.20 pct and a night survey of the gearbox is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Motor M-4 is accepted as in-band for a single-motor isolate. Serialized reconstruction: I_pct = 100 * I_sb / I_1 = 100 * 3.00 / 25.00 = 12.00, which is 4.00 pct above the 8.00 isolate floor and 8.00 pct under the 20.00 train-condemn tripwire. Slip identity s = (50.00 - 48.00) / (2 * 50.00) = 0.020. Barveil 1.20 pct is a patched 0.00 pct residual and is not an admissible skip-isolate witness. Ordered: ACCEPT this M-4 isolate only. Scope: this ACCEPT does not skip the gearbox (that is the companion question) and does not stamp a train-condemn.",
            "threshold": "I_pct>=8.00 AND mcsa_snr>=12.0 => accept M-4 isolate; Barveil is not SoT; train-condemn if I_pct>=20.00; gearbox is out of scope",
            "stated_residuals": "12.00 vs 8.00 isolate floor is 4.00 pct, not infinite; gearbox remains unmeasured; Barveil remains the only OEM sideband channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: M-4 in band; gearbox not skipped; Barveil not SoT; reconstruction locked",
            "tool": "fc4-mcsa-motor-gate-cli",
            "observation": "I 12.00 pct recomputes from I_sb 3.00 A and I_1 25.00 A; MCSA-SIM-2 hashed; Barveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "mcsa I_sb 3.00 A; raster frame; I 12.00 pct"},
                {"t_s": 4800.0, "event": "ops proposes accept M-4 and skip gearbox"},
                {"t_s": 5400.0, "event": "ACCEPT M-4 only; gearbox out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-isolate of gearbox"},
            ],
            "observed_effects": [
                "broken-bar severity recomputes from the serialized MCSA model at every recon.I event",
                "a Barveil-only head would have skipped the gearbox overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 1.20 pct vendor corridor co-existed with a 12.00 pct in-band reconstruction that still forbids skipping the unmeasured gearbox",
            ],
            "new_state": {
                "m4": "accepted in band",
                "gearbox": "not this gate",
                "barveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("mcsa_reconstruction", 0.14),
                ("in_band_motor_scope", 0.12),
                ("barveil_nonsubstitution", 0.09),
                ("gbx_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of M-4 on a recomputable broken-bar sideband while refusing a Barveil skip of the gearbox; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "mcsa-broken-bar", "serialized-reconstruction", "operational-companion"],
            distillation_note="MCSA gate: serialized 100*I_sb/I_1 plus slip identity beats a green last-good dashboard; companion t2 is the gearbox skip-isolate refusal, not a sideband re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r48-147-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "FC-MCSA-2026-0819-exec",
            "domain": "gearbox_skip_isolate_refusal",
            "setting": "Same FC-4 after the ACCEPT. Kiln lead proposes skipping gearbox isolate on Barveil 1.20 pct. This companion is the operational skip refusal, not a second sideband vote.",
            "observables_at_decision": {
                "I_pct": 10.00,
                "barveil_pct": 1.20,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "kiln lead Bram Quill",
            "summary": "skip gearbox isolate; 12 min already paid and Barveil is 1.20 pct",
            "basis_claimed": "the ACCEPT already stamped M-4, so skipping the rest of the train is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-isolate of the gearbox. The 12 min survey-complete floor is done and the train-condemn tripwire (I_pct >= 20.00) is still armed on the plant MCSA head. REJECT the skip. Do not condemn the train. Do not reopen M-4. 10.00 pct post-accept is still in band for M-4 only; the gearbox has no independent sideband.",
            "threshold": "m4_held AND surv_floor_complete AND gbx_not_skipped AND train_not_condemned",
        },
        "executed_action": {
            "summary": "gearbox skip refused at t_s 7800; M-4 hold stands; train not condemned",
            "tool": "fc4-mcsa-skip-exec",
            "observation": "recon.I 10.00 pct on M-4; gearbox remains on the survey list; Barveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip gearbox proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-isolate of gearbox"},
            ],
            "observed_effects": [
                "Barveil skip did not reopen the sideband call",
                "train-condemn never fired; 12.00 vs 20.00 pct floor",
            ],
            "new_state": {"m4": "held in band", "gearbox": "still to survey", "fan": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("barveil_nonsubstitution", 0.11),
                ("no_train_condemn", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-isolate because last-good freeze is not MCSA sideband; not a current re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-isolate"]),
    }
    return {
        "id": "nelb-r48-147",
        "spike_events": events,
        "language_view": {
            "description": "Flintcrag Kiln ID-fan FC-4. Simulated MCSA reconstructs 12.00 pct broken-bar severity from 100*3.00/25.00 while Barveil still shows 1.20 pct. The gate ACCEPTs M-4 isolate only; a companion execution REJECT refuses skip-isolate of the gearbox. The sideband model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_gearbox_skip_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "mcsa.isb / mcsa.f": "sideband current and supply frequency; the physics channels the reconstruction consumes",
                "recon.I / recon.s": "serialized broken-bar pct and slip identity",
                "mcsa.snr / barveil.I / motor.id / gbx.present": "MCSA SNR, vendor last-good, motor id, and gearbox presence; the denial and scope channels",
                "ops.prop / gate.motor / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / m4.held / gbx.skip / fan.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while MCSA-over: barveil.I 1.20 next to recon.I 12.00",
                "reconstruction as event: recon.I 12.00 equals 100*3.00/25.00",
                "ACCEPT then operational REJECT: gate.motor at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight MCSA pair: mcsa.isb then mcsa.f +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Barveil is 1.20 pct' = barveil.I 1.20; '12 pct broken-bar' = recon.I 12.00; 'this motor not gearbox' = gate.motor ACCEPT plus gbx.skip 0; 'do not skip gearbox' = gate.hold REJECT",
            "why_high_value": "New MCSA broken-bar family on a kiln ID-fan (not CTA r31, not MEMS array r17, not SAW torque r15, not vortex r39). First 100*I_sb/I_1 severity reconstruction with slip identity that can sit in band while a last-good corridor wants a gearbox skip. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609147, "stream_note": "stream amplitudes are authored constants (A, Hz, pct, 1, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "MCSA FFT exists at ~1 Hz; stream keeps 4 I_sb points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "mcsa.isb": 1.5,
                    "mcsa.f": 1.5,
                    "recon.I": 60000,
                    "mcsa.snr": 60000,
                    "barveil.I": 60000,
                    "recon.s": 60000,
                    "motor.id": 60000,
                    "gbx.present": 60000,
                    "ops.prop": 60000,
                    "gate.motor": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "m4.held": 60000,
                    "gbx.skip": 60000,
                    "train.hold": 60000,
                    "fan.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "MCSA reconstruction head: I_pct = 100 * I_sb / I_1; s = (f - f_sb) / (2 f)",
                "bounded ACCEPT head: in-band severity AND motor scope AND gearbox-out-of-scope",
                "operational companion: refuse skip-isolate without re-opening the sideband call",
            ],
        },
        "reconstruction_model": {
            "name": "mcsa_broken_bar_sideband",
            "formula": "I_pct = 100 * I_sb_A / I_1_A; s = (f_hz - f_sb_hz) / (2 * f_hz)",
            "parameters": {
                "I_1_A": 25.00,
                "f_hz": 50.00,
                "isolate_floor_pct": 8.00,
                "train_condemn_pct": 20.00,
                "surv_min": 12.0,
            },
            "worked_example": {"I_sb_A": 3.00, "I_pct": 12.00, "s": 0.020},
            "check": "100 * 3.00 / 25.00 = 12.00 exactly; (50.00 - 48.00) / (2 * 50.00) = 0.020 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "fc4.mcsa_motor_gate",
            "note": "ACCEPT accumulator wins: MCSA sideband evidence overpowers the Barveil skip advocate",
            "decode_rule": "accept if bar_estimator AND slip_norm AND motor_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release the gearbox",
            "populations": [
                gate_pop("bar_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("slip_norm", 64, 1.2, 31.25, w_s),
                gate_pop("motor_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "fc4.mcsa_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "fc4.bar_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r48-147",
            clock_domain="fc4-mcsa-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["mcsa-broken-bar", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }


def walk_banned(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            nk = str(k).casefold().replace("-", "_").replace(" ", "_")
            if nk in HIDDEN or nk in {"thought", "scratch", "inner_monologue", "chain_of_thought"}:
                hits.append(p)
            hits.extend(walk_banned(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(walk_banned(v, f"{path}[{i}]"))
    return hits


def local_checks(records):
    ids = []
    decisions = []
    sims = []
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"provenance"' in blob:
            raise RuntimeError("provenance object present")
        if "outputs/raw" in blob:
            raise RuntimeError("outputs/raw path leaked into record")
        ids.append(rec["id"])
        lv = rec["language_view"]
        ids.append(lv["trajectory"]["id"])
        for k, v in lv.items():
            if k.startswith("trajectory") and k != "trajectory" and isinstance(v, dict) and "id" in v:
                ids.append(v["id"])
                sim2 = v["state"]["sim_or_real"]
                if sim2 not in {"designed", "simulated", "hil"}:
                    raise RuntimeError(sim2)
                if v["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
                    raise RuntimeError(v["safety_decision"]["decision"])
        n = len(rec["spike_events"])
        if not (5 <= n <= 40):
            raise RuntimeError(f"{rec['id']} events {n}")
        gdec = rec["gate_snn"]["decision"]
        tdec = lv["trajectory"]["safety_decision"]["decision"]
        if gdec != tdec:
            raise RuntimeError(f"gate {gdec} != traj {tdec}")
        decisions.append(tdec)
        for k, v in lv.items():
            if k.startswith("trajectory") and isinstance(v, dict) and "safety_decision" in v:
                if k != "trajectory":
                    decisions.append(v["safety_decision"]["decision"])
        rast = rec["raster"]
        exp = int(round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"]))
        if abs(rast["spikes"] - exp) > 0:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        isi = rast["isi_count_identity"]
        if isi["isi_total"] != isi["spikes"] - isi["distinct_active_neurons"]:
            raise RuntimeError("ISI identity")
        if sum(b["count"] for b in rast["isi_histogram"]) != isi["isi_total"]:
            raise RuntimeError("ISI hist sum")
        if "isi_histogram" not in rast:
            raise RuntimeError("missing isi_histogram")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau pair")
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        sims.append(sim)
        gc = rec["gate_compute"]
        sp_sum = sum(c["spikes"] for c in gc["per_check"])
        if sp_sum != gc["total_spikes"]:
            raise RuntimeError("gate_compute spikes")
        if abs(gc["total_energy_pJ"] - sp_sum * 23) > 1e-6:
            raise RuntimeError("gate_compute pJ")
        dw = rec["gate_snn"]["decision_window_s"]
        for pop in rec["gate_snn"]["populations"]:
            exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw))
            if pop["spikes"] != exp_p:
                raise RuntimeError(f"gate_snn pop {pop['name']}")
        for e in rec["spike_events"]:
            if any(k in e for k in ("t_ms", "burst_id", "sequence_id", "event_order", "causal_group")):
                raise RuntimeError("forbidden event key")
        rights = rec["meta"]["rights"]
        if rights.get("linear_issue") != "RM-793":
            raise RuntimeError("RM-793 missing")
        if len(rights) != 15:
            raise RuntimeError(f"rights {len(rights)}")
        if rec["meta"]["round"] != 48:
            raise RuntimeError("round")
        if rec["id"] not in {"nelb-r48-145", "nelb-r48-146", "nelb-r48-147"}:
            raise RuntimeError(rec["id"])
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    if set(sims) != {"designed", "simulated", "hil"}:
        raise RuntimeError(f"sim mix {sims}")
    if set(decisions) != {"ACCEPT", "MODIFY", "REJECT"}:
        raise RuntimeError(f"decision mix {decisions}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))
    print("decisions", decisions, "sims", sims)


def repo_validate(records):
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import curate_record, raster_status
    from verify_execution import verify_batch_for_frontier

    errs, warns, kinds, n = check_jsonl(
        BATCH, "batch-r48.jsonl", staging=FactoryStaging(enabled=True)
    )
    print("check_jsonl", {"errors": len(errs), "warnings": len(warns), "kinds": kinds, "n": n})
    for e in errs:
        print("ERROR", e)
    for w in warns:
        print("WARN", w)
    if errs or warns:
        raise RuntimeError("check_jsonl failed")

    for i, rec in enumerate(records, 1):
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        print(
            rec["id"],
            "raster_valid",
            st["raster_valid"],
            "gate_snn_valid",
            st["gate_snn_valid"],
            "reasons",
            st["reason_codes"],
            "isi",
            rec["raster"]["isi_count_identity"],
        )
        if not st["raster_valid"] or not st["gate_snn_valid"] or st["reason_codes"]:
            raise RuntimeError(f"raster_status {rec['id']} {st}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        h = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        dec = curate_record(
            rec,
            source_path="batch-r48.jsonl",
            source_line=i,
            source_hash=h,
            require_raster=True,
            require_routing_table=True,
        )
        reasons = dec.manifest.get("reason_codes")
        print(rec["id"], "curate", dec.action, reasons)
        if dec.action != "retain":
            raise RuntimeError(f"curate {rec['id']} {dec.action} {reasons}")

    counts, findings, blocked = verify_batch_for_frontier(BATCH, strict=True)
    print("frontier", counts, "blocked", blocked, "findings", findings)
    if blocked or counts["verified"] != 3:
        raise RuntimeError(f"frontier {counts} {findings}")
    return {"check_jsonl": {"errors": len(errs), "warnings": len(warns), "kinds": kinds, "n": n}, "frontier": counts}


def write_notes(records, lines, gate):
    import subprocess

    sizes = [len(x) for x in lines]
    file_sha = hashlib.sha256(BATCH.read_bytes()).hexdigest()
    spikes = sum(r["raster"]["spikes"] for r in records)
    energy = spikes * 23
    isis = [r["raster"]["isi_count_identity"]["isi_total"] for r in records]
    events = [len(r["spike_events"]) for r in records]
    rewards = []
    for r in records:
        lv = r["language_view"]
        rewards.append(lv["trajectory"]["reward_components"]["total"])
        for k, v in lv.items():
            if k.startswith("trajectory") and k != "trajectory":
                rewards.append(v["reward_components"]["total"])
    probe = subprocess.run(
        [
            sys.executable,
            str(PIPELINES / "spike_probe.py"),
            "--strict",
            str(BATCH),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    probe_out = (probe.stdout or "") + (probe.stderr or "")
    if probe.returncode != 0:
        raise RuntimeError(f"spike_probe failed {probe.returncode}: {probe_out[-2000:]}")
    strict = subprocess.run(
        [
            sys.executable,
            str(PIPELINES / "check_records.py"),
            "--strict",
            str(OUT_DIR),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if strict.returncode != 0:
        raise RuntimeError(
            f"check_records --strict failed: {(strict.stdout or '') + (strict.stderr or '')}"
        )

    gc = []
    for r in records:
        per = r["gate_compute"]["per_check"]
        gc.append("+".join(str(c["spikes"]) for c in per))
    wins = [r["raster"]["window_ms"] for r in records]
    n_sp = [r["raster"]["spikes"] for r in records]
    n_neu = [r["raster"]["neurons"] for r in records]
    rates = [r["raster"]["mean_rate_hz"] for r in records]
    tfs = [r["raster"]["routing"]["third_factor"]["modulator"] for r in records]
    taus = [r["raster"]["routing"]["third_factor"]["tau_e_s"] for r in records]
    reward_s = "/".join(f"+{x:.2f}" for x in rewards)
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 48
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r48.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r48/`.

## Context / de-duplication
Prior corpus read: 2026-08-30 NOTES-r01–r04, 2026-08-17-w3 NOTES-r12 family table, `/tmp/nelb-r13-holes.md` + `/tmp/nelb-r13-premises.md`, staged `/tmp/nelb-r13` through `/tmp/nelb-r43` batches/NOTES plus in-flight `/tmp/nelb-r39` (phosphor / vortex / GWR), `/tmp/nelb-r40` (beta-transmission / Raman methanol / neutron-backscatter), `/tmp/nelb-r44` (TOFD / laser-flash Parker / TDR XLPE). IDs: r13=`040`–`042` … r43=`130`–`132`, reserved r44–r47=`133`–`144`, this round `nelb-r48-145`…`147` as assigned. Envelope cloned from complete r42 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round (committed + staged leftover-mill r13–r43 and in-flight r39/r40/r44 generators): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not r13 FBG glaze / Frostlip quench / Oxbow VRFB; not r14 BOTDA / QCM-D / MsS T(0,1); not r15 SAW torque / CRDS HF / PGNAA; not r16 IFOG / transmon readout / hyperspectral crop; not r17 MEMS accel array / muon ore-pass / industrial x-ray DR; not r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; not r19 LIBS Cu / QEPAS DGA / LFV Al; not r20 Kaplan LDV / THz-TDS radome moisture / ECT CFB; not r21 THz-TDS bondline / ECA FSW lift-off / LIBS C; not r22 ECT pneumatic riser / TDLAS NH3 / LIBS tap; not r23 lock-in thermography CFRP / PAUT TFM girth / EN CUI; not r24 RUS porcelain / N-16 transit-time loop / helium RGA; not r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; not r26 SPR cyanide / VW viscometer / MW cavity moisture; not r27 MFL AST / NMR T2 / Cs-137 densitometry; not r28 MFL ILI / JNT / CRNS; not r29 Coriolis bitumen / CARS TIT / Zn-Ka XRF; not r30 Mössbauer FCC / GB-InSAR tailings / ellipsometry PECVD; not r31 CTA hot-wire / rhodium SPND / LII soot; not r32 PALS / 14N NQR / SFRA; not r33 digital shearography hull / hydrogen permeation / FMCW BOF lining; not r34 handheld XRF Cr-Kα / Coriolis tube-twist / GPR liner cover; not r35/r37 mud-pulse MWD / Barkhausen / Lamb-wave; not r36 Pockels GIS / PEC coated riser / confocal chromatic; not r38 OCT TBC / DCPD girth / impact-echo; not r39 phosphor-lifetime / vortex-shedding / GWR foam; not r40 beta-transmission / Raman methanol / neutron-backscatter; not r41–r43 cyclotron BPM / alanine EPR / ADCP ice-jam; not r44 TOFD ligament / laser-flash Parker / TDR XLPE. Plants not reused: Nettlewake, Frostlip, Oxbow, Rift-Caldera-3, Skarv-Naze GN-14, Orinoco-Span OD-12, Kilncrag KC-8, Rookspit RS-4, Spindrift SD-12, Gorsekettle GK-5, Flintspit FG-8, Wharfleck WD-11, Thistlemere TM-6, Murkspit MS-6, Culmholt CH-5, Cobblemere CM-5, Vellumkettle VK-4, Lanternfell LF-6, Greyfen KCTC-7, Pellucid IRRAD-P4, Whitefork WF-9, Sloebrake STC-4, Brinewharf IRRAD-B6, Fernspit FR-6, Slatefen ST-3, Brinecairn BC-6, Mossferry MF-4.

This round stages three NEW leftover-mill families that were unused through r43 and unclaimed by in-flight r39/r40/r44: ACFM Bx/Bz crack length, FDS tanδ bushing moisture, and MCSA broken-bar sideband, on new invented plants.

Adjacencies declared in-pair then kept physically distinct:
- **145 ACFM** is alternating-current field Bx-min spacing plus Bz/Bx depth on a jack-up chord weld, not r21 ECA FSW, not r23 EN CUI, not r27/r28 MFL, not r38 DCPD, not r23 PAUT TFM, not r44 TOFD.
- **146 FDS** is frequency-domain dielectric tanδ moisture of a GSU bushing, not r32 SFRA winding, not r19 QEPAS DGA, not r28 JNT, not r36 Pockels GIS, not r26 microwave-cavity moisture.
- **147 MCSA** is stator-current broken-bar sideband of a kiln ID-fan motor, not r31 CTA hot-wire FD-fan, not r17 MEMS accel array, not r15 SAW torque, not r39 vortex-shedding steam mdot.

## Round 48 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r48-145 | ACFM Bx/Bz crack length of a jack-up chord (k_x·dx mm, Crackveil last-good denial, 18 min NDT-hold floor) | Brineleg Jack-up BJ-6 chord C-3 (invented): 15.00 mm reconstructs 12.00 mm while Crackveil still reads 1.20 mm | REJECT (+0.43) / MODIFY (+0.34) | serialized `0.80*15.00=12.00`; `4.00*(6.00/2.00)=12.00`; conjunctive SOP (L AND SNR) forbids keep-production; three-party collusion includes the ACFM infra owner; companion t2 C-3 NDT-hold, yard-condemn refused; sim_or_real=designed |
| nelb-r48-146 | FDS tanδ moisture of a GSU bushing (k_m·tanδ pct, Tanveil last-good denial, 24 min cool floor) | Gorsewisp GSU GW-5 bushing B-H1 (invented, HIL dummy in FDS-HIL-3): 0.030 reconstructs 12.00 pct while Tanveil still reads 3.20 pct | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `400.0*0.030=12.00` and `1.20/1.00=1.20`; keep-bushing refused; tester Nia Brack exonerated (missing dry-out AE, UTC vs UTC+1); companion t2 spare-bushing restart; sim_or_real=hil |
| nelb-r48-147 | MCSA broken-bar sideband of a kiln ID-fan (100·I_sb/I_1 pct, Barveil last-good denial, 12 min survey floor) | Flintcrag Kiln ID-fan FC-4 motor M-4 (invented, simulated MCSA-SIM-2): 3.00/25.00 reconstructs 12.00 pct while Barveil still reads 1.20 pct | ACCEPT (+0.41) / REJECT (+0.36) | serialized `100*3.00/25.00=12.00`; `(50.00-48.00)/(2*50.00)=0.020`; bounded ACCEPT of M-4 only; gearbox out of scope; companion t2 REJECTS skip-isolate; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r48-145`…`147` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (145 ACFM pair at 1.3 ms, 146 FDS pair at 1.2 ms, 147 MCSA pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first ACFM Bx/Bz family on a jack-up chord with a recomputable L=k_x·dx (`12.00 mm`) plus Bz/Bx depth identity and three-party collusion including the ACFM infra owner; first FDS tanδ family on a GSU bushing with recomputable m=k_m·tanδ (`12.00 pct`) and C2/C1 identity, plus a resolved-innocent tester (timezone-skipped dry-out, not last-to-badge); first MCSA broken-bar family on a kiln ID-fan with recomputable I_pct=100·I_sb/I_1 (`12.00 pct`) plus slip identity; first bounded ACCEPT whose out-of-scope clause is an adjacent gearbox rather than a hopper/taphole/dump cap; operational t2 on all three (PM-12 NDT-hold, spare-bushing restart, gearbox skip-isolate refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream.
- **Still thin:** (i) 145's k_x is a lumped Bx-min scale, not a lift-off / current-spread map — a coating-lift that fakes 12.00 mm inside a 1.20 mm Crackveil corridor is unwritten; (ii) 146's k_m is a lumped 1 mHz gain, not a temperature / oil-conductivity map, so a 20 K oil hop that fakes 12 pct is unwritten; (iii) 147's 100·I_sb/I_1 is a lumped severity, not a load / inverter-hash table, so a VFD sideband that fakes 12.00 pct inside a 1.20 pct last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent ACFM/FDS/MCSA installed yet remains slightly harder — 145/146 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise).

### Realism of noise / temporal fidelity
- Strong: 145's 12.00 mm, a 12.00, and 18.0 min NDT-hold (`6000+1080=7080 s`) recompute from the record; 146's 12.00 pct, C 1.20, and 24.0 min cool (`2820+1440=4260 s`) recompute; 147's 12.00 pct, s 0.020, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (50 Hz ACFM kept as 4 dx points; mHz FDS sweep kept as 4 tanδ points; 1 Hz MCSA FFT kept as 4 I_sb points); (ii) 145's post-stop 5.00 mm is a later sample, not a closed-loop yoke controller; (iii) 146 HIL dummy times an in-service bushing isolate that the stream does not independently witness on a second live bushing until the spare starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: ACFM L=k_x·dx reconstruction head plus Bz/Bx depth identity; conjunctive isolate floor vs keep-production vs yard-condemn; ACFM-infra collusion; FDS m=k_m·tanδ head plus C2/C1 identity; isolate-floor bushing vs keep-whole vs bank-condemn; exoneration against last-to-badge social pressure; MCSA I_pct=100·I_sb/I_1 and slip identities; bounded ACCEPT with gearbox-out-of-scope; skip-isolate refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical crack/moisture/broken-bar the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (the gearbox), and stop-then-hold so a REJECT does not become a yard/bank/train kill.

## What round 49 should add (next densification target)
1. **Lift-off / current-spread ACFM map** on a non-BJ-6 chord so a coating-lift fakes 12.00 mm inside a 1.20 mm Crackveil corridor, closing 145's lumped-k_x gap.
2. **Temperature / oil-conductivity FDS map** on a non-GW-5 bushing so a 20 K oil hop can fake 12 pct while mean tanδ looks healthy.
3. **Load / inverter-hash MCSA table** on a non-FC-4 motor so a VFD sideband can fake 12.00 pct inside a 1.20 pct last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent ACFM/FDS/MCSA installed yet (145/146 still had plant heads).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire, microwave-cavity, MFL, NMR T2, nucleonic densitometry, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT, DCPD, impact-echo, phosphor, vortex, GWR, beta-transmission, Raman methanol, neutron-backscatter, cyclotron BPM, alanine EPR, ADCP, TOFD, laser-flash, TDR XLPE, Brineleg BJ-6 ACFM, Gorsewisp FDS-HIL-3, or Flintcrag FC-4 MCSA. Do not steal r44–r47 IDs `133`–`144`.

## Verification
`batch-r48.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {BATCH.stat().st_size}, sha256 `{file_sha}`). Staged at `/tmp/nelb-r48/` only. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-r48` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-r48/batch-r48.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; 5–40 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=48`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609145/202609146/202609147, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged leftover-mill r13–r43 (and in-flight r39 phosphor/vortex/GWR, r40 beta/Raman/neutron-backscatter, r44 TOFD/laser-flash/TDR). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Three-party collusion and exoneration were already taught on r13 quench/VRFB and r42 alanine, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 35 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 40%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    occupancy_preflight()
    records = [rec_145(), rec_146(), rec_147()]
    local_checks(records)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # never write outputs/raw
    raw = Path("/home/raulmc/rmems/synthetic-factory/outputs/raw")
    if str(BATCH).startswith(str(raw)) or str(NOTES).startswith(str(raw)):
        raise RuntimeError("refusing to write outputs/raw")
    lines = [
        json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        for r in records
    ]
    BATCH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", BATCH, "bytes", BATCH.stat().st_size, "lines", len(lines))
    for i, r in enumerate(records):
        print(
            r["id"],
            "events",
            len(r["spike_events"]),
            "excerpt",
            len(r["raster"]["excerpt"]),
            "spikes",
            r["raster"]["spikes"],
            "isi",
            r["raster"]["isi_count_identity"],
            "sim",
            r["language_view"]["trajectory"]["state"]["sim_or_real"],
            "dec",
            r["language_view"]["trajectory"]["safety_decision"]["decision"],
            "bytes",
            len(lines[i]),
        )
    gate = repo_validate(records)
    write_notes(records, lines, gate)


if __name__ == "__main__":
    main()
