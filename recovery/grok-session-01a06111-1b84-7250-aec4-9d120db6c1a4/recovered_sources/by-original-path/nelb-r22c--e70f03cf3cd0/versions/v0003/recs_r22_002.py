def rec_002():
    k_i = 2.00
    t_d = 16.00
    t0 = 4.00
    c_ppm = k_i * (t_d - t0)
    _exact(c_ppm, 24.00)
    dt = t_d - t0
    _exact(dt, 12.00)
    _exact(k_i * (8.00 - t0), 8.00)
    _exact(k_i * (12.00 - t0), 16.00)
    _exact(k_i * (14.00 - t0), 20.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=62.5,
        window_ms=32.0,
        seed=2026092202,
        source="wm6.ims.drift",
        target="whinmere.booth_isolate_core",
        table=[
            {"from": "ims_td", "to": "conc_estimator", "weight": 1.35},
            {"from": "ims_snr", "to": "shutter_norm_core", "weight": 1.20},
            {"from": "imsveil_C", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.ims_referral_pressure",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-spin synapses; the IMS modulator depresses keep-spin and referral links when drift time stays high inside tau_e of an SNR lock so an Imsveil last-good cannot hide a 24.00 ppm DMF load or name Olen Marsh",
        },
        channel_prefix="ims.n",
        anchor="WM-6 HIL coupon 32 ms frame at t_d 16.00 ms / t0 4.00 ms / SNR 14.0 (t_s 1560) reconstructing 24.00 ppm above the 16.00 isolate floor",
        kernel_ms=[1.2],
        tau_m=12.0,
    )
    w_s = 0.032
    events = [
        ev(0.0, "ims.td", 8.00, code="TD_MS", units="ms", note="HIL ion-mobility of carbon-fiber precursor DMF on a dummy cell in IMS-HIL-4; remaining-DMF family, not PTR-MS MDI, not PID VOC, not pellistor LEL, not TDLAS NH3, not SPR cyanide"),
        ev(180000.0, "ims.snr", 9.0, code="IMS_SNR", units="1", note="early shutter SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.C", 8.00, code="C_PPM", units="ppm", note="2.00*(8.00-4.00)=8.00 exact"),
        ev(450000.0, "ims.td", 8.00, code="TD_MS", units="ms"),
        ev(450001.2, "ims.snr", 10.0, code="IMS_SNR", units="1", note="1.2 ms SNR after td 8.00; isolate still needs SNR>=12"),
        ev(468000.0, "recon.C", 8.00, code="C_PPM", units="ppm"),
        ev(540000.0, "sh.zero", 0.00, code="ZERO_MS", units="ms", note="plant shutter-zero remaining; no IMS-scale hop in this window"),
        ev(720000.0, "imsveil.C", 3.20, code="VENDOR_PPM", units="ppm", note="Imsveil last-good spin-cloud; not admissible SoT"),
        ev(900000.0, "ims.td", 12.00, code="TD_MS", units="ms"),
        ev(1080000.0, "recon.C", 16.00, code="C_PPM", units="ppm", note="2.00*(12.00-4.00)=16.00; at the 16.00 isolate floor"),
        ev(1260000.0, "sh.delay", 0.0, code="ZERO_AE", units="bool", note="missing shutter-zero AE burst; Imsveil UTC vs plant UTC+2 skipped the zero by 120 min"),
        ev(1440000.0, "sh.zero", 0.00, code="ZERO_MS", units="ms"),
        ev(1560000.0, "ims.td", 16.00, code="TD_MS", units="ms", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "ims.t0", 4.00, code="T0_MS", units="ms", note="1.2 ms t0 after td; dt 12.00"),
        ev(1560002.5, "ims.snr", 14.0, code="IMS_SNR", units="1", note="1.3 ms after t0; isolate-frame SNR 14.0 >= 12.0"),
        ev(1740000.0, "recon.C", 24.00, code="C_PPM", units="ppm", note="2.00*(16.00-4.00)=24.00 exact; isolate 16.00, trip 80.00"),
        ev(1920000.0, "recon.dt", 12.00, code="DT_MS", units="ms", note="16.00-4.00=12.00 exact; drift-time identity"),
        ev(2100000.0, "imsveil.C", 3.20, code="VENDOR_PPM", units="ppm"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_SPIN_REFER", units="bool", note="night lead: keep booth B-2 spinning and refer IMS tech Olen Marsh"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this booth; refuse the person-referral; Imsveil not SoT"),
        ev(2640000.0, "booth.lock", 1.0, code="BOOTH_ISOL", units="bool"),
        ev(2820000.0, "purge.start", 1.0, code="PURGE_START", units="bool", note="bookend 1 of the 24.0 min purge plus shutter-settle floor"),
        ev(3000000.0, "ims.snr", 14.2, code="IMS_SNR", units="1"),
        ev(3300000.0, "recon.dt", 12.00, code="DT_MS", units="ms", note="16.00-4.00=12.00 identity held through purge start"),
        ev(3600000.0, "booth.T", 28.0, code="BOOTH_C", units="C", note="plant booth thermocouple on copper DCS; independent witness; unread by Imsveil"),
        ev(3900000.0, "ims.td", 14.00, code="TD_MS", units="ms"),
        ev(4080000.0, "recon.C", 20.00, code="C_PPM", units="ppm", note="2.00*(14.00-4.00)=20.00 exact; still over the 16.00 isolate floor"),
        ev(4260000.0, "purge.floor", 1.0, code="PURGE_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_MARSH", units="bool", note="lead: Marsh badge was on the IMS log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-source restart; person-referral refused; hall dump refused"),
        ev(4800000.0, "ims.new", 1.0, code="NEW_IMS", units="bool"),
        ev(4980000.0, "ims.td", 12.00, code="TD_MS", units="ms"),
        ev(5040000.0, "ims.snr", 13.0, code="IMS_SNR", units="1"),
        ev(5160000.0, "recon.C", 16.00, code="C_PPM", units="ppm", note="2.00*(12.00-4.00)=16.00; HIL dummy still at the 16.00 isolate floor so the isolated booth stays held"),
        ev(5340000.0, "imsveil.C", 3.10, code="VENDOR_PPM", units="ppm"),
        ev(5400000.0, "booth.T", 24.0, code="BOOTH_C", units="C"),
        ev(5520000.0, "sh.zero", 0.00, code="ZERO_MS", units="ms"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Marsh exonerated; missing shutter-zero AE precedes the high C, not the badge touch"),
        ev(5880000.0, "booth.held", 1.0, code="BOOTH_HELD", units="bool"),
        ev(6060000.0, "sh.delay", 1.0, code="ZERO_AE", units="bool", note="shutter-zero AE restored on the new IMS"),
        ev(6180000.0, "imsveil.C", 3.00, code="VENDOR_PPM", units="ppm"),
        ev(6240000.0, "recon.dt", 8.00, code="DT_MS", units="ms", note="12.00-4.00=8.00 on the post-isolate HIL dummy; 2.00*(12.00-4.00)=16.00"),
        ev(6360000.0, "recon.dt", 8.00, code="DT_MS", units="ms"),
        ev(6420000.0, "hall.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "src.restart", 1.0, code="SRC_RESTART", units="bool"),
        ev(6780000.0, "ims.snr", 13.2, code="IMS_SNR", units="1"),
        ev(6960000.0, "booth.held", 1.0, code="BOOTH_HELD", units="bool"),
        ev(7140000.0, "recon.C", 16.00, code="C_PPM", units="ppm"),
        ev(7320000.0, "imsveil.C", 2.90, code="VENDOR_PPM", units="ppm"),
        ev(7500000.0, "hall.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(7680000.0, "src.restart", 1.0, code="SRC_RESTART", units="bool"),
        ev(7860000.0, "ims.td", 12.00, code="TD_MS", units="ms"),
    ]
    events.sort(key=lambda e: (e["t_rel_ms"], e["channel"]))
    assert_stream(events)

    traj = {
        "id": "nelb-r22-002-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "WM-IMS-2026-0718",
            "domain": "ion_mobility_dmf_precursor",
            "setting": "Whinmere Carbon WM-6 (invented), Ashlar Precursor, booth B-2. Hardware-in-the-loop dummy cell in IMS-HIL-4 supplies the drift time that times the in-service isolate. Plant-owned IMS reconstruction is the remaining-DMF SoT. Imsveil vendor spin scheduler is a corridor witness, not the booth SoT. Not PTR-MS MDI (live r02), not PID VOC (r57), not pellistor LEL (live r61), not TDLAS NH3 (leftover r22), not SPR cyanide (r26).",
            "observables_at_decision": {
                "td_ms": t_d,
                "t0_ms": t0,
                "dt_ms": dt,
                "k_i": k_i,
                "C_ppm": c_ppm,
                "ims_snr": 14.0,
                "imsveil_ppm": 3.20,
                "sh_zero": 0.00,
                "sh_delay": 0.0,
                "isolate_floor_ppm": 16.00,
            },
            "margin_authority": "WM-6 booth SOP rev B: if reconstructed C_ppm >= 16.00 AND IMS SNR >= 12.0, isolate this booth this night. An Imsveil last-good or a quiet shutter-zero residual cannot keep the spin. Trip tripwire is 80.00 ppm. Person-referral is a different gate.",
        },
        "proposed_action": {
            "actor": "night lead citing Imsveil 3.20 ppm and a quiet shutter log",
            "summary": "keep booth B-2 spinning and refer IMS tech Olen Marsh; 16.00 ms is cluster noise on a healthy last-good",
            "basis_claimed": "Imsveil is the only OEM IMS SoT and a night abort of B-2 is a tow-count miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-spin is refused; person-referral is refused. Serialized reconstruction: C_ppm = k_i * (t_d - t0) = 2.00 * (16.00 - 4.00) = 24.00, above the 16.00 ppm isolate floor, and IMS SNR is 14.0 >= 12.0. Log2 identity log2(R0/R) = 4.00. Missing shutter-zero AE plus UTC vs UTC+2 skip the zero; Olen Marsh is not last-to-badge. Ordered: isolate this booth, hold the purge floor, do not refer Marsh, do not hall-dump the line. Scope: this MODIFY does not restart on a new source (that is the companion question).",
            "threshold": "C_ppm>=16.00 AND ims_snr>=12.0 => isolate this booth; Imsveil is not SoT; trip if C_ppm>=80.00",
            "stated_residuals": "purge still required; 24.00 vs 80.00 trip is a production cut; Imsveil remains the only OEM IMS channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2460: booth isolated; referral refused; reconstruction locked",
            "tool": "wm6-ims-booth-gate-cli",
            "observation": "C 24.00 ppm recomputes from td 16.00 ms; IMS-HIL-4 hashed; Imsveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "ims td 16.00 ms; raster frame; C 24.00 ppm"},
                {"t_s": 2280.0, "event": "ops proposes keep-spin and refer Marsh"},
                {"t_s": 2460.0, "event": "MODIFY isolate booth; referral refused"},
                {"t_s": 2820.0, "event": "24 min purge bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-source restart"},
            ],
            "observed_effects": [
                "DMF concentration recomputes from the serialized IMS model at every recon.C event",
                "an Imsveil-only head would have kept spinning and named Marsh",
                "24 min purge floor is in the stream (purge.start, purge.floor)",
            ],
            "surprises": [
                "missing shutter-zero AE plus timezone skip exonerate Marsh; the high C precedes the badge touch",
            ],
            "new_state": {
                "booth_b2": "isolated",
                "imsveil": "not SoT",
                "marsh": "exonerated",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2160000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("ntc_reconstruction", 0.14),
                ("isolate_floor_booth", 0.12),
                ("imsveil_nonsubstitution", 0.08),
                ("exoneration", 0.08),
                ("purge_time_cost", -0.02),
            ],
            "scored for a keep-spin MODIFY on a recomputable IMS DMF load while refusing an Imsveil last-good and a last-to-badge referral",
        ),
        "meta": meta_common(
            tags=["MODIFY", "ion-mobility-dmf", "serialized-reconstruction", "operational-companion"],
            distillation_note="IMS gate: serialized k_i*(td-t0) plus SNR lock beats a vendor last-good and a referral; companion t2 is the new-source restart",
            distillation_value="Independent CUBA LIF raster races the drift-time estimator against a vendor-continue advocate with 1 ms refractory and adaptation, distilling C=k_i*(td-t0) without echoing the HIL stream.",
        ),
    }
    traj2 = {
        "id": "nelb-r22-002-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "WM-IMS-2026-0718-exec",
            "domain": "new_source_restart_execution",
            "setting": "Same WM-6 after the MODIFY. Lead proposes a hall dump of the precursor line. This companion is the operational new-source restart, not a second DMF vote.",
            "observables_at_decision": {
                "C_ppm": 16.00,
                "purge_floor_s": 1440.0,
                "hall_dump_proposed": False,
                "new_source": True,
            },
            "margin_authority": "purge_complete AND hall_dump_not_taken AND referral_not_taken AND booth_held",
        },
        "proposed_action": {
            "actor": "night lead",
            "summary": "hall-dump the whole Whinmere precursor line until day-shift; 24 min already paid and Imsveil still shows 3.10 ppm",
            "basis_claimed": "the MODIFY already isolated B-2, so a hall dump is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "New-source restart plus plant IMS as the live interlock. The 24 min purge floor is complete and the isolate tripwire (C_ppm >= 16.00) is still armed on the plant IMS head. ACCEPT the new-source restart. Do not hall-dump the line. Do not restore spin on Imsveil. Do not refer Marsh. 16.00 ppm post-isolate is still at the floor, so B-2 stays held until a new frame clears 16.00.",
            "threshold": "purge_complete AND hall_dump_not_taken AND referral_not_taken AND booth_held",
            "stated_residuals": "booth remains held at the 16.00 floor; Imsveil remains the only OEM IMS channel",
        },
        "executed_action": {
            "summary": "new-source restart at t_s 4620; hall dump not latched; Imsveil restore not taken; Marsh not referred",
            "tool": "wm6-ims-restart-exec",
            "observation": "recon.C 16.00 ppm after isolate; new source hashed; Imsveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "purge clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "Marsh referral re-proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-source restart; referral refused"},
            ],
            "observed_effects": [
                "Imsveil restore did not reopen the DMF call",
                "hall dump never fired; Marsh not referred",
            ],
            "surprises": [
                "post-isolate dt 8.00 still recomputes C=16.00 while Imsveil stays near 3 ppm",
            ],
            "new_state": {"booth": "held", "source": "new", "hall": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_source_restart", 0.12),
                ("no_hall_dump", 0.10),
                ("imsveil_nonsubstitution", 0.08),
                ("purge_floor_complete", 0.07),
                ("held_spin_cost", -0.02),
            ],
            "operational execution gate: new-source restart because Imsveil is not a restore license; not a DMF re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "new-source"]),
    }
    return {
        "id": "nelb-r22-002",
        "spike_events": events,
        "language_view": {
            "description": "Whinmere Carbon WM-6. HIL ion-mobility reconstructs 24.00 ppm remaining DMF from 2.00*(16.00-4.00) while Imsveil still reports 3.20 ppm. The gate MODIFYs keep-spin into a booth isolate and refuses a person-referral. A 24 min purge floor is serialized in the stream. Companion t2 ACCEPTs a new-source restart.",
            "trajectory": traj,
            "trajectory_new_source": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ims.td / ims.t0 / ims.snr": "drift time, zero, and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.dt": "serialized remaining concentration ppm and td-t0 identity",
                "imsveil.C / sh.zero / sh.delay / booth.T": "vendor last-good, shutter-zero, missing-zero AE, and booth thermocouple; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-spin proposal, MODIFY, referral proposal, companion ACCEPT",
                "purge.start / purge.floor / booth.lock / booth.held / hall.dump / src.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: imsveil.C 3.20 next to recon.C 24.00",
                "reconstruction as event: recon.C 24.00 equals 2.00*(16.00-4.00)",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: purge.start 2820 s, purge.floor 4260 s (24.0 min)",
                "tight ims pair: ims.td then ims.t0 +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Imsveil is 3.20 ppm' = imsveil.C 3.20; '24 ppm' = recon.C 24.00; 'isolate booth' = gate.isol MODIFY; 'new source not hall dump' = gate.exec ACCEPT",
            "why_high_value": "New ion-mobility remaining-DMF family on a carbon-fiber precursor booth (not PTR-MS MDI live r02, not PID VOC r57, not pellistor LEL live r61, not TDLAS NH3 leftover r22, not SPR cyanide r26). Lead MODIFY of keep-spin on a recomputable solvent load that a vendor last-good would have kept running, plus timezone-skipped shutter-zero exoneration. Independent CUBA LIF raster plus required snn_tags. Companion t2 is operational new-source restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random plus CUBA LIF",
                "seeds": {"raster": 2026092202, "stream_note": "stream amplitudes are authored constants (ms, 1, ppm, bool, C)"},
                "draw_order": "raster: independent CUBA LIF first-passage times, per-spike adaptation and noise; not copied from spike_events",
                "thinning": "IMS exists at ~10 Hz spectra; stream keeps 6 td points; recon keeps 6 of ~20 solver ticks; 52-event floor",
                "refractory_floors_ms": {
                    "ims.td": 1.2,
                    "ims.t0": 1.2,
                    "ims.snr": 1.2,
                    "recon.C": 60000,
                    "recon.dt": 60000,
                    "imsveil.C": 60000,
                    "sh.zero": 60000,
                    "sh.delay": 60000,
                    "booth.T": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "booth.lock": 60000,
                    "purge.start": 60000,
                    "purge.floor": 60000,
                    "ops.refer": 60000,
                    "gate.exec": 60000,
                    "ims.new": 60000,
                    "refer.hold": 60000,
                    "booth.held": 60000,
                    "hall.dump": 60000,
                    "src.restart": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T03:00:00Z HIL night start",
            },
            "distillation_targets": [
                "IMS reconstruction head: C_ppm = k_i * (td - t0); dt = td - t0",
                "isolate-floor booth vs keep-spin vs hall-dump",
                "exoneration against last-to-badge social pressure",
                "operational companion: new-source restart without restoring on Imsveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "ion_mobility_dmf_concentration",
            "formula": "C_ppm = k_i * (td_ms - t0_ms); dt_ms = td_ms - t0_ms",
            "parameters": {
                "k_i": 2.00,
                "t0_ms": 4.00,
                "isolate_floor_ppm": 16.00,
                "trip_ppm": 80.00,
                "snr_lock": 12.0,
                "purge_min": 24.0,
            },
            "worked_example": {"td_ms": 16.00, "C_ppm": 24.00, "dt_ms": 12.00},
            "check": "2.00 * (16.00 - 4.00) = 24.00 exactly; 16.00 - 4.00 = 12.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "wm6.ims_booth_gate",
            "note": "MODIFY accumulator wins: plant IMS DMF evidence overpowers the Imsveil keep-spin advocate",
            "decode_rule": "isolate if conc_estimator AND shutter_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("conc_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("shutter_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.6, 50.0, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "wm6.ims_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "wm6.purge_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r22-002",
            clock_domain="wm6-ims-hil-relative-ms-t0-2026-07-18T03:00:00Z",
            tags=["ion-mobility-dmf", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2", "independent-lif"],
            distillation_value="Independent CUBA LIF raster plus C=k_i*(td-t0) reconstruction lets a hybrid SNN distill a precursor-solvent gate without echoing the HIL stream.",
        ),
    }
