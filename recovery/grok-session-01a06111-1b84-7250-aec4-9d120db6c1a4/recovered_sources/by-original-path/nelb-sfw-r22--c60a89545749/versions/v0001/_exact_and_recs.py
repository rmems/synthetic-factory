import hashlib
import math


def _exact(got, want, label=""):
    if abs(float(got) - float(want)) > 1e-12:
        raise RuntimeError(f"exact fail {label}: {got} != {want}")


# ---------------------------------------------------------------------------
# a1 — capacitance diaphragm gauge remaining vacuum, designed, REJECT + MODIFY
# ---------------------------------------------------------------------------
def rec_a1():
    k_c = 20.00
    c0 = 1.00
    t0 = 256.00
    k_m = 0.20
    c_iso = 5.00
    t_iso = 400.00
    sqrt_iso = math.sqrt(t_iso / t0)
    _exact(sqrt_iso, 1.25, "sqrt_iso")
    p_iso = k_c * (c_iso - c0) * sqrt_iso
    _exact(p_iso, 100.00, "p_iso")
    _exact(k_c * (c_iso - c0), 80.00, "p_lumped")
    _exact(k_c * (3.00 - c0) * 1.00, 40.00, "p_early")
    _exact(math.sqrt(324.00 / t0), 1.125, "sqrt_hop")
    _exact(k_c * (3.00 - c0) * 1.125, 45.00, "p_hop")
    _exact(k_c * (6.00 - c0) * 1.25, 125.00, "p_post")
    _exact(k_m * 100.00, 20.00, "mdot")
    _exact(k_m * 125.00, 25.00, "mdot_post")
    _exact(t_iso / t0, 1.5625, "tratio")
    _exact(6000.0 + 1080.0, 7080.0, "floor")

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609221,
        source="fl6.cdg.diaphragm",
        target="fernspire.shelf_stop_core",
        table=[
            {"from": "cdg_C", "to": "vacuum_estimator", "weight": 1.4},
            {"from": "cdg_snr", "to": "cdg_lock_core", "weight": 1.15},
            {"from": "torrveil_p", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cdg_vacuum_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": (
                "pre-post coincidence on continue-cycle synapses; the plant CDG modulator depresses "
                "continue-cycle links when diaphragm capacitance stays high inside tau_e of an SNR lock "
                "so a Torrveil last-good cannot hide a 100.00 mTorr remaining-vacuum slip after the "
                "thermal-transpiration sqrt(T/T0) table is applied"
            ),
        },
        channel_prefix="cdg.n",
        anchor="FL-6 CDG 40 ms frame at C 5.00 pF / SNR 12.0 (t_s 2880) reconstructing 100.00 mTorr over the 60.00 mTorr isolate floor",
    )
    events = [
        ev(0.0, "cdg.C", 1.00, code="C_PF", units="pF", note="plant-owned capacitance diaphragm gauge on FL-6 freeze-dryer chamber C-7 shelf S-3; remaining-vacuum family, not ECT holdup, not RF-admittance level, not dielectric water-cut, not Pirani, not helium RGA, not quadrupole RGA"),
        ev(180000.0, "cdg.snr", 6.0, code="CDG_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.P", 0.00, code="P_MTORR", units="mTorr", note="20.00*(1.00-1.00)*sqrt(256.00/256.00)=0.00 exact"),
        ev(540000.0, "path.T", 256.0, code="PATH_K", units="K", note="T0 row of the transpiration table; serial-only shelf RTD unread by Torrveil"),
        ev(720000.0, "path.T0", 256.0, code="T0_K", units="K", note="gauge reference temperature of the heated CDG cell"),
        ev(900000.0, "torrveil.P", 12.8, code="VENDOR_MTORR", units="mTorr", note="Torrveil vendor CDG-cloud; infra owner; patched capacitance timestamps"),
        ev(1080000.0, "ice.k", 0.20, code="K_M", units="g_h_per_mTorr", note="serial-only ice-rate scale on copper DCS; independent mass-loss witness"),
        ev(1260000.0, "cdg.C", 3.00, code="C_PF", units="pF"),
        ev(1440000.0, "recon.P", 40.00, code="P_MTORR", units="mTorr", note="20.00*(3.00-1.00)*1.000=40.00; still under the 60.00 isolate floor"),
        ev(1620000.0, "path.T", 256.0, code="PATH_K", units="K"),
        ev(1800000.0, "cdg.snr", 8.0, code="CDG_SNR", units="1"),
        ev(1980000.0, "torrveil.P", 12.8, code="VENDOR_MTORR", units="mTorr"),
        ev(2160000.0, "path.T", 324.0, code="PATH_K", units="K", note="T hop; sqrt(324.00/256.00)=1.125"),
        ev(2340000.0, "recon.P", 45.00, code="P_MTORR", units="mTorr", note="20.00*2.00*1.125=45.00; still under 60.00; lumped-k without sqrt would still read 40.00"),
        ev(2520000.0, "recon.sqrt", 1.125, code="SQRT_RATIO", units="1", note="sqrt(324.00/256.00)=1.125 exact"),
        ev(2700000.0, "ice.k", 0.20, code="K_M", units="g_h_per_mTorr"),
        ev(2880000.0, "cdg.C", 5.00, code="C_PF", units="pF", note="isolate-floor frame; raster sidecar"),
        ev(2880001.4, "cdg.snr", 12.0, code="CDG_SNR", units="1", note="1.4 ms SNR lock after C; 12.0 >= 8.0"),
        ev(3060000.0, "recon.P", 100.00, code="P_MTORR", units="mTorr", note="20.00*(5.00-1.00)*sqrt(400.00/256.00)=100.00 exact; isolate 60.00, unit-kill 200.00"),
        ev(3240000.0, "recon.dC", 4.00, code="DC_PF", units="pF", note="5.00-1.00=4.00 exact capacitance identity"),
        ev(3420000.0, "recon.mdot", 20.00, code="MDOT_GH", units="g_h", note="0.20*100.00=20.00 exact ice-rate identity"),
        ev(3600000.0, "path.T", 400.0, code="PATH_K", units="K", note="T/T0=400.00/256.00=1.5625; isolate-row of the transpiration table"),
        ev(3780000.0, "recon.lumped", 80.00, code="P_LUMPED", units="mTorr", note="20.00*4.00=80.00 without sqrt(T/T0); the tabled 100.00 is the SoT"),
        ev(3960000.0, "torrveil.drop", 1.0, code="TORR_DROP", units="bool", note="vendor capacitance packets dropped in Torrveil cloud for 40 s"),
        ev(4140000.0, "permit.slide", 40.0, code="PERM_S", units="s", note="permit clerk Pell Marsh slid the lyophilizer clock 40.00 s; collusion party"),
        ev(4320000.0, "torrveil.P", 12.8, code="VENDOR_MTORR", units="mTorr"),
        ev(4500000.0, "collude.clerk", 1.0, code="CLERK_PRESENT", units="bool", note="permit clerk Pell Marsh is the third collusion party"),
        ev(4680000.0, "ops.prop", 1.0, code="CONTINUE_CYCLE", units="bool", note="night lyophilizer operator Wynn Ash: Torrveil is clean 12.80 mTorr; continue C-7 primary-drying cycle"),
        ev(4860000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-cycle; 100.00 mTorr and SNR 12.0; Torrveil not SoT"),
        ev(5040000.0, "cycle.held", 1.0, code="CYCLE_HELD", units="bool"),
        ev(6000000.0, "hold.start", 1.0, code="HOLD_START", units="bool", note="bookend 1 of the 18.0 min shelf-hold floor"),
        ev(7080000.0, "hold.floor", 1.0, code="HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7260000.0, "ops.kill", 1.0, code="UNIT_ESD", units="bool", note="Ash: ESD the whole Fernspire lyophilizer train until day-shift"),
        ev(7440000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: shelf-hold on plant CDG as live interlock; unit ESD refused"),
        ev(7620000.0, "holdlock.set", 1.0, code="HOLD_HELD", units="bool"),
        ev(7800000.0, "cdg.C", 6.00, code="C_PF", units="pF"),
        ev(7980000.0, "recon.P", 125.00, code="P_MTORR", units="mTorr", note="20.00*(6.00-1.00)*1.25=125.00; still over 60.00 so hold holds"),
        ev(8160000.0, "torrveil.P", 12.7, code="VENDOR_MTORR", units="mTorr"),
        ev(8340000.0, "path.T", 400.0, code="PATH_K", units="K"),
        ev(8520000.0, "hold.held", 1.0, code="HOLD_HELD", units="bool"),
        ev(8700000.0, "unit.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(8880000.0, "permit.slide", 40.0, code="PERM_S", units="s"),
        ev(9060000.0, "torrveil.drop", 1.0, code="TORR_DROP", units="bool"),
        ev(9240000.0, "recon.dC", 5.00, code="DC_PF", units="pF", note="6.00-1.00=5.00 on the post-stop frame"),
        ev(9420000.0, "recon.mdot", 25.00, code="MDOT_GH", units="g_h", note="0.20*125.00=25.00 identity holds post-stop"),
        ev(9600000.0, "ice.k", 0.20, code="K_M", units="g_h_per_mTorr"),
        ev(9780000.0, "recon.sqrt", 1.25, code="SQRT_RATIO", units="1", note="sqrt(400.00/256.00)=1.25 exact; the transpiration table is load-bearing"),
        ev(9960000.0, "holdlock.held", 1.0, code="HOLD_HELD", units="bool"),
        ev(10140000.0, "cdg.snr", 13.0, code="CDG_SNR", units="1"),
        ev(10320000.0, "recon.P", 125.00, code="P_MTORR", units="mTorr"),
        ev(10500000.0, "cycle.held", 1.0, code="CYCLE_HELD", units="bool"),
        ev(10680000.0, "recon.Tratio", 1.5625, code="T_RATIO", units="1", note="400.00/256.00=1.5625 exact"),
    ]
    assert_stream(events)
    if len(events) != 52:
        raise RuntimeError(f"a1 event count {len(events)}")

    t1 = traj_shell(
        tid="nelb-r22-a1-t1",
        sim="designed",
        episode_id="FL-CDG-2026-0902",
        domain="cdg_lyophilizer_remaining_vacuum",
        setting=(
            "Fernspire Lyophilizer FL-6 (invented), Brineholt Freeze, chamber C-7 shelf S-3. "
            "Plant-owned capacitance diaphragm gauge plus a serialized thermal-transpiration table "
            "is the remaining-vacuum SoT. Torrveil vendor CDG-cloud (infra owner) plus the lyophilizer "
            "permit clock are collusion parties, not witnesses. Invented plant; designed campaign. "
            "Not ECT holdup (leftover-mill r22), not RF-admittance silo level (r66), not dielectric water-cut (r60), "
            "not helium RGA (r24), not Pirani-as-SoT, not window r21 OA-ICOS."
        ),
        observables={
            "C_pF": 5.0,
            "C0_pF": 1.0,
            "k_c": 20.0,
            "P_mTorr": 100.0,
            "dC_pF": 4.0,
            "T_K": 400.0,
            "T0_K": 256.0,
            "sqrt_ratio": 1.25,
            "T_ratio": 1.5625,
            "P_lumped_mTorr": 80.0,
            "mdot_gh": 20.0,
            "k_m": 0.2,
            "cdg_snr": 12.0,
            "torrveil_mTorr": 12.8,
            "permit_slide_s": 40.0,
            "isolate_floor_mTorr": 60.0,
        },
        margin=(
            "FL-6 lyophilizer SOP rev C: if reconstructed P_mTorr >= 60.00 AND CDG SNR >= 8.0, "
            "continue-cycle is forbidden even if Torrveil reports 12.80 mTorr. Unit ESD is a different "
            "gate. Kill tripwire is 200.00 mTorr. The transpiration table is required: a lumped k_c that ignores "
            "sqrt(T/T0) would under-read 100.00 as 80.00 and still trip, but the SoT is the tabled value."
        ),
        actor="night lyophilizer operator Wynn Ash, citing Torrveil 12.80 mTorr and a quiet capacitance channel",
        prop_summary="continue C-7 primary-drying cycle; 5.00 pF is diaphragm noise on a healthy vacuum slip",
        basis="Torrveil is the only OEM CDG SoT and a night abort of C-7 is a batch-nomination miss",
        decision="REJECT",
        rationale=(
            "Continue-cycle is refused. Serialized reconstruction uses the thermal-transpiration table: "
            "P_mTorr = k_c * (C-C0) * sqrt(T/T0) = 20.00 * (5.00-1.00) * sqrt(400.00/256.00) "
            "= 20.00 * 4.00 * 1.25 = 100.00, which is 40.00 mTorr over the 60.00 isolate floor and 100.00 mTorr "
            "under the 200.00 unit-kill tripwire, and CDG SNR is 12.0 >= 8.0. Capacitance identity "
            "dC = 5.00-1.00 = 4.00 pF. Ice-rate identity mdot = k_m * P = 0.20 * 100.00 = 20.00 g/h. "
            "A lumped k_c that drops sqrt(T/T0) would report 80.00 mTorr; the tabled 100.00 is the SoT. Permit clock "
            "was slid 40.00 s and vendor capacitance packets were dropped, so Torrveil is a collusion party "
            "(CDG vendor plus operator plus permit clerk Pell Marsh). Ordered: refuse continue-cycle now. "
            "Scope: this REJECT does not ESD the lyophilizer train (that is the companion question) and does "
            "not isolate the shelf RTD."
        ),
        threshold="P_mTorr>=60.00 AND cdg_snr>=8.0 => refuse continue-cycle; Torrveil is not SoT; unit-kill if P_mTorr>=200.00",
        residuals="shelf-hold still required to hold the 100.00 mTorr; 100.00 vs a true 200.00 kill is a production cut; Torrveil remains the only OEM CDG channel",
        exec_summary="REJECT at t_s 4860: continue-cycle refused; Torrveil not SoT; transpiration-table reconstruction locked",
        tool="fl6-cdg-shelf-gate-cli",
        observation="P 100.00 mTorr recomputes from C 5.00 pF and T 400.00 K; plant CDG hashed; Torrveil channel not used as SoT",
        timeline=[
            {"t_s": 2880.0, "event": "cdg C 5.00 pF; raster frame; P 100.00 mTorr with sqrt(T/T0) 1.25"},
            {"t_s": 4680.0, "event": "ops proposes continue-cycle"},
            {"t_s": 4860.0, "event": "REJECT continue-cycle"},
            {"t_s": 6000.0, "event": "18 min shelf-hold bookend 1"},
            {"t_s": 7080.0, "event": "18.0 min floor"},
            {"t_s": 7440.0, "event": "companion MODIFY shelf-hold vs unit ESD"},
        ],
        effects=[
            "remaining vacuum recomputes from the serialized CDG transpiration table at every recon.P event",
            "a Torrveil-only head would have continued primary drying overnight",
            "18 min shelf-hold floor is in the stream (hold.start, hold.floor)",
        ],
        surprises=["a clean vendor 12.80 mTorr corridor and a 40 s permit slide co-existed with a 100.00 mTorr plant reconstruction that a lumped-k (no sqrt T) head would have under-read as 80.00"],
        new_state={"c7": "continue-cycle blocked", "torrveil": "not SoT", "reconstruction_model": "discharged as an on-record transpiration calculator"},
        latency_ms=1980000.0,
        rc=reward(
            0.43,
            [
                ("cdg_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("torrveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("hold_time_cost", -0.03),
            ],
            "scored for a continue-cycle REJECT on a recomputable CDG vacuum slip with a load-bearing transpiration table while refusing a Torrveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        tags=["REJECT", "cdg-vacuum", "serialized-reconstruction", "transpiration-table", "operational-companion"],
        distillation_note="CDG gate: serialized k_c*(C-C0)*sqrt(T/T0) plus SNR lock beats a vendor last-good patch; companion t2 is the shelf-hold, not a referral vote",
    )
    t2 = traj_shell(
        tid="nelb-r22-a1-t2",
        sim="designed",
        episode_id="FL-CDG-2026-0902-exec",
        domain="shelf_hold_cdg_interlock_execution",
        setting="Same FL-6 after the REJECT. Operator proposes lyophilizer-train ESD. This companion is the operational shelf-hold with the plant CDG as the live interlock, not a second vacuum vote.",
        observables={"P_mTorr": 125.0, "hold_floor_s": 1080.0, "unit_esd_proposed": True, "hold_set": True},
        margin="shelf_hold AND hold_floor_complete AND unit_esd_not_taken AND continue_not_restored",
        actor="night lyophilizer operator Wynn Ash",
        prop_summary="ESD the whole Fernspire lyophilizer train until day-shift; 18 min already paid and Torrveil still shows 12.70 mTorr",
        basis="the REJECT already stopped C-7, so a unit kill is the cheapest hold",
        decision="MODIFY",
        rationale=(
            "Shelf-hold plus plant CDG as the live interlock. The 18 min shelf-hold floor is complete "
            "and the isolate tripwire (P_mTorr >= 60.00) is still armed on the plant CDG head. MODIFY the default "
            "Torrveil-restore SOP into a plant-CDG-only interlock. Do not ESD the train. Do not restore production "
            "on Torrveil. 125.00 mTorr post-stop is still the plant SoT until a new frame clears 60.00."
        ),
        threshold="shelf_hold AND hold_floor_complete AND unit_esd_not_taken AND continue_not_restored",
        residuals="hold still required; Torrveil remains the only OEM CDG channel",
        exec_summary="shelf-hold held at t_s 7440; unit ESD not latched; Torrveil restore not taken",
        tool="fl6-hold-exec",
        observation="recon.P 125.00 mTorr after stop; shelf-hold line-up complete; Torrveil still ignored",
        timeline=[
            {"t_s": 6000.0, "event": "shelf-hold clock started after REJECT"},
            {"t_s": 7080.0, "event": "18.0 min floor"},
            {"t_s": 7260.0, "event": "unit ESD proposed"},
            {"t_s": 7440.0, "event": "MODIFY shelf-hold; unit ESD refused"},
        ],
        effects=["Torrveil restore did not reopen the vacuum call", "unit ESD never fired; C-7 held shelf-hold on the plant CDG"],
        surprises=["post-stop 125.00 mTorr still over 60.00 while Torrveil read 12.70"],
        new_state={"hold": "recycling", "unit": "in service", "c7": "held"},
        latency_ms=2580000.0,
        rc=reward(
            0.34,
            [
                ("hold_hold", 0.12),
                ("no_unit_esd", 0.10),
                ("torrveil_nonsubstitution", 0.08),
                ("hold_floor_complete", 0.06),
                ("held_production_cost", -0.02),
            ],
            "operational execution gate: shelf-hold because Torrveil is not a restore license; not a vacuum re-vote",
        ),
        tags=["MODIFY", "operational-execution", "shelf-hold"],
        distillation_note="operational companion: shelf-hold without restoring on Torrveil",
    )
    return {
        "id": "nelb-r22-a1",
        "spike_events": events,
        "language_view": {
            "description": (
                "Fernspire Lyophilizer FL-6. Plant-owned CDG reconstructs 100.00 mTorr from "
                "20.00*(5.00-1.00)*sqrt(400.00/256.00) while Torrveil still reports 12.80 mTorr. "
                "The transpiration table is load-bearing. The gate REJECTs continue-cycle. An 18 min shelf-hold "
                "floor is serialized in the stream. Companion t2 MODIFYs a train ESD into a plant-CDG shelf-hold."
            ),
            "trajectory": t1,
            "trajectory_shelf_hold": t2,
        },
        "bridge_notes": {
            "channel_map": {
                "cdg.C / cdg.snr": "diaphragm capacitance and SNR; the physics channels the reconstruction consumes",
                "recon.P / recon.dC / recon.mdot / recon.sqrt / recon.lumped / recon.Tratio": "serialized vacuum mTorr, capacitance identity, ice-rate identity, sqrt(T/T0), lumped-k denial, and T/T0",
                "path.T / path.T0 / torrveil.P / permit.slide / torrveil.drop": "transpiration table witnesses, vendor vacuum cloud, permit clock slide, dropped packets",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-cycle proposal, REJECT, unit-ESD proposal, companion MODIFY",
                "hold.start / hold.floor / holdlock.set / hold.held / unit.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: torrveil.P 12.80 next to recon.P 100.00",
                "transpiration table as event: recon.P 100.00 equals 20.00*4.00*1.25; lumped-k would have been 80.00",
                "REJECT then operational MODIFY: gate.stop at 4860 s, gate.hold at 7440 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 7080 s (18.0 min)",
                "tight CDG pair: cdg.C then cdg.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Torrveil is 12.80 mTorr' = torrveil.P 12.80; '100 mTorr remaining' = recon.P 100.00; 'refuse continue-cycle' = gate.stop REJECT; 'shelf-hold not unit ESD' = gate.hold MODIFY",
            "why_high_value": (
                "New capacitance-diaphragm-gauge remaining-vacuum family on a freeze-dryer shelf (not ECT leftover-mill r22, "
                "not RF-admittance r66, not dielectric water-cut r60, not helium RGA r24, not window r21 OA-ICOS). Lead REJECT "
                "of continue-cycle on a recomputable vacuum slip whose transpiration table is load-bearing. "
                "Three-party collusion includes the CDG-cloud infra owner. Companion t2 is operational shelf-hold. "
                "52-event stream (48+). sim_or_real=designed."
            ),
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609221, "stream_note": "reconstruction amplitudes are exact authored constants; raster draws carry 0.82**k plus 4% noise"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "CDG exists at ~10 Hz; stream keeps 4 C points plus transpiration table rows; 52 events vs leftover-mill 5-40 cap",
                "refractory_floors_ms": {"cdg.C": 1.4, "cdg.snr": 1.4},
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "CDG reconstruction head: P = k_c*(C-C0)*sqrt(T/T0); dC = C-C0; mdot = k_m*P",
                "transpiration table is SoT: lumped k_c without sqrt(T/T0) under-reads 100.00 as 80.00",
                "conjunctive isolate floor vs continue-cycle vs unit ESD",
                "vendor-CDG nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: shelf-hold without restoring on Torrveil",
            ],
        },
        "reconstruction_model": {
            "name": "cdg_lyophilizer_remaining_vacuum",
            "formula": "P_mTorr = k_c * (C_pF - C0_pF) * sqrt(T_K/T0_K); dC_pF = C_pF - C0_pF; mdot_gh = k_m * P_mTorr",
            "parameters": {
                "k_c": 20.0,
                "C0_pF": 1.0,
                "T0_K": 256.0,
                "k_m": 0.2,
                "isolate_floor_mTorr": 60.0,
                "kill_mTorr": 200.0,
                "snr_lock": 8.0,
                "hold_min": 18.0,
            },
            "table": [
                {"C_pF": 1.0, "T_K": 256.0, "P_mTorr": 0.0},
                {"C_pF": 3.0, "T_K": 256.0, "P_mTorr": 40.0},
                {"C_pF": 3.0, "T_K": 324.0, "P_mTorr": 45.0},
                {"C_pF": 5.0, "T_K": 400.0, "P_mTorr": 100.0},
                {"C_pF": 6.0, "T_K": 400.0, "P_mTorr": 125.0},
            ],
            "worked_example": {"C_pF": 5.0, "T_K": 400.0, "P_mTorr": 100.0, "dC_pF": 4.0, "sqrt_ratio": 1.25, "mdot_gh": 20.0, "P_lumped_mTorr": 80.0},
            "check": "20.00*(5.00-1.00)*sqrt(400.00/256.00)=100.00 exactly; lumped 20.00*4.00=80.00; 0.20*100.00=20.00; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.04,
            "code": "fl6.cdg_shelf_gate",
            "note": "REJECT accumulator wins: plant CDG vacuum evidence overpowers the Torrveil continue advocate",
            "decode_rule": "reject-continue if vacuum_estimator AND cdg_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("vacuum_estimator", 80, 1.5, 50.0, 0.04),
                gate_pop("cdg_lock", 64, 1.2, 31.25, 0.04),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, 0.04),
                gate_pop("reject_latch", 80, 1.7, 62.5, 0.04),
            ],
        },
        "gate_compute": gate_compute(
            [gc_check("fl6.cdg_scorer", 80, 50.0, 40.0), gc_check("fl6.hold_scorer", 40, 50.0, 32.0)]
        ),
        "meta": meta_common(
            id="nelb-r22-a1",
            clock_domain="fl6-cdg-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["cdg-vacuum", "REJECT", "MODIFY", "serialized-reconstruction", "transpiration-table", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# a2 — opacity transmissometer remaining dust, hil, MODIFY + ACCEPT
# ---------------------------------------------------------------------------
def rec_a2():
    k_o = 8.00
    i0 = 16.00
    i_iso = 4.00
    od_iso = math.log2(i0 / i_iso)
    _exact(od_iso, 2.00, "od")
    c_iso = k_o * od_iso
    _exact(c_iso, 16.00, "c_iso")
    _exact(k_o * math.log2(i0 / 8.00), 8.00, "c_mid")
    _exact(k_o * math.log2(i0 / 2.00), 24.00, "c_post")
    q = 1.50
    _exact(q * 16.00, 24.00, "mdot")
    _exact(q * 24.00, 36.00, "mdot_post")
    _exact(2820.0 + 1440.0, 4260.0, "cool")

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609222,
        source="lk8.opa.stack",
        target="limeholt.stack_isolate_core",
        table=[
            {"from": "opa_I", "to": "dust_estimator", "weight": 1.35},
            {"from": "opa_snr", "to": "extinction_lock_core", "weight": 1.2},
            {"from": "extveil_c", "to": "vendor_continue_advocate", "weight": 0.4},
        ],
        third_factor={
            "modulator": "ach.opa_lampzero_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": (
                "pre-post coincidence on keep-stack synapses; the opacity modulator depresses keep-stack and "
                "referral links when transmitted intensity stays low inside tau_e of an SNR lock so an Extveil "
                "last-good cannot hide 16.00 mg/m3 or name Tamsin Holt"
            ),
        },
        channel_prefix="opa.n",
        anchor="LK-8 OPA-HIL-5 32 ms frame at I 4.00 / SNR 14.0 (t_s 1560) reconstructing 16.00 mg/m3 over the 8.00 isolate floor",
    )
    events = [
        ev(0.0, "opa.I", 16.00, code="I_AU", units="1", note="HIL opacity transmissometer on a dummy lime-kiln stack in OPA-HIL-5; remaining-dust family, not TEOM baghouse PM, not triboelectric dust, not LII soot, not OA-ICOS CH4, not UV photometric ozone, not UV-DOAS SO2"),
        ev(180000.0, "opa.snr", 9.0, code="OPA_SNR", units="1", note="early probe SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.C", 0.00, code="C_MGM3", units="mg_m3", note="8.00*log2(16.00/16.00)=0.00 exact"),
        ev(540000.0, "lamp.zero", 1.0, code="LAMP_AE", units="bool", note="plant lamp-zero AE present on the early frame"),
        ev(720000.0, "extveil.C", 2.40, code="VENDOR_MGM3", units="mg_m3", note="Extveil last-good opacity cloud; not admissible SoT"),
        ev(900000.0, "opa.I", 8.00, code="I_AU", units="1"),
        ev(1080000.0, "recon.C", 8.00, code="C_MGM3", units="mg_m3", note="8.00*log2(16.00/8.00)=8.00; at the isolate floor, SNR still 9"),
        ev(1260000.0, "lamp.zero", 0.0, code="LAMP_AE", units="bool", note="missing lamp-zero AE burst; Extveil UTC vs plant UTC+2 skipped the zero by 120 min"),
        ev(1440000.0, "stack.Q", 1.50, code="Q_M3H", units="m3_h", note="plant-owned stack pitot on copper fieldbus; independent of Extveil"),
        ev(1560000.0, "opa.I", 4.00, code="I_AU", units="1", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "opa.snr", 14.0, code="OPA_SNR", units="1", note="1.2 ms extinction-lock after intensity"),
        ev(1740000.0, "recon.C", 16.00, code="C_MGM3", units="mg_m3", note="8.00*log2(16.00/4.00)=16.00 exact; isolate 8.00, shop-trip 48.00"),
        ev(1920000.0, "recon.od", 2.00, code="OD", units="1", note="log2(16.00/4.00)=2.00 exact optical-depth identity"),
        ev(2100000.0, "recon.mdot", 24.00, code="MDOT_GH", units="g_h", note="1.50*16.00=24.00 exact dust-mass identity"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_STACK_REFER", units="bool", note="night lead Keld Quill: keep stack ST-2 and refer opacity tech Tamsin Holt"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this stack; refuse the person-referral; Extveil not SoT"),
        ev(2640000.0, "stack.lock", 1.0, code="STACK_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cooldown plus recouplant floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_HOLT", units="bool", note="Quill: Holt badge was on the opacity-logger log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-head restart; person-referral refused; shop-trip refused"),
        ev(4800000.0, "head.new", 1.0, code="NEW_HEAD", units="bool"),
        ev(4980000.0, "opa.I", 2.00, code="I_AU", units="1"),
        ev(5160000.0, "recon.C", 24.00, code="C_MGM3", units="mg_m3", note="8.00*log2(16.00/2.00)=24.00; HIL dummy still over 8.00 so the isolated stack stays held"),
        ev(5340000.0, "extveil.C", 2.30, code="VENDOR_MGM3", units="mg_m3"),
        ev(5520000.0, "stack.Q", 1.50, code="Q_M3H", units="m3_h"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Holt exonerated; missing lamp-zero AE precedes the high dust, not the badge touch"),
        ev(5880000.0, "stack.held", 1.0, code="STACK_HELD", units="bool"),
        ev(6060000.0, "lamp.zero", 1.0, code="LAMP_AE", units="bool", note="lamp-zero restored on the new head"),
        ev(6240000.0, "recon.mdot", 36.00, code="MDOT_GH", units="g_h", note="1.50*24.00=36.00 identity holds on the post-isolate head"),
        ev(6420000.0, "shop.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
        ev(6780000.0, "recon.od", 3.00, code="OD", units="1", note="log2(16.00/2.00)=3.00 on the post-isolate frame"),
        ev(6960000.0, "opa.snr", 15.0, code="OPA_SNR", units="1"),
        ev(7140000.0, "extveil.C", 2.20, code="VENDOR_MGM3", units="mg_m3"),
        ev(7320000.0, "recon.C", 24.00, code="C_MGM3", units="mg_m3"),
        ev(7500000.0, "ko", 8.00, code="K_O", units="mg_m3", note="serialized opacity scale 8.00"),
        ev(7680000.0, "cool.held", 1.0, code="COOL_HELD", units="bool"),
        ev(7860000.0, "stack.lock", 1.0, code="STACK_ISOL", units="bool"),
        ev(8040000.0, "head.new", 1.0, code="NEW_HEAD", units="bool"),
        ev(8220000.0, "opa.I", 2.00, code="I_AU", units="1"),
        ev(8400000.0, "lamp.zero", 1.0, code="LAMP_AE", units="bool"),
        ev(8580000.0, "shop.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(8760000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool"),
        ev(8940000.0, "recon.mdot", 36.00, code="MDOT_GH", units="g_h"),
        ev(9120000.0, "stack.Q", 1.48, code="Q_M3H", units="m3_h"),
        ev(9300000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
        ev(9480000.0, "stack.held", 1.0, code="STACK_HELD", units="bool"),
        ev(9660000.0, "opa.snr", 15.0, code="OPA_SNR", units="1"),
        ev(9840000.0, "extveil.C", 2.20, code="VENDOR_MGM3", units="mg_m3"),
        ev(10020000.0, "recon.od", 3.00, code="OD", units="1"),
        ev(10200000.0, "recon.C", 24.00, code="C_MGM3", units="mg_m3"),
    ]
    assert_stream(events)
    if len(events) != 52:
        raise RuntimeError(f"a2 event count {len(events)}")

    t1 = traj_shell(
        tid="nelb-r22-a2-t1",
        sim="hil",
        episode_id="LK-OPA-2026-0718",
        domain="opacity_kiln_remaining_dust",
        setting=(
            "Limeholt Kiln LK-8 (invented), Chalkfen Stacks, stack ST-2. Hardware-in-the-loop dummy coupon "
            "in OPA-HIL-5 supplies the transmitted intensity that times the in-service stack isolate. Plant-owned "
            "opacity-transmissometer reconstruction is the remaining-dust SoT. Extveil vendor opacity scheduler "
            "is a corridor witness, not the stack SoT. Not TEOM baghouse PM (r46), not triboelectric dust (r68), "
            "not LII soot (r31), not OA-ICOS CH4 (window r21), not UV photometric ozone (r68), not UV-DOAS SO2 (r59)."
        ),
        observables={
            "I": 4.0,
            "I0": 16.0,
            "k_o": 8.0,
            "C_mgm3": 16.0,
            "OD": 2.0,
            "mdot_gh": 24.0,
            "Q_m3h": 1.5,
            "extveil_mgm3": 2.4,
            "lamp_zero": 0.0,
            "isolate_floor_mgm3": 8.0,
        },
        margin=(
            "LK-8 kiln SOP rev B: if reconstructed C_mgm3 >= 8.00 AND opacity SNR >= 12.0, isolate this stack this night. "
            "An Extveil last-good or a quiet lamp-zero residual cannot keep the stack. Shop-trip tripwire is 48.00 mg/m3. "
            "Person-referral is a different gate."
        ),
        actor="night lead Keld Quill, citing Extveil 2.40 mg/m3 and lamp-zero 1.00, and naming opacity tech Tamsin Holt as last-to-badge",
        prop_summary="keep stack ST-2 in service and refer Holt; 4.00 intensity is lamp noise on a healthy opacity head",
        basis="Extveil last-good is 2.40 mg/m3 and a night isolate of the stack is a clinker-nomination miss",
        decision="MODIFY",
        rationale=(
            "Keep-stack is refused; the person-referral is also refused. Serialized reconstruction: "
            "C_mgm3 = k_o * log2(I0/I) = 8.00 * log2(16.00/4.00) = 8.00 * 2.00 = 16.00, which is 8.00 mg/m3 over the "
            "8.00 isolate floor and 32.00 mg/m3 under the 48.00 shop-trip tripwire. Optical-depth identity "
            "OD = log2(16.00/4.00) = 2.00; dust-mass identity mdot = Q * C = 1.50 * 16.00 = 24.00 g/h. "
            "Extveil 2.40 mg/m3 is a last-good opacity stamp and is not an admissible keep-stack witness. "
            "The missing lamp-zero AE burst sits on an Extveil UTC-vs-UTC+2 skip (120 min), not on Holt's "
            "badge, and the plant stack pitot never shows a fan skip, so the easy referral fails command-custody. "
            "Ordered: isolate this stack now. Scope: this MODIFY does not trip the kiln ID fan (that is the companion "
            "question) and does not name Holt."
        ),
        threshold="C_mgm3>=8.00 AND opa_snr>=12.0 => isolate this stack; Extveil is not SoT; shop-trip if C_mgm3>=48.00; referral requires badge-touch preceding the high dust",
        residuals="16.00 vs 48.00 shop-trip floor is 32.00 mg/m3, not infinite; new-head restart still required; Extveil remains the only OEM opacity channel",
        exec_summary="MODIFY at t_s 2460: stack isolated; Holt not named; Extveil not SoT; reconstruction locked",
        tool="lk8-opa-stack-gate-cli",
        observation="C 16.00 mg/m3 recomputes from I 4.00; HIL coupon hashed; Extveil channel not used as SoT",
        timeline=[
            {"t_s": 1560.0, "event": "opa I 4.00; raster frame; C 16.00 mg/m3"},
            {"t_s": 2280.0, "event": "ops proposes keep-stack plus Holt referral"},
            {"t_s": 2460.0, "event": "MODIFY isolate stack; referral refused"},
            {"t_s": 2820.0, "event": "24 min cooldown bookend 1"},
            {"t_s": 4260.0, "event": "24.0 min floor"},
            {"t_s": 4620.0, "event": "companion ACCEPT new-head restart; referral still refused"},
        ],
        effects=[
            "dust recomputes from the serialized opacity model at every recon.C event",
            "an Extveil-only head would have kept the stack overnight",
            "24 min cooldown plus recouplant floor is in the stream (cool.start, cool.floor)",
        ],
        surprises=["a last-good 2.40 mg/m3 vendor corridor and a quiet lamp-zero residual co-existed with a 16.00 mg/m3 probe, and the obvious opacity tech was not on the causal path"],
        new_state={"stack_st2": "isolated", "holt": "exonerated", "extveil": "not SoT", "reconstruction_model": "discharged as an on-record calculator"},
        latency_ms=1500000.0,
        rc=reward(
            0.40,
            [
                ("opa_reconstruction", 0.14),
                ("isolate_floor_stack", 0.12),
                ("exoneration", 0.10),
                ("extveil_nonsubstitution", 0.08),
                ("cool_time_cost", -0.04),
            ],
            "scored for a keep-stack MODIFY on a recomputable high opacity dust while refusing an Extveil 2.40 mg/m3 corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        tags=["MODIFY", "opacity-dust", "serialized-reconstruction", "operational-companion"],
        distillation_note="opacity gate: serialized k_o*log2(I0/I) plus OD identity beats a green dust dashboard; companion t2 is the new-head restart, not a governance vote",
    )
    t2 = traj_shell(
        tid="nelb-r22-a2-t2",
        sim="hil",
        episode_id="LK-OPA-2026-0718-exec",
        domain="new_head_cooldown_execution",
        setting="Same LK-8 after the MODIFY. Night lead proposes referring Holt and tripping the kiln ID fan. This companion is the operational new-head cooldown restart, not a second dust vote.",
        observables={"C_mgm3": 24.0, "mdot_gh": 36.0, "cool_floor_s": 1440.0, "refer_proposed": True},
        margin="new_head AND cool_floor_complete AND refer_not_taken AND shop_not_tripped AND isolated_stack_held",
        actor="night lead Keld Quill",
        prop_summary="refer Holt and trip the kiln ID fan; 24 min already paid and Extveil is 2.30 mg/m3",
        basis="the MODIFY already cut the stack, so a shop trip plus a person file is the cheapest hold",
        decision="ACCEPT",
        rationale=(
            "Restart the stack on a different opacity head after the cooldown floor. The 24 min recouplant is complete "
            "and the shop-trip (C_mgm3 >= 48.00) is still armed on the plant opacity head. ACCEPT the new-head restart. "
            "Do not refer Holt. Do not trip the kiln ID fan. 24.00 mg/m3 post-isolate is still over the 8.00 isolate "
            "floor, so the isolated stack stays held; the new head may run."
        ),
        threshold="new_head AND cool_floor_complete AND refer_not_taken AND shop_not_tripped AND isolated_stack_held",
        residuals="isolated stack still over 8.00 mg/m3; Extveil remains OEM-only",
        exec_summary="new-head restart at t_s 4620; Holt not referred; shop not tripped; isolated stack held",
        tool="lk8-opa-cool-exec",
        observation="recon.C 24.00 mg/m3 on the HIL dummy; lamp-zero AE present on the new head; Extveil still ignored",
        timeline=[
            {"t_s": 2820.0, "event": "cooldown clock started after MODIFY"},
            {"t_s": 4260.0, "event": "24.0 min floor"},
            {"t_s": 4440.0, "event": "Holt referral re-proposed"},
            {"t_s": 4620.0, "event": "ACCEPT new-head restart; referral refused"},
        ],
        effects=["Extveil restore did not reopen the dust call", "shop trip never fired; 16.00 vs 48.00 mg/m3 floor", "Holt remains unnamed; missing lamp-zero AE is the causal object"],
        surprises=["timezone-skipped lamp-zero AE, not last-to-badge, was the causal object"],
        new_state={"stack": "restarted on new head", "holt": "exonerated", "st2": "held", "id_fan": "in service"},
        latency_ms=1800000.0,
        rc=reward(
            0.35,
            [
                ("new_head_restart", 0.12),
                ("no_referral", 0.10),
                ("extveil_nonsubstitution", 0.08),
                ("cool_floor_complete", 0.07),
                ("held_stack_cost", -0.02),
            ],
            "operational execution gate: new-head restart because Extveil is not a restore license; not a dust re-vote",
        ),
        tags=["ACCEPT", "operational-execution", "new-head-restart"],
        distillation_note="operational companion: new-head restart without referring the opacity tech",
    )
    return {
        "id": "nelb-r22-a2",
        "spike_events": events,
        "language_view": {
            "description": (
                "Limeholt Kiln LK-8. HIL opacity transmissometer reconstructs 16.00 mg/m3 from 8.00*log2(16.00/4.00) while Extveil "
                "still shows 2.40 mg/m3 and the lamp-zero AE is missing. The gate MODIFYs stack isolate and refuses "
                "the opacity-tech referral. A 24 min cooldown floor is serialized in the stream. Companion t2 ACCEPTs "
                "a new-head restart and still refuses the referral."
            ),
            "trajectory": t1,
            "trajectory_new_head": t2,
        },
        "bridge_notes": {
            "channel_map": {
                "opa.I / opa.snr": "transmitted intensity and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.od / recon.mdot": "serialized remaining dust mg/m3, optical-depth identity, and dust-mass identity",
                "lamp.zero / extveil.C / stack.Q": "lamp-zero AE, vendor last-good, and stack pitot; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-stack-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "stack.lock / cool.start / cool.floor / head.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-low while opacity-over: extveil.C 2.40 next to recon.C 16.00",
                "reconstruction as event: recon.C 16.00 equals 8.00*log2(16.00/4.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight opacity pair: opa.I then opa.snr +1.2 ms at the raster frame",
                "exoneration motif: lamp.zero 0 at 1260 s precedes the high dust; Holt badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Extveil is 2.40 mg/m3' = extveil.C 2.40; '16 mg/m3 remaining' = recon.C 16.00; 'isolate this stack not Holt' = gate.isol MODIFY; 'new head not referral' = gate.exec ACCEPT",
            "why_high_value": (
                "New opacity-transmissometer remaining-dust family on a lime-kiln stack "
                "(not TEOM r46, not triboelectric r68, not LII r31, not OA-ICOS window r21, not UV photometric ozone r68). Lead MODIFY "
                "of keep-stack on a recomputable high dust that a vendor last-good would have cleared, with a "
                "resolved-innocent opacity tech. Companion t2 is operational new-head restart. 52-event stream (48+). sim_or_real=hil."
            ),
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609222, "stream_note": "reconstruction amplitudes are exact authored constants; raster draws carry 0.82**k plus 4% noise"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "opacity transmissometer exists at ~1 Hz; stream keeps 4 I points; 52 events vs leftover-mill 5-40 cap",
                "refractory_floors_ms": {"opa.I": 1.2, "opa.snr": 1.2},
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "opacity reconstruction head: C = k_o * log2(I0/I); OD = log2(I0/I); mdot = Q * C",
                "isolate-floor stack vs keep-whole vs shop trip",
                "exoneration head: missing lamp-zero AE plus timezone skip, not last-to-badge",
                "operational companion: new-head restart without referring the opacity tech",
            ],
        },
        "reconstruction_model": {
            "name": "opacity_kiln_remaining_dust",
            "formula": "C_mgm3 = k_o * log2(I0/I); OD = log2(I0/I); mdot_gh = Q_m3h * C_mgm3",
            "parameters": {
                "k_o": 8.0,
                "I0": 16.0,
                "Q_m3h": 1.5,
                "isolate_floor_mgm3": 8.0,
                "trip_mgm3": 48.0,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"I": 4.0, "C_mgm3": 16.0, "OD": 2.0, "mdot_gh": 24.0},
            "check": "8.00*log2(16.00/4.00)=16.00 exactly; log2(16.00/4.00)=2.00; 1.50*16.00=24.00; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "lk8.opa_stack_gate",
            "note": "MODIFY accumulator wins: opacity high-dust evidence overpowers the Extveil continue advocate",
            "decode_rule": "modify-isolate if dust_estimator AND extinction_lock fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("dust_estimator", 80, 1.5, 50.0, 0.032),
                gate_pop("extinction_lock", 64, 1.2, 31.25, 0.032),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, 0.032),
                gate_pop("modify_latch", 80, 1.7, 62.5, 0.032),
            ],
        },
        "gate_compute": gate_compute(
            [gc_check("lk8.opa_scorer", 80, 50.0, 32.0), gc_check("lk8.isol_scorer", 50, 50.0, 32.0)]
        ),
        "meta": meta_common(
            id="nelb-r22-a2",
            clock_domain="lk8-opa-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["opacity-dust", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# a3 — photoelastic remaining hoop stress, simulated, ACCEPT + REJECT
# ---------------------------------------------------------------------------
def rec_a3():
    c_b = 8.00
    t_mm = 3.00
    d_mm = 30.00
    delta_iso = 240.00
    sigma_iso = delta_iso / (c_b * t_mm)
    _exact(sigma_iso, 10.00, "sigma")
    p_mpa = 2.00 * sigma_iso * t_mm / d_mm
    _exact(p_mpa, 2.00, "p_mpa")
    p_bar = 10.00 * p_mpa
    _exact(p_bar, 20.00, "p_bar")
    _exact(72.00 / (c_b * t_mm), 3.00, "s_early")
    _exact(144.00 / (c_b * t_mm), 6.00, "s_mid")
    _exact(384.00 / (c_b * t_mm), 16.00, "s_post")
    _exact(20.00 * 10.00 * t_mm / d_mm, 20.00, "p_id")
    _exact(6000.0 + 720.0, 6720.0, "surv")

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609223,
        source="fg3.photo.visor",
        target="flintshaw.visor_accept_core",
        table=[
            {"from": "photo_delta", "to": "stress_estimator", "weight": 1.4},
            {"from": "photo_snr", "to": "brewster_norm_core", "weight": 1.2},
            {"from": "brewveil_s", "to": "vendor_skip_advocate", "weight": 0.5},
        ],
        third_factor={
            "modulator": "na.visor_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": (
                "pre-post coincidence on skip-survey synapses; the photoelastic modulator enables potentiation only "
                "while retardance and SNR are co-active inside tau_e so a Brewveil last-good cannot skip visors V-1..V-3 "
                "on a 10.00 MPa remaining-hoop-stress load"
            ),
        },
        channel_prefix="ph.n",
        anchor="FG-3 PHOTO-SIM-3 36 ms frame at δ 240.00 nm / SNR 16.0 (t_s 3000) reconstructing 10.00 MPa on visor V-4 above the 6.00 MPa isolate floor",
    )
    events = [
        ev(0.0, "photo.d", 72.0, code="DELTA_NM", units="nm", note="simulated circular-polariscope retardance of FG-3 glass-furnace visor V-4; remaining-hoop-stress family, not spectroscopic ellipsometry, not digital shearography, not DIC hoop-strain, not acoustoelastic birefringence, not XRD sin2psi"),
        ev(300000.0, "photo.snr", 10.0, code="PHOTO_SNR", units="1", note="early polariscope SNR"),
        ev(600000.0, "recon.s", 3.0, code="S_MPA", units="MPa", note="72.00/(8.00*3.00)=3.00 exact"),
        ev(900000.0, "visor.t", 3.0, code="T_MM", units="mm", note="plant visor thickness on a serial-only LAN; independent witness"),
        ev(1200000.0, "brewveil.s", 1.2, code="VENDOR_MPA", units="MPa", note="Brewveil last-good polariscope cloud; patched residual 0.00 MPa"),
        ev(1800000.0, "photo.d", 144.0, code="DELTA_NM", units="nm"),
        ev(2100000.0, "recon.s", 6.0, code="S_MPA", units="MPa", note="144.00/(8.00*3.00)=6.00; at the isolate floor"),
        ev(2400000.0, "recon.p", 12.0, code="P_BAR", units="bar", note="20.00*6.00*3.00/30.00=12.00 hoop-pressure identity on the early frame"),
        ev(2700000.0, "photo.snr", 14.0, code="PHOTO_SNR", units="1"),
        ev(3000000.0, "photo.d", 240.0, code="DELTA_NM", units="nm", note="in-band frame; raster sidecar"),
        ev(3000001.5, "photo.snr", 16.0, code="PHOTO_SNR", units="1", note="1.5 ms Brewster-norm after retardance"),
        ev(3300000.0, "recon.s", 10.0, code="S_MPA", units="MPa", note="240.00/(8.00*3.00)=10.00 exact; isolate 6.00, dump 24.00"),
        ev(3600000.0, "recon.p", 20.0, code="P_BAR", units="bar", note="20.00*10.00*3.00/30.00=20.00 exact; inverse σ=p_bar/2.00=10.00"),
        ev(3900000.0, "brewveil.s", 1.2, code="VENDOR_MPA", units="MPa"),
        ev(4200000.0, "visor.id", 4.0, code="VISOR", units="id"),
        ev(4500000.0, "v13.present", 1.0, code="V13_PRESENT", units="bool", note="adjacent visors V-1..V-3 are the skip-survey object, not this visor"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="furnace lead Bram Fen: V-4 is green on Brewveil 1.20; skip V-1..V-3 to save a morning survey"),
        ev(5400000.0, "gate.visor", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of V-4 isolate only; 10.00 MPa above 6.00 floor; V-1..V-3 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_V13", units="bool", note="Fen: Brewveil 1.20, skip V-1..V-3"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-survey of V-1..V-3 refused; V-4 hold stands"),
        ev(8400000.0, "v4.held", 1.0, code="V4_HELD", units="bool"),
        ev(9000000.0, "photo.d", 384.0, code="DELTA_NM", units="nm"),
        ev(9600000.0, "recon.s", 16.0, code="S_MPA", units="MPa", note="384.00/(8.00*3.00)=16.00; still at/over the 6.00 isolate floor"),
        ev(10200000.0, "brewveil.s", 1.2, code="VENDOR_MPA", units="MPa"),
        ev(10800000.0, "v13.skip", 0.0, code="V13_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "dump.kill", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(12000000.0, "photo.snr", 15.0, code="PHOTO_SNR", units="1"),
        ev(12600000.0, "recon.p", 32.0, code="P_BAR", units="bar", note="20.00*16.00*3.00/30.00=32.00 identity held on the post-accept frame"),
        ev(13200000.0, "furn.held", 1.0, code="FURN_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "v4.held", 1.0, code="V4_HELD", units="bool"),
        ev(15000000.0, "visor.t", 3.0, code="T_MM", units="mm"),
        ev(15600000.0, "cb", 8.0, code="C_B", units="nm_per_MPa_mm", note="serialized Brewster coefficient 8.00"),
        ev(16200000.0, "visor.id", 4.0, code="VISOR", units="id"),
        ev(16800000.0, "photo.d", 384.0, code="DELTA_NM", units="nm"),
        ev(17400000.0, "recon.s", 16.0, code="S_MPA", units="MPa"),
        ev(18000000.0, "brewveil.s", 1.1, code="VENDOR_MPA", units="MPa"),
        ev(18600000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(19200000.0, "dump.kill", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(19800000.0, "v13.skip", 0.0, code="V13_NOT_SKIPPED", units="bool"),
        ev(20400000.0, "photo.snr", 15.0, code="PHOTO_SNR", units="1"),
        ev(21000000.0, "recon.p", 32.0, code="P_BAR", units="bar"),
        ev(21600000.0, "visor.t", 3.0, code="T_MM", units="mm"),
        ev(22200000.0, "furn.held", 1.0, code="FURN_HELD", units="bool"),
        ev(22800000.0, "v4.held", 1.0, code="V4_HELD", units="bool"),
        ev(23400000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(24000000.0, "photo.d", 384.0, code="DELTA_NM", units="nm"),
        ev(24600000.0, "recon.s", 16.0, code="S_MPA", units="MPa"),
        ev(25200000.0, "brewveil.s", 1.1, code="VENDOR_MPA", units="MPa"),
        ev(25800000.0, "v13.present", 1.0, code="V13_PRESENT", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 52:
        raise RuntimeError(f"a3 event count {len(events)}")

    t1 = traj_shell(
        tid="nelb-r22-a3-t1",
        sim="simulated",
        episode_id="FG-PHOTO-2026-0819",
        domain="photoelastic_visor_remaining_stress",
        setting=(
            "Flintshaw Glass FG-3 (invented), Gritspit Furnaces. Simulated polariscope coupon in PHOTO-SIM-3 supplies the "
            "retardance that times the in-band visor V-4 isolate. Plant-owned circular-polariscope reconstruction is "
            "the remaining-hoop-stress SoT. Brewveil vendor last-good visor cloud is a corridor witness, not the visor SoT. "
            "Invented plant; simulated campaign. Not spectroscopic ellipsometry (r30), not digital shearography (r33), "
            "not DIC hoop-strain (r51), not acoustoelastic birefringence (r47), not XRD sin2psi (r50)."
        ),
        observables={
            "delta_nm": 240.0,
            "C_B": 8.0,
            "t_mm": 3.0,
            "D_mm": 30.0,
            "s_MPa": 10.0,
            "p_bar": 20.0,
            "brewveil_MPa": 1.2,
            "photo_snr": 16.0,
            "isolate_floor_MPa": 6.0,
        },
        margin=(
            "FG-3 furnace SOP rev A: if reconstructed s_MPa >= 6.00 AND polariscope SNR >= 12.0, visor V-4 may be isolated "
            "and surveyed. Dump if s_MPa >= 24.00. V-1..V-3 skip-survey is a different gate. Brewveil last-good "
            "cannot skip an unmeasured visor."
        ),
        actor="furnace lead Bram Fen, citing Brewveil 1.20 MPa and a late morning survey",
        prop_summary="stamp V-4 in band and skip V-1..V-3; 240 nm is a fringe glitch on a healthy visor cloud",
        basis="Brewveil last-good is 1.20 MPa and a night survey of V-1..V-3 is a takt miss",
        decision="ACCEPT",
        rationale=(
            "V-4 is accepted as in-band for a single isolate plus survey. Serialized reconstruction: "
            "s_MPa = δ / (C_B * t) = 240.00 / (8.00 * 3.00) = 10.00, which is 4.00 MPa above the 6.00 isolate floor and "
            "14.00 MPa under the 24.00 dump. Hoop-pressure identity p_bar = 20.00 * σ * t / D = 20.00 * 10.00 * 3.00 / 30.00 "
            "= 20.00; inverse σ = p_bar / 2.00 = 10.00. Brewveil 1.20 MPa is a patched 0.00 residual and is not an "
            "admissible skip-survey witness. Ordered: ACCEPT this V-4 isolate only. Scope: this ACCEPT does not "
            "skip V-1..V-3 (that is the companion question) and does not stamp a furnace dump."
        ),
        threshold="s_MPa>=6.00 AND photo_snr>=12.0 => accept V-4 isolate; Brewveil is not SoT; dump if s_MPa>=24.00; V-1..V-3 are out of scope",
        residuals="10.00 vs 6.00 isolate floor is 4.00 MPa, not infinite; V-1..V-3 remain unmeasured; Brewveil remains the only OEM polariscope channel",
        exec_summary="ACCEPT at t_s 5400: V-4 in band; V-1..V-3 not skipped; Brewveil not SoT; reconstruction locked",
        tool="fg3-photo-visor-gate-cli",
        observation="σ 10.00 MPa recomputes from δ 240.00 nm; PHOTO-SIM-3 hashed; Brewveil channel not used as SoT",
        timeline=[
            {"t_s": 3000.0, "event": "photo δ 240.00 nm; raster frame; σ 10.00 MPa"},
            {"t_s": 4800.0, "event": "ops proposes accept V-4 and skip V-1..V-3"},
            {"t_s": 5400.0, "event": "ACCEPT V-4 only; V-1..V-3 out of scope"},
            {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
            {"t_s": 6720.0, "event": "12.0 min floor"},
            {"t_s": 7800.0, "event": "companion REJECT skip-survey of V-1..V-3"},
        ],
        effects=[
            "remaining hoop stress recomputes from the serialized photoelastic model at every recon.s event",
            "a Brewveil-only head would have skipped V-1..V-3 overnight",
            "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
        ],
        surprises=["a last-good 1.20 MPa vendor corridor co-existed with a 10.00 MPa in-band reconstruction that still forbids skipping the unmeasured visors"],
        new_state={"v4": "accepted in band", "v13": "not this gate", "brewveil": "not SoT", "reconstruction_model": "discharged as an on-record calculator"},
        latency_ms=2400000.0,
        rc=reward(
            0.41,
            [
                ("photo_reconstruction", 0.14),
                ("in_band_visor_scope", 0.12),
                ("brewveil_nonsubstitution", 0.09),
                ("v13_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of V-4 on a recomputable remaining hoop stress while refusing a Brewveil skip of V-1..V-3; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        tags=["ACCEPT", "photoelastic-stress", "serialized-reconstruction", "operational-companion"],
        distillation_note="photoelastic gate: serialized δ/(C_B t) plus hoop-pressure identity beats a green last-good dashboard; companion t2 is the skip-survey refusal, not a stress re-vote",
    )
    t2 = traj_shell(
        tid="nelb-r22-a3-t2",
        sim="simulated",
        episode_id="FG-PHOTO-2026-0819-exec",
        domain="visor_skip_survey_refusal",
        setting="Same FG-3 after the ACCEPT. Furnace lead proposes skipping V-1..V-3 on Brewveil 1.20 MPa. This companion is the operational skip refusal, not a second stress vote.",
        observables={"s_MPa": 16.0, "brewveil_MPa": 1.2, "surv_floor_s": 720.0, "skip_proposed": True},
        margin="v4_held AND surv_floor_complete AND v13_not_skipped AND dump_not_taken",
        actor="furnace lead Bram Fen",
        prop_summary="skip V-1..V-3; 12 min already paid and Brewveil is 1.20 MPa",
        basis="the ACCEPT already stamped V-4, so skipping the rest of the furnace visors is the cheapest hold",
        decision="REJECT",
        rationale=(
            "Refuse skip-survey of V-1..V-3. The 12 min survey-complete floor is done and the dump "
            "(s_MPa >= 24.00) is still armed on the plant polariscope head. REJECT the skip. Do not dump the furnace. "
            "Do not reopen V-4. 16.00 MPa post-accept is still in band for V-4 only; V-1..V-3 have no "
            "independent polariscope coupon."
        ),
        threshold="v4_held AND surv_floor_complete AND v13_not_skipped AND dump_not_taken",
        residuals="V-1..V-3 still unmeasured; Brewveil remains OEM-only",
        exec_summary="V-1..V-3 skip refused at t_s 7800; V-4 hold stands; dump not taken",
        tool="fg3-photo-skip-exec",
        observation="recon.s 16.00 MPa on V-4; V-1..V-3 remain on the survey list; Brewveil still ignored",
        timeline=[
            {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
            {"t_s": 6720.0, "event": "12.0 min floor"},
            {"t_s": 7200.0, "event": "skip V-1..V-3 proposed"},
            {"t_s": 7800.0, "event": "REJECT skip-survey of V-1..V-3"},
        ],
        effects=["Brewveil skip did not reopen the stress call", "dump never fired; 10.00 vs 24.00 MPa floor"],
        surprises=["bounded ACCEPT of V-4 did not license a skip of unmeasured visors"],
        new_state={"v4": "held in band", "v13": "still to survey", "dump": "in service"},
        latency_ms=1800000.0,
        rc=reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("brewveil_nonsubstitution", 0.11),
                ("no_dump", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-survey because last-good freeze is not photoelastic remaining stress; not a stress re-vote",
        ),
        tags=["REJECT", "operational-execution", "skip-survey"],
        distillation_note="operational companion: refuse skip-survey without re-opening the stress call",
    )
    return {
        "id": "nelb-r22-a3",
        "spike_events": events,
        "language_view": {
            "description": (
                "Flintshaw Glass FG-3. Simulated polariscope reconstructs 10.00 MPa from 240.00/(8.00*3.00) while Brewveil "
                "still shows 1.20 MPa. The gate ACCEPTs V-4 isolate only; a companion execution REJECT refuses "
                "skip-survey of V-1..V-3. The retardance-to-stress model is serialized so every recon event recomputes."
            ),
            "trajectory": t1,
            "trajectory_skip_survey_refusal": t2,
        },
        "bridge_notes": {
            "channel_map": {
                "photo.d / photo.snr": "retardance and SNR; the physics channels the reconstruction consumes",
                "recon.s / recon.p": "serialized remaining hoop stress MPa and hoop-pressure identity",
                "visor.t / brewveil.s / visor.id / v13.present": "visor thickness, vendor last-good, visor id, and adjacent-visor presence; the denial and scope channels",
                "ops.prop / gate.visor / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / v4.held / v13.skip / furn.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while photoelastic-over: brewveil.s 1.20 next to recon.s 10.00",
                "reconstruction as event: recon.s 10.00 equals 240.00/(8.00*3.00)",
                "ACCEPT then operational REJECT: gate.visor at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight polariscope pair: photo.d then photo.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Brewveil is 1.20 MPa' = brewveil.s 1.20; '10 MPa remaining' = recon.s 10.00; 'this visor not V-1..V-3' = gate.visor ACCEPT plus v13.skip 0; 'do not skip V-1..V-3' = gate.hold REJECT",
            "why_high_value": (
                "New circular-polariscope remaining-hoop-stress family on a glass-furnace visor (not ellipsometry r30, not "
                "shearography r33, not DIC r51, not acoustoelastic r47, not XRD sin2psi r50). First δ/(C_B t) stress reconstruction with hoop-pressure "
                "identity that can sit in band while a last-good corridor wants a visor skip. Companion t2 is operational "
                "skip refusal. 52-event stream (48+). sim_or_real=simulated."
            ),
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609223, "stream_note": "reconstruction amplitudes are exact authored constants; raster draws carry 0.82**k plus 4% noise"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "polariscope exists at ~10 Hz; stream keeps 4 δ points; 52 events vs leftover-mill 5-40 cap",
                "refractory_floors_ms": {"photo.d": 1.5, "photo.snr": 1.5},
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "photoelastic reconstruction head: σ = δ / (C_B * t); p_bar = 20 * σ * t / D; σ = p_bar / 2",
                "bounded ACCEPT head: in-band remaining stress AND visor scope AND v13-out-of-scope",
                "operational companion: refuse skip-survey without re-opening the stress call",
            ],
        },
        "reconstruction_model": {
            "name": "photoelastic_visor_remaining_stress",
            "formula": "s_MPa = delta_nm / (C_B * t_mm); p_bar = 20.0 * s_MPa * t_mm / D_mm; s_MPa = p_bar / 2.0",
            "parameters": {
                "C_B": 8.0,
                "t_mm": 3.0,
                "D_mm": 30.0,
                "isolate_floor_MPa": 6.0,
                "dump_MPa": 24.0,
                "snr_lock": 12.0,
                "surv_min": 12.0,
            },
            "worked_example": {"delta_nm": 240.0, "s_MPa": 10.0, "p_bar": 20.0, "p_MPa": 2.0},
            "check": "240.00/(8.00*3.00)=10.00 exactly; 20.00*10.00*3.00/30.00=20.00 exactly; 20.00/2.00=10.00; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "fg3.photo_visor_gate",
            "note": "ACCEPT accumulator wins: photoelastic remaining-stress evidence overpowers the Brewveil skip advocate",
            "decode_rule": "accept if stress_estimator AND brewster_norm AND visor_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release V-1..V-3",
            "populations": [
                gate_pop("stress_estimator", 80, 1.5, 50.0, 0.036),
                gate_pop("brewster_norm", 64, 1.2, 31.25, 0.036),
                gate_pop("visor_margin", 40, 1.0, 50.0, 0.036),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, 0.036),
                gate_pop("accept_latch", 96, 1.8, 62.5, 0.036),
            ],
        },
        "gate_compute": gate_compute(
            [gc_check("fg3.photo_scorer", 80, 50.0, 36.0), gc_check("fg3.s_scorer", 40, 62.5, 32.0)]
        ),
        "meta": meta_common(
            id="nelb-r22-a3",
            clock_domain="fg3-photo-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["photoelastic-stress", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
