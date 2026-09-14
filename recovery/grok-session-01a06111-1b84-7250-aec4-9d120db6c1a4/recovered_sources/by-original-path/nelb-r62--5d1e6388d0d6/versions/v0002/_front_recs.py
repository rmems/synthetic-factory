def occupancy_preflight():
    claimed = (
        "gamma backscatter",
        "backveil",
        "peatshaw",
        "glenmere",
        "olen voss",
        "ndir remaining",
        "non-dispersive infrared",
        "carbveil",
        "woldshaw",
        "quillfen hydro",
        "mira venn",
        "joss hale",
        "ndir-hil-3",
        "ultrasonic doppler",
        "shiftveil",
        "bramblefen",
        "slatemere",
        "nessa holt",
        "usd-sim-2",
    )
    steal = (
        "irisveil",
        "gageveil",
        "beadveil",
        "laser triangulation",
        "catalytic-bead",
        "pellistor",
        "fidveil",
        "doasveil",
        "flame-ionization",
        "turbine k-factor",
        "photoionization-detector",
        "contact pulse-echo remaining-wall",
        "zirconia-nernst",
        "rogowski-coil",
        "beta-attenuation",
        "uv-doas remaining",
        "aluminum-oxide remaining-moisture",
        "load-cell remaining-mass",
        "dielectric remaining",
        "stern-volmer",
        "fmcw tank-radar",
        "critical-angle-refractometer",
        "white-light-interferometry",
        "annubar-averaging-pitot",
        "orifice-plate dP",
        "katharometer",
        "venturi remaining",
        "polarographic",
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
        + sorted(root.glob("nelb-r*/_recs_*.py"))
        + sorted(root.glob("nelb-r*/_recs_and_tail.py"))
    )
    import re
    for n in scan:
        if "nelb-r62" in str(n):
            continue
        raw = n.read_text(encoding="utf-8", errors="replace")
        text = raw.casefold()
        leads = re.findall(r'why_high_value": "new ([^"]+)', text)
        leads += re.findall(r"^# record \d+[^\n]*", text, flags=re.M)
        leads += re.findall(r"\| (nelb-r\d+-\d+) \| ([^|]+) \|", text)
        blob_leads = " ".join(
            x if isinstance(x, str) else " ".join(x) for x in leads
        )
        for b in claimed:
            if b in blob_leads:
                hits.append(f"{n}:{b}")
            elif b in text and "(r62)" not in text and "nelb-r62" not in text:
                # plant/vendor tokens should not appear as leads elsewhere
                if b in {
                    "backveil",
                    "peatshaw",
                    "glenmere",
                    "olen voss",
                    "carbveil",
                    "woldshaw",
                    "quillfen hydro",
                    "mira venn",
                    "joss hale",
                    "ndir-hil-3",
                    "shiftveil",
                    "bramblefen",
                    "slatemere",
                    "nessa holt",
                    "usd-sim-2",
                }:
                    hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"family/plant collision {hits}")
    blob = json.dumps([rec_187(), rec_188(), rec_189()], ensure_ascii=False).casefold()
    for s in steal:
        if s in blob:
            raise RuntimeError(f"r62 stole occupied family {s}")


