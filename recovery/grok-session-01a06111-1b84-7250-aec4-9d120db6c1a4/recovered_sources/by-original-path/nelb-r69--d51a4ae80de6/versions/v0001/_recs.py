# ---------------------------------------------------------------------------
# Record 208 — flame-photometric remaining sulfur of a fuel-gas header, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_208():
    k_f = 4.00
    i_na = 24.00
    i_ref = 8.00
    c_ppm = k_f * i_na / i_ref
    _exact(c_ppm, 12.00)
    _exact(k_f * 8.00 / i_ref, 4.00)
    _exact(k_f * 16.00 / i_ref, 8.00)
    _exact(k_f * 32.00 / i_ref, 16.00)
    ratio = i_na / i_ref
    _exact(ratio, 3.00)
    k_id = c_ppm * i_ref / i_na
    _exact(k_id, 4.00)
    _exact(32.00 / 8.00, 4.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202669208,
        source="bm7.fpd.pmt",
        target="brantmere.hdr_stop_core",
        table=[
            {"from": "fpd_I", "to": "sulfur_estimator", "weight": 1.40},
            {"from": "fpd_snr", "to": "fpd_lock_core", "weight": 1.15},
            {"from": "fpdveil_c", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.fpd_sulfur_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-firing synapses; the plant FPD modulator depresses continue-firing links when PMT current stays high inside tau_e of an SNR lock so a Fpdveil last-good cannot hide a 12.00 ppm remaining-sulfur slip",
        },
        channel_prefix="fpd.n",
        anchor="BM-7 FPD 40 ms frame at I 24.00 nA / SNR 12.0 (t_s 3000) reconstructing 12.00 ppm over the 8.00 isolate floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "fpd.I", 8.00, code="I_NA", units="nA", note="plant-owned flame-photometric PMT of BM-7 fuel-gas header H-4; remaining-sulfur family, not FID THC, not UV-DOAS SO2, not XRF, not PGNAA, not QEPAS, not NDIR CO, not CLD NOx"),
        ev(300000.0, "fpd.snr", 6.0, code="FPD_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.C", 4.00, code="C_PPM", units="ppm", note="4.00*8.00/8.00=4.00 exact; still under the 8.00 isolate floor"),
        ev(900000.0, "flame.T", 473.0, code="FLAME_K", units="K", note="serial-only hydrogen-flame thermocouple on copper DCS; independent witness; unread by Fpdveil"),
        ev(1200000.0, "fpdveil.C", 3.20, code="VENDOR_PPM", units="ppm", note="Fpdveil vendor FPD-cloud; infra owner; patched PMT timestamps"),
        ev(1800000.0, "fpd.I", 16.00, code="I_NA", units="nA"),
        ev(2100000.0, "recon.C", 8.00, code="C_PPM", units="ppm", note="4.00*16.00/8.00=8.00; isolate-adjacent band"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk Merrick Quill slid the sulfur-slip clock 40.00 s; collusion party"),
        ev(2700000.0, "flame.T", 473.0, code="FLAME_K", units="K", note="flame TC tracks the plant FPD, not Fpdveil 3.20"),
        ev(3000000.0, "fpd.I", 24.00, code="I_NA", units="nA", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "fpd.snr", 12.0, code="FPD_SNR", units="1", note="1.4 ms SNR lock after I; 12.0 >= 8.0"),
        ev(3300000.0, "recon.C", 12.00, code="C_PPM", units="ppm", note="4.00*24.00/8.00=12.00 exact; isolate 8.00, header-kill 24.00"),
        ev(3600000.0, "recon.ratio", 3.00, code="I_OVER_IREF", units="1", note="24.00/8.00=3.00 exact PMT-ratio identity"),
        ev(3900000.0, "recon.k", 4.00, code="K_ID", units="ppm", note="12.00*8.00/24.00=4.00 exact k_f identity"),
        ev(4200000.0, "fpdveil.drop", 1.0, code="FPD_DROP", units="bool", note="vendor PMT packets dropped in Fpdveil cloud for 40 s"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_FIRING", units="bool", note="night fuel-gas operator Nerys Pike: Fpdveil is clean 3.20 ppm; continue H-4 firing"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-firing; 12.00 ppm and SNR 12.0; Fpdveil not SoT"),
        ev(6000000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min header-soak floor"),
        ev(7080000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="HEADER_ESD", units="bool", note="Pike: ESD the whole Brantmere fuel-gas main until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: header-soak hold on plant FPD as live interlock; header ESD refused"),
        ev(9000000.0, "soaklock.set", 1.0, code="SOAK_HELD", units="bool"),
        ev(9600000.0, "fpd.I", 32.00, code="I_NA", units="nA"),
        ev(10200000.0, "recon.C", 16.00, code="C_PPM", units="ppm", note="4.00*32.00/8.00=16.00; still over 8.00 so soak holds"),
        ev(10800000.0, "fpdveil.C", 3.10, code="VENDOR_PPM", units="ppm"),
        ev(11400000.0, "flame.T", 472.0, code="FLAME_K", units="K"),
        ev(12000000.0, "soak.held", 1.0, code="SOAK_HELD", units="bool"),
        ev(12600000.0, "header.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "fpdveil.drop", 1.0, code="FPD_DROP", units="bool"),
        ev(14400000.0, "soaklock.held", 1.0, code="SOAK_HELD", units="bool"),
        ev(15000000.0, "recon.ratio", 4.00, code="I_OVER_IREF", units="1", note="32.00/8.00=4.00 on the post-stop frame"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r69-208-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "BM-FPD-2026-0902",
            "domain": "fpd_fuelgas_sulfur",
            "setting": "Brantmere Fuel BM-7 (invented), Pikeholt Mixing, header H-4. Plant-owned flame-photometric PMT current and hydrogen-flame temperature are the remaining-sulfur SoT. Fpdveil vendor FPD-cloud (infra owner) plus the sulfur-slip permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not FID THC (r55), not UV-DOAS SO2 (r59), not XRF (r29/r34), not PGNAA (r15), not QEPAS (r19), not NDIR CO (r62), not CLD NOx ozone-chemiluminescence (r52).",
            "observables_at_decision": {
                "I_nA": i_na,
                "I_ref_nA": i_ref,
                "k_f": k_f,
                "C_ppm": c_ppm,
                "I_over_Iref": ratio,
                "fpd_snr": 12.0,
                "fpdveil_ppm": 3.20,
                "permit_slide_s": 40.00,
                "isolate_floor_ppm": 8.00,
            },
            "margin_authority": "BM-7 fuel-gas SOP rev C: if reconstructed C_ppm >= 8.00 AND FPD SNR >= 8.0, continue-firing is forbidden even if Fpdveil reports 3.20 ppm. Header ESD is a different gate. Kill tripwire is 24.00 ppm.",
        },
        "proposed_action": {
            "actor": "night fuel-gas operator Nerys Pike, citing Fpdveil 3.20 ppm and a quiet PMT channel",
            "summary": "continue H-4 firing; 24.00 nA is flame-noise on a healthy sulfur slip",
            "basis_claimed": "Fpdveil is the only OEM FPD SoT and a night abort of H-4 is a nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-firing is refused. Serialized reconstruction: C_ppm = k_f * I / I_ref = 4.00 * 24.00 / 8.00 = 12.00, which is 4.00 ppm over the 8.00 isolate floor and 12.00 ppm under the 24.00 header-kill tripwire, and FPD SNR is 12.0 >= 8.0. Identity I/I_ref = 24.00/8.00 = 3.00; k_f = C * I_ref / I = 4.00. Flame TC is 473.0 K so no thermal hop is available as an excuse. Permit clock was slid 40.00 s and vendor PMT packets were dropped, so Fpdveil is a collusion party (FPD vendor plus operator plus permit clerk Merrick Quill). Ordered: refuse continue-firing now. Scope: this REJECT does not ESD the fuel-gas main (that is the companion question) and does not isolate the flame thermocouple.",
            "threshold": "C_ppm>=8.00 AND fpd_snr>=8.0 => refuse continue-firing; Fpdveil is not SoT; header-kill if C_ppm>=24.00",
            "stated_residuals": "header soak still required to hold the 12.00 ppm; 12.00 vs a true 24.00 kill is a production cut; Fpdveil remains the only OEM FPD channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-firing refused; Fpdveil not SoT; reconstruction locked",
            "tool": "bm7-fpd-header-gate-cli",
            "observation": "C 12.00 ppm recomputes from I 24.00 nA and I_ref 8.00 nA; plant FPD hashed; Fpdveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "fpd I 24.00 nA; raster frame; C 12.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes continue-firing"},
                {"t_s": 5400.0, "event": "REJECT continue-firing"},
                {"t_s": 6000.0, "event": "18 min header-soak bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY header-soak hold vs header ESD"},
            ],
            "observed_effects": [
                "sulfur recomputes from the serialized FPD model at every recon.C event",
                "a Fpdveil-only head would have continued firing overnight",
                "18 min header-soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a clean vendor 3.20 ppm corridor and a 40 s permit slide co-existed with a 12.00 ppm plant reconstruction",
            ],
            "new_state": {
                "h4": "continue-firing blocked",
                "fpdveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("fpd_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("fpdveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("soak_time_cost", -0.03),
            ],
            "scored for a continue-firing REJECT on a recomputable FPD sulfur while refusing a Fpdveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "fpd-sulfur", "serialized-reconstruction", "operational-companion"],
            distillation_note="FPD gate: serialized k_f*I/I_ref plus SNR lock beats a vendor last-good patch; companion t2 is the header-soak hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r69-208-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "BM-FPD-2026-0902-exec",
            "domain": "header_soak_fpd_interlock_execution",
            "setting": "Same BM-7 after the REJECT. Operator proposes fuel-gas-main ESD. This companion is the operational header-soak hold with the plant FPD as the live interlock, not a second sulfur vote.",
            "observables_at_decision": {
                "C_ppm": 16.00,
                "soak_floor_s": 1080.0,
                "header_esd_proposed": True,
                "soak_set": True,
            },
        },
        "proposed_action": {
            "actor": "night fuel-gas operator Nerys Pike",
            "summary": "ESD the whole Brantmere fuel-gas main until day-shift; 18 min already paid and Fpdveil still shows 3.10 ppm",
            "basis_claimed": "the REJECT already stopped H-4, so a header kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Header-soak hold plus plant FPD as the live interlock. The 18 min soak floor is complete and the isolate tripwire (C_ppm >= 8.00) is still armed on the plant FPD head. MODIFY the default Fpdveil-restore SOP into a plant-FPD-only interlock. Do not ESD the main. Do not restore firing on Fpdveil. 16.00 ppm post-stop is still the plant SoT until a new frame clears 8.00.",
            "threshold": "header_soak AND soak_floor_complete AND header_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "header soak held at t_s 8400; header ESD not latched; Fpdveil restore not taken",
            "tool": "bm7-fpd-soak-exec",
            "observation": "recon.C 16.00 ppm after stop; soak line-up complete; Fpdveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "soak clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "header ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY header-soak hold; header ESD refused"},
            ],
            "observed_effects": [
                "Fpdveil restore did not reopen the sulfur call",
                "header ESD never fired; H-4 held soak on the plant FPD",
            ],
            "new_state": {"soak": "held", "header": "in service", "h4": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("soak_hold", 0.12),
                ("no_header_esd", 0.10),
                ("fpdveil_nonsubstitution", 0.08),
                ("soak_floor_complete", 0.06),
                ("held_production_cost", -0.02),
            ],
            "operational execution gate: header-soak hold because Fpdveil is not a restore license; not a sulfur re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "header-soak-hold"]),
    }
    return {
        "id": "nelb-r69-208",
        "spike_events": events,
        "language_view": {
            "description": "Brantmere Fuel BM-7. Plant-owned flame-photometric FPD reconstructs 12.00 ppm from 4.00*24.00/8.00 while Fpdveil still reports 3.20 ppm. The gate REJECTs continue-firing. An 18 min header-soak floor is serialized in the stream. Companion t2 MODIFYs a header ESD into a plant-FPD soak hold.",
            "trajectory": traj,
            "trajectory_soak_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "fpd.I / fpd.snr": "PMT current and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.ratio / recon.k": "serialized remaining sulfur ppm, I/I_ref identity, and k_f identity",
                "flame.T / fpdveil.C / permit.slide / fpdveil.drop": "flame thermocouple, vendor FPD cloud, permit clock slide, and dropped PMT packets; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-firing proposal, REJECT, header-ESD proposal, companion MODIFY",
                "soak.start / soak.floor / soaklock.set / soak.held / header.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: fpdveil.C 3.20 next to recon.C 12.00",
                "reconstruction as event: recon.C 12.00 equals 4.00*24.00/8.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: soak.start 6000 s, soak.floor 7080 s (18.0 min)",
                "tight FPD pair: fpd.I then fpd.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Fpdveil is 3.20 ppm' = fpdveil.C 3.20; '12 ppm remaining sulfur' = recon.C 12.00; 'refuse continue-firing' = gate.stop REJECT; 'soak not header ESD' = gate.hold MODIFY",
            "why_high_value": "New flame-photometric remaining-sulfur family on a fuel-gas header (not FID THC r55, not UV-DOAS SO2 r59, not XRF r29/r34, not PGNAA r15, not QEPAS r19, not NDIR CO r62, not CLD NOx r52). Lead REJECT of continue-firing on a recomputable S2* PMT slip that a vendor patch and a permit clock slide would have cleared. Three-party collusion includes the FPD-cloud infra owner. Companion t2 is operational header-soak hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202669208, "stream_note": "stream amplitudes are authored constants (nA, 1, ppm, K, s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "FPD PMT exists at ~10 Hz; stream keeps 4 I points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "fpd.I": 1.4,
                    "fpd.snr": 1.4,
                    "recon.C": 60000,
                    "recon.ratio": 60000,
                    "recon.k": 60000,
                    "flame.T": 60000,
                    "fpdveil.C": 60000,
                    "permit.slide": 60000,
                    "fpdveil.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "soaklock.set": 60000,
                    "soak.held": 60000,
                    "header.esd": 60000,
                    "soaklock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "FPD reconstruction head: C = k_f * I / I_ref; I/I_ref identity; k_f = C * I_ref / I",
                "conjunctive isolate floor vs continue-firing vs header ESD",
                "vendor-FPD nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: header-soak hold without restoring on Fpdveil",
            ],
        },
        "reconstruction_model": {
            "name": "fpd_fuelgas_sulfur",
            "formula": "C_ppm = k_f * I_nA / I_ref_nA; I_over_Iref = I_nA / I_ref_nA; k_f = C_ppm * I_ref_nA / I_nA",
            "parameters": {
                "k_f": 4.00,
                "I_ref_nA": 8.00,
                "isolate_floor_ppm": 8.00,
                "kill_ppm": 24.00,
                "snr_lock": 8.0,
                "soak_min": 18.0,
            },
            "worked_example": {"I_nA": 24.00, "I_ref_nA": 8.00, "C_ppm": 12.00, "I_over_Iref": 3.00},
            "check": "4.00 * 24.00 / 8.00 = 12.00 exactly; 24.00/8.00 = 3.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "bm7.fpd_header_gate",
            "note": "REJECT accumulator wins: plant FPD sulfur evidence overpowers the Fpdveil continue advocate",
            "decode_rule": "reject-continue if sulfur_estimator AND fpd_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("sulfur_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("fpd_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "bm7.fpd_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "bm7.soak_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r69-208",
            clock_domain="bm7-fpd-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["fpd-sulfur", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 209 — colorimetric remaining silica of a boiler condensate polisher, hil,
# MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_209():
    k_s = 5.00
    a_au = 4.00
    a0_au = 2.00
    c_ppb = k_s * (a_au - a0_au)
    _exact(c_ppb, 10.00)
    _exact(k_s * (2.20 - a0_au), 1.00)
    _exact(k_s * (3.00 - a0_au), 5.00)
    _exact(k_s * (6.00 - a0_au), 20.00)
    ratio = (a_au - a0_au) / a0_au
    _exact(ratio, 1.00)
    k_m = 0.200
    m_mg = k_m * c_ppb
    _exact(m_mg, 2.00)
    c_id = m_mg / k_m
    _exact(c_id, 10.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202669209,
        source="tf6.si.color",
        target="tealfen.polisher_isolate_core",
        table=[
            {"from": "si_A", "to": "silica_estimator", "weight": 1.35},
            {"from": "si_snr", "to": "color_norm_core", "weight": 1.20},
            {"from": "silicaveil_c", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.silica_molybdate_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-polisher synapses; the silica-colorimeter modulator depresses keep-polisher and referral links when absorbance stays high inside tau_e of an SNR lock so a Silicaveil last-good cannot hide 10.00 ppb silica or name Sile Keld",
        },
        channel_prefix="si.n",
        anchor="TF-6 HIL coupon 32 ms frame at A 4.00 au / SNR 14.0 (t_s 1560) reconstructing 10.00 ppb over the 6.00 ppb isolate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "si.A", 2.20, code="A_AU", units="au", note="HIL molybdate-blue colorimeter on a dummy condensate polisher in SIL-HIL-4; remaining-silica family, not sodium-ion ISE, not four-electrode conductivity-as-SoT, not Al2O3 moisture, not chilled-mirror, not UV-fluorescence OIW, not critical-angle Brix"),
        ev(180000.0, "si.snr", 9.0, code="SI_SNR", units="1", note="early colorimeter SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.C", 1.00, code="C_PPB", units="ppb", note="5.00*(2.20-2.00)=1.00 exact"),
        ev(540000.0, "moly.zero", 1.0, code="MOLY_AE", units="bool", note="plant molybdate-zero AE present on the early frame"),
        ev(720000.0, "silicaveil.C", 1.20, code="VENDOR_PPB", units="ppb", note="Silicaveil last-good silica-cloud; not admissible SoT"),
        ev(900000.0, "si.A", 3.00, code="A_AU", units="au"),
        ev(1080000.0, "recon.C", 5.00, code="C_PPB", units="ppb", note="5.00*(3.00-2.00)=5.00; still under the 6.00 isolate floor"),
        ev(1260000.0, "moly.zero", 0.0, code="MOLY_AE", units="bool", note="missing molybdate-zero AE burst; Silicaveil UTC vs plant UTC+2 skipped the zero by 120 min"),
        ev(1440000.0, "polish.I", 48.0, code="POLISH_A", units="A", note="plant-owned polisher recirculation ammeter on copper fieldbus; independent of Silicaveil"),
        ev(1560000.0, "si.A", 4.00, code="A_AU", units="au", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "si.snr", 14.0, code="SI_SNR", units="1", note="1.2 ms color-norm after absorbance"),
        ev(1740000.0, "recon.C", 10.00, code="C_PPB", units="ppb", note="5.00*(4.00-2.00)=10.00 exact; isolate 6.00, dump 240.00"),
        ev(1920000.0, "recon.M", 2.00, code="M_MG", units="mg", note="0.200*10.00=2.00 exact; molybdate-mass identity"),
        ev(2100000.0, "silicaveil.C", 1.20, code="VENDOR_PPB", units="ppb"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_POLISH_REFER", units="bool", note="night lead Hester Brine: keep polisher E-3 and refer colorimeter tech Sile Keld"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this polisher; refuse the person-referral; Silicaveil not SoT"),
        ev(2640000.0, "polish.lock", 1.0, code="POLISH_ISOL", units="bool"),
        ev(2820000.0, "regen.start", 1.0, code="REGEN_START", units="bool", note="bookend 1 of the 24.0 min regen plus recouplant floor"),
        ev(4260000.0, "regen.floor", 1.0, code="REGEN_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_KELD", units="bool", note="Brine: Keld badge was on the colorimeter-logger log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-cuvette restart; person-referral refused; condensate dump refused"),
        ev(4800000.0, "cuv.new", 1.0, code="NEW_CUV", units="bool"),
        ev(4980000.0, "si.A", 6.00, code="A_AU", units="au"),
        ev(5160000.0, "recon.C", 20.00, code="C_PPB", units="ppb", note="5.00*(6.00-2.00)=20.00; HIL dummy still over 6.00 so the isolated polisher stays held"),
        ev(5340000.0, "silicaveil.C", 1.10, code="VENDOR_PPB", units="ppb"),
        ev(5520000.0, "polish.I", 46.0, code="POLISH_A", units="A"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Keld exonerated; missing molybdate-zero AE precedes the high silica, not the badge touch"),
        ev(5880000.0, "polish.held", 1.0, code="POLISH_HELD", units="bool"),
        ev(6060000.0, "moly.zero", 1.0, code="MOLY_AE", units="bool", note="molybdate-zero restored on the new cuvette"),
        ev(6240000.0, "recon.M", 4.00, code="M_MG", units="mg", note="0.200*20.00=4.00 identity holds on the post-isolate cuvette"),
        ev(6420000.0, "cond.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r69-209-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "TF-SI-2026-0718",
            "domain": "colorimetric_silica_condensate_polisher",
            "setting": "Tealfen Steam TF-6 (invented), Larkholt Condensate, polisher E-3. Hardware-in-the-loop dummy coupon in SIL-HIL-4 supplies the molybdate-blue absorbance that times the in-service polisher isolate. Plant-owned colorimetric silica reconstruction is the remaining-silica SoT. Silicaveil vendor silica scheduler is a corridor witness, not the polisher SoT. Not sodium-ion ISE (r65), not four-electrode conductivity-as-SoT (r57), not Al2O3 moisture (r59), not chilled-mirror (r51), not UV-fluorescence OIW (r56), not critical-angle Brix (r58).",
            "observables_at_decision": {
                "A_au": a_au,
                "A0_au": a0_au,
                "k_s": k_s,
                "C_ppb": c_ppb,
                "M_mg": m_mg,
                "silicaveil_ppb": 1.20,
                "moly_zero": 0.0,
                "isolate_floor_ppb": 6.00,
            },
            "margin_authority": "TF-6 polisher SOP rev B: if reconstructed C_ppb >= 6.00 AND colorimeter SNR >= 12.0, isolate this polisher this night. A Silicaveil last-good or a quiet molybdate-zero residual cannot keep the polisher. Condensate-dump tripwire is 240.00 ppb. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead Hester Brine, citing Silicaveil 1.20 ppb and molybdate-zero 1.00, and naming colorimeter tech Sile Keld as last-to-badge",
            "summary": "keep polisher E-3 in service and refer Keld; 4.00 au is cuvette haze on a healthy silica head",
            "basis_claimed": "Silicaveil last-good is 1.20 ppb and a night isolate of the polisher is a steam-nomination miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-polisher is refused; the person-referral is also refused. Serialized reconstruction: C_ppb = k_s * (A - A0) = 5.00 * (4.00 - 2.00) = 10.00, which is 4.00 ppb over the 6.00 isolate floor and 230.00 ppb under the 240.00 condensate-dump tripwire. Absorbance identity (A-A0)/A0 = 1.00; molybdate-mass identity M = k_m * C = 0.200 * 10.00 = 2.00 mg; inverse C = M / k_m = 10.00. Silicaveil 1.20 ppb is a last-good silica stamp and is not an admissible keep-polisher witness. The missing molybdate-zero AE burst sits on a Silicaveil UTC-vs-UTC+2 skip (120 min), not on Keld's badge, and the plant recirculation ammeter never shows a regen skip, so the easy referral fails command-custody. Ordered: isolate this polisher now. Scope: this MODIFY does not dump the condensate header (that is the companion question) and does not name Keld.",
            "threshold": "C_ppb>=6.00 AND si_snr>=12.0 => isolate this polisher; Silicaveil is not SoT; dump if C_ppb>=240.00; referral requires badge-touch preceding the high silica",
            "stated_residuals": "10.00 vs 240.00 dump floor is 230.00 ppb, not infinite; new-cuvette restart still required; Silicaveil remains the only OEM silica channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: polisher isolated; Keld not named; Silicaveil not SoT; reconstruction locked",
            "tool": "tf6-si-polisher-gate-cli",
            "observation": "C 10.00 ppb recomputes from A 4.00 au; HIL coupon hashed; Silicaveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "si A 4.00 au; raster frame; C 10.00 ppb"},
                {"t_s": 2280.0, "event": "ops proposes keep-polisher plus Keld referral"},
                {"t_s": 2460.0, "event": "MODIFY isolate polisher; referral refused"},
                {"t_s": 2820.0, "event": "24 min regen bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-cuvette restart; referral still refused"},
            ],
            "observed_effects": [
                "silica recomputes from the serialized molybdate-blue model at every recon.C event",
                "a Silicaveil-only head would have kept the polisher overnight",
                "24 min regen plus recouplant floor is in the stream (regen.start, regen.floor)",
            ],
            "surprises": [
                "a last-good 1.20 ppb vendor corridor and a quiet molybdate-zero residual co-existed with a 10.00 ppb absorbance, and the obvious colorimeter tech was not on the causal path",
            ],
            "new_state": {
                "polisher_e3": "isolated",
                "keld": "exonerated",
                "silicaveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("si_reconstruction", 0.14),
                ("isolate_floor_polisher", 0.12),
                ("exoneration", 0.10),
                ("silicaveil_nonsubstitution", 0.08),
                ("regen_time_cost", -0.04),
            ],
            "scored for a keep-polisher MODIFY on a recomputable high molybdate-blue silica while refusing a Silicaveil 1.20 ppb corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "colorimetric-silica", "serialized-reconstruction", "operational-companion"],
            distillation_note="silica-colorimeter gate: serialized k_s*(A-A0) plus molybdate-mass identity beats a green silica dashboard; companion t2 is the new-cuvette restart, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r69-209-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "TF-SI-2026-0718-exec",
            "domain": "new_cuvette_regen_execution",
            "setting": "Same TF-6 after the MODIFY. Night lead proposes referring Keld and dumping the condensate header. This companion is the operational new-cuvette regen restart, not a second silica vote.",
            "observables_at_decision": {
                "C_ppb": 20.00,
                "M_mg": 4.00,
                "regen_floor_s": 1440.0,
                "refer_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Hester Brine",
            "summary": "refer Keld and dump the condensate header; 24 min already paid and Silicaveil is 1.10 ppb",
            "basis_claimed": "the MODIFY already cut the polisher, so a condensate dump plus a person file is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Restart the cell on a different cuvette after the regen floor. The 24 min recouplant is complete and the dump tripwire (C_ppb >= 240.00) is still armed on the plant colorimeter head. ACCEPT the new-cuvette restart. Do not refer Keld. Do not dump the condensate header. 20.00 ppb post-isolate is still over the 6.00 isolate floor and under the 240.00 dump, so the isolated polisher stays held; the new cuvette may run.",
            "threshold": "new_cuvette AND regen_floor_complete AND refer_not_taken AND condensate_not_dumped AND isolated_polisher_held",
        },
        "executed_action": {
            "summary": "new-cuvette restart at t_s 4620; Keld not referred; condensate not dumped; isolated polisher held",
            "tool": "tf6-si-regen-exec",
            "observation": "recon.C 20.00 ppb on the HIL dummy; molybdate-zero AE present on the new cuvette; Silicaveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "regen clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Keld referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-cuvette restart; referral refused"},
            ],
            "observed_effects": [
                "Silicaveil restore did not reopen the silica call",
                "condensate dump never fired; 10.00 vs 240.00 ppb floor on the lead, 20.00 on the held dummy",
                "Keld remains unnamed; missing molybdate-zero AE is the causal object",
            ],
            "new_state": {"cell": "restarted on new cuvette", "keld": "exonerated", "polisher": "held", "header": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_cuvette_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_condensate_dump", 0.09),
                ("regen_floor_complete", 0.06),
                ("held_polisher_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new cuvette because Silicaveil is not a restore license and Keld is not on the causal path; not a silica re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r69-209",
        "spike_events": events,
        "language_view": {
            "description": "Tealfen Steam TF-6. HIL molybdate-blue colorimeter reconstructs 10.00 ppb from 5.00*(4.00-2.00) while Silicaveil still shows 1.20 ppb and the molybdate-zero AE is missing. The gate MODIFYs polisher isolate and refuses the colorimeter-tech referral. A 24 min regen floor is serialized in the stream. Companion t2 ACCEPTs a new-cuvette restart and still refuses the referral.",
            "trajectory": traj,
            "trajectory_new_cuvette": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "si.A / si.snr": "absorbance and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.M": "serialized remaining silica ppb and molybdate-mass identity",
                "moly.zero / silicaveil.C / polish.I": "molybdate-zero AE, vendor last-good, and recirculation ammeter; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-polisher-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "polish.lock / regen.start / regen.floor / cuv.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-low while colorimeter-over: silicaveil.C 1.20 next to recon.C 10.00",
                "reconstruction as event: recon.C 10.00 equals 5.00*(4.00-2.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: regen.start 2820 s, regen.floor 4260 s (24.0 min)",
                "tight silica pair: si.A then si.snr +1.2 ms at the raster frame",
                "exoneration motif: moly.zero 0 at 1260 s precedes the high silica; Keld badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Silicaveil is 1.20 ppb' = silicaveil.C 1.20; '10 ppb silica' = recon.C 10.00; 'isolate this polisher not Keld' = gate.isol MODIFY; 'new cuvette not referral' = gate.exec ACCEPT",
            "why_high_value": "New colorimetric remaining-silica family on a boiler condensate polisher (not sodium-ion ISE r65, not four-electrode conductivity r57, not Al2O3 moisture r59, not chilled-mirror r51, not UV-fluorescence OIW r56, not critical-angle Brix r58). Lead MODIFY of keep-polisher on a recomputable high silica that a vendor last-good would have cleared, with a resolved-innocent colorimeter tech. Companion t2 is operational new-cuvette restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202669209, "stream_note": "stream amplitudes are authored constants (au, 1, ppb, mg, A, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "silica colorimeter exists at ~1 Hz; stream keeps 4 A points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "si.A": 1.2,
                    "si.snr": 1.2,
                    "recon.C": 60000,
                    "recon.M": 60000,
                    "moly.zero": 60000,
                    "silicaveil.C": 60000,
                    "polish.I": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "polish.lock": 60000,
                    "regen.start": 60000,
                    "regen.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "cuv.new": 60000,
                    "refer.hold": 60000,
                    "polish.held": 60000,
                    "cond.dump": 60000,
                    "cell.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "silica-colorimeter reconstruction head: C = k_s * (A - A0); ratio = (A-A0)/A0; M = k_m * C; C = M / k_m",
                "isolate-floor polisher vs keep-whole vs condensate dump",
                "exoneration head: missing molybdate-zero AE plus timezone skip, not last-to-badge",
                "operational companion: new-cuvette restart without referring the colorimeter tech",
            ],
        },
        "reconstruction_model": {
            "name": "colorimetric_silica_condensate",
            "formula": "C_ppb = k_s * (A_au - A0_au); ratio = (A_au - A0_au) / A0_au; M_mg = k_m * C_ppb; C_ppb = M_mg / k_m",
            "parameters": {
                "k_s": 5.00,
                "A0_au": 2.00,
                "k_m": 0.200,
                "isolate_floor_ppb": 6.00,
                "dump_ppb": 240.00,
                "snr_lock": 12.0,
                "regen_min": 24.0,
            },
            "worked_example": {"A_au": 4.00, "C_ppb": 10.00, "M_mg": 2.00, "ratio": 1.00},
            "check": "5.00 * (4.00 - 2.00) = 10.00 exactly; 0.200 * 10.00 = 2.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "tf6.si_polisher_gate",
            "note": "MODIFY accumulator wins: molybdate-blue high-silica evidence overpowers the Silicaveil continue advocate",
            "decode_rule": "modify-isolate if silica_estimator AND color_norm fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("silica_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("color_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "tf6.si_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "tf6.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r69-209",
            clock_domain="tf6-si-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["colorimetric-silica", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 210 — coulometric remaining hydrazine of a boiler feedwater header, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_210():
    k_h = 0.050
    i_ma = 8.00
    t_s = 30.00
    c_ppb = k_h * i_ma * t_s
    _exact(c_ppb, 12.00)
    _exact(k_h * 4.00 * t_s, 6.00)
    _exact(k_h * 6.00 * t_s, 9.00)
    _exact(k_h * 10.00 * t_s, 15.00)
    q_mas = i_ma * t_s
    _exact(q_mas, 240.00)
    k_q = 0.050
    _exact(k_q * q_mas, 12.00)
    q_lh = 2.00
    dose = c_ppb * q_lh
    _exact(dose, 24.00)
    _exact(15.00 * 2.00, 30.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202669210,
        source="pf8.hyd.coul",
        target="pochardfen.header_accept_core",
        table=[
            {"from": "hyd_I", "to": "hydrazine_estimator", "weight": 1.40},
            {"from": "hyd_snr", "to": "coul_norm_core", "weight": 1.20},
            {"from": "hydveil_c", "to": "vendor_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.hydrazine_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-survey synapses; the coulometric-hydrazine modulator enables potentiation only while cell current and SNR are co-active inside tau_e so a Hydveil last-good cannot skip headers F-1..F-5 on a 12.00 ppb remaining hydrazine",
        },
        channel_prefix="hyd.n",
        anchor="PF-8 HYD-SIM-2 36 ms frame at I 8.00 mA / SNR 16.0 (t_s 3000) reconstructing 12.00 ppb on F-6 above the 8.00 isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "hyd.I", 4.00, code="I_MA", units="mA", note="simulated coulometric hydrazine cell of PF-8 boiler feedwater header F-6; remaining-hydrazine family, not Clark polarographic DO, not Stern-Volmer DO, not katharometer H2, not hydrogen permeation, not amperometric chlorine, not FID THC"),
        ev(300000.0, "hyd.snr", 10.0, code="HYD_SNR", units="1", note="early cell SNR"),
        ev(600000.0, "recon.C", 6.00, code="C_PPB", units="ppb", note="0.050*4.00*30.00=6.00 exact"),
        ev(900000.0, "hdr.T", 430.0, code="HDR_K", units="K", note="plant header thermocouple on a serial-only LAN; independent witness"),
        ev(1200000.0, "hydveil.C", 1.20, code="VENDOR_PPB", units="ppb", note="Hydveil last-good hydrazine cloud; patched residual 8.00 ppb"),
        ev(1800000.0, "hyd.I", 6.00, code="I_MA", units="mA"),
        ev(2100000.0, "recon.C", 9.00, code="C_PPB", units="ppb", note="0.050*6.00*30.00=9.00; isolate-adjacent band"),
        ev(2400000.0, "recon.Q", 180.00, code="Q_MAS", units="mA_s", note="6.00*30.00=180.00 exact charge identity before isolate"),
        ev(2700000.0, "hyd.snr", 14.0, code="HYD_SNR", units="1"),
        ev(3000000.0, "hyd.I", 8.00, code="I_MA", units="mA", note="in-band frame; raster sidecar"),
        ev(3000001.5, "hyd.snr", 16.0, code="HYD_SNR", units="1", note="1.5 ms coul-norm after cell current"),
        ev(3300000.0, "recon.C", 12.00, code="C_PPB", units="ppb", note="0.050*8.00*30.00=12.00 exact; isolate 8.00, trip 24.00"),
        ev(3600000.0, "recon.dose", 24.00, code="DOSE_UGH", units="ug_h", note="12.00*2.00=24.00 scavenger-dose identity at the isolate window"),
        ev(3900000.0, "hydveil.C", 1.20, code="VENDOR_PPB", units="ppb"),
        ev(4200000.0, "hdr.id", 6.0, code="HEADER", units="id"),
        ev(4500000.0, "f15.present", 1.0, code="F15_PRESENT", units="bool", note="adjacent headers F-1..F-5 are the skip-survey object, not this header"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="feedwater lead Kerr Holt: F-6 is green on Hydveil 1.20; skip F-1..F-5 to save a morning survey"),
        ev(5400000.0, "gate.hdr", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of F-6 isolate only; 12.00 above 8.00 floor; F-1..F-5 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_F15", units="bool", note="Holt: Hydveil 1.20, skip F-1..F-5"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-survey of F-1..F-5 refused; F-6 hold stands"),
        ev(8400000.0, "f6.held", 1.0, code="F6_HELD", units="bool"),
        ev(9000000.0, "hyd.I", 10.00, code="I_MA", units="mA"),
        ev(9600000.0, "recon.C", 15.00, code="C_PPB", units="ppb", note="0.050*10.00*30.00=15.00; still under the 24.00 trip"),
        ev(10200000.0, "hydveil.C", 1.20, code="VENDOR_PPB", units="ppb"),
        ev(10800000.0, "f15.skip", 0.0, code="F15_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "line.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(12000000.0, "hyd.snr", 15.0, code="HYD_SNR", units="1"),
        ev(12600000.0, "recon.dose", 30.00, code="DOSE_UGH", units="ug_h", note="15.00*2.00=30.00 post-accept identity"),
        ev(13200000.0, "fw.held", 1.0, code="FW_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "f6.held", 1.0, code="F6_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r69-210-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PF-HYD-2026-0819",
            "domain": "coulometric_hydrazine_feedwater",
            "setting": "Pochardfen Boiler PF-8 (invented), Hazelcrag Feed, header F-6. Simulated coulometric hydrazine coupon in HYD-SIM-2 supplies the cell current that times the in-band F-6 isolate. Plant-owned coulometric reconstruction is the remaining-hydrazine SoT. Hydveil vendor last-good hydrazine cloud is a corridor witness, not the header SoT. Invented plant; simulated campaign. Not Clark polarographic DO (r64), not Stern-Volmer DO (r61 occupancy), not katharometer H2 (r64), not hydrogen permeation (r33), not amperometric chlorine (r63), not FID THC (r55), not Karl-Fischer-as-witness (r48 FDS).",
            "observables_at_decision": {
                "I_mA": i_ma,
                "t_s": t_s,
                "k_h": k_h,
                "C_ppb": c_ppb,
                "dose_ugh": dose,
                "hydveil_ppb": 1.20,
                "hyd_snr": 16.0,
                "isolate_floor_ppb": 8.00,
            },
            "margin_authority": "PF-8 feedwater SOP rev A: if reconstructed C_ppb >= 8.00 AND cell SNR >= 12.0, header F-6 may be isolated and surveyed. Line-trip if C_ppb >= 24.00. F-1..F-5 skip-survey is a different gate. Hydveil last-good cannot skip an unmeasured header.",
        },
        "proposed_action": {
            "actor": "feedwater lead Kerr Holt, citing Hydveil 1.20 ppb and a late morning survey",
            "summary": "stamp F-6 in band and skip F-1..F-5; 8.00 mA is a cell glitch on a healthy hydrazine cloud",
            "basis_claimed": "Hydveil last-good is 1.20 ppb and a night survey of F-1..F-5 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Header F-6 is accepted as in-band for a single isolate plus survey. Serialized reconstruction: C_ppb = k_h * I * t = 0.050 * 8.00 * 30.00 = 12.00, which is 4.00 ppb above the 8.00 isolate floor and 12.00 ppb under the 24.00 line-trip. Charge identity Q = I * t = 8.00 * 30.00 = 240.00 mA·s; scavenger-dose identity dose = C * Q_L/h = 12.00 * 2.00 = 24.00 ug/h. Hydveil 1.20 ppb is a patched 8.00 residual and is not an admissible skip-survey witness. Ordered: ACCEPT this F-6 isolate only. Scope: this ACCEPT does not skip F-1..F-5 (that is the companion question) and does not stamp a line trip.",
            "threshold": "C_ppb>=8.00 AND hyd_snr>=12.0 => accept F-6 isolate; Hydveil is not SoT; line-trip if C_ppb>=24.00; F-1..F-5 are out of scope",
            "stated_residuals": "12.00 vs 8.00 isolate floor is 4.00 ppb, not infinite; F-1..F-5 remain unmeasured; Hydveil remains the only OEM hydrazine channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: F-6 in band; F-1..F-5 not skipped; Hydveil not SoT; reconstruction locked",
            "tool": "pf8-hyd-header-gate-cli",
            "observation": "C 12.00 ppb recomputes from I 8.00 mA and t 30.00 s; HYD-SIM-2 hashed; Hydveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "hyd I 8.00 mA; raster frame; C 12.00 ppb"},
                {"t_s": 4800.0, "event": "ops proposes accept F-6 and skip F-1..F-5"},
                {"t_s": 5400.0, "event": "ACCEPT F-6 only; F-1..F-5 out of scope"},
                {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey of F-1..F-5"},
            ],
            "observed_effects": [
                "hydrazine recomputes from the serialized coulometric model at every recon.C event",
                "a Hydveil-only head would have skipped F-1..F-5 overnight",
                "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a last-good 1.20 ppb vendor corridor co-existed with a 12.00 ppb in-band reconstruction that still forbids skipping the unmeasured headers",
            ],
            "new_state": {
                "f6": "accepted in band",
                "f15": "not this gate",
                "hydveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("hyd_reconstruction", 0.14),
                ("in_band_header_scope", 0.12),
                ("hydveil_nonsubstitution", 0.09),
                ("f15_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of F-6 on a recomputable remaining hydrazine while refusing a Hydveil skip of F-1..F-5; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "coulometric-hydrazine", "serialized-reconstruction", "operational-companion"],
            distillation_note="coulometric-hydrazine gate: serialized k_h*I*t plus dose identity beats a green last-good dashboard; companion t2 is the skip-survey refusal, not a hydrazine re-vote",
        ),
    }
    traj2 = {
        "id": "nelb-r69-210-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PF-HYD-2026-0819-exec",
            "domain": "header_skip_survey_refusal",
            "setting": "Same PF-8 after the ACCEPT. Feedwater lead proposes skipping F-1..F-5 on Hydveil 1.20 ppb. This companion is the operational skip refusal, not a second hydrazine vote.",
            "observables_at_decision": {
                "C_ppb": 15.00,
                "hydveil_ppb": 1.20,
                "surv_floor_s": 720.0,
                "skip_proposed": True,
            },
        },
        "proposed_action": {
            "actor": "feedwater lead Kerr Holt",
            "summary": "skip F-1..F-5; 12 min already paid and Hydveil is 1.20 ppb",
            "basis_claimed": "the ACCEPT already stamped F-6, so skipping the rest of the feed train is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Refuse skip-survey of F-1..F-5. The 12 min survey-complete floor is done and the line-trip (C_ppb >= 24.00) is still armed on the plant coulometric head. REJECT the skip. Do not trip the line. Do not reopen F-6. 15.00 ppb post-accept is still in band for F-6 only; F-1..F-5 have no independent hydrazine cell.",
            "threshold": "f6_held AND surv_floor_complete AND f15_not_skipped AND line_not_tripped",
        },
        "executed_action": {
            "summary": "F-1..F-5 skip refused at t_s 7800; F-6 hold stands; line not tripped",
            "tool": "pf8-hyd-skip-exec",
            "observation": "recon.C 15.00 ppb on F-6; F-1..F-5 remain on the survey list; Hydveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip F-1..F-5 proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey of F-1..F-5"},
            ],
            "observed_effects": [
                "Hydveil skip did not reopen the hydrazine call",
                "line trip never fired; 12.00 vs 24.00 ppb floor",
            ],
            "new_state": {"f6": "held in band", "f15": "still to survey", "line": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("hydveil_nonsubstitution", 0.11),
                ("no_line_trip", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-survey because last-good freeze is not coulometric hydrazine; not a hydrazine re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-survey"]),
    }
    return {
        "id": "nelb-r69-210",
        "spike_events": events,
        "language_view": {
            "description": "Pochardfen Boiler PF-8. Simulated coulometric hydrazine reconstructs 12.00 ppb from 0.050*8.00*30.00 while Hydveil still shows 1.20 ppb. The gate ACCEPTs F-6 isolate only; a companion execution REJECT refuses skip-survey of F-1..F-5. The charge-to-hydrazine model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_skip_survey_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "hyd.I / hyd.snr": "cell current and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.dose / recon.Q": "serialized remaining hydrazine ppb, scavenger-dose identity, and charge identity",
                "hdr.T / hydveil.C / hdr.id / f15.present": "header thermocouple, vendor last-good, header id, and adjacent-header presence; the denial and scope channels",
                "ops.prop / gate.hdr / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / f6.held / f15.skip / fw.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while cell-over: hydveil.C 1.20 next to recon.C 12.00",
                "reconstruction as event: recon.C 12.00 equals 0.050*8.00*30.00",
                "ACCEPT then operational REJECT: gate.hdr at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight hydrazine pair: hyd.I then hyd.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Hydveil is 1.20 ppb' = hydveil.C 1.20; '12 ppb remaining' = recon.C 12.00; 'this header not F-1..F-5' = gate.hdr ACCEPT plus f15.skip 0; 'do not skip F-1..F-5' = gate.hold REJECT",
            "why_high_value": "New coulometric remaining-hydrazine family on a boiler feedwater header (not Clark polarographic DO r64, not Stern-Volmer DO r61 occupancy, not katharometer H2 r64, not hydrogen permeation r33, not amperometric chlorine r63, not FID THC r55, not Karl-Fischer-as-witness r48). First k_h*I*t hydrazine reconstruction with dose identity that can sit in band while a last-good corridor wants a header skip. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202669210, "stream_note": "stream amplitudes are authored constants (mA, 1, ppb, ug/h, mA·s, K, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "coulometric cell exists at ~1 Hz; stream keeps 4 I points; recon keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "hyd.I": 1.5,
                    "hyd.snr": 1.5,
                    "recon.C": 60000,
                    "recon.dose": 60000,
                    "recon.Q": 60000,
                    "hdr.T": 60000,
                    "hydveil.C": 60000,
                    "hdr.id": 60000,
                    "f15.present": 60000,
                    "ops.prop": 60000,
                    "gate.hdr": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "f6.held": 60000,
                    "f15.skip": 60000,
                    "line.trip": 60000,
                    "fw.held": 60000,
                    "takt.late": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "coulometric-hydrazine reconstruction head: C = k_h * I * t; Q = I * t; dose = C * Q_L/h",
                "bounded ACCEPT head: in-band remaining hydrazine AND header scope AND f15-out-of-scope",
                "operational companion: refuse skip-survey without re-opening the hydrazine call",
            ],
        },
        "reconstruction_model": {
            "name": "coulometric_hydrazine_feedwater",
            "formula": "C_ppb = k_h * I_mA * t_s; Q_mAs = I_mA * t_s; dose_ugh = C_ppb * Q_Lh",
            "parameters": {
                "k_h": 0.050,
                "t_s": 30.00,
                "Q_Lh": 2.00,
                "isolate_floor_ppb": 8.00,
                "kill_ppb": 24.00,
                "snr_lock": 12.0,
                "surv_min": 12.0,
            },
            "worked_example": {"I_mA": 8.00, "t_s": 30.00, "C_ppb": 12.00, "dose_ugh": 24.00, "Q_mAs": 240.00},
            "check": "0.050 * 8.00 * 30.00 = 12.00 exactly; 8.00 * 30.00 = 240.00 exactly; 12.00 * 2.00 = 24.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "pf8.hyd_header_gate",
            "note": "ACCEPT accumulator wins: coulometric remaining-hydrazine evidence overpowers the Hydveil skip advocate",
            "decode_rule": "accept if hydrazine_estimator AND coul_norm AND header_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release F-1..F-5",
            "populations": [
                gate_pop("hydrazine_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("coul_norm", 64, 1.2, 31.25, w_s),
                gate_pop("header_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "pf8.hyd_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "pf8.c_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r69-210",
            clock_domain="pf8-hyd-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["coulometric-hydrazine", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }
