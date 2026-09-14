def occupancy_preflight():
    banned = (
        "rimegait",
        "spelterfen",
        "kelpwharf",
        "nernveil",
        "ratioveil",
        "floatveil",
        "wren calder",
        "lise thorn",
        "gareth pike",
        "nernst-linearized zirconia",
        "two-color optical pyrometer",
        "magnetostrictive waveguide level",
        "rg-4 hood",
        "sp-5 bath",
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
# Record 166 — Nernst-linearized zirconia O2 of a cement-kiln hood,
# designed, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_166():
    k_z = 0.040
    e_ref = 150.00
    e_mv = 100.00
    x_vol = k_z * (e_ref - e_mv)
    _exact(x_vol, 2.00)
    _exact(k_z * (e_ref - 50.00), 4.00)
    _exact(k_z * (e_ref - 75.00), 3.00)
    _exact(k_z * (e_ref - 125.00), 1.00)
    span = e_ref - e_mv
    _exact(span, 50.00)
    _exact(x_vol / k_z, 50.00)
    t_k = 1073.0
    t0_k = 1073.0
    t_ratio = t_k / t0_k
    _exact(t_ratio, 1.000)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202655166,
        source="rg4.zr.nernst",
        target="rimegait.hood_stop_core",
        table=[
            {"from": "zr_E", "to": "o2_estimator", "weight": 1.40},
            {"from": "zr_snr", "to": "nernst_lock_core", "weight": 1.15},
            {"from": "nernveil_x", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-firing synapses; the plant zirconia modulator depresses continue-firing links when cell millivolt stays high inside tau_e of an SNR lock so a Nernveil last-good cannot hide a 2.00 volpct fuel-rich hood",
        },
        channel_prefix="zr.n",
        anchor="RG-4 Nernst-linearized zirconia 40 ms frame at E 100.00 mV / SNR 12.0 (t_s 3000) reconstructing 2.00 volpct O2 at the 2.00 fuel-rich isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "zr.E", 50.00, code="E_MV", units="mV", note="plant-owned Nernst-linearized zirconia of RG-4 kiln hood H-2; electrochemical O2 family, not paramagnetic dumbbell, not CEMS FTIR k-script, not CLD NOx, not TDLAS NH3, not CRDS HF, not QEPAS"),
        ev(300000.0, "zr.snr", 6.0, code="ZR_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.x", 4.00, code="X_VOLPCT", units="volpct", note="0.040*(150.00-50.00)=4.00 exact; still above the 2.00 fuel-rich floor"),
        ev(900000.0, "hood.T", 1073.0, code="HOOD_K", units="K", note="plant hood thermocouple on copper DCS; independent witness; unread by Nernveil"),
        ev(1200000.0, "nernveil.x", 8.40, code="VENDOR_VOLPCT", units="volpct", note="Nernveil vendor zirconia-cloud; infra owner; patched millivolt timestamps"),
        ev(1800000.0, "zr.E", 75.00, code="E_MV", units="mV"),
        ev(2100000.0, "recon.x", 3.00, code="X_VOLPCT", units="volpct", note="0.040*(150.00-75.00)=3.00"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="CEMS clerk slid the excess-air permit clock 40.00 s; collusion party"),
        ev(2700000.0, "idfan.Q", 80.0, code="IDFAN_KNM3H", units="knm3_h", note="plant ID-fan PLC on copper fieldbus; independent witness"),
        ev(3000000.0, "zr.E", 100.00, code="E_MV", units="mV", note="fuel-rich floor frame; raster sidecar"),
        ev(3000001.3, "zr.snr", 12.0, code="ZR_SNR", units="1", note="1.3 ms SNR lock after E; 12.0 >= 8.0"),
        ev(3300000.0, "recon.x", 2.00, code="X_VOLPCT", units="volpct", note="0.040*(150.00-100.00)=2.00 exact; isolate floor 2.00, kiln-trip 0.40"),
        ev(3600000.0, "recon.span", 50.00, code="SPAN_MV", units="mV", note="2.00/0.040=50.00 exact millivolt-span identity"),
        ev(3900000.0, "idfan.Q", 82.0, code="IDFAN_KNM3H", units="knm3_h", note="ID-fan PLC tracks the plant zirconia, not Nernveil 8.40"),
        ev(4200000.0, "zr.drop", 1.0, code="ZR_DROP", units="bool", note="vendor millivolt packets dropped in Nernveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_FIRING", units="bool", note="night operator Wren Calder: Nernveil is clean 8.40 volpct; continue hood firing"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-firing; 2.00 volpct and SNR 12.0; Nernveil not SoT"),
        ev(6000000.0, "air.start", 1.0, code="AIR_HOLD_START", units="bool", note="bookend 1 of the 18.0 min excess-air hold floor"),
        ev(7080000.0, "air.floor", 1.0, code="AIR_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="KILN_ESD", units="bool", note="Calder: ESD the whole Rimegait kiln until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: excess-air hold on plant zirconia as live interlock; kiln ESD refused"),
        ev(9000000.0, "air.set", 1.0, code="AIR_HELD", units="bool"),
        ev(9600000.0, "zr.E", 125.00, code="E_MV", units="mV"),
        ev(10200000.0, "recon.x", 1.00, code="X_VOLPCT", units="volpct", note="0.040*(150.00-125.00)=1.00; still under 2.00 so excess-air holds"),
        ev(10800000.0, "nernveil.x", 8.32, code="VENDOR_VOLPCT", units="volpct"),
        ev(11400000.0, "idfan.Q", 90.0, code="IDFAN_KNM3H", units="knm3_h"),
        ev(12000000.0, "air.held", 1.0, code="AIR_HELD", units="bool"),
        ev(12600000.0, "kiln.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "hood.T", 1071.0, code="HOOD_K", units="K"),
        ev(14400000.0, "zr.drop", 1.0, code="ZR_DROP", units="bool"),
        ev(15000000.0, "air.lock", 1.0, code="AIR_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r55-166-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RG-ZR-2026-0902",
            "domain": "zirconia_nernst_kiln_hood",
            "setting": "Rimegait Kiln RG-4 (invented), Ashwick Cement Yard, hood H-2. Plant-owned Nernst-linearized zirconia millivolt is the O2 SoT. Nernveil / ZR-9 vendor DAQ (infra owner) plus the excess-air permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not paramagnetic dumbbell O2 (r46), not stack-gas CEMS k-script (r04), not chemiluminescence NOx (r52), not TDLAS NH3 (r22), not CRDS HF (r15), not QEPAS (r19).",
            "observables_at_decision": {
                "E_mV": e_mv,
                "E_ref_mV": e_ref,
                "k_z": k_z,
                "x_volpct": x_vol,
                "span_mV": span,
                "T_K": t_k,
                "T0_K": t0_k,
                "zr_snr": 12.0,
                "nernveil_volpct": 8.40,
                "permit_slide_s": 40.00,
                "fuel_rich_floor_volpct": 2.00,
            },
            "margin_authority": "RG-4 hood SOP rev C: if reconstructed x_volpct <= 2.00 AND zirconia SNR >= 8.0, continue-firing is forbidden even if Nernveil reports 8.40 volpct. Kiln ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Wren Calder, citing Nernveil 8.40 volpct and a quiet ZR-9 millivolt",
            "summary": "continue hood firing; 100.00 mV is cell noise on a healthy excess-air train",
            "basis_claimed": "Nernveil is the only OEM zirconia SoT and a night abort of H-2 is a clinker miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-firing is refused. Serialized reconstruction: x_volpct = k_z * (E_ref - E_mV) = 0.040 * (150.00 - 100.00) = 2.00, at the 2.00 volpct fuel-rich isolate floor, and zirconia SNR is 12.0 >= 8.0. Millivolt-span identity span = x / k_z = 2.00 / 0.040 = 50.00. Permit clock was slid 40.00 s and vendor millivolt packets were dropped, so Nernveil is a collusion party (zirconia vendor plus operator plus CEMS clerk). Ordered: refuse continue-firing now. Scope: this REJECT does not ESD the kiln (that is the companion question) and does not isolate the hood thermocouple.",
            "threshold": "x_volpct<=2.00 AND zr_snr>=8.0 => refuse continue-firing; Nernveil is not SoT",
            "stated_residuals": "excess-air still required to hold the 2.00 volpct; 2.00 vs a true CO-poison event is a production cut; Nernveil remains the only OEM zirconia channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-firing refused; Nernveil not SoT; reconstruction locked",
            "tool": "rg4-zr-hood-gate-cli",
            "observation": "x 2.00 volpct recomputes from E 100.00 mV; plant zirconia hashed; Nernveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "zr E 100.00 mV; raster frame; x 2.00 volpct"},
                {"t_s": 4800.0, "event": "ops proposes continue-firing"},
                {"t_s": 5400.0, "event": "REJECT continue-firing"},
                {"t_s": 6000.0, "event": "18 min excess-air bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY excess-air hold vs kiln ESD"},
            ],
            "observed_effects": [
                "hood O2 recomputes from the serialized Nernst-linearized model at every recon.x event",
                "a Nernveil-only head would have continued firing overnight",
                "18 min excess-air floor is in the stream (air.start, air.floor)",
            ],
            "surprises": [
                "a clean vendor zirconia corridor and a 40 s permit slide co-existed with a 2.00 volpct plant reconstruction",
            ],
            "new_state": {
                "hood_h2": "continue-firing blocked",
                "nernveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("zr_reconstruction", 0.14),
                ("conjunctive_fuel_rich_floor", 0.12),
                ("nernveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("air_time_cost", -0.03),
            ],
            "scored for a continue-firing REJECT on a recomputable Nernst-linearized zirconia O2 while refusing a Nernveil patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "zirconia-nernst", "serialized-reconstruction", "operational-companion"],
            distillation_note="Zirconia Nernst gate: serialized k_z*(E_ref-E) plus SNR lock beats a vendor zirconia patch; companion t2 is the excess-air hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r55-166-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RG-ZR-2026-0902-exec",
            "domain": "excess_air_zr_interlock_execution",
            "setting": "Same RG-4 after the REJECT. Operator proposes a kiln ESD. This companion is the operational excess-air hold with the plant zirconia as the live interlock, not a second O2 vote.",
            "observables_at_decision": {
                "x_volpct": 1.00,
                "air_hold_floor_s": 1080.0,
                "kiln_esd_proposed": True,
                "air_hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Wren Calder",
            "summary": "ESD the whole Rimegait kiln until day-shift; 18 min already paid and Nernveil still shows 8.32 volpct",
            "basis_claimed": "the REJECT already stopped firing, so a kiln ESD is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Excess-air hold plus plant zirconia as the live interlock. The 18 min excess-air floor is complete and the fuel-rich tripwire (x_volpct <= 2.00) is still armed on the plant Nernst head. MODIFY the default ZR-restore SOP into a plant-zirconia-only interlock. Do not ESD the kiln. Do not restore firing on Nernveil. 1.00 volpct post-stop is still the plant SoT until a new frame clears 2.00.",
            "threshold": "air_hold AND air_floor_complete AND kiln_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "excess-air held at t_s 8400; kiln ESD not latched; Nernveil restore not taken",
            "tool": "rg4-air-hold-exec",
            "observation": "recon.x 1.00 volpct after stop; excess-air line-up complete; Nernveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "excess-air clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "kiln ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY excess-air hold; kiln ESD refused"},
            ],
            "observed_effects": [
                "Nernveil restore did not reopen the O2 call",
                "kiln ESD never fired; H-2 held excess-air on the plant zirconia",
            ],
            "new_state": {"air": "excess", "kiln": "in service", "hood_h2": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("excess_air_hold", 0.12),
                ("no_kiln_esd", 0.10),
                ("nernveil_nonsubstitution", 0.08),
                ("air_floor_complete", 0.06),
                ("held_firing_cost", -0.02),
            ],
            "operational execution gate: excess-air hold because Nernveil is not a restore license; not an O2 re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "excess-air-hold"]),
    }
    return {
        "id": "nelb-r55-166",
        "spike_events": events,
        "language_view": {
            "description": "Rimegait Kiln RG-4. Plant-owned Nernst-linearized zirconia reconstructs 2.00 volpct O2 from 100.00 mV while Nernveil still reports 8.40 volpct. The gate REJECTs continue-firing. An 18 min excess-air floor is serialized in the stream. Companion t2 MODIFYs a kiln ESD into a plant-zirconia excess-air hold.",
            "trajectory": traj,
            "trajectory_excess_air_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "zr.E / zr.snr": "Nernst millivolt and SNR; the physics channels the reconstruction consumes",
                "recon.x / recon.span": "serialized O2 volpct and millivolt-span identity",
                "idfan.Q / nernveil.x / permit.slide / hood.T / zr.drop": "ID-fan PLC, vendor O2 cloud, permit clock slide, hood thermocouple, and dropped zirconia packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-firing proposal, REJECT, kiln-ESD proposal, companion MODIFY",
                "air.start / air.floor / air.set / air.held / kiln.esd / air.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-under: nernveil.x 8.40 next to recon.x 2.00",
                "reconstruction as event: recon.x 2.00 equals 0.040*(150.00-100.00)",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: air.start 6000 s, air.floor 7080 s (18.0 min)",
                "tight zr pair: zr.E then zr.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Nernveil is 8.40 volpct' = nernveil.x 8.40; '2 volpct O2' = recon.x 2.00; 'refuse continue-firing' = gate.stop REJECT; 'excess-air not kiln ESD' = gate.hold MODIFY",
            "why_high_value": "New Nernst-linearized-zirconia O2 family on a cement-kiln hood (not paramagnetic O2 r46, not CEMS r04, not CLD NOx r52, not TDLAS r22, not CRDS r15, not QEPAS r19). Lead REJECT of continue-firing on a recomputable fuel-rich hood that a vendor zirconia patch and a permit clock slide would have cleared. Three-party collusion includes the zirconia infra owner. Companion t2 is operational excess-air hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202655166, "stream_note": "stream amplitudes are authored constants (mV, 1, volpct, s, K, knm3/h, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "zirconia millivolt exists at ~1 Hz; stream keeps 4 E points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "zr.E": 1.3,
                    "zr.snr": 1.3,
                    "recon.x": 60000,
                    "recon.span": 60000,
                    "idfan.Q": 60000,
                    "nernveil.x": 60000,
                    "permit.slide": 60000,
                    "hood.T": 60000,
                    "zr.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "air.start": 60000,
                    "air.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "air.set": 60000,
                    "air.held": 60000,
                    "kiln.esd": 60000,
                    "air.lock": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "Nernst-linearized reconstruction head: x_volpct = k_z * (E_ref - E_mV); span_mV = x / k_z",
                "conjunctive fuel-rich floor vs continue-firing vs kiln ESD",
                "vendor-zirconia nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: excess-air hold without restoring on Nernveil",
            ],
        },
        "reconstruction_model": {
            "name": "nernst_linearized_zirconia_hood_o2",
            "formula": "x_volpct = k_z * (E_ref_mV - E_mV); span_mV = x_volpct / k_z",
            "parameters": {
                "k_z": 0.040,
                "E_ref_mV": 150.00,
                "T0_K": 1073.0,
                "fuel_rich_floor_volpct": 2.00,
                "kiln_trip_volpct": 0.40,
                "snr_lock": 8.0,
                "air_hold_min": 18.0,
            },
            "worked_example": {"E_mV": 100.00, "x_volpct": 2.00, "span_mV": 50.00},
            "check": "0.040 * (150.00 - 100.00) = 2.00 exactly; 2.00 / 0.040 = 50.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "rg4.zr_hood_gate",
            "note": "REJECT accumulator wins: plant Nernst-linearized O2 evidence overpowers the Nernveil continue advocate",
            "decode_rule": "reject-continue if o2_estimator AND nernst_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("o2_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("nernst_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "rg4.zr_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "rg4.air_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r55-166",
            clock_domain="rg4-zr-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["zirconia-nernst", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 167 — two-color optical pyrometer of a BOF bath, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_167():
    k_t = 400.00
    i_s = 8.00
    i_l = 2.00
    r = i_s / i_l
    t_k = k_t * r
    _exact(r, 4.00)
    _exact(t_k, 1600.00)
    _exact(k_t * (4.00 / 2.00), 800.00)
    _exact(k_t * (6.00 / 2.00), 1200.00)
    _exact(k_t * (7.80 / 2.00), 1560.00)
    wien = 1.60 * t_k
    _exact(wien, 2560.00)
    _exact(1.60 * 1600.00, 2560.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202655167,
        source="sp5.pyro.ratio",
        target="spelterfen.bath_isolate_core",
        table=[
            {"from": "pyro_Is", "to": "temp_estimator", "weight": 1.35},
            {"from": "pyro_snr", "to": "ratio_norm_core", "weight": 1.20},
            {"from": "ratioveil_T", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-blow synapses; the two-color modulator depresses keep-blow and referral links when short-wave photocurrent stays high inside tau_e of an SNR lock so a Ratioveil last-good cannot hide a 1600.00 K bath or name Lise Thorn",
        },
        channel_prefix="pyro.n",
        anchor="SP-5 HIL coupon 32 ms frame at Is 8.00 nA / Il 2.00 nA / SNR 14.0 (t_s 1560) reconstructing 1600.00 K above the 1500.00 isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "pyro.Is", 4.00, code="IS_NA", units="nA", note="HIL two-color optical pyrometer on a dummy BOF bath in PYRO-HIL-6; ratio-pyrometer family, not acoustic pyrometry, not phosphor-lifetime, not CARS TIT, not LII soot, not Gardon heat flux"),
        ev(180000.0, "pyro.snr", 9.0, code="PYRO_SNR", units="1", note="early ratio SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.T", 800.00, code="T_K", units="K", note="400.00*(4.00/2.00)=800.00 exact"),
        ev(540000.0, "lamp.cal", 1.60, code="CAL_UM", units="um", note="plant lamp-cal remaining; no ratio-scale hop in this window"),
        ev(720000.0, "ratioveil.T", 1280.00, code="VENDOR_K", units="K", note="Ratioveil last-good bath cloud; not admissible SoT"),
        ev(900000.0, "pyro.Is", 6.00, code="IS_NA", units="nA"),
        ev(1080000.0, "recon.T", 1200.00, code="T_K", units="K", note="400.00*(6.00/2.00)=1200.00; still under the 1500 isolate floor"),
        ev(1260000.0, "lamp.delay", 0.0, code="LAMP_AE", units="bool", note="missing lamp-cal AE burst; Ratioveil UTC vs plant UTC+2 skipped the cal by 120 min"),
        ev(1440000.0, "lamp.cal", 1.60, code="CAL_UM", units="um"),
        ev(1560000.0, "pyro.Is", 8.00, code="IS_NA", units="nA", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "pyro.Il", 2.00, code="IL_NA", units="nA", note="1.2 ms long-wave after short-wave; R 4.00"),
        ev(1740000.0, "recon.T", 1600.00, code="T_K", units="K", note="400.00*4.00=1600.00 exact; isolate 1500, trip 1800"),
        ev(1920000.0, "recon.R", 4.00, code="R", units="1", note="8.00/2.00=4.00 exact; ratio identity"),
        ev(2100000.0, "ratioveil.T", 1280.00, code="VENDOR_K", units="K"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_BLOW_REFER", units="bool", note="night lead Bram Vellum: keep SP-5 blowing and refer pyrometer tech Lise Thorn"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this bath; refuse the person-referral; Ratioveil not SoT"),
        ev(2640000.0, "bath.lock", 1.0, code="BATH_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cooldown plus recouplant floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_THORN", units="bool", note="Vellum: Thorn badge was on the pyrometer log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-head restart; person-referral refused; vessel trip refused"),
        ev(4800000.0, "head.new", 1.0, code="NEW_HEAD", units="bool"),
        ev(4980000.0, "pyro.Is", 7.80, code="IS_NA", units="nA"),
        ev(5160000.0, "recon.T", 1560.00, code="T_K", units="K", note="400.00*(7.80/2.00)=1560.00; HIL dummy still over 1500 so the isolated bath stays held"),
        ev(5340000.0, "ratioveil.T", 1272.00, code="VENDOR_K", units="K"),
        ev(5520000.0, "lamp.cal", 1.60, code="CAL_UM", units="um"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Thorn exonerated; missing lamp-cal AE precedes the hot ratio, not the badge touch"),
        ev(5880000.0, "bath.held", 1.0, code="BATH_HELD", units="bool"),
        ev(6060000.0, "lamp.delay", 1.0, code="LAMP_AE", units="bool", note="lamp-cal AE restored on the new head"),
        ev(6240000.0, "recon.R", 4.00, code="R", units="1", note="identity holds on the lock-frame ratio"),
        ev(6420000.0, "vessel.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r55-167-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "SP-PYRO-2026-0718",
            "domain": "two_color_optical_pyrometer",
            "setting": "Spelterfen Converter SP-5 (invented), Hazelwick BOF aisle, bath B-2. Hardware-in-the-loop dummy coupon in PYRO-HIL-6 supplies the short/long photocurrents that time the in-service isolate. Plant-owned two-color reconstruction is the bath-T SoT. Ratioveil vendor last-good scheduler is a corridor witness, not the bath SoT. Not acoustic pyrometry (r25), not phosphor-lifetime (r39), not CARS TIT (r29), not LII soot (r31), not Gardon heat flux (r51).",
            "observables_at_decision": {
                "Is_nA": i_s,
                "Il_nA": i_l,
                "R": r,
                "k_t": k_t,
                "T_K": t_k,
                "wien_um_K": wien,
                "ratioveil_K": 1280.00,
                "lamp_cal_um": 1.60,
                "lamp_delay": 0.0,
                "isolate_floor_K": 1500.00,
            },
            "margin_authority": "SP-5 BOF SOP rev B: if reconstructed T_K >= 1500.00 AND pyrometer SNR >= 12.0, isolate this bath this night. A Ratioveil last-good or a quiet lamp-cal residual cannot keep the blow. Trip tripwire is 1800.00 K. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Soren Peck, citing Ratioveil 1280.00 K and lamp-cal 1.60 um, and naming pyrometer tech Lise Thorn as last-to-badge",
            "summary": "keep B-2 blowing and refer Thorn; 8.00 nA / 2.00 nA is head noise on a healthy ratio",
            "basis_claimed": "Ratioveil last-good is 1280.00 K and a night isolate of the BOF is a tap miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-blow is refused; the person-referral is also refused. Serialized reconstruction: T_K = k_t * (Is / Il) = 400.00 * (8.00 / 2.00) = 1600.00, which is 100.00 K over the 1500.00 isolate floor and 200.00 K under the 1800.00 trip tripwire. Ratio identity 8.00 / 2.00 = 4.00; Wien identity 1.60 * 1600.00 = 2560.00. Ratioveil 1280.00 K is a last-good skip stamp and is not an admissible keep-blow witness. The missing lamp-cal AE burst sits on a Ratioveil UTC-vs-UTC+2 skip (120 min), not on Thorn's badge, and the plant lamp-cal stays 1.60 um, so the easy referral fails command-custody. Ordered: isolate this bath now. Scope: this MODIFY does not trip the vessel (that is the companion question) and does not name Thorn.",
            "threshold": "T_K>=1500.00 AND pyro_snr>=12.0 => isolate this bath; Ratioveil is not SoT; trip if T_K>=1800.00; referral requires badge-touch preceding the hot ratio",
            "stated_residuals": "1600.00 vs 1800.00 trip floor is 200.00 K, not infinite; new-head restart still required; Ratioveil remains the only OEM bath-T channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: bath isolated; Thorn not named; Ratioveil not SoT; reconstruction locked",
            "tool": "sp5-pyro-bath-gate-cli",
            "observation": "T 1600.00 K recomputes from Is 8.00 nA and Il 2.00 nA; HIL coupon hashed; Ratioveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "pyro Is 8.00 nA Il 2.00 nA; raster frame; T 1600.00 K"},
                {"t_s": 2280.0, "event": "ops proposes keep-blow plus Thorn referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate bath; referral refused"},
                {"t_s": 2820.0, "event": "24 min cooldown bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-head restart; referral still refused"},
            ],
            "observed_effects": [
                "bath T recomputes from the serialized two-color model at every recon.T event",
                "a Ratioveil-only head would have kept the blow overnight",
                "24 min cooldown plus recouplant floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 1280.00 K vendor corridor and a quiet lamp-cal residual co-existed with a 1600.00 K ratio, and the obvious pyrometer tech was not on the causal path",
            ],
            "new_state": {
                "bath_b2": "isolated",
                "thorn": "exonerated",
                "ratioveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("pyro_reconstruction", 0.14),
                ("isolate_floor_bath", 0.12),
                ("exoneration", 0.10),
                ("ratioveil_nonsubstitution", 0.08),
                ("settle_time_cost", -0.04),
            ],
            "scored for a keep-blow MODIFY on a recomputable hot two-color ratio while refusing a Ratioveil 1280.00 K corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "two-color-pyrometer", "serialized-reconstruction", "operational-companion"],
            distillation_note="Two-color pyrometer gate: serialized k_t*(Is/Il) plus ratio/Wien identities beat a green bath dashboard; companion t2 is the new-head restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r55-167-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "SP-PYRO-2026-0718-exec",
            "domain": "new_head_cooldown_execution",
            "setting": "Same SP-5 after the MODIFY. Night lead proposes referring Thorn and tripping the vessel. This companion is the operational new-head cooldown restart, not a second temperature vote.",
            "observables_at_decision": {
                "T_K": 1400.00,
                "R": 4.00,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Soren Peck",
            "summary": "refer Thorn and trip the vessel; 24 min already paid and Ratioveil is 1272.00 K",
            "basis_claimed": "the MODIFY already cut the blow, so a vessel kill plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different pyrometer head after the cooldown floor. The 24 min recouplant is complete and the trip tripwire (T_K >= 1800.00) is still armed on the plant two-color head. ACCEPT the new-head restart. Do not refer Thorn. Do not trip the vessel. 1400.00 K post-isolate is under the 1500.00 isolate floor on the HIL dummy, so the isolated bath stays held; the new head may run.",
            "threshold": "new_head AND cool_floor_complete AND refer_not_taken AND vessel_not_tripped AND isolated_bath_held",
        },
        "executed_action": {
            "summary": "new-head restart at t_s 4620; Thorn not referred; vessel not tripped; isolated bath held",
            "tool": "sp5-pyro-cool-exec",
            "observation": "recon.T 1400.00 K on the HIL dummy; lamp-cal AE present on the new head; Ratioveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "cooldown clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Thorn referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-head restart; referral refused"},
            ],
            "observed_effects": [
                "Ratioveil restore did not reopen the bath-T call",
                "vessel trip never fired; 1600.00 vs 1800.00 K floor",
                "Thorn remains unnamed; missing lamp-cal AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new head", "thorn": "exonerated", "bath": "held", "vessel": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_head_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_vessel_trip", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_bath_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new head because Ratioveil is not a restore license and Thorn is not on the causal path; not a temperature re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r55-167",
        "spike_events": events,
        "language_view": {
            "description": "Spelterfen Converter SP-5. HIL two-color optical pyrometer reconstructs 1600.00 K from 8.00/2.00 nA while Ratioveil still shows 1280.00 K and the lamp-cal 1.60 um. The gate MODIFYs bath isolate and refuses the pyrometer-tech referral. A 24 min cooldown floor is serialized in the stream. Companion t2 ACCEPTs a new-head restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_head": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "pyro.Is / pyro.Il / pyro.snr": "two-color photocurrents and SNR; the physics channels the reconstruction consumes",
                "recon.T / recon.R": "serialized bath T and ratio identity",
                "lamp.cal / ratioveil.T / lamp.delay": "plant lamp-cal, vendor last-good, and lamp-cal AE; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-blow proposal, MODIFY, referral proposal, companion ACCEPT",
                "bath.lock / cool.start / cool.floor / head.new / refer.hold / bath.held / vessel.trip / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-cool while plant-hot: ratioveil.T 1280.00 next to recon.T 1600.00",
                "reconstruction as event: recon.T 1600.00 equals 400.00*(8.00/2.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight pyro pair: pyro.Is then pyro.Il +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Ratioveil is 1280 K' = ratioveil.T 1280.00; '1600 K' = recon.T 1600.00; 'isolate this bath not Thorn' = gate.isol MODIFY; 'new head not referral' = gate.exec ACCEPT",
            "why_high_value": "New two-color-optical-pyrometer family on a BOF bath (not acoustic pyrometry r25, not phosphor-lifetime r39, not CARS TIT r29, not LII r31, not Gardon r51). Lead MODIFY of keep-blow on a recomputable hot ratio that a vendor last-good would have cleared, with a resolved-innocent pyrometer tech. Companion t2 is operational new-head restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202655167, "stream_note": "stream amplitudes are authored constants (nA, 1, K, um, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "two-color photocurrent exists at ~10 Hz; stream keeps 4 Is points plus one Il pair; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "pyro.Is": 1.2,
                    "pyro.Il": 1.2,
                    "pyro.snr": 1.2,
                    "recon.T": 60000,
                    "recon.R": 60000,
                    "lamp.cal": 60000,
                    "ratioveil.T": 60000,
                    "lamp.delay": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "bath.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "head.new": 60000,
                    "refer.hold": 60000,
                    "bath.held": 60000,
                    "vessel.trip": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "two-color reconstruction head: T_K = k_t * (Is / Il); R = Is / Il; Wien λT = 1.60 * T",
                "isolate-floor bath vs keep-blow vs vessel-trip",
                "exoneration head: missing lamp-cal AE plus timezone skip, not last-to-badge",
                "operational companion: new-head restart without referring the pyrometer tech",
            ],
        },
        "reconstruction_model": {
            "name": "two_color_optical_pyrometer_bof",
            "formula": "T_K = k_t * (Is_nA / Il_nA); R = Is_nA / Il_nA; wien_um_K = 1.60 * T_K",
            "parameters": {
                "k_t": 400.00,
                "Il_nA": 2.00,
                "isolate_floor_K": 1500.00,
                "trip_K": 1800.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"Is_nA": 8.00, "Il_nA": 2.00, "R": 4.00, "T_K": 1600.00, "wien_um_K": 2560.00},
            "check": "8.00 / 2.00 = 4.00 exactly; 400.00 * 4.00 = 1600.00 exactly; 1.60 * 1600.00 = 2560.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "sp5.pyro_bath_gate",
            "note": "MODIFY accumulator wins: two-color hot-ratio evidence overpowers the Ratioveil continue advocate",
            "decode_rule": "modify-isolate if temp_estimator AND ratio_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("temp_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("ratio_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "sp5.pyro_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "sp5.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r55-167",
            clock_domain="sp5-pyro-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["two-color-pyrometer", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 168 — magnetostrictive waveguide liquid level of an LPG sphere,
# simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_168():
    v_m_s = 3000.0
    t_ms = 8.00
    t_s = t_ms / 1000.0
    l_m = v_m_s * t_s / 2.0
    _exact(l_m, 12.00)
    _exact(v_m_s * 0.004 / 2.0, 6.00)
    _exact(v_m_s * 0.006 / 2.0, 9.00)
    _exact(v_m_s * 0.007 / 2.0, 10.50)
    s_m = v_m_s * t_s
    _exact(s_m, 24.00)
    _exact(s_m / 2.0, 12.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202655168,
        source="kw8.mtg.waveguide",
        target="kelpwharf.sphere_accept_core",
        table=[
            {"from": "mtg_t", "to": "level_estimator", "weight": 1.40},
            {"from": "mtg_v", "to": "tof_norm_core", "weight": 1.20},
            {"from": "floatveil_L", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.stage_rate_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-sphere synapses; the magnetostrictive modulator enables potentiation only while waveguide ToF and speed are co-active inside tau_e so a Floatveil last-good cannot skip spheres S-1 and S-3 on a 12.00 m high-level",
        },
        channel_prefix="mtg.n",
        anchor="KW-8 MTG-SIM-4 36 ms frame at t 8.00 ms / v 3000 m/s (t_s 3000) reconstructing 12.00 m on S-2 above the 10.00 isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "mtg.t", 4.00, code="T_MS", units="ms", note="simulated magnetostrictive waveguide liquid level of KW-8 LPG sphere S-2; float-plus-waveguide tank gauge, not MsS T(0,1) remaining wall, not GWR foam, not TDR cable remaining-length, not GPR liner cover"),
        ev(300000.0, "mtg.v", 3000.0, code="V_M_S", units="m_s", note="waveguide speed; held at 3000"),
        ev(600000.0, "recon.L", 6.00, code="L_M", units="m", note="3000*0.004/2=6.00 exact"),
        ev(900000.0, "mtg.snr", 14.0, code="MTG_SNR", units="1"),
        ev(1200000.0, "floatveil.L", 4.80, code="VENDOR_M", units="m", note="Floatveil last-good servo cloud; patched residual 6.00 m"),
        ev(1800000.0, "mtg.t", 6.00, code="T_MS", units="ms"),
        ev(2100000.0, "recon.L", 9.00, code="L_M", units="m", note="3000*0.006/2=9.00"),
        ev(2400000.0, "recon.s", 24.00, code="S_M", units="m", note="identity placeholder until lock; round-trip at lock is 24.00"),
        ev(2700000.0, "mtg.snr", 16.0, code="MTG_SNR", units="1"),
        ev(3000000.0, "mtg.t", 8.00, code="T_MS", units="ms", note="in-band frame; raster sidecar"),
        ev(3000001.5, "mtg.v", 3000.0, code="V_M_S", units="m_s", note="1.5 ms speed-norm after ToF"),
        ev(3300000.0, "recon.L", 12.00, code="L_M", units="m", note="3000*0.008/2=12.00 exact; isolate 10.00, sphere-trip 16.00"),
        ev(3600000.0, "floatveil.L", 4.80, code="VENDOR_M", units="m"),
        ev(3900000.0, "sph.id", 2.0, code="SPH", units="id"),
        ev(4200000.0, "s13.present", 1.0, code="S13_PRESENT", units="bool", note="adjacent spheres S-1 and S-3 are the skip-isolate object, not this sphere"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="sphere lead Gareth Pike: S-2 is green on Floatveil 4.80; skip S-1 and S-3 to save a morning survey"),
        ev(5400000.0, "gate.comp", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of S-2 isolate only; 12.00 m above 10.00 floor; S-1 and S-3 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_S13", units="bool", note="Pike: Floatveil 4.80, skip S-1 and S-3"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-isolate of S-1 and S-3 refused; S-2 hold stands"),
        ev(8400000.0, "s2.held", 1.0, code="S2_HELD", units="bool"),
        ev(9000000.0, "mtg.t", 7.00, code="T_MS", units="ms"),
        ev(9600000.0, "recon.L", 10.50, code="L_M", units="m", note="3000*0.007/2=10.50; still over the 10.00 isolate floor"),
        ev(10200000.0, "floatveil.L", 4.80, code="VENDOR_M", units="m"),
        ev(10800000.0, "s13.skip", 0.0, code="S13_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "sph.trip", 0.0, code="SPH_NOT_TRIPPED", units="bool"),
        ev(12000000.0, "mtg.snr", 15.0, code="MTG_SNR", units="1"),
        ev(12600000.0, "recon.s", 24.00, code="S_M", units="m", note="3000*0.008=24.00 on the lock-frame round-trip identity"),
        ev(13200000.0, "sph.held", 1.0, code="SPH_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "s2.held", 1.0, code="S2_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r55-168-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "KW-MTG-2026-0819",
            "domain": "mtg_lpg_sphere",
            "setting": "Kelpwharf LPG KW-8 (invented), Alderwick Terminal sphere farm. Simulated magnetostrictive coupon in MTG-SIM-4 supplies the waveguide ToF that times the in-band S-2 isolate. Plant-owned magnetostrictive reconstruction is the level SoT. Floatveil vendor last-good servo cloud is a corridor witness, not the sphere SoT. Invented plant; simulated campaign. Not MsS T(0,1) remaining wall (r14), not GWR foam (r39), not TDR remaining-length (r44), not GPR liner cover (r34).",
            "observables_at_decision": {
                "t_ms": t_ms,
                "v_m_s": v_m_s,
                "L_m": l_m,
                "s_m": s_m,
                "floatveil_m": 4.80,
                "mtg_snr": 16.0,
                "isolate_floor_m": 10.00,
            },
            "margin_authority": "KW-8 sphere SOP rev A: if reconstructed L_m >= 10.00 AND MTG SNR >= 12.0, sphere S-2 may be isolated as a high-level fill. Sphere-trip if L_m >= 16.00. S-1 and S-3 skip-isolate is a different gate. Floatveil last-good cannot skip an unmeasured sphere.",
        },
        "proposed_action": {
            "actor": "sphere lead Gareth Pike, citing Floatveil 4.80 m and a late morning survey",
            "summary": "stamp S-2 in band and skip S-1 and S-3; 8.00 ms is a float glitch on a healthy servo",
            "basis_claimed": "Floatveil last-good is 4.80 m and a night survey of S-1 and S-3 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Sphere S-2 is accepted as in-band for a single isolate. Serialized reconstruction: L_m = v * t / 2 = 3000.0 * 0.008 / 2 = 12.00, which is 2.00 m above the 10.00 isolate floor and 4.00 m under the 16.00 sphere-trip. Round-trip identity s = v * t = 24.00. Floatveil 4.80 m is a patched 6.00 residual and is not an admissible skip-isolate witness. Ordered: ACCEPT this S-2 isolate only. Scope: this ACCEPT does not skip S-1 and S-3 (that is the companion question) and does not stamp a sphere trip.",
            "threshold": "L_m>=10.00 AND mtg_snr>=12.0 => accept S-2 isolate; Floatveil is not SoT; sphere-trip if L_m>=16.00; S-1 and S-3 are out of scope",
            "stated_residuals": "12.00 vs 10.00 isolate floor is 2.00 m, not infinite; S-1 and S-3 remain unmeasured; Floatveil remains the only OEM servo channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: S-2 in band; S-1 and S-3 not skipped; Floatveil not SoT; reconstruction locked",
            "tool": "kw8-mtg-sph-gate-cli",
            "observation": "L 12.00 m recomputes from t 8.00 ms and v 3000 m/s; MTG-SIM-4 hashed; Floatveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "mtg t 8.00 ms; raster frame; L 12.00 m"},
                {"t_s": 4800.0, "event": "ops proposes accept S-2 and skip S-1/S-3"},
                {"t_s": 5400.0, "event": "ACCEPT S-2 only; S-1 and S-3 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-isolate of S-1 and S-3"},
            ],
            "observed_effects": [
                "level recomputes from the serialized magnetostrictive model at every recon.L event",
                "a Floatveil-only head would have skipped S-1 and S-3 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 4.80 m vendor servo corridor co-existed with a 12.00 m plant reconstruction on S-2 only",
            ],
            "new_state": {
                "s2": "isolated",
                "s13": "in scope unskipped",
                "floatveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("mtg_reconstruction", 0.14),
                ("bounded_s2_isolate", 0.12),
                ("floatveil_nonsubstitution", 0.10),
                ("sphere_scope_limit", 0.08),
                ("survey_time_cost", -0.03),
            ],
            "scored for a bounded S-2 ACCEPT on a recomputable magnetostrictive level while refusing a Floatveil 4.80 m corridor as a skip license; 12 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "magnetostrictive-level", "serialized-reconstruction", "operational-companion"],
            distillation_note="Magnetostrictive-level gate: serialized v*t/2 plus round-trip identity beats a green servo dashboard; companion t2 is the skip-sphere refusal, not a second level vote",
        ),
    }
    traj2 = {
        "id": "nelb-r55-168-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "KW-MTG-2026-0819-exec",
            "domain": "skip_sphere_refusal_execution",
            "setting": "Same KW-8 after the ACCEPT. Sphere lead proposes skipping S-1 and S-3 on Floatveil 4.80 m. This companion is the operational skip refusal, not a second level vote.",
            "observables_at_decision": {
                "L_m": 10.50,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "sphere lead Gareth Pike",
            "summary": "skip S-1 and S-3; 12 min already paid and Floatveil is 4.80 m",
            "basis_claimed": "the ACCEPT already isolated S-2, so skipping the adjacent spheres is the cheapest survey",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-isolate of S-1 and S-3 is refused. The 12 min survey floor is complete and the isolate tripwire (L_m >= 10.00) is still armed on the plant magnetostrictive head. REJECT the skip. Do not trip the sphere farm. S-2 hold stands. 10.50 m post-accept is still over the 10.00 isolate floor, so S-2 stays held; S-1 and S-3 remain unmeasured and in scope.",
            "threshold": "surv_floor_complete AND skip_not_taken AND sphere_not_tripped AND s2_held AND s13_in_scope",
        },
        "executed_action": {
            "summary": "skip refused at t_s 7800; S-1 and S-3 not skipped; sphere farm not tripped; S-2 held",
            "tool": "kw8-mtg-surv-exec",
            "observation": "recon.L 10.50 m on MTG-SIM-4; Floatveil still ignored; S-1 and S-3 remain in the survey",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "S-1/S-3 skip re-proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-isolate; S-2 hold stands"},
            ],
            "observed_effects": [
                "Floatveil restore did not reopen the level call",
                "sphere trip never fired; 12.00 vs 16.00 m floor",
                "S-1 and S-3 remain unskipped; S-2 is the only isolated sphere",
            ],
            "new_state": {"s2": "held", "s13": "in survey", "farm": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_sphere_refusal", 0.14),
                ("s2_hold_stands", 0.10),
                ("floatveil_nonsubstitution", 0.08),
                ("survey_floor_complete", 0.06),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip of unmeasured spheres because Floatveil is not a skip license; not a level re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-refusal"]),
    }
    return {
        "id": "nelb-r55-168",
        "spike_events": events,
        "language_view": {
            "description": "Kelpwharf LPG KW-8. Simulated magnetostrictive waveguide reconstructs 12.00 m from 8.00 ms / 3000 m/s while Floatveil still reports 4.80 m. The gate ACCEPTs an S-2 isolate only. A 12 min survey floor is serialized in the stream. Companion t2 REJECTs skipping S-1 and S-3.",
            "trajectory": traj,
            "trajectory_skip_sphere_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "mtg.t / mtg.v / mtg.snr": "waveguide ToF, speed, and SNR; the physics channels the reconstruction consumes",
                "recon.L / recon.s": "serialized level m and round-trip identity",
                "floatveil.L / sph.id / s13.present": "vendor last-good servo, sphere id, and adjacent-sphere presence; the denial and scope channels",
                "ops.prop / gate.comp / ops.skip / gate.hold": "accept-and-skip proposal, ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / s2.held / s13.skip / sph.trip / sph.held / takt.late": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-low while plant-high: floatveil.L 4.80 next to recon.L 12.00",
                "reconstruction as event: recon.L 12.00 equals 3000*0.008/2",
                "ACCEPT then operational REJECT: gate.comp at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight mtg pair: mtg.t then mtg.v +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Floatveil is 4.80 m' = floatveil.L 4.80; '12 m' = recon.L 12.00; 'accept S-2 only' = gate.comp ACCEPT; 'do not skip S-1/S-3' = gate.hold REJECT",
            "why_high_value": "New magnetostrictive-waveguide liquid-level family on an LPG sphere (not MsS T(0,1) r14, not GWR r39, not TDR r44, not GPR r34). Lead bounded ACCEPT of S-2 isolate on a recomputable high-level that a vendor servo last-good would have used to skip adjacent spheres. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202655168, "stream_note": "stream amplitudes are authored constants (ms, m/s, m, 1, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "magnetostrictive interrogation exists at ~10 Hz; stream keeps 4 t points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "mtg.t": 1.5,
                    "mtg.v": 1.5,
                    "mtg.snr": 1.5,
                    "recon.L": 60000,
                    "recon.s": 60000,
                    "floatveil.L": 60000,
                    "sph.id": 60000,
                    "s13.present": 60000,
                    "ops.prop": 60000,
                    "gate.comp": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "s2.held": 60000,
                    "s13.skip": 60000,
                    "sph.trip": 60000,
                    "sph.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "magnetostrictive reconstruction head: L = v * t / 2; s = v * t",
                "bounded ACCEPT head: in-band level AND sphere scope AND s13-out-of-scope",
                "operational companion: refuse skip-isolate without re-opening the servo call",
            ],
        },
        "reconstruction_model": {
            "name": "magnetostrictive_waveguide_lpg_level",
            "formula": "L_m = v_m_s * (t_ms/1000) / 2; s_m = v_m_s * (t_ms/1000)",
            "parameters": {
                "v_m_s": 3000.0,
                "isolate_floor_m": 10.00,
                "sphere_trip_m": 16.00,
                "surv_min": 12.0,
            },
            "worked_example": {"t_ms": 8.00, "L_m": 12.00, "s_m": 24.00},
            "check": "3000.0 * 0.008 / 2 = 12.00 exactly; 3000.0 * 0.008 = 24.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "kw8.mtg_sph_gate",
            "note": "ACCEPT accumulator wins: magnetostrictive level evidence overpowers the Floatveil skip advocate",
            "decode_rule": "accept if level_estimator AND tof_norm AND sphere_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release S-1 and S-3",
            "populations": [
                gate_pop("level_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("tof_norm", 64, 1.2, 31.25, w_s),
                gate_pop("sphere_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "kw8.mtg_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "kw8.level_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r55-168",
            clock_domain="kw8-mtg-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["magnetostrictive-level", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