# ---------------------------------------------------------------------------
# Record 187 — gamma-backscatter remaining lining of a rotary kiln, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_187():
    k_b = 32.00
    i_nA = 4.00
    d_mm = k_b / i_nA
    _exact(d_mm, 8.00)
    t_nom = 20.00
    loss_mm = t_nom - d_mm
    _exact(loss_mm, 12.00)
    _exact(i_nA * d_mm, 32.00)
    _exact(k_b / 2.00, 16.00)
    _exact(k_b / (8.00 / 3.00), 12.00)
    _exact(k_b / 3.20, 10.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609187,
        source="ps7.gbs.I",
        target="peatshaw.kiln_stop_core",
        table=[
            {"from": "gbs_I", "to": "lining_estimator", "weight": 1.40},
            {"from": "gbs_snr", "to": "gbs_lock_core", "weight": 1.15},
            {"from": "backveil_d", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-firing synapses; the plant gamma-backscatter modulator depresses continue-firing links when scatter current stays high inside tau_e of an SNR lock so a Backveil last-campaign patch cannot hide an 8.00 mm remaining lining",
        },
        channel_prefix="gbs.n",
        anchor="PS-7 gamma-backscatter 40 ms frame at I 4.00 nA / SNR 12.0 (t_s 3000) reconstructing 8.00 mm remaining lining below the 12.00 min-lining floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "gbs.I", 2.00, code="I_NA", units="nA", note="plant-owned gamma backscatter on PS-7 kiln K-3; remaining-lining family, not Cs-137 densitometry, not He-3 neutron-backscatter, not Kr-85 beta, not FMCW lining, not IRIS pulse-echo, not contact pulse-echo, not PAUT TFM"),
        ev(300000.0, "gbs.snr", 6.0, code="GBS_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.d", 16.00, code="D_MM", units="mm", note="32.00/2.00=16.00 exact; still above the 12.00 min-lining floor"),
        ev(900000.0, "kiln.shell", 612.0, code="SHELL_K", units="K", note="plant shell thermocouple on copper fieldbus; independent witness; unread by Backveil"),
        ev(1200000.0, "backveil.d", 18.40, code="VENDOR_MM", units="mm", note="Backveil vendor GBS-9 last-campaign cloud; infra owner; patched I timestamps"),
        ev(1800000.0, "gbs.I", 8.00 / 3.00, code="I_NA", units="nA"),
        ev(2100000.0, "recon.d", 12.00, code="D_MM", units="mm", note="32.00/(8.00/3.00)=12.00; at the 12.00 min-lining floor"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="turnaround clerk slid the remaining-lining permit clock 40.00 s; collusion party"),
        ev(2700000.0, "idfan.Q", 80.0, code="IDFAN_KNM3H", units="knm3_h", note="plant ID-fan PLC on copper DCS; independent witness"),
        ev(3000000.0, "gbs.I", 4.00, code="I_NA", units="nA", note="min-lining frame; raster sidecar"),
        ev(3000001.3, "gbs.snr", 12.0, code="GBS_SNR", units="1", note="1.3 ms SNR lock after I; 12.0 >= 8.0"),
        ev(3300000.0, "recon.d", 8.00, code="D_MM", units="mm", note="32.00/4.00=8.00 exact; min-lining 12.00"),
        ev(3600000.0, "recon.prod", 32.00, code="I_D", units="nA_mm", note="4.00*8.00=32.00 exact product identity"),
        ev(3900000.0, "kiln.shell", 618.0, code="SHELL_K", units="K", note="shell TC tracks the plant gamma head, not Backveil 18.40"),
        ev(4200000.0, "gbs.drop", 1.0, code="GBS_DROP", units="bool", note="vendor I packets dropped in Backveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_FIRING", units="bool", note="night operator Olen Voss: Backveil is clean 18.40 mm; keep K-3 in service"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-firing; 8.00 mm and SNR 12.0; Backveil not SoT"),
        ev(6000000.0, "soak.start", 1.0, code="SOAK_HOLD_START", units="bool", note="bookend 1 of the 18.0 min kiln-soak hold floor"),
        ev(7080000.0, "soak.floor", 1.0, code="SOAK_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="KILN_TRIP", units="bool", note="Voss: trip the whole Peatshaw kiln until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: kiln-soak hold on plant gamma as live interlock; kiln trip refused"),
        ev(9000000.0, "soak.set", 1.0, code="SOAK_HELD", units="bool"),
        ev(9600000.0, "gbs.I", 3.20, code="I_NA", units="nA"),
        ev(10200000.0, "recon.d", 10.00, code="D_MM", units="mm", note="32.00/3.20=10.00; still below 12.00 so soak holds"),
        ev(10800000.0, "backveil.d", 18.32, code="VENDOR_MM", units="mm"),
        ev(11400000.0, "idfan.Q", 82.0, code="IDFAN_KNM3H", units="knm3_h"),
        ev(12000000.0, "soak.held", 1.0, code="SOAK_HELD", units="bool"),
        ev(12600000.0, "kiln.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "kiln.shell", 610.0, code="SHELL_K", units="K"),
        ev(14400000.0, "gbs.drop", 1.0, code="GBS_DROP", units="bool"),
        ev(15000000.0, "soak.lock", 1.0, code="SOAK_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r62-187-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "PS-GBS-2026-0902",
            "domain": "gamma_backscatter_kiln_remaining_lining",
            "setting": "Peatshaw Kiln PS-7 (invented), Glenmere Cement Yard, kiln K-3. Plant-owned gamma-backscatter current is the remaining-lining SoT. Backveil / GBS-9 vendor DAQ (infra owner) plus the remaining-lining permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not Cs-137 densitometry (r27), not He-3 neutron-backscatter (r40), not Kr-85 beta (r40), not FMCW lining (r33), not IRIS pulse-echo (r56), not contact pulse-echo (r57), not PAUT TFM (r23).",
            "observables_at_decision": {
                "I_nA": i_nA,
                "k_b": k_b,
                "d_mm": d_mm,
                "t_nom_mm": t_nom,
                "loss_mm": loss_mm,
                "gbs_snr": 12.0,
                "backveil_mm": 18.40,
                "permit_slide_s": 40.00,
                "min_lining_mm": 12.00,
            },
            "margin_authority": "PS-7 kiln SOP rev C: if reconstructed d_mm <= 12.00 AND gamma SNR >= 8.0, continue-firing is forbidden even if Backveil reports 18.40 mm. Kiln trip is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Olen Voss, citing Backveil 18.40 mm and a quiet GBS-9 current",
            "summary": "keep kiln K-3 firing; 4.00 nA is a dust-plume glitch on a healthy 18.40 mm last campaign",
            "basis_claimed": "Backveil is the only OEM gamma SoT and a night abort of K-3 is a turnaround miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-firing is refused. Serialized reconstruction: d_mm = k_b / I = 32.00 / 4.00 = 8.00, below the 12.00 mm min-lining floor, and gamma SNR is 12.0 >= 8.0. Product identity I * d = 4.00 * 8.00 = 32.00. Loss identity t_nom - d = 20.00 - 8.00 = 12.00. Permit clock was slid 40.00 s and vendor I packets were dropped, so Backveil is a collusion party (gamma vendor plus operator plus turnaround clerk). Ordered: refuse continue-firing now. Scope: this REJECT does not trip the kiln (that is the companion question) and does not isolate the shell thermocouple.",
            "threshold": "d_mm<=12.00 AND gbs_snr>=8.0 => refuse continue-firing; Backveil is not SoT",
            "stated_residuals": "soak still required to hold the 8.00 mm; 8.00 vs a true shell hotspot is a production cut; Backveil remains the only OEM gamma channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-firing refused; Backveil not SoT; reconstruction locked",
            "tool": "ps7-gbs-kiln-gate-cli",
            "observation": "d 8.00 mm recomputes from I 4.00 nA; plant gamma hashed; Backveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "gbs I 4.00 nA; raster frame; d 8.00 mm"},
                {"t_s": 4800.0, "event": "ops proposes continue-firing"},
                {"t_s": 5400.0, "event": "REJECT continue-firing"},
                {"t_s": 6000.0, "event": "18 min kiln-soak bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY kiln-soak hold vs kiln trip"},
            ],
            "observed_effects": [
                "remaining lining recomputes from the serialized gamma-backscatter model at every recon.d event",
                "a Backveil-only head would have continued firing overnight",
                "18 min kiln-soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a clean vendor gamma corridor and a 40 s permit slide co-existed with an 8.00 mm plant reconstruction",
            ],
            "new_state": {
                "kiln_k3": "continue-firing blocked",
                "backveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("gbs_reconstruction", 0.14),
                ("conjunctive_min_lining", 0.12),
                ("backveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("soak_time_cost", -0.03),
            ],
            "scored for a continue-firing REJECT on a recomputable gamma-backscatter remaining lining while refusing a Backveil last-campaign patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "gamma-backscatter", "serialized-reconstruction", "operational-companion"],
            distillation_note="Gamma-backscatter remaining-lining gate: serialized k_b/I plus SNR lock beats a vendor last-campaign patch; companion t2 is the kiln-soak hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r62-187-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "PS-GBS-2026-0902-exec",
            "domain": "kiln_soak_gbs_interlock_execution",
            "setting": "Same PS-7 after the REJECT. Operator proposes a kiln trip. This companion is the operational kiln-soak hold with the plant gamma head as the live interlock, not a second remaining-lining vote.",
            "observables_at_decision": {
                "d_mm": 10.00,
                "soak_hold_floor_s": 1080.0,
                "kiln_trip_proposed": True,
                "soak_hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Olen Voss",
            "summary": "trip the whole Peatshaw kiln until day-shift; 18 min already paid and Backveil still shows 18.32 mm",
            "basis_claimed": "the REJECT already stopped firing, so a kiln trip is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Kiln-soak hold plus plant gamma as the live interlock. The 18 min soak floor is complete and the min-lining tripwire (d_mm <= 12.00) is still armed on the plant gamma head. MODIFY the default GBS-restore SOP into a plant-gamma-only interlock. Do not trip the kiln. Do not restore firing on Backveil. 10.00 mm post-stop is still the plant SoT until a new frame clears 12.00.",
            "threshold": "soak_hold AND soak_floor_complete AND kiln_trip_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "kiln-soak held at t_s 8400; kiln trip not latched; Backveil restore not taken",
            "tool": "ps7-kiln-soak-exec",
            "observation": "recon.d 10.00 mm after stop; soak line-up complete; Backveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "kiln-soak clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "kiln trip proposed"},
                {"t_s": 8400.0, "event": "MODIFY kiln-soak hold; kiln trip refused"},
            ],
            "observed_effects": [
                "Backveil restore did not reopen the remaining-lining call",
                "kiln trip never fired; K-3 held soak on the plant gamma head",
            ],
            "new_state": {"soak": "held", "kiln": "in service", "kiln_k3": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("kiln_soak_hold", 0.12),
                ("no_kiln_trip", 0.10),
                ("backveil_nonsubstitution", 0.08),
                ("soak_floor_complete", 0.06),
                ("held_firing_cost", -0.02),
            ],
            "operational execution gate: kiln-soak hold because Backveil is not a restore license; not a remaining-lining re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "kiln-soak-hold"]),
    }
    return {
        "id": "nelb-r62-187",
        "spike_events": events,
        "language_view": {
            "description": "Peatshaw Kiln PS-7. Plant-owned gamma backscatter reconstructs 8.00 mm remaining lining from 4.00 nA while Backveil still reports 18.40 mm. The gate REJECTs continue-firing. An 18 min kiln-soak floor is serialized in the stream. Companion t2 MODIFYs a kiln trip into a plant-gamma soak hold.",
            "trajectory": traj,
            "trajectory_kiln_soak_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "gbs.I / gbs.snr": "gamma-backscatter current and SNR; the physics channels the reconstruction consumes",
                "recon.d / recon.prod": "serialized remaining lining mm and I*d product identity",
                "kiln.shell / backveil.d / permit.slide / idfan.Q / gbs.drop": "shell TC, vendor last-campaign, permit clock slide, ID-fan, and dropped gamma packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-firing proposal, REJECT, kiln-trip proposal, companion MODIFY",
                "soak.start / soak.floor / soak.set / soak.held / kiln.trip / soak.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-under: backveil.d 18.40 next to recon.d 8.00",
                "reconstruction as event: recon.d 8.00 equals 32.00/4.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: soak.start 6000 s, soak.floor 7080 s (18.0 min)",
                "tight gbs pair: gbs.I then gbs.snr +1.3 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Backveil is 18.40 mm' = backveil.d 18.40; '8 mm remaining' = recon.d 8.00; 'refuse continue-firing' = gate.stop REJECT; 'soak not kiln trip' = gate.hold MODIFY",
            "why_high_value": "New gamma-backscatter remaining-lining family on a rotary kiln (not Cs-137 densitometry r27, not He-3 backscatter r40, not Kr-85 beta r40, not FMCW lining r33, not IRIS r56, not contact pulse-echo r57, not PAUT TFM r23). Lead REJECT of continue-firing on a recomputable remaining lining that a vendor last-campaign patch and a permit clock slide would have cleared. Three-party collusion includes the gamma infra owner. Companion t2 is operational kiln-soak hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609187, "stream_note": "stream amplitudes are authored constants (nA, 1, mm, s, K, knm3_h, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "gamma backscatter exists at ~1 Hz; stream keeps 4 I points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "gbs.I": 1.3,
                    "gbs.snr": 1.3,
                    "recon.d": 60000,
                    "recon.prod": 60000,
                    "kiln.shell": 60000,
                    "backveil.d": 60000,
                    "permit.slide": 60000,
                    "idfan.Q": 60000,
                    "gbs.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "soak.set": 60000,
                    "soak.held": 60000,
                    "kiln.trip": 60000,
                    "soak.lock": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "gamma-backscatter reconstruction head: d_mm = k_b / I; I * d = k_b; loss = t_nom - d",
                "conjunctive min-lining floor vs continue-firing vs kiln trip",
                "vendor-gamma nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: kiln-soak hold without restoring on Backveil",
            ],
        },
        "reconstruction_model": {
            "name": "gamma_backscatter_kiln_lining",
            "formula": "d_mm = k_b / I_nA; prod = I_nA * d_mm; loss_mm = t_nom_mm - d_mm",
            "parameters": {
                "k_b": 32.00,
                "t_nom_mm": 20.00,
                "min_lining_mm": 12.00,
                "snr_lock": 8.0,
                "soak_hold_min": 18.0,
            },
            "worked_example": {"I_nA": 4.00, "d_mm": 8.00, "prod": 32.00, "loss_mm": 12.00},
            "check": "32.00 / 4.00 = 8.00 exactly; 4.00 * 8.00 = 32.00 exactly; 20.00 - 8.00 = 12.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "ps7.gbs_kiln_gate",
            "note": "REJECT accumulator wins: plant gamma-backscatter remaining-lining evidence overpowers the Backveil continue advocate",
            "decode_rule": "reject-continue if lining_estimator AND gbs_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("lining_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("gbs_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ps7.gbs_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "ps7.soak_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r62-187",
            clock_domain="ps7-gbs-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["gamma-backscatter", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 188 — NDIR remaining CO of a reformer arch, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_188():
    k_n = 10.00
    i0 = 8.00
    i_ndir = 2.00
    c_ppm = k_n * (i0 / i_ndir - 1.0)
    _exact(c_ppm, 30.00)
    r_i = i0 / i_ndir
    _exact(r_i, 4.00)
    _exact(k_n * (i0 / 4.00 - 1.0), 10.00)
    _exact(k_n * (i0 / (8.00 / 3.00) - 1.0), 20.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609188,
        source="ws4.ndir.I",
        target="woldshaw.arch_isolate_core",
        table=[
            {"from": "ndir_I", "to": "co_estimator", "weight": 1.35},
            {"from": "ndir_snr", "to": "lamp_norm_core", "weight": 1.20},
            {"from": "carbveil_c", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-firing synapses; the NDIR modulator depresses keep-firing and referral links when the CO optical depth stays high inside tau_e of an SNR lock so a Carbveil last-good cannot hide a 30.00 ppm arch or name Joss Hale",
        },
        channel_prefix="ndir.n",
        anchor="WS-4 HIL coupon 32 ms frame at I 2.00 / I0 8.00 / SNR 14.0 (t_s 1560) reconstructing 30.00 ppm CO above the 20.00 isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "ndir.I", 4.00, code="I_NA", units="nA", note="HIL NDIR CO bench on a dummy reformer arch in NDIR-HIL-3; remaining-CO family, not TDLAS NH3, not CRDS HF, not QEPAS, not CEMS FTIR k-script, not UV-DOAS SO2, not CLD NOx, not paramagnetic O2, not PID VOC, not FID THC"),
        ev(180000.0, "ndir.snr", 9.0, code="NDIR_SNR", units="1", note="early NDIR SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.C", 10.00, code="C_PPM", units="ppm", note="10.00*(8.00/4.00-1)=10.00 exact"),
        ev(540000.0, "lamp.cal", 1.00, code="CAL", units="1", note="plant lamp-cal remaining; no path-length hop in this window"),
        ev(720000.0, "carbveil.C", 4.80, code="VENDOR_PPM", units="ppm", note="Carbveil last-good CO-cloud; not admissible SoT"),
        ev(900000.0, "ndir.I", 8.00 / 3.00, code="I_NA", units="nA"),
        ev(1080000.0, "recon.C", 20.00, code="C_PPM", units="ppm", note="10.00*(8.00/(8.00/3.00)-1)=20.00; at the 20.00 isolate floor"),
        ev(1260000.0, "lamp.delay", 0.0, code="LAMP_AE", units="bool", note="missing lamp-cal AE burst; Carbveil UTC vs plant UTC+2 skipped the cal by 120 min"),
        ev(1440000.0, "lamp.cal", 1.00, code="CAL", units="1"),
        ev(1560000.0, "ndir.I", 2.00, code="I_NA", units="nA", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "ndir.I0", 8.00, code="I0", units="nA", note="1.2 ms I0 after sample beam; ratio 4.00"),
        ev(1740000.0, "recon.C", 30.00, code="C_PPM", units="ppm", note="10.00*(8.00/2.00-1)=30.00 exact; isolate 20.00, trip 80.00"),
        ev(1920000.0, "recon.R", 4.00, code="R", units="1", note="8.00/2.00=4.00 exact; I0/I identity"),
        ev(2100000.0, "carbveil.C", 4.80, code="VENDOR_PPM", units="ppm"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_FIRE_REFER", units="bool", note="night lead Mira Venn: keep arch A-1 firing and refer NDIR tech Joss Hale"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this arch; refuse the person-referral; Carbveil not SoT"),
        ev(2640000.0, "arch.lock", 1.0, code="ARCH_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min steam-standby plus NDIR-settle floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_HALE", units="bool", note="Venn: Hale badge was on the NDIR log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-NDIR restart; person-referral refused; reformer trip refused"),
        ev(4800000.0, "ndir.new", 1.0, code="NEW_NDIR", units="bool"),
        ev(4980000.0, "ndir.I", 8.00 / 3.00, code="I_NA", units="nA"),
        ev(5160000.0, "recon.C", 20.00, code="C_PPM", units="ppm", note="10.00*(8.00/(8.00/3.00)-1)=20.00; HIL dummy still at the 20.00 isolate floor so the isolated arch stays held"),
        ev(5340000.0, "carbveil.C", 4.74, code="VENDOR_PPM", units="ppm"),
        ev(5520000.0, "lamp.cal", 1.00, code="CAL", units="1"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Hale exonerated; missing lamp-cal AE precedes the high CO, not the badge touch"),
        ev(5880000.0, "arch.held", 1.0, code="ARCH_HELD", units="bool"),
        ev(6060000.0, "lamp.delay", 1.0, code="LAMP_AE", units="bool", note="lamp-cal AE restored on the new NDIR"),
        ev(6240000.0, "recon.R", 4.00, code="R", units="1", note="identity holds on the isolate-frame ratio"),
        ev(6420000.0, "ref.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r62-188-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "WS-NDIR-2026-0718",
            "domain": "ndir_reformer_remaining_co",
            "setting": "Woldshaw Reformer WS-4 (invented), Quillfen Hydro Yard, arch A-1. Hardware-in-the-loop dummy arch in NDIR-HIL-3 supplies the NDIR beam current that times the in-service isolate. Plant-owned NDIR reconstruction is the CO SoT. Carbveil vendor CO scheduler is a corridor witness, not the arch SoT. Not TDLAS NH3 (r22), not CRDS HF (r15), not QEPAS (r19), not CEMS FTIR (r04), not UV-DOAS SO2 (r59), not CLD NOx (r52), not paramagnetic O2 (r46), not PID VOC (r57), not FID THC (r55).",
            "observables_at_decision": {
                "I": i_ndir,
                "I0": i0,
                "R": r_i,
                "k_n": k_n,
                "C_ppm": c_ppm,
                "carbveil_ppm": 4.80,
                "lamp_cal": 1.00,
                "lamp_delay": 0.0,
                "isolate_floor_ppm": 20.00,
            },
            "margin_authority": "WS-4 arch SOP rev B: if reconstructed C_ppm >= 20.00 AND NDIR SNR >= 12.0, isolate this arch this night. A Carbveil last-good or a quiet lamp-cal residual cannot keep the fire. Trip tripwire is 80.00 ppm. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Mira Venn, citing Carbveil 4.80 ppm and lamp-cal 1.00, and naming NDIR tech Joss Hale as last-to-badge",
            "summary": "keep arch A-1 firing and refer Hale; 2.00 nA is a soot-window glitch on a healthy bench",
            "basis_claimed": "Carbveil last-good is 4.80 ppm and a night isolate of A-1 is a takt miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-firing is refused; the person-referral is also refused. Serialized reconstruction: C_ppm = k_n * (I0 / I - 1) = 10.00 * (8.00 / 2.00 - 1) = 30.00, which is 10.00 ppm over the 20.00 isolate floor and 50.00 ppm under the 80.00 trip tripwire. Ratio identity I0/I = 8.00/2.00 = 4.00. Carbveil 4.80 ppm is a last-good skip stamp and is not an admissible keep-firing witness. The missing lamp-cal AE burst sits on a Carbveil UTC-vs-UTC+2 skip (120 min), not on Hale's badge, and the plant lamp-cal stays 1.00, so the easy referral fails command-custody. Ordered: isolate this arch now. Scope: this MODIFY does not trip the reformer (that is the companion question) and does not name Hale.",
            "threshold": "C_ppm>=20.00 AND ndir_snr>=12.0 => isolate this arch; Carbveil is not SoT; trip if C_ppm>=80.00; referral requires badge-touch preceding the high CO",
            "stated_residuals": "30 vs 80 trip floor is 50 ppm, not infinite; new-NDIR restart still required; Carbveil remains the only OEM CO channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: arch isolated; Hale not named; Carbveil not SoT; reconstruction locked",
            "tool": "ws4-ndir-arch-gate-cli",
            "observation": "C 30.00 ppm recomputes from I 2.00 and I0 8.00; HIL coupon hashed; Carbveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "ndir I 2.00 I0 8.00; raster frame; C 30.00 ppm"},
                {"t_s": 2280.0, "event": "ops proposes keep-firing plus Hale referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate arch; referral refused"},
                {"t_s": 2820.0, "event": "24 min steam-standby bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-NDIR restart; referral still refused"},
            ],
            "observed_effects": [
                "C recomputes from the serialized NDIR model at every recon.C event",
                "a Carbveil-only head would have kept the arch firing overnight",
                "24 min steam-standby plus NDIR-settle floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a last-good 4.80 ppm vendor corridor and a quiet lamp-cal residual co-existed with a 30.00 ppm arch, and the obvious NDIR tech was not on the causal path",
            ],
            "new_state": {
                "arch_a1": "isolated",
                "hale": "exonerated",
                "carbveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("ndir_reconstruction", 0.14),
                ("isolate_floor_arch", 0.12),
                ("exoneration", 0.10),
                ("carbveil_nonsubstitution", 0.08),
                ("settle_time_cost", -0.04),
            ],
            "scored for a keep-firing MODIFY on a recomputable high CO while refusing a Carbveil 4.80 ppm corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "ndir-co", "serialized-reconstruction", "operational-companion"],
            distillation_note="NDIR remaining-CO gate: serialized k_n*(I0/I-1) plus ratio identity beats a green CO dashboard; companion t2 is the new-NDIR restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r62-188-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "WS-NDIR-2026-0718-exec",
            "domain": "new_ndir_standby_execution",
            "setting": "Same WS-4 after the MODIFY. Night lead proposes referring Hale and tripping the reformer. This companion is the operational new-NDIR steam-standby restart, not a second CO vote.",
            "observables_at_decision": {
                "C_ppm": 20.00,
                "R": 4.00,
                "cool_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Mira Venn",
            "summary": "refer Hale and trip the reformer; 24 min already paid and Carbveil is 4.74 ppm",
            "basis_claimed": "the MODIFY already cut the arch, so a reformer kill plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different NDIR after the steam-standby floor. The 24 min NDIR-settle is complete and the trip tripwire (C_ppm >= 80.00) is still armed on the plant NDIR head. ACCEPT the new-NDIR restart. Do not refer Hale. Do not trip the reformer. 20.00 ppm post-isolate is still at the 20.00 isolate floor, so the isolated arch stays held; the new NDIR may run.",
            "threshold": "new_ndir AND cool_floor_complete AND refer_not_taken AND reformer_not_tripped AND isolated_arch_held",
        },
        "executed_action": {
            "summary": "new-NDIR restart at t_s 4620; Hale not referred; reformer not tripped; isolated arch held",
            "tool": "ws4-ndir-cool-exec",
            "observation": "recon.C 20.00 ppm on the HIL dummy; lamp-cal AE present on the new NDIR; Carbveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "steam-standby clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Hale referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-NDIR restart; referral refused"},
            ],
            "observed_effects": [
                "Carbveil restore did not reopen the CO call",
                "reformer trip never fired; 30 vs 80 ppm floor",
                "Hale remains unnamed; missing lamp-cal AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new NDIR", "hale": "exonerated", "arch": "held", "reformer": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_ndir_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_reformer_trip", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_arch_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new NDIR because Carbveil is not a restore license and Hale is not on the causal path; not a CO re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r62-188",
        "spike_events": events,
        "language_view": {
            "description": "Woldshaw Reformer WS-4. HIL NDIR reconstructs 30.00 ppm CO from 8.00/2.00 nA while Carbveil still shows 4.80 ppm and the lamp-cal 1.00. The gate MODIFYs arch isolate and refuses the NDIR-tech referral. A 24 min steam-standby floor is serialized in the stream. Companion t2 ACCEPTs a new-NDIR restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_ndir": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ndir.I / ndir.I0 / ndir.snr": "NDIR sample beam, lamp I0, and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.R": "serialized CO ppm and I0/I identity",
                "lamp.cal / carbveil.C / lamp.delay": "plant lamp-cal, vendor last-good, and lamp-cal AE; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-firing proposal, MODIFY, referral proposal, companion ACCEPT",
                "arch.lock / cool.start / cool.floor / ndir.new / refer.hold / arch.held / ref.trip / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: carbveil.C 4.80 next to recon.C 30.00",
                "reconstruction as event: recon.C 30.00 equals 10.00*(8.00/2.00-1)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight ndir pair: ndir.I then ndir.I0 +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Carbveil is 4.80 ppm' = carbveil.C 4.80; '30 ppm CO' = recon.C 30.00; 'isolate this arch not Hale' = gate.isol MODIFY; 'new NDIR not referral' = gate.exec ACCEPT",
            "why_high_value": "New NDIR remaining-CO family on a reformer arch (not TDLAS r22, not CRDS r15, not QEPAS r19, not CEMS r04, not UV-DOAS r59, not CLD NOx r52, not paramagnetic O2 r46, not PID r57, not FID r55). Lead MODIFY of keep-firing on a recomputable high CO that a vendor last-good would have cleared, with a resolved-innocent NDIR tech. Companion t2 is operational new-NDIR restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609188, "stream_note": "stream amplitudes are authored constants (nA, 1, ppm, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "NDIR beam exists at ~1 Hz; stream keeps 4 I points plus one I0 pair; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "ndir.I": 1.2,
                    "ndir.I0": 1.2,
                    "ndir.snr": 1.2,
                    "recon.C": 60000,
                    "recon.R": 60000,
                    "lamp.cal": 60000,
                    "carbveil.C": 60000,
                    "lamp.delay": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "arch.lock": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "ndir.new": 60000,
                    "refer.hold": 60000,
                    "arch.held": 60000,
                    "ref.trip": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "NDIR reconstruction head: C_ppm = k_n * (I0 / I - 1); R = I0 / I",
                "isolate-floor arch vs keep-firing vs reformer-trip",
                "exoneration head: missing lamp-cal AE plus timezone skip, not last-to-badge",
                "operational companion: new-NDIR restart without referring the NDIR tech",
            ],
        },
        "reconstruction_model": {
            "name": "ndir_reformer_remaining_co",
            "formula": "C_ppm = k_n * (I0 / I - 1); R = I0 / I",
            "parameters": {
                "k_n": 10.00,
                "I0": 8.00,
                "isolate_floor_ppm": 20.00,
                "trip_ppm": 80.00,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"I": 2.00, "I0": 8.00, "R": 4.00, "C_ppm": 30.00},
            "check": "8.00 / 2.00 = 4.00 exactly; 10.00 * (8.00 / 2.00 - 1) = 30.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "ws4.ndir_arch_gate",
            "note": "MODIFY accumulator wins: NDIR high-CO evidence overpowers the Carbveil continue advocate",
            "decode_rule": "modify-isolate if co_estimator AND lamp_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("co_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("lamp_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ws4.ndir_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "ws4.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r62-188",
            clock_domain="ws4-ndir-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["ndir-co", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }

