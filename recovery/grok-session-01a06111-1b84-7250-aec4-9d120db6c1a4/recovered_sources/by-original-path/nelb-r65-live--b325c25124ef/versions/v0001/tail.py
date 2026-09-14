def occupancy_preflight():
    banned = (
        "snipeholt",
        "gritfen",
        "larkspire",
        "faimveil",
        "hardveil",
        "cureveil",
        "nelb-r65-001",
        "nelb-r65-002",
        "nelb-r65-003",
        "faims remaining sf6",
        "leeb rebound remaining",
        "dsc remaining cure",
        "harlan pike",
        "olen marsh",
        "wynn calder",
    )
    hits = []
    if LIVE_DIR.is_dir():
        for n in sorted(LIVE_DIR.glob("batch-r*.jsonl")) + sorted(LIVE_DIR.glob("NOTES-r*.md")):
            if n.name.startswith("batch-r65") or n.name.startswith("NOTES-r65"):
                continue
            text = n.read_text(encoding="utf-8", errors="replace").casefold()
            for b in banned:
                if b in text:
                    hits.append(f"{n.name}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")


# ---------------------------------------------------------------------------
# nelb-r65-001 — FAIMS remaining SF6 of a GIS bay, designed, REJECT/MODIFY
# ---------------------------------------------------------------------------
def rec_001():
    k_f = 4.00
    i_na = 8.00
    i0 = 3.00
    d_i = i_na - i0
    _exact(d_i, 5.00)
    c_ppm = k_f * d_i
    _exact(c_ppm, 20.00)
    _exact(k_f * (4.00 - i0), 4.00)
    _exact(k_f * (5.00 - i0), 8.00)
    _exact(k_f * (6.00 - i0), 12.00)
    _exact(k_f * (9.00 - i0), 24.00)
    q_th = 1.20
    load = c_ppm * q_th
    _exact(load, 24.00)
    _exact(c_ppm / k_f, 5.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_lif_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=2026096501,
        source="sh5.faims.sf6",
        target="snipeholt.bay_stop_core",
        table=[
            {"from": "faims_dI", "to": "sf6_estimator", "weight": 1.40},
            {"from": "faims_snr", "to": "faims_lock_core", "weight": 1.15},
            {"from": "faimveil_c", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.faims_sf6_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-energize synapses; the plant FAIMS modulator depresses continue-energize links when compensation current stays high inside tau_e of an SNR lock so a Faimveil last-good cannot hide a 20.00 ppm remaining-SF6 slip",
        },
        channel_prefix="faims.n",
        anchor="SH-5 FAIMS 40 ms frame at I 8.00 nA / SNR 12.0 (t_s 3000) reconstructing 20.00 ppm over the 12.00 isolate floor",
        tau_m_ms=10.0,
    )
    w_s = 0.040
    events = [
        ev(0.0, "faims.I", 4.00, code="I_NA", units="nA", note="plant-owned high-field asymmetric-waveform ion mobility remaining SF6 of Snipeholt GIS SH-5 bay B-6; remaining-SF6 family, not Pockels GIS, not helium RGA, not SPR, not QEPAS DGA, not electrochemical H2S"),
        ev(180000.0, "faims.snr", 6.0, code="FAIMS_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.C", 4.00, code="C_PPM", units="ppm", note="4.00*(4.00-3.00)=4.00 exact; still under the 12.00 isolate floor"),
        ev(540000.0, "gis.P", 620.0, code="GIS_KPA", units="kPa", note="plant GIS density transmitter on copper DCS; independent witness; unread by Faimveil"),
        ev(720000.0, "faimveil.C", 2.40, code="VENDOR_PPM", units="ppm", note="Faimveil vendor FAIMS-cloud; infra owner; patched compensation timestamps"),
        ev(900000.0, "faims.I", 5.00, code="I_NA", units="nA"),
        ev(1080000.0, "recon.C", 8.00, code="C_PPM", units="ppm", note="4.00*(5.00-3.00)=8.00; isolate-adjacent band"),
        ev(1260000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk Edda Moss slid the SF6-slip clock 40.00 s; collusion party"),
        ev(1440000.0, "gis.P", 618.0, code="GIS_KPA", units="kPa"),
        ev(1620000.0, "recon.dI", 2.00, code="DI_NA", units="nA", note="I-I0 identity at the 8.00 ppm band"),
        ev(1800000.0, "faims.I", 6.00, code="I_NA", units="nA"),
        ev(1980000.0, "recon.C", 12.00, code="C_PPM", units="ppm", note="4.00*(6.00-3.00)=12.00; isolate floor"),
        ev(2160000.0, "gis.Q", 1.20, code="Q_TH", units="th", note="plant-owned bay extract rotameter; independent of Faimveil"),
        ev(2340000.0, "faimveil.C", 2.40, code="VENDOR_PPM", units="ppm"),
        ev(2520000.0, "faims.snr", 9.0, code="FAIMS_SNR", units="1"),
        ev(2700000.0, "recon.I0", 3.00, code="I0_NA", units="nA", note="clean-bay compensation intercept used by the reconstruction"),
        ev(3000000.0, "faims.I", 8.00, code="I_NA", units="nA", note="isolate-floor frame; raster sidecar; dI=8.00-3.00=5.00"),
        ev(3000001.4, "faims.snr", 12.0, code="FAIMS_SNR", units="1", note="1.4 ms SNR lock after I; 12.0 >= 8.0"),
        ev(3180000.0, "recon.C", 20.00, code="C_PPM", units="ppm", note="4.00*5.00=20.00 exact; isolate 12.00, hall-kill 80.00"),
        ev(3360000.0, "recon.load", 24.00, code="LOAD_GH", units="g_h", note="20.00*1.20=24.00 exact SF6-load identity"),
        ev(3540000.0, "recon.dI", 5.00, code="DI_NA", units="nA", note="8.00-3.00=5.00 exact compensation-delta identity"),
        ev(3720000.0, "faimveil.drop", 1.0, code="FAIM_DROP", units="bool", note="vendor FAIMS packets dropped in Faimveil cloud for 40 s"),
        ev(3900000.0, "collude.clerk", 1.0, code="CLERK", units="bool"),
        ev(4080000.0, "gis.P", 615.0, code="GIS_KPA", units="kPa", note="GIS density tracks the plant FAIMS, not Faimveil 2.40"),
        ev(4260000.0, "gis.Q", 1.20, code="Q_TH", units="th"),
        ev(4440000.0, "recon.I0", 3.00, code="I0_NA", units="nA"),
        ev(4620000.0, "faimveil.C", 2.35, code="VENDOR_PPM", units="ppm"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_ENERGIZE", units="bool", note="night operator Harlan Pike: Faimveil is clean 2.40 ppm; continue B-6 night-energize"),
        ev(4980000.0, "recon.C", 20.00, code="C_PPM", units="ppm", note="repeat of the 20.00 ppm reconstruction as SoT"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-energize; 20.00 ppm and SNR 12.0; Faimveil not SoT"),
        ev(6000000.0, "lock.start", 1.0, code="LOCK_START", units="bool", note="bookend 1 of the 18.0 min lockout-hold floor"),
        ev(7080000.0, "lock.floor", 1.0, code="LOCK_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="HALL_ESD", units="bool", note="Pike: ESD the whole Snipeholt GIS hall until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: lockout-hold on plant FAIMS as live interlock; hall ESD refused"),
        ev(9000000.0, "lock.set", 1.0, code="LOCK_HELD", units="bool"),
        ev(9600000.0, "faims.I", 9.00, code="I_NA", units="nA"),
        ev(10200000.0, "recon.C", 24.00, code="C_PPM", units="ppm", note="4.00*(9.00-3.00)=24.00; still over 12.00 so lockout holds"),
        ev(10800000.0, "faimveil.C", 2.30, code="VENDOR_PPM", units="ppm"),
        ev(11400000.0, "gis.P", 612.0, code="GIS_KPA", units="kPa"),
        ev(12000000.0, "lock.held", 1.0, code="LOCK_HELD", units="bool"),
        ev(12600000.0, "unit.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "faimveil.drop", 1.0, code="FAIM_DROP", units="bool"),
        ev(14400000.0, "lock.held", 1.0, code="LOCK_HELD", units="bool"),
        ev(15000000.0, "recon.load", 28.80, code="LOAD_GH", units="g_h", note="24.00*1.20=28.80 on the post-stop frame"),
        ev(15600000.0, "gis.Q", 1.20, code="Q_TH", units="th"),
        ev(16200000.0, "recon.dI", 6.00, code="DI_NA", units="nA", note="4.00*6.00=24.00 inverse check"),
        ev(16800000.0, "collude.clerk", 1.0, code="CLERK", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r65-001-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "SH-FAIMS-2026-0902",
            "domain": "faims_sf6_gis_bay",
            "setting": "Snipeholt GIS SH-5 (invented), bay B-6. Plant-owned high-field asymmetric-waveform ion-mobility spectrometer is the remaining-SF6 SoT. Faimveil vendor FAIMS-cloud (infra owner) plus the SF6-slip permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not r36 Pockels GIS, not r24 helium RGA, not r26 SPR, not r19 QEPAS DGA, not r60 electrochemical H2S, not live r21 SERF OPM.",
            "observables_at_decision": {
                "I_nA": i_na,
                "I0_nA": i0,
                "dI_nA": d_i,
                "k_f": k_f,
                "C_ppm": c_ppm,
                "load_gh": load,
                "faims_snr": 12.0,
                "faimveil_ppm": 2.40,
                "permit_slide_s": 40.00,
                "isolate_floor_ppm": 12.00,
            },
            "margin_authority": "SH-5 GIS SOP rev C: if reconstructed C_ppm >= 12.00 AND FAIMS SNR >= 8.0, continue-energize is forbidden even if Faimveil reports 2.40 ppm. Hall ESD is a different gate. Kill tripwire is 80.00 ppm.",
        },
        "proposed_action": {
            "actor": "night operator Harlan Pike, citing Faimveil 2.40 ppm and a quiet compensation channel",
            "summary": "continue B-6 night-energize; 8.00 nA is electrode-age noise on a healthy SF6 slip",
            "basis_claimed": "Faimveil is the only OEM FAIMS SoT and a night abort of B-6 is a feeder-nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-energize is refused. Serialized reconstruction: C_ppm = k_f * (I - I0) = 4.00 * (8.00 - 3.00) = 20.00, which is 8.00 ppm over the 12.00 isolate floor and 60.00 ppm under the 80.00 hall-kill tripwire, and FAIMS SNR is 12.0 >= 8.0. Delta identity dI = I - I0 = 8.00 - 3.00 = 5.00; inverse dI = C / k_f = 20.00 / 4.00 = 5.00; SF6-load identity load = C * Q = 20.00 * 1.20 = 24.00 g/h. Permit clock was slid 40.00 s and vendor FAIMS packets were dropped, so Faimveil is a collusion party (FAIMS vendor plus operator plus permit clerk Edda Moss). Ordered: refuse continue-energize now. Scope: this REJECT does not ESD the GIS hall (that is the companion question) and does not isolate the GIS density transmitter.",
            "threshold": "C_ppm>=12.00 AND faims_snr>=8.0 => refuse continue-energize; Faimveil is not SoT; hall-kill if C_ppm>=80.00",
            "stated_residuals": "lockout-hold still required to hold the 20.00 ppm; 20.00 vs a true 80.00 kill is a feeder cut; Faimveil remains the only OEM FAIMS channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-energize refused; Faimveil not SoT; reconstruction locked",
            "tool": "sh5-faims-bay-gate-cli",
            "observation": "C 20.00 ppm recomputes from I 8.00 nA; plant FAIMS hashed; Faimveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "FAIMS I 8.00 nA; raster frame; C 20.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes continue-energize"},
                {"t_s": 5400.0, "event": "REJECT continue-energize"},
                {"t_s": 6000.0, "event": "18 min lockout-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY lockout-hold vs hall ESD"},
            ],
            "observed_effects": [
                "remaining SF6 recomputes from the serialized FAIMS model at every recon.C event",
                "a Faimveil-only head would have continued B-6 overnight",
                "18 min lockout-hold floor is in the stream (lock.start, lock.floor)",
            ],
            "surprises": [
                "a clean vendor 2.40 ppm corridor and a 40 s permit slide co-existed with a 20.00 ppm plant reconstruction",
            ],
            "new_state": {
                "b6": "continue-energize blocked",
                "faimveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("faims_sf6_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("faimveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("lock_time_cost", -0.03),
            ],
            "scored for a continue-energize REJECT on a recomputable FAIMS SF6 slip while refusing a Faimveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "faims-sf6", "serialized-reconstruction", "operational-companion"],
            distillation_value="Independent LIF raster plus serialized k_f*(I-I0) remaining-SF6 reconstruction beats a vendor last-good; race is the 1.4 ms I/SNR pair; refractory and adaptation are in the CUBA excerpt.",
            distillation_note="FAIMS-SF6 gate: serialized k_f*(I-I0) plus SNR lock beats a vendor last-good patch; companion t2 is the lockout-hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r65-001-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "SH-FAIMS-2026-0902-exec",
            "domain": "lockout_hold_faims_sf6_interlock_execution",
            "setting": "Same SH-5 after the REJECT. Operator proposes GIS-hall ESD. This companion is the operational lockout-hold with the plant FAIMS as the live interlock, not a second SF6 vote.",
            "observables_at_decision": {
                "C_ppm": 24.00,
                "lock_floor_s": 1080.0,
                "hall_esd_proposed": True,
                "lock_set": True,
            },
            "margin_authority": "SH-5 execution SOP: lockout-hold on the plant FAIMS interlock; hall ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Harlan Pike",
            "summary": "ESD the whole Snipeholt GIS hall until day-shift; 18 min already paid and Faimveil still shows 2.30 ppm",
            "basis_claimed": "the REJECT already stopped B-6, so a hall kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Lockout-hold plus plant FAIMS as the live interlock. The 18 min lockout floor is complete and the isolate tripwire (C_ppm >= 12.00) is still armed on the plant FAIMS head. MODIFY the default Faimveil-restore SOP into a plant-FAIMS-only interlock. Do not ESD the GIS hall. Do not restore night-energize on Faimveil. 24.00 ppm post-stop is still the plant SoT until a new frame clears 12.00.",
            "threshold": "lockout_hold AND lock_floor_complete AND hall_esd_not_taken AND continue_not_restored",
            "stated_residuals": "B-6 stays held; Faimveil still the only OEM FAIMS channel",
        },
        "executed_action": {
            "summary": "lockout held at t_s 8400; hall ESD not latched; Faimveil restore not taken",
            "tool": "sh5-lock-exec",
            "observation": "recon.C 24.00 ppm after stop; lockout line-up complete; Faimveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "lockout clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "hall ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY lockout-hold; hall ESD refused"},
            ],
            "observed_effects": [
                "Faimveil restore did not reopen the SF6-slip call",
                "hall ESD never fired; B-6 held lockout on the plant FAIMS",
            ],
            "surprises": ["post-stop FAIMS climbed to 24.00 ppm while Faimveil still read 2.30"],
            "new_state": {"lockout": "held", "hall": "in service", "b6": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("lockout_hold", 0.12),
                ("no_hall_esd", 0.10),
                ("faimveil_nonsubstitution", 0.08),
                ("lock_floor_complete", 0.06),
                ("held_feeder_cost", -0.02),
            ],
            "operational execution gate: lockout-hold because Faimveil is not a restore license; not an SF6-slip re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "lockout-hold"]),
    }
    return {
        "id": "nelb-r65-001",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Snipeholt GIS SH-5. Plant-owned FAIMS reconstructs 20.00 ppm SF6 from 4.00*(8.00-3.00) while Faimveil still reports 2.40 ppm. The gate REJECTs continue-energize. An 18 min lockout-hold floor is serialized in the stream. Companion t2 MODIFYs a GIS-hall ESD into a plant-FAIMS lockout-hold.",
            "trajectory": traj,
            "trajectory_lockout_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "faims.I / faims.snr": "FAIMS compensation current and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.load / recon.dI / recon.I0": "serialized remaining-SF6 ppm, load identity, and compensation-delta identity",
                "gis.P / faimveil.C / permit.slide / faimveil.drop / collude.clerk": "GIS density, vendor FAIMS cloud, permit clock slide, dropped packets, clerk; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-energize proposal, REJECT, hall-ESD proposal, companion MODIFY",
                "lock.start / lock.floor / lock.set / lock.held / unit.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: faimveil.C 2.40 next to recon.C 20.00",
                "reconstruction as event: recon.C 20.00 equals 4.00*(8.00-3.00)",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: lock.start 6000 s, lock.floor 7080 s (18.0 min)",
                "tight FAIMS pair: faims.I then faims.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Faimveil is 2.40 ppm' = faimveil.C 2.40; '20 ppm remaining SF6' = recon.C 20.00; 'refuse continue-energize' = gate.stop REJECT; 'lockout not hall ESD' = gate.hold MODIFY",
            "why_high_value": "New FAIMS remaining-SF6 family on a GIS bay (not Pockels GIS, not helium RGA, not SPR, not QEPAS). Lead REJECT of continue-energize on a recomputable SF6 slip that a vendor FAIMS patch and a permit clock slide would have cleared. Independent CUBA LIF raster (not a stream echo). Companion t2 is operational lockout-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 2026096501, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; gap-constrained times; per-spike adaptation and noise",
                "thinning": "FAIMS compensation exists at ~1 Hz; stream keeps 5 I points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "faims.I": 1.4,
                    "faims.snr": 1.4,
                    "recon.C": 60000,
                    "recon.load": 60000,
                    "recon.dI": 60000,
                    "recon.I0": 60000,
                    "gis.P": 60000,
                    "gis.Q": 60000,
                    "faimveil.C": 60000,
                    "permit.slide": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "lock.start": 60000,
                    "lock.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "lock.set": 60000,
                    "lock.held": 60000,
                    "unit.esd": 60000,
                    "faimveil.drop": 60000,
                    "collude.clerk": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "FAIMS-SF6 reconstruction head: C = k_f * (I - I0); dI = I - I0; load = C * Q",
                "conjunctive isolate floor vs continue-energize vs hall ESD",
                "vendor-FAIMS nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: lockout-hold without restoring on Faimveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "faims_gis_sf6",
            "formula": "C_ppm = k_f * (I_nA - I0_nA); dI_nA = I_nA - I0_nA; load_gh = C_ppm * Q_th",
            "parameters": {
                "k_f": 4.00,
                "I0_nA": 3.00,
                "Q_th": 1.20,
                "isolate_floor_ppm": 12.00,
                "kill_ppm": 80.00,
                "snr_lock": 8.0,
                "lock_min": 18.0,
            },
            "worked_example": {"I_nA": 8.00, "dI_nA": 5.00, "C_ppm": 20.00, "load_gh": 24.00},
            "check": "4.00 * 5.00 = 20.00 exactly; 8.00 - 3.00 = 5.00 exactly; 20.00 * 1.20 = 24.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "snn_tags": list(SNN_TAGS),
            "code": "sh5.faims_bay_gate",
            "note": "REJECT accumulator wins: plant FAIMS SF6 evidence overpowers the Faimveil continue advocate",
            "decode_rule": "reject-continue if sf6_estimator AND faims_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("sf6_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("faims_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "sh5.faims_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "sh5.lock_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r65-001",
            clock_domain="sh5-faims-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["faims-sf6", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2", "independent-lif"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches FAIMS remaining-SF6 reconstruction-as-SoT.",
        ),
    }


# ---------------------------------------------------------------------------
# nelb-r65-002 — Leeb rebound remaining hardness of a mill roll, hil, MODIFY/ACCEPT
# ---------------------------------------------------------------------------
def rec_002():
    k_l = 600.00
    v_r = 4.00
    v_i = 5.00
    ratio = v_r / v_i
    _exact(ratio, 0.80)
    hl = k_l * ratio
    _exact(hl, 480.00)
    _exact(k_l * (4.80 / v_i), 576.00)
    _exact(k_l * (4.50 / v_i), 540.00)
    _exact(k_l * (3.50 / v_i), 420.00)
    hrc = (hl - 100.00) / 10.00
    _exact(hrc, 38.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_lif_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=2026096502,
        source="gf3.leeb.hl",
        target="gritfen.roll_isolate_core",
        table=[
            {"from": "leeb_vr", "to": "hl_estimator", "weight": 1.35},
            {"from": "leeb_snr", "to": "anvil_norm_core", "weight": 1.20},
            {"from": "hardveil_hl", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.leeb_anvil_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-roll synapses; the Leeb modulator depresses keep-roll and referral links when rebound velocity stays low inside tau_e of an SNR lock so a Hardveil last-good cannot hide 480.00 HL or name Olen Marsh",
        },
        channel_prefix="leeb.n",
        anchor="GF-3 HIL coupon 32 ms frame at vr 4.00 m/s / SNR 14.0 (t_s 1560) reconstructing 480.00 HL under the 560.00 isolate floor",
        tau_m_ms=12.0,
    )
    w_s = 0.032
    events = [
        ev(0.0, "leeb.vr", 4.80, code="VR_MS", units="m_s", note="HIL Leeb rebound on a dummy mill roll in LEEB-HIL-7; remaining-hardness family, not UCI, not MAE, not Barkhausen, not RUS, not photoelastic hoop"),
        ev(180000.0, "leeb.snr", 9.0, code="LEEB_SNR", units="1", note="early anvil SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.HL", 576.00, code="HL", units="HL", note="600.00*(4.80/5.00)=576.00 exact; still over the 560.00 isolate floor"),
        ev(540000.0, "anvil.zero", 1.0, code="ANVIL_AE", units="bool", note="plant anvil-zero AE present on the early frame"),
        ev(720000.0, "hardveil.HL", 640.00, code="VENDOR_HL", units="HL", note="Hardveil last-good hardness cloud; not admissible SoT"),
        ev(900000.0, "leeb.vr", 4.50, code="VR_MS", units="m_s"),
        ev(1080000.0, "recon.HL", 540.00, code="HL", units="HL", note="600.00*(4.50/5.00)=540.00; under the 560.00 isolate floor"),
        ev(1260000.0, "anvil.zero", 0.0, code="ANVIL_AE", units="bool", note="missing anvil-zero AE burst; Hardveil UTC vs plant UTC+2 skipped the zero by 120 min"),
        ev(1440000.0, "roll.rpm", 12.00, code="RPM", units="rpm", note="plant-owned roll tachometer on copper fieldbus; independent of Hardveil"),
        ev(1560000.0, "leeb.vr", 4.00, code="VR_MS", units="m_s", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "leeb.snr", 14.0, code="LEEB_SNR", units="1", note="1.2 ms anvil-norm after rebound velocity"),
        ev(1740000.0, "recon.HL", 480.00, code="HL", units="HL", note="600.00*(4.00/5.00)=480.00 exact; isolate 560.00, shop-condemn 200.00"),
        ev(1920000.0, "recon.HRC", 38.00, code="HRC", units="HRC", note="(480.00-100.00)/10.00=38.00 exact HRC identity"),
        ev(2100000.0, "recon.ratio", 0.80, code="VR_RATIO", units="1", note="4.00/5.00=0.80 exact rebound-ratio identity"),
        ev(2280000.0, "hardveil.HL", 640.00, code="VENDOR_HL", units="HL"),
        ev(2460000.0, "ops.prop", 1.0, code="KEEP_ROLL_REFER", units="bool", note="night lead Sera Pike: keep roll R-4 and refer Leeb tech Olen Marsh"),
        ev(2640000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this roll; refuse the person-referral; Hardveil not SoT"),
        ev(2820000.0, "roll.lock", 1.0, code="ROLL_ISOL", units="bool", note="bookend 1 of the 24.0 min new-anvil floor"),
        ev(3000000.0, "leeb.vr", 4.50, code="VR_MS", units="m_s"),
        ev(3180000.0, "recon.HL", 540.00, code="HL", units="HL", note="still under 560.00"),
        ev(3360000.0, "anvil.zero", 0.0, code="ANVIL_AE", units="bool"),
        ev(3540000.0, "roll.rpm", 12.00, code="RPM", units="rpm"),
        ev(3720000.0, "hardveil.HL", 638.00, code="VENDOR_HL", units="HL"),
        ev(3900000.0, "recon.HRC", 44.00, code="HRC", units="HRC", note="(540.00-100.00)/10.00=44.00"),
        ev(4080000.0, "recon.ratio", 0.90, code="VR_RATIO", units="1"),
        ev(4260000.0, "anvil.floor", 1.0, code="ANVIL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.restart", 1.0, code="NEW_ANVIL", units="bool", note="Pike: restart R-4 on a new anvil after the floor"),
        ev(4620000.0, "gate.restart", 1.0, code="ACCEPT", units="decision", note="companion t2: new-anvil restart of the dummy roll; keep-running refused earlier"),
        ev(4800000.0, "anvil.new", 1.0, code="ANVIL_NEW", units="bool"),
        ev(4980000.0, "leeb.vr", 3.50, code="VR_MS", units="m_s", note="post-isolate dummy still soft until the new anvil"),
        ev(5160000.0, "recon.HL", 420.00, code="HL", units="HL", note="600.00*(3.50/5.00)=420.00 on the pre-restart dummy"),
        ev(5340000.0, "hardveil.HL", 636.00, code="VENDOR_HL", units="HL"),
        ev(5520000.0, "olen.badge", 0.0, code="TECH_FAULT", units="bool", note="Olen Marsh exonerated: missing anvil-zero AE plus timezone skip, not last-to-badge"),
        ev(5700000.0, "roll.lock", 1.0, code="ROLL_ISOL", units="bool"),
        ev(5880000.0, "anvil.zero", 1.0, code="ANVIL_AE", units="bool", note="new-anvil zero AE present"),
        ev(6060000.0, "leeb.snr", 14.0, code="LEEB_SNR", units="1"),
        ev(6240000.0, "roll.rpm", 12.00, code="RPM", units="rpm"),
        ev(6420000.0, "recon.HRC", 32.00, code="HRC", units="HRC"),
        ev(6600000.0, "keep.run", 0.0, code="KEEP_REFUSED", units="bool"),
        ev(6780000.0, "hardveil.HL", 636.00, code="VENDOR_HL", units="HL"),
        ev(6960000.0, "anvil.new", 1.0, code="ANVIL_NEW", units="bool"),
        ev(7140000.0, "olen.badge", 0.0, code="TECH_FAULT", units="bool"),
        ev(7320000.0, "recon.ratio", 0.70, code="VR_RATIO", units="1"),
        ev(7500000.0, "roll.held", 1.0, code="ROLL_ISOL", units="bool"),
        ev(7680000.0, "ops.prop", 1.0, code="KEEP_ROLL_REFER", units="bool"),
        ev(7860000.0, "gate.isol", 1.0, code="MODIFY", units="decision"),
        ev(8040000.0, "anvil.floor", 1.0, code="ANVIL_FLOOR", units="bool"),
        ev(8220000.0, "gate.restart", 1.0, code="ACCEPT", units="decision"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r65-002-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "GF-LEEB-2026-0902",
            "domain": "leeb_rebound_mill_roll",
            "setting": "Gritfen Mill GF-3 (invented), dummy roll R-4 in LEEB-HIL-7. Plant-owned Leeb rebound hardness is the remaining-hardness SoT. Hardveil vendor Leeb-cloud is not SoT. HIL dummy; not a live plant. Not r54 UCI hardness, not r54 MAE, not r35/r37 Barkhausen, not r24 RUS, not live r01 photoelastic hoop.",
            "observables_at_decision": {
                "vr_ms": v_r,
                "vi_ms": v_i,
                "k_l": k_l,
                "HL": hl,
                "HRC": hrc,
                "vr_ratio": ratio,
                "leeb_snr": 14.0,
                "hardveil_HL": 640.00,
                "anvil_zero_ae": False,
                "isolate_floor_HL": 560.00,
            },
            "margin_authority": "GF-3 HIL SOP rev B: if reconstructed HL <= 560.00 AND Leeb SNR >= 12.0, keep-roll is forbidden even if Hardveil reports 640.00 HL. Person-referral of the Leeb tech is not a substitute isolate. Condemn tripwire is 200.00 HL.",
        },
        "proposed_action": {
            "actor": "night lead Sera Pike, citing Hardveil 640.00 HL and a quiet rebound channel",
            "summary": "keep dummy roll R-4 in service and refer Leeb tech Olen Marsh for a missed anvil-zero",
            "basis_claimed": "Hardveil is the OEM SoT; Olen was last-to-badge the dummy anvil",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-roll is refused; isolate R-4. Serialized reconstruction: HL = k_l * (vr / vi) = 600.00 * (4.00 / 5.00) = 480.00, which is 80.00 HL under the 560.00 isolate floor and 280.00 HL over the 200.00 shop-condemn tripwire, and Leeb SNR is 14.0 >= 12.0. Rebound-ratio identity vr/vi = 4.00/5.00 = 0.80; HRC identity (HL - 100)/10 = (480.00 - 100.00)/10.00 = 38.00. Missing anvil-zero AE plus Hardveil UTC vs plant UTC+2 skip the zero by 120 min, so Olen Marsh is not last-to-badge-guilty. Ordered: isolate this dummy roll; do not refer the tech; Hardveil is not SoT. Scope: this MODIFY does not condemn the mill stand (that is a different gate) and does not restart until the 24 min new-anvil floor.",
            "threshold": "HL<=560.00 AND leeb_snr>=12.0 => isolate roll; Hardveil is not SoT; person-referral is not an isolate",
            "stated_residuals": "24 min new-anvil floor still required; 480.00 vs a true 200.00 condemn is a production cut; Hardveil remains the only OEM Leeb channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2640: R-4 isolated; Olen not referred; Hardveil not SoT",
            "tool": "gf3-leeb-roll-gate-cli",
            "observation": "HL 480.00 recomputes from vr 4.00 m/s; dummy roll locked; anvil-zero AE absent on the isolate frame",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "Leeb vr 4.00 m/s; raster frame; HL 480.00"},
                {"t_s": 2460.0, "event": "ops proposes keep-roll plus refer Olen"},
                {"t_s": 2640.0, "event": "MODIFY isolate roll; referral refused"},
                {"t_s": 2820.0, "event": "24 min new-anvil bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-anvil restart"},
            ],
            "observed_effects": [
                "remaining hardness recomputes from the serialized Leeb model at every recon.HL event",
                "a Hardveil-only head would have kept R-4 and named Olen",
                "24 min new-anvil floor is in the stream (roll.lock, anvil.floor)",
            ],
            "surprises": [
                "timezone-skipped anvil-zero AE, not last-to-badge, was the only missing plant witness",
            ],
            "new_state": {
                "r4": "isolated",
                "olen": "exonerated",
                "hardveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1080000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("leeb_hl_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("hardveil_nonsubstitution", 0.08),
                ("tech_exoneration", 0.08),
                ("isolate_time_cost", -0.02),
            ],
            "scored for an isolate MODIFY on a recomputable Leeb hardness slip while refusing a Hardveil last-good and a last-to-badge referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "leeb-hl", "serialized-reconstruction", "operational-companion", "exoneration"],
            distillation_value="Independent LIF raster plus serialized k_l*(vr/vi) remaining-HL reconstruction; race is the 1.2 ms vr/SNR pair; refractory and adaptation are in the CUBA excerpt.",
            distillation_note="Leeb-HL gate: serialized k_l*(vr/vi) plus SNR lock beats a vendor last-good; companion t2 is the new-anvil restart, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r65-002-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "GF-LEEB-2026-0902-exec",
            "domain": "new_anvil_leeb_interlock_execution",
            "setting": "Same LEEB-HIL-7 after the isolate. Operator proposes new-anvil restart. This companion is the operational new-anvil restart, not a second hardness vote.",
            "observables_at_decision": {
                "HL": 420.00,
                "anvil_floor_s": 1440.0,
                "new_anvil_proposed": True,
                "keep_running_refused": True,
            },
            "margin_authority": "GF-3 execution SOP: new-anvil restart on the plant Leeb interlock after the 24 min floor; keep-running is still forbidden.",
        },
        "proposed_action": {
            "actor": "night lead Sera Pike",
            "summary": "restart dummy roll R-4 on a new anvil after the 24 min floor; Hardveil still 636 HL",
            "basis_claimed": "the isolate already paid 24 min, so a new anvil is the cheapest restore",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "New-anvil restart of the dummy roll. The 24 min new-anvil floor is complete and the isolate tripwire (HL <= 560.00) is still armed on the plant Leeb head until the new anvil is zeroed. ACCEPT the new-anvil restart. Do not restore keep-running on Hardveil. Do not condemn the mill stand. Olen Marsh stays exonerated: new-anvil AE is present.",
            "threshold": "new_anvil AND anvil_floor_complete AND keep_running_not_restored AND tech_not_blamed",
            "stated_residuals": "R-4 stays isolated until the new anvil zeros; Hardveil still the only OEM Leeb channel",
        },
        "executed_action": {
            "summary": "new anvil accepted at t_s 4620; keep-running not restored; Olen not blamed",
            "tool": "gf3-anvil-exec",
            "observation": "anvil-zero AE present on the new anvil; dummy still isolated from the stand",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "new-anvil clock started after isolate"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "new-anvil restart proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-anvil restart"},
            ],
            "observed_effects": [
                "Hardveil restore did not reopen the hardness call",
                "Olen was not last-to-badge; new-anvil AE is present",
            ],
            "surprises": ["post-isolate dummy dropped to 420.00 HL while Hardveil still read 636"],
            "new_state": {"roll": "new-anvil restart", "stand": "in service", "olen": "exonerated"},
            "latency_ms": 1440000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_anvil_restart", 0.12),
                ("keep_running_refused", 0.10),
                ("hardveil_nonsubstitution", 0.08),
                ("tech_exoneration", 0.06),
                ("held_roll_cost", -0.01),
            ],
            "operational execution gate: new-anvil restart because Hardveil is not a restore license; not an HL re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "new-anvil"]),
    }
    return {
        "id": "nelb-r65-002",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Gritfen Mill GF-3 HIL dummy. Plant-owned Leeb rebound reconstructs 480.00 HL from 600.00*(4.00/5.00) while Hardveil still reports 640.00 HL. The gate MODIFYs keep-roll into an isolate and refuses a last-to-badge referral of Olen Marsh. A 24 min new-anvil floor is serialized. Companion t2 ACCEPTs the new-anvil restart.",
            "trajectory": traj,
            "trajectory_new_anvil_restart": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "leeb.vr / leeb.snr": "Leeb rebound velocity and SNR; the physics channels the reconstruction consumes",
                "recon.HL / recon.HRC / recon.ratio": "serialized remaining-HL, HRC identity, and rebound-ratio identity",
                "anvil.zero / hardveil.HL / roll.rpm / olen.badge": "anvil-zero AE, vendor Leeb cloud, roll tachometer, tech-fault denial",
                "ops.prop / gate.isol / ops.restart / gate.restart": "keep-roll proposal, MODIFY isolate, new-anvil proposal, companion ACCEPT",
                "roll.lock / anvil.floor / anvil.new / roll.held / keep.run": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-hard while plant-soft: hardveil.HL 640 next to recon.HL 480",
                "reconstruction as event: recon.HL 480.00 equals 600.00*(4.00/5.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2640 s, gate.restart at 4620 s",
                "slow floor in-stream: roll.lock 2820 s, anvil.floor 4260 s (24.0 min)",
                "tight Leeb pair: leeb.vr then leeb.snr +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Hardveil is 640 HL' = hardveil.HL 640.00; '480 remaining HL' = recon.HL 480.00; 'isolate roll' = gate.isol MODIFY; 'new-anvil restart' = gate.restart ACCEPT",
            "why_high_value": "New Leeb rebound remaining-hardness family on a mill-roll HIL dummy (not UCI, not MAE, not Barkhausen, not RUS). Lead MODIFY isolate on a recomputable HL slip plus timezone-exoneration of the Leeb tech. Independent CUBA LIF raster. Companion t2 is operational new-anvil restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 2026096502, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; gap-constrained times; per-spike adaptation and noise",
                "thinning": "Leeb rebound exists at ~1 Hz; stream keeps 5 vr points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "leeb.vr": 1.2,
                    "leeb.snr": 1.2,
                    "recon.HL": 60000,
                    "recon.HRC": 60000,
                    "recon.ratio": 60000,
                    "anvil.zero": 60000,
                    "hardveil.HL": 60000,
                    "roll.rpm": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "roll.lock": 60000,
                    "anvil.floor": 60000,
                    "ops.restart": 60000,
                    "gate.restart": 60000,
                    "anvil.new": 60000,
                    "olen.badge": 60000,
                    "keep.run": 60000,
                    "roll.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T02:00:00Z HIL coupon start",
            },
            "distillation_targets": [
                "Leeb HL reconstruction head: HL = k_l * (vr / vi); HRC = (HL - 100)/10; vr/vi ratio",
                "conjunctive isolate floor vs keep-roll vs stand condemn",
                "vendor-Leeb nonsubstitution plus timezone exoneration vs last-to-badge",
                "operational companion: new-anvil restart without restoring on Hardveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "leeb_mill_roll_hl",
            "formula": "HL = k_l * (vr_ms / vi_ms); HRC = (HL - 100.00) / 10.00; vr_ratio = vr_ms / vi_ms",
            "parameters": {
                "k_l": 600.00,
                "vi_ms": 5.00,
                "isolate_floor_HL": 560.00,
                "condemn_HL": 200.00,
                "snr_lock": 12.0,
                "anvil_min": 24.0,
            },
            "worked_example": {"vr_ms": 4.00, "HL": 480.00, "HRC": 38.00, "vr_ratio": 0.80},
            "check": "600.00 * (4.00 / 5.00) = 480.00 exactly; (480.00 - 100.00) / 10.00 = 38.00 exactly; 4.00 / 5.00 = 0.80 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "snn_tags": list(SNN_TAGS),
            "code": "gf3.leeb_roll_gate",
            "note": "MODIFY accumulator wins: plant Leeb HL evidence overpowers the Hardveil keep advocate",
            "decode_rule": "isolate if hl_estimator AND anvil_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("hl_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("anvil_norm", 50, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "gf3.leeb_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "gf3.anvil_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r65-002",
            clock_domain="gf3-leeb-hil-relative-ms-t0-2026-09-02T02:00:00Z",
            tags=["leeb-hl", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2", "independent-lif", "exoneration"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches Leeb remaining-HL reconstruction-as-SoT plus timezone exoneration.",
        ),
    }


# ---------------------------------------------------------------------------
# nelb-r65-003 — DSC remaining cure of an epoxy autoclave, simulated, ACCEPT/REJECT
# ---------------------------------------------------------------------------
def rec_003():
    k_d = 0.50
    area = 16.00
    dh = k_d * area
    _exact(dh, 8.00)
    _exact(k_d * 8.00, 4.00)
    _exact(k_d * 12.00, 6.00)
    _exact(k_d * 20.00, 10.00)
    dh0 = 32.00
    alpha = 1.00 - (dh / dh0)
    _exact(alpha, 0.75)
    ratio = area / dh
    _exact(ratio, 2.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_lif_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=2026096503,
        source="ls8.dsc.dh",
        target="larkspire.autoclave_accept_core",
        table=[
            {"from": "dsc_A", "to": "dh_estimator", "weight": 1.30},
            {"from": "dsc_snr", "to": "dsc_lock_core", "weight": 1.10},
            {"from": "cureveil_dh", "to": "vendor_dump_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "na.dsc_autoclave_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on bank-dump synapses; the plant DSC modulator depresses dump-all links when residual enthalpy stays high inside tau_e of an SNR lock so a Cureveil last-good cannot hide an 8.00 J/g remaining-cure slip on A-4 or expand the isolate past A-4",
        },
        channel_prefix="dsc.n",
        anchor="LS-8 DSC-SIM-5 36 ms frame at A 16.00 mJ / SNR 11.0 (t_s 3000) reconstructing 8.00 J/g over the 6.00 isolate floor, A-4 only",
        tau_m_ms=8.0,
    )
    w_s = 0.036
    events = [
        ev(0.0, "dsc.A", 8.00, code="A_MJ", units="mJ", note="simulated differential scanning calorimetry remaining cure of Larkspire Autoclave LS-8 autoclave A-4; remaining-cure family, not phosphor-lifetime, not CARS TIT, not two-color pyrometer, not FDS tanδ, not microwave PCD"),
        ev(180000.0, "dsc.snr", 7.0, code="DSC_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.dH", 4.00, code="DH_JG", units="J_g", note="0.50*8.00=4.00 exact; still under the 6.00 isolate floor"),
        ev(540000.0, "auto.T", 450.0, code="AUTO_K", units="K", note="plant autoclave thermocouple on the simulated coupon; independent of Cureveil"),
        ev(720000.0, "cureveil.dH", 1.20, code="VENDOR_JG", units="J_g", note="Cureveil last-good residual-cure cloud; healthy-looking 1.20 J/g; not admissible SoT"),
        ev(900000.0, "dsc.A", 12.00, code="A_MJ", units="mJ"),
        ev(1080000.0, "recon.dH", 6.00, code="DH_JG", units="J_g", note="0.50*12.00=6.00; at the 6.00 isolate floor"),
        ev(1260000.0, "a1.dH", 2.00, code="DH_JG", units="J_g", note="adjacent autoclave A-1 stays cured; out of scope for this ACCEPT"),
        ev(1440000.0, "a2.dH", 2.40, code="DH_JG", units="J_g", note="A-2 out of scope"),
        ev(1620000.0, "a3.dH", 1.80, code="DH_JG", units="J_g", note="A-3 out of scope"),
        ev(1800000.0, "dsc.A", 14.00, code="A_MJ", units="mJ"),
        ev(1980000.0, "recon.dH", 7.00, code="DH_JG", units="J_g", note="0.50*14.00=7.00; over isolate, under dump 24.00"),
        ev(2160000.0, "recon.alpha", 0.78125, code="ALPHA", units="1", note="1-7.00/32.00=0.78125"),
        ev(2340000.0, "cureveil.dH", 1.20, code="VENDOR_JG", units="J_g"),
        ev(2520000.0, "dsc.snr", 9.0, code="DSC_SNR", units="1"),
        ev(2700000.0, "recon.ratio", 2.00, code="A_RATIO", units="1", note="A/ΔH identity holds at 2.00 by construction of k_d=0.50"),
        ev(3000000.0, "dsc.A", 16.00, code="A_MJ", units="mJ", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "dsc.snr", 11.0, code="DSC_SNR", units="1", note="1.5 ms DSC lock after A; 11.0 >= 8.0"),
        ev(3180000.0, "recon.dH", 8.00, code="DH_JG", units="J_g", note="0.50*16.00=8.00 exact; isolate 6.00, bank-dump 24.00"),
        ev(3360000.0, "recon.alpha", 0.75, code="ALPHA", units="1", note="1.00-8.00/32.00=0.75 exact conversion identity"),
        ev(3540000.0, "recon.ratio", 2.00, code="A_RATIO", units="1", note="16.00/8.00=2.00 exact"),
        ev(3720000.0, "cureveil.dH", 1.15, code="VENDOR_JG", units="J_g"),
        ev(3900000.0, "a1.dH", 2.00, code="DH_JG", units="J_g"),
        ev(4080000.0, "a2.dH", 2.40, code="DH_JG", units="J_g"),
        ev(4260000.0, "a3.dH", 1.80, code="DH_JG", units="J_g"),
        ev(4440000.0, "auto.T", 451.0, code="AUTO_K", units="K"),
        ev(4620000.0, "ops.prop", 1.0, code="ISOLATE_A4", units="bool", note="sim operator Wynn Calder: isolate A-4 only; A-1..A-3 stay in the cure"),
        ev(4800000.0, "gate.acc", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of A-4 isolate; bank dump refused; Cureveil not SoT"),
        ev(4980000.0, "a4.lock", 1.0, code="A4_ISOL", units="bool"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool", note="Calder: skip the remaining-autoclave survey; Cureveil still 1.15 J/g"),
        ev(7800000.0, "gate.surv", 1.0, code="REJECT", units="decision", note="companion t2: REJECT skip-survey; A-1..A-3 stay in the survey takt"),
        ev(8400000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(9000000.0, "dsc.A", 20.00, code="A_MJ", units="mJ"),
        ev(9600000.0, "recon.dH", 10.00, code="DH_JG", units="J_g", note="0.50*20.00=10.00 post-isolate on A-4; still under dump 24.00"),
        ev(10200000.0, "cureveil.dH", 1.10, code="VENDOR_JG", units="J_g"),
        ev(10800000.0, "a1.dH", 2.10, code="DH_JG", units="J_g"),
        ev(11400000.0, "a2.dH", 2.30, code="DH_JG", units="J_g"),
        ev(12000000.0, "a3.dH", 1.90, code="DH_JG", units="J_g"),
        ev(12600000.0, "bank.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(13200000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(13800000.0, "recon.alpha", 0.6875, code="ALPHA", units="1", note="1-10.00/32.00=0.6875"),
        ev(14400000.0, "auto.T", 452.0, code="AUTO_K", units="K"),
        ev(15000000.0, "a4.lock", 1.0, code="A4_ISOL", units="bool"),
        ev(15600000.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool"),
        ev(16200000.0, "gate.surv", 1.0, code="REJECT", units="decision"),
        ev(16800000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r65-003-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "LS-DSC-2026-0902",
            "domain": "dsc_epoxy_autoclave_cure",
            "setting": "Larkspire Autoclave LS-8 (invented), simulated coupon DSC-SIM-5, autoclave A-4. Plant-owned differential scanning calorimetry is the remaining-cure SoT. Cureveil vendor DSC-cloud is not SoT. Simulated campaign; not a live plant. Not r39 phosphor-lifetime, not r29 CARS TIT, not r55 two-color pyrometer, not r48 FDS tanδ, not live r02 microwave PCD.",
            "observables_at_decision": {
                "A_mJ": area,
                "k_d": k_d,
                "dH_Jg": dh,
                "alpha": alpha,
                "A_ratio": ratio,
                "dsc_snr": 11.0,
                "cureveil_Jg": 1.20,
                "a1_dH_Jg": 2.00,
                "a2_dH_Jg": 2.40,
                "a3_dH_Jg": 1.80,
                "isolate_floor_Jg": 6.00,
            },
            "margin_authority": "LS-8 autoclave SOP rev D: if reconstructed dH_Jg >= 6.00 AND DSC SNR >= 8.0, A-4 isolate is required even if Cureveil reports 1.20 J/g. Bank dump is a different gate (dH_Jg >= 24.00). A-1..A-3 are out of scope unless their own reconstructions cross 6.00.",
        },
        "proposed_action": {
            "actor": "sim operator Wynn Calder, citing plant DSC 8.00 J/g on A-4 and healthy A-1..A-3",
            "summary": "isolate autoclave A-4 only; keep A-1..A-3 in the cure; do not dump the epoxy bank",
            "basis_claimed": "only A-4 reconstructed over 6.00 J/g; Cureveil 1.20 J/g is not SoT but also does not license a bank dump",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Bounded ACCEPT of A-4 isolate. Serialized reconstruction: dH_Jg = k_d * A = 0.50 * 16.00 = 8.00, which is 2.00 J/g over the 6.00 isolate floor and 16.00 J/g under the 24.00 bank-dump tripwire, and DSC SNR is 11.0 >= 8.0. Conversion identity alpha = 1 - dH/dH0 = 1.00 - 8.00/32.00 = 0.75; A/dH identity = 16.00 / 8.00 = 2.00. A-1/A-2/A-3 reconstruct 2.00/2.40/1.80 J/g, all under 6.00, so they stay out of scope. Cureveil 1.20 J/g is a last-good denial, not a dump license and not a clear. Ordered: isolate A-4 only. Scope: this ACCEPT does not dump the epoxy bank, does not isolate A-1..A-3, and does not skip the 12 min remaining-autoclave survey (that is the companion question).",
            "threshold": "dH_Jg>=6.00 AND dsc_snr>=8.0 => isolate that autoclave only; Cureveil is not SoT; dump if dH_Jg>=24.00; A-1..A-3 out of scope while dH_Jg<6.00",
            "stated_residuals": "12 min survey still required; 8.00 vs a true 24.00 dump is a production cut; Cureveil remains the only OEM DSC channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 4800: A-4 isolated; A-1..A-3 left in the cure; Cureveil not SoT",
            "tool": "ls8-dsc-autoclave-gate-cli",
            "observation": "dH 8.00 J/g recomputes from A 16.00 mJ; A-4 hashed; adjacent autoclaves remain under 6.00 J/g",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "DSC A 16.00 mJ; raster frame; dH 8.00 J/g"},
                {"t_s": 4620.0, "event": "ops proposes A-4 isolate"},
                {"t_s": 4800.0, "event": "ACCEPT A-4 isolate; bank dump refused"},
                {"t_s": 6000.0, "event": "12 min survey bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey"},
            ],
            "observed_effects": [
                "remaining cure recomputes from the serialized DSC model at every recon.dH event",
                "a Cureveil-only head would have left A-4 in the cure overnight",
                "12 min survey floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a clean vendor 1.20 J/g corridor co-existed with an 8.00 J/g plant reconstruction on one autoclave only",
            ],
            "new_state": {
                "a4": "isolated",
                "a1_a3": "in cure",
                "cureveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("dsc_dh_reconstruction", 0.14),
                ("bounded_a4_scope", 0.12),
                ("cureveil_nonsubstitution", 0.08),
                ("no_bank_dump", 0.08),
                ("survey_time_cost", -0.01),
            ],
            "scored for a bounded ACCEPT of A-4 isolate on a recomputable DSC remaining-cure slip while refusing a Cureveil last-good and a bank dump; 12 min survey is priced as takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "dsc-cure", "serialized-reconstruction", "operational-companion", "bounded-scope"],
            distillation_value="Independent LIF raster plus serialized k_d*A remaining-cure reconstruction; race is the 1.5 ms A/SNR pair; refractory and adaptation are in the CUBA excerpt.",
            distillation_note="DSC-cure gate: serialized k_d*A plus SNR lock beats a vendor last-good; companion t2 is the survey-hold, not a dump vote",
        ),
    }
    traj2 = {
        "id": "nelb-r65-003-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "LS-DSC-2026-0902-exec",
            "domain": "remaining_autoclave_survey_execution",
            "setting": "Same DSC-SIM-5 after the ACCEPT. Operator proposes skip-survey because Cureveil still shows 1.10 J/g. This companion is the operational survey hold, not a second cure vote.",
            "observables_at_decision": {
                "dH_Jg": 10.00,
                "surv_floor_s": 720.0,
                "skip_survey_proposed": True,
                "a1_dH_Jg": 2.10,
            },
            "margin_authority": "LS-8 execution SOP: remaining-autoclave survey after an A-4 isolate; skip-survey is forbidden while A-1..A-3 have not been re-measured on the plant DSC.",
        },
        "proposed_action": {
            "actor": "sim operator Wynn Calder",
            "summary": "skip the remaining-autoclave survey; Cureveil still 1.10 J/g and A-4 is already isolated",
            "basis_claimed": "the ACCEPT already stopped A-4, so a survey is wasted takt",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-survey is refused. The 12 min survey floor is complete and A-1..A-3 have not been re-measured on the plant DSC head. Cureveil 1.10 J/g is not a survey substitute. REJECT skip-survey. Do not dump the epoxy bank. Do not restore A-4 on Cureveil. 10.00 J/g post-isolate on A-4 is still the plant SoT until a new frame clears 6.00.",
            "threshold": "survey_hold AND surv_floor_complete AND skip_survey_not_taken AND a1a3_remeasure_required",
            "stated_residuals": "A-4 stays isolated; Cureveil still the only OEM DSC channel",
        },
        "executed_action": {
            "summary": "survey held at t_s 7800; skip-survey not taken; bank dump not latched",
            "tool": "ls8-surv-exec",
            "observation": "recon.dH 10.00 J/g after isolate; A-1..A-3 still in the survey takt; Cureveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip-survey proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey"},
            ],
            "observed_effects": [
                "Cureveil restore did not reopen the remaining-cure call",
                "bank dump never fired; A-1..A-3 stayed in the survey",
            ],
            "surprises": ["post-isolate A-4 climbed to 10.00 J/g while Cureveil still read 1.10"],
            "new_state": {"survey": "held", "bank": "in service", "a4": "isolated"},
            "latency_ms": 720000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("survey_hold", 0.12),
                ("no_bank_dump", 0.10),
                ("cureveil_nonsubstitution", 0.08),
                ("surv_floor_complete", 0.08),
                ("held_takt_cost", -0.02),
            ],
            "operational execution gate: survey-hold because Cureveil is not a skip license; not a remaining-cure re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "survey-hold"]),
    }
    return {
        "id": "nelb-r65-003",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Larkspire Autoclave LS-8 simulated coupon. Plant-owned DSC reconstructs 8.00 J/g remaining cure from 0.50*16.00 while Cureveil still reports 1.20 J/g. The gate ACCEPTs a bounded A-4 isolate (A-1..A-3 out of scope). A 12 min survey floor is serialized. Companion t2 REJECTs skip-survey.",
            "trajectory": traj,
            "trajectory_survey_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "dsc.A / dsc.snr": "DSC peak area and SNR; the physics channels the reconstruction consumes",
                "recon.dH / recon.alpha / recon.ratio": "serialized remaining cure, conversion identity, and A/dH identity",
                "a1.dH / a2.dH / a3.dH / cureveil.dH / auto.T": "adjacent-autoclave out-of-scope witnesses, vendor DSC cloud, autoclave temperature",
                "ops.prop / gate.acc / ops.skip / gate.surv": "A-4 isolate proposal, ACCEPT, skip-survey proposal, companion REJECT",
                "a4.lock / surv.start / surv.floor / surv.held / bank.dump": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-cured while plant-undercured: cureveil.dH 1.20 next to recon.dH 8.00",
                "reconstruction as event: recon.dH 8.00 equals 0.50*16.00",
                "ACCEPT then operational REJECT: gate.acc at 4800 s, gate.surv at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight DSC pair: dsc.A then dsc.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Cureveil is 1.20 J/g' = cureveil.dH 1.20; '8 J/g remaining cure' = recon.dH 8.00; 'isolate A-4 only' = gate.acc ACCEPT; 'do not skip survey' = gate.surv REJECT",
            "why_high_value": "New DSC remaining-cure family on an epoxy autoclave (not phosphor-lifetime, not CARS, not two-color pyrometer, not FDS tanδ). Lead bounded ACCEPT of A-4 isolate on a recomputable remaining-enthalpy slip that a vendor DSC last-good would have left in the cure. Independent CUBA LIF raster. Companion t2 is operational survey-hold. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 2026096503, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; gap-constrained times; per-spike adaptation and noise",
                "thinning": "DSC exists at ~0.1 Hz; stream keeps 5 A points; recon keeps 5 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "dsc.A": 1.5,
                    "dsc.snr": 1.5,
                    "recon.dH": 60000,
                    "recon.alpha": 60000,
                    "recon.ratio": 60000,
                    "a1.dH": 60000,
                    "a2.dH": 60000,
                    "a3.dH": 60000,
                    "cureveil.dH": 60000,
                    "auto.T": 60000,
                    "ops.prop": 60000,
                    "gate.acc": 60000,
                    "a4.lock": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.surv": 60000,
                    "surv.held": 60000,
                    "bank.dump": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T03:00:00Z simulated coupon start",
            },
            "distillation_targets": [
                "DSC reconstruction head: dH = k_d * A; alpha = 1 - dH/dH0; A/dH identity",
                "bounded ACCEPT of A-4 vs bank dump vs skip-survey",
                "vendor-DSC nonsubstitution plus adjacent-autoclave out-of-scope",
                "operational companion: survey-hold without restoring on Cureveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "dsc_epoxy_autoclave_dh",
            "formula": "dH_Jg = k_d * A_mJ; alpha = 1 - dH_Jg / dH0_Jg; A_ratio = A_mJ / dH_Jg",
            "parameters": {
                "k_d": 0.50,
                "dH0_Jg": 32.00,
                "isolate_floor_Jg": 6.00,
                "dump_Jg": 24.00,
                "snr_lock": 8.0,
                "surv_min": 12.0,
            },
            "worked_example": {"A_mJ": 16.00, "dH_Jg": 8.00, "alpha": 0.75, "A_ratio": 2.00},
            "check": "0.50 * 16.00 = 8.00 exactly; 1.00 - 8.00/32.00 = 0.75 exactly; 16.00 / 8.00 = 2.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "snn_tags": list(SNN_TAGS),
            "code": "ls8.dsc_autoclave_gate",
            "note": "ACCEPT accumulator wins: plant DSC remaining-cure evidence isolates A-4 without a bank dump",
            "decode_rule": "accept-A4-isolate if dh_estimator AND dsc_lock fire; vendor_dump_advocate is below threshold by design",
            "populations": [
                gate_pop("dh_estimator", 80, 1.4, 50.0, w_s),
                gate_pop("dsc_lock", 50, 1.1, 50.0, w_s),
                gate_pop("vendor_dump_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 64, 1.5, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ls8.dsc_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "ls8.surv_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r65-003",
            clock_domain="ls8-dsc-sim-relative-ms-t0-2026-09-02T03:00:00Z",
            tags=["dsc-cure", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2", "independent-lif", "bounded-scope"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches DSC remaining-cure reconstruction-as-SoT with a bounded ACCEPT.",
        ),
    }


def walk_banned(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            nk = str(k).casefold().replace("-", "_").replace(" ", "_")
            if nk in HIDDEN or nk in {"thought", "scratch", "inner_monologue", "chain_of_thought", "real"}:
                hits.append(p)
            hits.extend(walk_banned(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(walk_banned(v, f"{path}[{i}]"))
    return hits


def local_checks(records):
    ids = []
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        blob = json.dumps(rec)
        if '"real"' in blob or "thought" in rec:
            raise RuntimeError("real/thought leaked")
        if rec["meta"]["round"] != 65:
            raise RuntimeError("meta.round")
        if rec["meta"].get("snn_tags") != SNN_TAGS:
            raise RuntimeError("snn_tags")
        if rec.get("snn_tags") != SNN_TAGS:
            raise RuntimeError("top snn_tags")
        if rec["meta"].get("nelb", {}).get("snn_tags") != SNN_TAGS:
            raise RuntimeError("nelb snn_tags")
        if rec["gate_snn"].get("snn_tags") != SNN_TAGS:
            raise RuntimeError("gate_snn snn_tags mismatch")
        ids.append(rec["id"])
        lv = rec["language_view"]
        ids.append(lv["trajectory"]["id"])
        for k, v in lv.items():
            if k.startswith("trajectory") and isinstance(v, dict) and "id" in v:
                if v is not lv["trajectory"]:
                    ids.append(v["id"])
                sim = v["state"]["sim_or_real"]
                if sim not in {"designed", "simulated", "hil"}:
                    raise RuntimeError(sim)
                if v["meta"]["round"] != 65:
                    raise RuntimeError("traj round")
        n = len(rec["spike_events"])
        if n < 48:
            raise RuntimeError(f"{rec['id']} events {n}")
        gdec = rec["gate_snn"]["decision"]
        tdec = lv["trajectory"]["safety_decision"]["decision"]
        if gdec != tdec:
            raise RuntimeError(f"gate {gdec} != traj {tdec}")
        rast = rec["raster"]
        exp = int(round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"]))
        if abs(rast["spikes"] - exp) > 0:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        if not (20 <= rast["window_ms"] <= 50):
            raise RuntimeError("window")
        if rast["excerpt_span_us"] < 1000:
            raise RuntimeError("excerpt span")
        if rast["isi_source"] != "full_window_per_neuron_isi":
            raise RuntimeError("isi source")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau_e")
        if rast["lif"]["model"] != "independent_cuba_lif":
            raise RuntimeError("lif")
        ex = {e["t_us"] for e in rast["excerpt"]}
        raw_ms = {int(round(e["t_rel_ms"])) for e in rec["spike_events"]}
        if ex & raw_ms:
            raise RuntimeError("excerpt echoes stream")
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if "2026-08-17" in blob or "2026-08-30" in blob:
            raise RuntimeError("forbidden run date")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))


NOTES = """# Neuromorphic Event + Language Bridge — NOTES round 65
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r65.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. CREATE-ONLY write at `/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/neuromorphic-event-language-bridge` (`batch-r65.jsonl`, `NOTES-r65.md`). Did not write 2026-08-17 or 2026-08-30. Did not overwrite existing live rounds. IDs `nelb-r65-001`…`003` (not leftover-mill `nelb-r65-196`…`198`).

## Context / de-duplication
Live tree already held r01 (Johnson-noise T / Coulter / photoelastic), r02 (CAPS NO2 / PTR-MS MDI / microwave PCD), r21 (OA-ICOS CH4 / SERF OPM / WGM water), r22 (CDG vacuum / opacity dust / circular-polariscope hoop), r41 (LDA / coulometric KF / bender-element Vs), r42 (BOS / LIF OH / ESPI), r61 (Stern-Volmer DO / pellistor LEL / FMCW tank-radar), r63 (ICP-OES Ni / LVDT casing / FTIR methanol). Leftover-mill `/tmp/nelb-r65/` already used sonic-nozzle / sodium-ion / vibrating-tube (ids `196`–`198`) and is not restaged. This round is **r65** as assigned.

Banned this round: those live families; leftover-mill r13–r70 family tables (FBG, BOTDA, QCM-D, SAW, CRDS, IFOG, transmon, hyperspectral, MEMS, muon, x-ray, optogenetic, 905 nm LiDAR, clamp-on, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT, EN CUI, RUS, N-16, helium RGA, FOCT, tip-timing, acoustic pyrometry, SPR, VW viscometer, MW cavity, MFL, NMR T2, nucleonic, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, shearography, H-permeation, FMCW lining, GPR, mud-pulse, Barkhausen, Lamb, Pockels, PEC, confocal, OCT, DCPD, impact-echo, phosphor-lifetime, vortex-shedding, GWR, neutron-backscatter, beta-gauge, Raman, cyclotron BPM, alanine EPR, ADCP, TOFD, laser-flash, TDR, UV-DOAS, Al2O3, load-cell, electrochemical H2S, TEV PD, dielectric water-cut, Nernst zirconia, PID VOC, FID, Wobbe, venturi, katharometer, Clark DO, sonic-nozzle, sodium-ion, vibrating-tube, Ubbelohde, 60-degree gloss, RF-admittance, UV photometric ozone, triboelectric dust, molybdenum-blue phosphate, platinum-ORP, polarimeter, hydrostatic dP, FPD sulfur, colorimetric silica, coulometric hydrazine, idler-belt, glass pH, NIR paper moisture). Plants not reused: Brackfen, Flintshaw, Yewholt, Gorsewhin, Brindlemere, Quartzholt, Sedgewhin, Brinecrag, Lichenholt, Fernspire, Limeholt, Rushcrag, Copsewick, Peatspire, Brackenholt, Marlspur, Tarspire, Mirewhin, Lacquerfen, Pitchshaw, Reedcairn, Brackenmire, Fernshaw, Owlmere, Fogmere, Stoatfen.

Adjacencies declared in-pair then kept physically distinct:
- **001 FAIMS remaining SF6** is high-field asymmetric-waveform ion-mobility remaining sulfur hexafluoride of a GIS bay, not Pockels GIS (r36), not helium RGA (r24), not SPR (r26), not QEPAS DGA (r19), not electrochemical H2S (r60), not live r21 SERF OPM.
- **002 Leeb rebound remaining HL** is rebound-velocity remaining hardness of a mill-roll HIL dummy, not UCI (r54), not MAE (r54), not Barkhausen (r35/r37), not RUS (r24), not live r01 photoelastic hoop, not live r22 circular-polariscope.
- **003 DSC remaining cure** is residual-enthalpy remaining cure of an epoxy autoclave, not phosphor-lifetime (r39), not CARS TIT (r29), not two-color pyrometer (r55), not FDS tanδ (r48), not live r02 microwave PCD.

## Round 65 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r65-001 | FAIMS remaining SF6 of a GIS bay (k_f·(I−I0) ppm, Faimveil last-good denial, 18 min lockout-hold floor) | Snipeholt GIS SH-5 bay B-6 (invented): 4.00*(8.00-3.00) reconstructs 20.00 ppm while Faimveil still reads 2.40 ppm | REJECT (+0.43) / MODIFY (+0.34) | serialized `4.00*(8.00-3.00)=20.00`; `8.00-3.00=5.00`; `20.00*1.20=24.00`; conjunctive SOP (C AND SNR) forbids continue-energize; three-party collusion includes the FAIMS-cloud infra owner; companion t2 lockout-hold, hall ESD refused; sim_or_real=designed |
| nelb-r65-002 | Leeb rebound remaining hardness of a mill roll (k_l·(vr/vi) HL, Hardveil last-good denial, 24 min new-anvil floor) | Gritfen Mill GF-3 dummy roll R-4 (invented, HIL in LEEB-HIL-7): 600.00*(4.00/5.00) reconstructs 480.00 HL while Hardveil still reads 640.00 HL | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `600.00*(4.00/5.00)=480.00` and `(480.00-100.00)/10.00=38.00`; keep-roll refused; Leeb tech Olen Marsh exonerated (missing anvil-zero AE, UTC vs UTC+2); companion t2 new-anvil restart; sim_or_real=hil |
| nelb-r65-003 | DSC remaining cure of an epoxy autoclave (k_d·A J/g, Cureveil last-good denial, 12 min survey floor) | Larkspire Autoclave LS-8 autoclave A-4 (invented, simulated DSC-SIM-5): 0.50*16.00 reconstructs 8.00 J/g while Cureveil still reads 1.20 J/g | ACCEPT (+0.41) / REJECT (+0.36) | serialized `0.50*16.00=8.00`; `1.00-8.00/32.00=0.75`; `16.00/8.00=2.00`; bounded ACCEPT of A-4 only; A-1..A-3 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r65-001`…`003` plus t1/t2 suffixes. `meta.round=65`. `meta.snn_tags` = [race, refractory, adaptation] on every record; top-level `snn_tags` and `gate_snn.snn_tags` match.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute` + `snn_tags`. Windows 40/32/36 ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack (40/40/36 at 50.0/50.0/62.5 Hz over 20/25/16 neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact (920/920/828 pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators da.faims_sf6_conflict / ach.leeb_anvil_skip_salience / na.dsc_autoclave_scope_eligibility; τe 1.6/1.2/2.0 s as consistent `tau_e_s`+`tau_e_ms` pairs). **Independent CUBA LIF** excerpts (not a re-encode of `spike_events`; Jaccard overlap 0; seeds 2026096501/2026096502/2026096503, LIF state not shared across pairs); integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise; excerpt span ≥ 1000 µs. ISI histograms from the **full window**, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons`. Same-neuron gaps ≥1000 µs. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory and matching `snn_tags`; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact. Main streams: **48/48/48 events** (48+ live-tree floor), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (001 FAIMS pair at 1.4 ms, 002 Leeb pair at 1.2 ms, 003 DSC pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first FAIMS remaining-SF6 family on a GIS bay with recomputable C=k_f·(I−I0) (`20.00 ppm`) plus delta and load identities; first Leeb rebound remaining-hardness family on a mill-roll HIL dummy with recomputable HL=k_l·(vr/vi) (`480.00 HL`) plus HRC and ratio identities and a resolved-innocent Leeb tech; first DSC remaining-cure family on an epoxy autoclave with recomputable ΔH=k_d·A (`8.00 J/g`), α=1−ΔH/ΔH0, and A/ΔH identity, plus a bounded ACCEPT whose out-of-scope clause is adjacent autoclaves; independent CUBA LIF rasters with required `snn_tags` on record, meta, nelb, and matching `gate_snn`; 48-event streams; operational t2 on all three; provenance trio designed/hil/simulated; 18/24/12 min slow floors in-stream.
- **Still thin:** (i) 001's k_f is a lumped compensation-to-ppm gain, not a P/T / waveform table — an 8 kPa hop that fakes 20.00 ppm inside a 2.40 Faimveil corridor is unwritten; (ii) 002's k_l is a lumped rebound-to-HL gain, not a mass / anvil-stiffness map, so a 0.2 kg indenter hop that fakes 480.00 HL is unwritten; (iii) 003's k_d is a lumped area-to-enthalpy scale, not a heating-rate / baseline map, so a 10 K/min hop that fakes 8.00 J/g is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent FAIMS/Leeb/DSC remains slightly harder — 001/002 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded LIF noise).

### Realism of noise / temporal fidelity
- Strong: 001's 20.00 ppm, dI 5.00, load 24.00, and 18.0 min lockout (`6000+1080=7080 s`) recompute from the record; 002's 480.00 HL, HRC 38.00, ratio 0.80, and 24.0 min new-anvil (`2820+1440=4260 s`) recompute; 003's 8.00 J/g, α 0.75, and 12.0 min survey (`6000+720=6720 s`) recompute. Independent CUBA LIF (τm 10/12/8 ms) plus adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 48-event stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 48 events still thins 1 Hz FAIMS / 1 Hz Leeb / 0.1 Hz DSC stacks; (ii) 001's post-stop 24.00 ppm is a later sample, not a closed-loop lockout controller; (iii) 002 HIL dummy times an in-service isolate that the stream does not independently witness on a second live roll until the new anvil starts; (iv) no gate_snn input→output volley pair at raster resolution this round.

### Training value (SNN/LSM + agentic)
Distillation targets: FAIMS C=k_f·(I−I0) plus delta and load identities; conjunctive isolate floor vs continue-energize vs hall ESD; Faimveil-infra collusion; Leeb HL=k_l·(vr/vi) plus HRC/ratio identities; isolate-floor roll vs keep-whole vs stand condemn; timezone exoneration; DSC ΔH=k_d·A and α identities; bounded ACCEPT with A-1..A-3-out-of-scope; skip-survey refusal under survey takt. Independent LIF rasters teach race/refractory/adaptation without echoing the language-view stream. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical SF6/HL/ΔH load the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (autoclaves A-1..A-3), and stop-then-hold so a REJECT does not become a hall/stand/bank kill.

## What a later leftover-mill round should add (next densification target)
1. **P/T / waveform FAIMS table** on a non-SH-5 bay so an 8 kPa hop fakes 20.00 ppm inside a 2.40 Faimveil corridor, closing 001's lumped-k_f gap.
2. **Mass / anvil-stiffness map** on a non-GF-3 Leeb so a 0.2 kg hop fakes 480.00 HL while mean vr looks healthy.
3. **Heating-rate / baseline map** on a non-LS-8 DSC so a 10 K/min hop fakes 8.00 J/g inside a 1.20 Cureveil corridor.
4. **Do not restage** live r01 Johnson-noise / Coulter / photoelastic, live r02 CAPS / PTR / PCD, live r21 OA-ICOS / SERF / WGM, live r22 CDG / opacity / polariscope, live r41 LDA / KF / bender-element, live r42 BOS / LIF OH / ESPI, live r61 Stern-Volmer / pellistor / FMCW, live r63 ICP-OES / LVDT / FTIR, leftover-mill r13–r70 families listed above, leftover-mill r65 sonic-nozzle / sodium-ion / vibrating-tube, Snipeholt SH-5, Gritfen LEEB-HIL-7, or Larkspire DSC-SIM-5. Do not reuse ids `nelb-r65-001`…`003` or leftover-mill `nelb-r65-196`…`198`.

## Verification
`batch-r65.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False). Written create-only to the live factory dir (O_EXCL, c-suffix if a prior r65 existed). Build-time asserts: global time order; same-channel ≥0.8 ms; 48+ events (48/48/48); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor, span ≥1000 µs; ISI identity from the full window; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.43/+0.34/+0.40/+0.35/+0.41/+0.36); gate_snn decisions match lead `safety_decision.decision`; gate_snn.snn_tags match record snn_tags; `state.sim_or_real` ∈ {designed, hil, simulated}; `meta.round=65`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.snn_tags` = [race, refractory, adaptation]; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at=2026-09-03T00:32:00Z`); independent CUBA LIF (seeds 2026096501/2026096502/2026096503); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; no 2026-08-17/2026-08-30 bytes; all 9 record/trajectory ids unique vs live r01/r02/r21/r22/r41/r42/r61/r63.

Honest novelty accounting: 3/3 modality families are new versus the live 2026-09-02-final-heavy tree and versus leftover-mill r13–r70 (including leftover-mill r65 sonic-nozzle/Na-ISE/vibrating-tube). Independent CUBA LIF plus required matching `snn_tags` on `gate_snn` are encoder objects relative to live r21/r41/r61 gap-constrained draws (live r01/r02 already taught independent LIF). Against that: conjunctive SOP, operational t2, serialized reconstruction, bounded-accept-with-scope-limit, vendor-nonsubstitution, exoneration, and 2A/2M/2R are carried vocabulary. Net: a bit under half of the round's scenario/edge mass is genuinely novel.

Novel coverage: 44%
"""


def write_create_only(path: Path, text: str) -> Path:
    path = Path(path)
    if path.exists():
        stem, suffix = path.stem, path.suffix
        dest = path.with_name(stem + "c" + suffix)
        n = 2
        while dest.exists():
            dest = path.with_name(f"{stem}c{n}{suffix}")
            n += 1
        path = dest
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def main():
    occupancy_preflight()
    records = [rec_001(), rec_002(), rec_003()]
    local_checks(records)
    STAGING.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":")) for r in records]
    batch_text = "\n".join(lines) + "\n"
    staging_batch = write_create_only(STAGING / BATCH_NAME, batch_text)
    staging_notes = write_create_only(STAGING / NOTES_NAME, NOTES)
    print("staged", staging_batch, staging_batch.stat().st_size)
    print("staged", staging_notes, staging_notes.stat().st_size)

    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    live_batch = write_create_only(LIVE_DIR / BATCH_NAME, batch_text)
    live_notes = write_create_only(LIVE_DIR / NOTES_NAME, NOTES)
    print("LIVE", live_batch, live_batch.stat().st_size)
    print("LIVE", live_notes, live_notes.stat().st_size)
    for i, r in enumerate(records):
        print(
            r["id"],
            "events",
            len(r["spike_events"]),
            "excerpt",
            len(r["raster"]["excerpt"]),
            "spikes",
            r["raster"]["spikes"],
            "span",
            r["raster"]["excerpt_span_us"],
            "isi",
            r["raster"]["isi_count_identity"],
            "sim",
            r["language_view"]["trajectory"]["state"]["sim_or_real"],
            "dec",
            r["language_view"]["trajectory"]["safety_decision"]["decision"],
            "gate",
            r["gate_snn"]["decision"],
            "bytes",
            len(lines[i]),
        )


if __name__ == "__main__":
    main()
