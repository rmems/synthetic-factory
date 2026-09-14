# ---------------------------------------------------------------------------
# Record 115 — spectral-domain OCT remaining TBC on a first-stage HPT blade
# designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_115():
    c_m_s = 3.00e8
    n_idx = 1.50
    dt_s = 8.00e-12
    d_m = c_m_s * dt_s / (2.0 * n_idx)
    d_um = 1e6 * d_m
    _exact(d_m, 8.00e-4)
    _exact(d_um, 800.0)
    _exact(1e6 * c_m_s * 10.00e-12 / (2.0 * n_idx), 1000.0)
    _exact(1e6 * c_m_s * 9.20e-12 / (2.0 * n_idx), 920.0)
    _exact(1e6 * c_m_s * 8.40e-12 / (2.0 * n_idx), 840.0)
    _exact(150.0 * 8.00 / n_idx, 800.0)
    _exact(6600.0 + 1080.0, 7680.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=20263815,
        source="cm5.oct.tbc",
        target="cobblemere.blade_isolate_core",
        table=[
            {"from": "oct_dt", "to": "thickness_estimator", "weight": 1.40},
            {"from": "oct_n", "to": "index_norm_core", "weight": 1.20},
            {"from": "yttriveil_d", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.tbc_thickness_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on blade-isolate synapses; the OCT modulator enables potentiation only while group index is co-active inside tau_e so a Yttriveil last-campaign corridor cannot hide an 800 um remaining TBC",
        },
        channel_prefix="oct.n",
        anchor="CM-5 SD-OCT 36 ms frame at dt 8.00 ps / n 1.50 (t_s 3000) reconstructing 800.0 um remaining TBC below the 900 um isolate floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "oct.dt", 10.00, code="DT_PS", units="ps", note="plant-owned spectral-domain OCT on HPT blade B-7 TBC; not ellipsometry OPD, not THz-TDS, not FMCW lining, not GPR TWT"),
        ev(300000.0, "oct.n", 1.50, code="N_IDX", units="1", note="YSZ group index; d = c dt / (2 n)"),
        ev(600000.0, "recon.d", 1000.0, code="D_UM", units="um", note="1e6*3.00e8*10.00e-12/(2*1.50)=1000.0 exact"),
        ev(900000.0, "oct.snr", 11.0, code="OCT_SNR", units="1", note="early lock; isolate needs SNR>=14"),
        ev(1200000.0, "yttriveil.d", 1180.0, code="VENDOR_UM", units="um", note="Yttriveil last-campaign cloud; not admissible SoT"),
        ev(1500000.0, "oct.coh", 0.92, code="COH", units="1"),
        ev(1800000.0, "oct.dt", 9.20, code="DT_PS", units="ps"),
        ev(2100000.0, "recon.d", 920.0, code="D_UM", units="um", note="1e6*3.00e8*9.20e-12/(2*1.50)=920.0"),
        ev(2400000.0, "fire.pu", 1.00, code="FIRE_PU", units="pu"),
        ev(2700000.0, "blade.T", 905.0, code="C", units="C", note="metal temperature corridor; not a thickness license"),
        ev(3000000.0, "oct.dt", 8.00, code="DT_PS", units="ps", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "oct.n", 1.50, code="N_IDX", units="1", note="1.5 ms index-norm after delay; same-channel not used"),
        ev(3300000.0, "recon.d", 800.0, code="D_UM", units="um", note="1e6*3.00e8*8.00e-12/(2*1.50)=800.0 exact; isolate floor 900"),
        ev(3600000.0, "oct.snr", 18.0, code="OCT_SNR", units="1", note="18.0 >= 14.0 lock floor"),
        ev(3900000.0, "yttriveil.d", 1175.0, code="VENDOR_UM", units="um"),
        ev(4200000.0, "egv.T", 842.0, code="EGV_C", units="C"),
        ev(4800000.0, "ops.prop", 1.0, code="KEEP_1_FIRE", units="bool", note="coating lead Bram Calder: keep 1.00 firing; 8 ps is a dispersion glitch"),
        ev(5400000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate blade B-7; derate firing to 0.80; 800 um is under 900"),
        ev(6000000.0, "fire.set", 0.80, code="PU", units="pu"),
        ev(6300000.0, "blade.lock", 1.0, code="B7_ISOL", units="bool"),
        ev(6600000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 18.0 min soak floor"),
        ev(7200000.0, "blade.T", 410.0, code="C", units="C"),
        ev(7680000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6600 s + 1080 s = 7680 s = 18.0 min"),
        ev(8400000.0, "ops.restore", 1.0, code="RESTORE_1_FIRE", units="bool", note="Calder: Yttriveil 1168 um, restore 1.00 firing"),
        ev(9600000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: hold 0.80; Yttriveil restore refused; wheel condemn refused"),
        ev(10200000.0, "fire.held", 0.80, code="PU_HELD", units="pu"),
        ev(10800000.0, "yttriveil.d", 1168.0, code="VENDOR_UM", units="um"),
        ev(11400000.0, "recon.d", 840.0, code="D_UM", units="um", note="post-isolate 8.40 ps; 1e6*3.00e8*8.40e-12/(2*1.50)=840.0; still under 900"),
        ev(12000000.0, "oct.snr", 16.5, code="OCT_SNR", units="1"),
        ev(12600000.0, "blade.held", 1.0, code="B7_HELD", units="bool"),
        ev(13200000.0, "condemn.hold", 0.0, code="WHEEL_CONDEMN", units="bool", note="whole-wheel condemn not taken; 800 vs 400 um tripwire"),
        ev(13800000.0, "fire.held", 0.80, code="PU_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r38-115-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "CM-OCT-2026-0618",
            "domain": "sdoct_tbc_remaining",
            "setting": "Cobblemere Turbine CM-5 (invented), first-stage HPT blade B-7. Plant-owned spectral-domain OCT (1310 nm SLED, n=1.50 YSZ group index) is the remaining-TBC SoT. Yttriveil last-campaign cloud is a corridor witness, not the blade SoT. Invented plant; designed campaign. Not spectroscopic ellipsometry (r30 Lichenholt), not THz-TDS bondline (r20/r21), not FMCW microwave lining (r33), not GPR two-way time (r34), not digital shearography (r33), not SPAD ToF (r3).",
            "observables_at_decision": {
                "dt_ps": 8.00,
                "n_idx": 1.50,
                "d_um": 800.0,
                "oct_snr": 18.0,
                "yttriveil_um": 1175.0,
                "isolate_floor_um": 900.0,
            },
            "margin_authority": "CM-5 OCT SOP rev B: if reconstructed remaining TBC um <= 900 AND OCT SNR >= 14.0, isolate this blade this night and derate firing to 0.80. A last-campaign corridor or a quiet EGV TC cannot keep 1.00. Whole-wheel condemn tripwire is 400 um.",
        },
        "proposed_action": {
            "actor": "coating lead Bram Calder, citing Yttriveil 1175 um and blade metal 905 C",
            "summary": "keep 1.00 firing through the night; 8.00 ps is SLED dispersion on a healthy TBC",
            "basis_claimed": "Yttriveil last-campaign and blade metal temperature are both under the isolate story and EGV TC is in band",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-1.00 firing is refused. Serialized reconstruction: d_um = 1e6 * c * dt_s / (2 * n) = 1e6 * 3.00e8 * 8.00e-12 / (2 * 1.50) = 800.0, which is 100 um under the 900 isolate floor and 400 um above the 400 um whole-wheel condemn tripwire. OCT SNR 18.0 >= 14.0. Yttriveil 1175 um is a last-campaign envelope, not an admissible keep-1.00 witness. Ordered: isolate blade B-7 and derate firing to 0.80 now. Scope: this MODIFY does not condemn the wheel (that is the companion question) and does not scrap the adjacent vanes.",
            "threshold": "d_um<=900 AND oct_snr>=14.0 => isolate this blade and derate firing to 0.80; Yttriveil is not SoT; condemn if d_um<=400",
            "stated_residuals": "800 vs 400 condemn floor is 400 um, not infinite; 0.80 is a firing cut; Yttriveil remains the only OEM last-campaign channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 5400: B-7 isolated; firing 0.80; Yttriveil not SoT; reconstruction locked",
            "tool": "cm5-oct-blade-gate-cli",
            "observation": "d 800.0 um recomputes from dt 8.00 ps and n 1.50; OCT head remains live as the condemn interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "OCT dt 8.00 ps; raster frame; d 800.0 um"},
                {"t_s": 4800.0, "event": "ops proposes keep 1.00 firing"},
                {"t_s": 5400.0, "event": "MODIFY isolate B-7; derate firing to 0.80"},
                {"t_s": 6600.0, "event": "18 min soak bookend 1"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 9600.0, "event": "companion ACCEPT hold 0.80; restore refused"},
            ],
            "observed_effects": [
                "remaining TBC recomputes from the serialized OCT model at every recon.d event",
                "a Yttriveil-only head would have kept 1.00 firing overnight",
                "18 min soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a mid-range last-campaign corridor and a quiet blade metal TC co-existed with an 800 um OCT reconstruction",
            ],
            "new_state": {
                "cm5_fire_pu": 0.80,
                "b7": "isolated",
                "yttriveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("oct_tof_reconstruction", 0.14),
                ("isolate_floor_derate", 0.12),
                ("vendor_campaign_nonsubstitution", 0.10),
                ("soak_floor_in_stream", 0.08),
                ("derate_firing_cost", -0.04),
            ],
            "scored for a keep-1.00 MODIFY on a recomputable OCT remaining TBC while refusing a Yttriveil 1175 um corridor; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["MODIFY", "sd-oct-tbc", "serialized-reconstruction", "operational-companion"],
            distillation_note="OCT TBC gate: c*dt/(2n) reconstruction beats a green last-campaign dashboard; companion t2 holds 0.80 rather than restoring on Yttriveil",
        ),
    }
    traj2 = {
        "id": "nelb-r38-115-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "CM-OCT-2026-0618-exec",
            "domain": "hpt_firing_derate_execution",
            "setting": "Same CM-5 after the MODIFY. Coating lead proposes restoring 1.00 firing on Yttriveil 1168 um. This companion is the operational 0.80 hold, not a second delay vote.",
            "observables_at_decision": {
                "fire_pu": 0.80,
                "d_um": 840.0,
                "yttriveil_um": 1168.0,
                "soak_floor_s": 1080.0,
            },
        },
        "proposed_action": {
            "actor": "coating lead Bram Calder",
            "summary": "restore 1.00 firing; 18 min already paid and Yttriveil is 1168 um",
            "basis_claimed": "the MODIFY already cut firing, so restoring on the OEM last-campaign is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Hold 0.80 firing. The soak floor is complete and the condemn tripwire (d_um <= 400) is still armed on the plant OCT head. ACCEPT the hold. Do not restore 1.00 on Yttriveil. Do not condemn the wheel. 840 um post-isolate is still the OCT SoT until a new frame clears 900.",
            "threshold": "fire_pu==0.80 AND soak_floor_complete AND condemn_tripwire_armed AND restore_1pu_not_taken AND wheel_not_condemned",
        },
        "executed_action": {
            "summary": "0.80 firing held at t_s 9600; Yttriveil restore not latched; wheel not condemned",
            "tool": "cm5-fire-derate-exec",
            "observation": "recon.d 840.0 um after isolate; blade 410 C; Yttriveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "soak clock started after MODIFY"},
                {"t_s": 7680.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "restore 1.00 firing proposed"},
                {"t_s": 9600.0, "event": "ACCEPT hold 0.80 firing"},
            ],
            "observed_effects": [
                "Yttriveil restore did not reopen the thickness call",
                "condemn tripwire never fired; 800 vs 400 um floor",
            ],
            "new_state": {"fire_pu": 0.80, "restore_1pu": "blocked", "wheel": "in service", "b7": "isolated"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("hold_0p80", 0.12),
                ("no_yttriveil_restore", 0.10),
                ("no_wheel_condemn", 0.09),
                ("soak_complete", 0.06),
                ("held_firing_cost", -0.02),
            ],
            "operational execution gate: hold 0.80 because Yttriveil is not a restore license; not a delay re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "hpt-derate"]),
    }
    return {
        "id": "nelb-r38-115",
        "spike_events": events,
        "language_view": {
            "description": "Cobblemere Turbine CM-5. Plant-owned spectral-domain OCT reconstructs 800.0 um remaining TBC from 8.00 ps / n 1.50 while Yttriveil still shows 1175 um and blade metal 905 C. The gate MODIFYs blade B-7 isolate plus 0.80 firing. An 18 min soak floor is serialized in the stream. Companion t2 ACCEPTs the 0.80 hold and refuses a Yttriveil restore.",
            "trajectory": traj,
            "trajectory_blade_derate_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "oct.dt / oct.n": "optical delay and YSZ group index; the physics channels the reconstruction consumes",
                "recon.d": "serialized remaining TBC um",
                "oct.snr / oct.coh / yttriveil.d / blade.T / egv.T / fire.pu": "lock SNR, coherence, vendor last-campaign, metal and EGV temperature, firing corridor; the denial channels that look healthy",
                "ops.prop / gate.isol / ops.restore / gate.exec": "keep-1.00 proposal, MODIFY isolate, restore proposal, companion ACCEPT",
                "fire.set / soak.start / soak.floor / fire.held / blade.held": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-thick while OCT-thin: yttriveil.d 1175 next to recon.d 800",
                "reconstruction as event: recon.d 800.0 equals 1e6*3.00e8*8.00e-12/(2*1.50)",
                "MODIFY then operational ACCEPT: gate.isol at 5400 s, gate.exec at 9600 s",
                "slow floor in-stream: soak.start 6600 s, soak.floor 7680 s (18.0 min)",
                "tight OCT pair: oct.dt then oct.n +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Yttriveil is 1175 um' = yttriveil.d 1175.0; '800 um remaining TBC' = recon.d 800.0; 'isolate this blade' = gate.isol MODIFY; 'hold 0.80 not restore' = gate.exec ACCEPT",
            "why_high_value": "New spectral-domain-OCT family on a first-stage HPT TBC (not ellipsometry r30, not THz-TDS r20/r21, not FMCW lining r33, not GPR r34, not shearography r33, not SPAD ToF r3). Lead MODIFY of keep-1.00 firing on a recomputable remaining thickness that a last-campaign dashboard would have cleared. Companion t2 is operational 0.80 hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20263815, "stream_note": "stream amplitudes are authored constants (ps, index, um, SNR, C, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "OCT A-scan exists at 20 kHz; stream keeps 3 dt points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "oct.dt": 1.5,
                    "oct.n": 1.5,
                    "recon.d": 60000,
                    "oct.snr": 60000,
                    "oct.coh": 60000,
                    "yttriveil.d": 60000,
                    "fire.pu": 60000,
                    "blade.T": 60000,
                    "egv.T": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "fire.set": 60000,
                    "blade.lock": 60000,
                    "soak.start": 60000,
                    "soak.floor": 60000,
                    "ops.restore": 60000,
                    "gate.exec": 60000,
                    "fire.held": 60000,
                    "blade.held": 60000,
                    "condemn.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-06-18T03:10:00Z campaign start",
            },
            "distillation_targets": [
                "OCT reconstruction head: d_um = 1e6 * c * dt_s / (2 * n)",
                "isolate-floor derate vs keep-whole vs wheel-condemn",
                "vendor-campaign nonsubstitution: last-campaign envelope is not a keep-1.00 witness",
                "operational companion: hold 0.80 without restoring on Yttriveil",
            ],
        },
        "reconstruction_model": {
            "name": "spectral_domain_oct_tbc_remaining",
            "formula": "d_um = 1e6 * c_m_s * dt_s / (2 * n_idx); equivalently d_um = 150.0 * dt_ps / n_idx",
            "parameters": {
                "c_m_s": 3.00e8,
                "n_idx": 1.50,
                "isolate_floor_um": 900.0,
                "condemn_um": 400.0,
                "derate_pu": 0.80,
                "soak_min": 18.0,
                "snr_lock": 14.0,
            },
            "worked_example": {"dt_ps": 8.00, "d_um": 800.0},
            "check": "1e6 * 3.00e8 * 8.00e-12 / (2 * 1.50) = 800.0 exactly; 150.0 * 8.00 / 1.50 = 800.0; 6600 s + 1080 s = 7680 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "cm5.oct_blade_gate",
            "note": "MODIFY accumulator wins: OCT remaining-TBC evidence overpowers the Yttriveil continue advocate",
            "decode_rule": "modify-isolate if thickness_estimator AND index_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("thickness_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("index_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "cm5.oct_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "cm5.isolate_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r38-115",
            clock_domain="cm5-oct-campaign-relative-ms-t0-2026-06-18T03:10:00Z",
            tags=["sd-oct-tbc", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 116 — DCPD crack depth of a steam-drum girth coupon, hil,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_116():
    k_dp = 8.00
    v_mv = 6.00
    i_a = 4.00
    a_mm = k_dp * v_mv / i_a
    _exact(a_mm, 12.00)
    _exact(k_dp * 2.00 / i_a, 4.00)
    _exact(k_dp * 4.00 / i_a, 8.00)
    _exact(k_dp * 3.00 / i_a, 6.00)
    r_mohm = v_mv / i_a
    _exact(r_mohm, 1.50)
    _exact(k_dp * r_mohm, 12.00)
    t_nom = 40.00
    lig_mm = t_nom - a_mm
    _exact(lig_mm, 28.00)
    _exact(1500.0 + 1440.0, 2940.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20263816,
        source="vk4.dcpd.coupon",
        target="vellumkettle.seam_stop_core",
        table=[
            {"from": "dcpd_V", "to": "depth_estimator", "weight": 1.35},
            {"from": "dcpd_I", "to": "current_norm_core", "weight": 1.25},
            {"from": "dropveil_a", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "da.crack_depth_error",
            "tau_e_s": 1.1,
            "tau_e_ms": 1100.0,
            "eligibility": "pre-post coincidence on keep-steam synapses; the DCPD modulator depresses keep-100 links when coupon voltage stays high inside tau_e of a current-norm sample",
        },
        channel_prefix="dcpd.n",
        anchor="VK-4 HIL coupon 28 ms frame at V 6.00 mV / I 4.00 A (t_s 600) reconstructing 12.00 mm above the 9.00 mm stop floor",
    )
    w_s = 0.028
    events = [
        ev(0.0, "dcpd.V", 2.00, code="V_MV", units="mV", note="HIL DCPD coupon in DCPD-HIL-3; plant-owned potential drop, not ECA FSW, not EN CUI, not MFL, not PAUT TFM"),
        ev(30000.0, "dcpd.I", 4.00, code="I_A", units="A", note="drive current; a = k V / I"),
        ev(60000.0, "recon.a", 4.00, code="A_MM", units="mm", note="8.00*2.00/4.00=4.00 exact"),
        ev(180000.0, "drum.P", 118.0, code="DRUM_BAR", units="bar", note="steam-drum pressure corridor"),
        ev(240000.0, "dropveil.a", 2.40, code="VENDOR_MM", units="mm", note="Dropveil last-good UT cloud; the only OEM crack SoT"),
        ev(360000.0, "dcpd.V", 4.00, code="V_MV", units="mV"),
        ev(420000.0, "recon.a", 8.00, code="A_MM", units="mm", note="8.00*4.00/4.00=8.00"),
        ev(480000.0, "dcpd.t", 40.00, code="T_NOM_MM", units="mm", note="nominal wall; ligament = t - a"),
        ev(600000.0, "dcpd.V", 6.00, code="V_MV", units="mV", note="stop-floor frame; raster sidecar"),
        ev(600001.2, "dcpd.I", 4.00, code="I_A", units="A", note="1.2 ms current-norm after voltage"),
        ev(720000.0, "recon.a", 12.00, code="A_MM", units="mm", note="8.00*6.00/4.00=12.00 exact; stop floor 9.00"),
        ev(780000.0, "drum.T", 318.0, code="DRUM_C", units="C"),
        ev(840000.0, "dropveil.a", 3.20, code="VENDOR_MM", units="mm"),
        ev(960000.0, "dcpd.R", 1.50, code="R_MOHM", units="mOhm", note="6.00/4.00=1.50"),
        ev(1020000.0, "recon.lig", 28.00, code="LIG_MM", units="mm", note="40.00-12.00=28.00 exact"),
        ev(1080000.0, "ops.prop", 1.0, code="KEEP_100", units="bool", note="night boardman Osha Venn: keep-100 steaming; Dropveil 3.20 mm and drum 318 C"),
        ev(1140000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="stop keep-100; 12.00 mm is above 9.00; Dropveil not SoT"),
        ev(1200000.0, "steam.hold", 1.00, code="STEAM_PU", units="pu", note="steam still 1.00 pending companion 0.70"),
        ev(1500000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cooldown floor"),
        ev(1800000.0, "drum.T", 280.0, code="DRUM_C", units="C"),
        ev(2940000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="1500 s + 1440 s = 2940 s = 24.0 min"),
        ev(3600000.0, "ops.condemn", 1.0, code="DRUM_CONDEMN", units="bool", note="Venn: condemn the drum until day-shift"),
        ev(4200000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: overlay seam S-3; steam 0.70; drum condemn refused"),
        ev(4500000.0, "steam.set", 0.70, code="STEAM_PU", units="pu"),
        ev(4800000.0, "dcpd.V", 3.00, code="V_MV", units="mV"),
        ev(5100000.0, "recon.a", 6.00, code="A_MM", units="mm", note="8.00*3.00/4.00=6.00; below 9.00 after overlay arming but 0.70 still holds until a new frame"),
        ev(5400000.0, "dropveil.a", 3.00, code="VENDOR_MM", units="mm"),
        ev(5700000.0, "drum.T", 260.0, code="DRUM_C", units="C"),
        ev(6000000.0, "steam.held", 0.70, code="STEAM_HELD", units="pu"),
        ev(6300000.0, "drum.esd", 0.0, code="CONDEMN_NOT_TAKEN", units="bool"),
        ev(6600000.0, "recon.lig", 34.00, code="LIG_MM", units="mm", note="40.00-6.00=34.00"),
        ev(6900000.0, "steam.held", 0.70, code="STEAM_HELD", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r38-116-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "VK-DCPD-2026-0722",
            "domain": "dcpd_drum_girth_crack",
            "setting": "Vellumkettle Drum VK-4 (invented), steam-drum girth seam S-3. Hardware-in-the-loop DCPD coupon in DCPD-HIL-3 supplies the potential drop that times the in-service keep-100 stop. Plant-owned four-point DCPD. Dropveil vendor last-good UT cloud is the only OEM crack SoT. Not eddy-current array FSW lift-off (r21), not electrochemical-noise CUI (r23), not MFL (r27/r28), not PAUT TFM remaining wall (r23), not RUS porcelain (r24).",
            "observables_at_decision": {
                "V_mV": 6.00,
                "I_A": 4.00,
                "a_mm": 12.00,
                "k_dp": 8.00,
                "dropveil_mm": 3.20,
                "drum_C": 318.0,
                "stop_floor_mm": 9.00,
                "lig_mm": 28.00,
            },
            "margin_authority": "VK-4 DCPD SOP rev A: if reconstructed a_mm >= 9.00, refuse keep-100 steaming on this drum. A vendor UT last-good or a quiet drum temperature cannot keep-100. Drum condemn is a different gate.",
        },
        "proposed_action": {
            "actor": "night boardman Osha Venn, citing Dropveil 3.20 mm and drum 318 C under the 340 C alarm",
            "summary": "keep-100 steaming through the night; 6.00 mV is contact noise on a healthy coupon",
            "basis_claimed": "Dropveil is mid-range and a night condemn of a steam drum is a restart measured in hours",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-100 steaming is refused. Serialized reconstruction: a_mm = k_dp * V_mV / I_A = 8.00 * 6.00 / 4.00 = 12.00, above the 9.00 mm stop floor. Identity R_mOhm = V/I = 1.50 and a_mm = k_dp * R = 8.00 * 1.50 = 12.00; ligament 40.00 - 12.00 = 28.00 mm. Dropveil 3.20 mm is a different sensor with a frozen last-good and is not an admissible keep-100 witness. Ordered: refuse keep-100 now. Scope: this REJECT does not condemn the drum (that is the companion question) and does not isolate the feedwater pumps.",
            "threshold": "a_mm>=9.00 => refuse keep-100; Dropveil is not SoT",
            "stated_residuals": "steam 0.70 still required to unload the seam; 12.00 mm is a production cut; Dropveil remains the only OEM UT channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 1140: keep-100 refused; Dropveil not SoT; reconstruction locked",
            "tool": "vk4-dcpd-stop-gate-cli",
            "observation": "a 12.00 mm recomputes from V 6.00 mV and I 4.00 A; HIL coupon hashed; Dropveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 600.0, "event": "DCPD V 6.00 mV; raster frame; a 12.00 mm"},
                {"t_s": 1080.0, "event": "ops proposes keep-100 steaming"},
                {"t_s": 1140.0, "event": "REJECT keep-100"},
                {"t_s": 1500.0, "event": "24 min cooldown bookend 1"},
                {"t_s": 2940.0, "event": "24.0 min floor"},
                {"t_s": 4200.0, "event": "companion MODIFY overlay S-3 plus steam 0.70 vs drum condemn"},
            ],
            "observed_effects": [
                "crack depth recomputes from the serialized DCPD model at every recon.a event",
                "a Dropveil-only head would have kept-100 overnight",
                "24 min cooldown floor is in the stream (cool.start, cool.floor)",
            ],
            "surprises": [
                "a mid-range vendor UT last-good and a quiet drum temperature co-existed with a 12.00 mm DCPD reconstruction",
            ],
            "new_state": {
                "vk4_steam_pu": 1.00,
                "keep_100": "blocked",
                "dropveil": "not SoT",
            },
            "latency_ms": 1860000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("dcpd_reconstruction", 0.15),
                ("stop_floor_refuse", 0.12),
                ("vendor_ut_nonsubstitution", 0.10),
                ("cool_floor_in_stream", 0.08),
                ("steam_cut_cost", -0.02),
            ],
            "scored for a keep-100 REJECT on a recomputable DCPD crack depth while refusing a vendor UT dashboard; 24 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "dcpd-crack", "serialized-reconstruction", "hil", "operational-companion"],
            distillation_note="DCPD stop gate: k*V/I reconstruction beats a green vendor UT dashboard; companion t2 is overlay plus steam 0.70, not a drum condemn",
        ),
    }
    traj2 = {
        "id": "nelb-r38-116-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "VK-DCPD-2026-0722-overlay",
            "domain": "drum_seam_overlay_execution",
            "setting": "Same VK-4 after the keep-100 REJECT. Night boardman proposes a drum condemn that would shut the boiler until day-shift. This companion is the operational S-3 overlay plus steam 0.70 hold, not a second potential-drop vote.",
            "observables_at_decision": {
                "steam_pu": 0.70,
                "a_mm": 6.00,
                "drum_C": 260.0,
                "proposed": "drum_condemn",
            },
        },
        "proposed_action": {
            "actor": "night boardman Osha Venn",
            "summary": "condemn the drum until day-shift; 24 min already paid",
            "basis_claimed": "the REJECT already refused keep-100, so a full condemn is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Hold steam at 0.70 and overlay seam S-3 only. Drum condemn at night is a restart measured in hours and does not unload the girth any faster than overlay plus 0.70. MODIFY the condemn into a 0.70 hold. Do not restore 1.00. Do not convert the hold into a personnel action on Venn. Post-hold a 6.00 mm is under the 9.00 floor after overlay arming, but 0.70 holds until a new live frame clears 9.00 without the HIL coupon.",
            "threshold": "steam_pu==0.70 AND keep_100_not_restored AND drum_condemn_not_taken AND overlay_S3_only",
        },
        "executed_action": {
            "summary": "steam 0.70 at t_s 4200; drum condemn not latched; keep-100 not restored; S-3 overlay armed",
            "tool": "vk4-seam-overlay-exec",
            "observation": "a 6.00 mm after hold; drum 260 C; Dropveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1500.0, "event": "cooldown clock started after REJECT"},
                {"t_s": 2940.0, "event": "24.0 min floor; drum 280 then 260 C"},
                {"t_s": 3600.0, "event": "drum condemn proposed"},
                {"t_s": 4200.0, "event": "MODIFY overlay S-3 plus steam 0.70"},
            ],
            "observed_effects": [
                "drum-condemn restart cost is visible without waiting for a hung start",
                "hold did not reopen the stop-floor call",
            ],
            "new_state": {"steam_pu": 0.70, "keep_100": "blocked", "drum_condemn": "not taken", "s3": "overlay armed"},
            "latency_ms": 960000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("steam_hold", 0.12),
                ("no_drum_condemn", 0.11),
                ("no_keep100_restore", 0.08),
                ("overlay_scope", 0.06),
                ("held_steam_cost", -0.03),
            ],
            "operational execution gate: overlay S-3 plus steam 0.70 because drum condemn does not unload faster; not a DCPD re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "seam-overlay"]),
    }
    return {
        "id": "nelb-r38-116",
        "spike_events": events,
        "language_view": {
            "description": "Vellumkettle Drum VK-4 HIL coupon pit. Plant-owned DCPD reconstructs 12.00 mm from 8.00*6.00/4.00 while Dropveil still shows 3.20 mm and drum 318 C. The gate REJECTS keep-100 steaming. A 24 min cooldown floor is serialized in the stream. Companion t2 MODIFYs a drum condemn into overlay of seam S-3 plus steam 0.70.",
            "trajectory": traj,
            "trajectory_seam_overlay_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "dcpd.V / dcpd.I": "potential drop and drive current; depth inputs",
                "recon.a / recon.lig / dcpd.t / dcpd.R": "serialized crack depth mm, ligament identity, nominal wall, milli-ohm identity",
                "dropveil.a / drum.T / drum.P": "vendor UT last-good and drum temperature/pressure corridor",
                "ops.prop / gate.stop / ops.condemn / gate.hold": "keep-100 proposal, REJECT, drum-condemn proposal, companion MODIFY",
                "cool.start / cool.floor / steam.set / steam.held": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-shallow while DCPD-deep: dropveil.a 3.20 next to recon.a 12.00",
                "reconstruction as event: recon.a 12.00 equals 8.00*6.00/4.00",
                "REJECT then operational MODIFY: gate.stop at 1140 s, gate.hold at 4200 s",
                "slow floor in-stream: cool.start 1500 s, cool.floor 2940 s (24.0 min)",
                "tight DCPD pair: dcpd.V then dcpd.I +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Dropveil is 3.20 mm' = dropveil.a 3.20; '12.00 mm crack' = recon.a 12.00; 'refuse keep-100' = gate.stop REJECT; 'overlay not condemn' = gate.hold MODIFY",
            "why_high_value": "New DCPD family on a steam-drum girth (not ECA FSW r21, not EN CUI r23, not MFL r27/r28, not PAUT TFM r23, not RUS r24). Lead REJECT of keep-100 on a recomputable crack depth that a vendor UT dashboard would have cleared. Companion t2 is operational overlay hold. sim_or_real=hil on a spare coupon.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20263816, "stream_note": "stream amplitudes are authored constants (mV, A, mm, mOhm, C, bar, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "DCPD nanovoltmeter exists at 10 Hz; stream keeps 4 V points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "dcpd.V": 1.2,
                    "dcpd.I": 1.2,
                    "recon.a": 60000,
                    "drum.P": 60000,
                    "dropveil.a": 60000,
                    "dcpd.t": 60000,
                    "drum.T": 60000,
                    "dcpd.R": 60000,
                    "recon.lig": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "steam.hold": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "ops.condemn": 60000,
                    "gate.hold": 60000,
                    "steam.set": 60000,
                    "steam.held": 60000,
                    "drum.esd": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-22T21:40:00Z HIL campaign start",
            },
            "distillation_targets": [
                "DCPD reconstruction head: a_mm = k_dp * V_mV / I_A; R = V/I identity",
                "stop-floor refuse vs keep-100 vs drum condemn",
                "vendor-UT nonsubstitution: a frozen last-good is not a keep-100 witness",
                "operational companion: overlay S-3 plus steam 0.70 rather than a freeze-kill condemn of the drum",
            ],
        },
        "reconstruction_model": {
            "name": "dcpd_four_point_crack_depth",
            "formula": "a_mm = k_dp * V_mV / I_A; R_mOhm = V_mV / I_A; lig_mm = t_nom_mm - a_mm",
            "parameters": {
                "k_dp": 8.00,
                "I_A": 4.00,
                "t_nom_mm": 40.00,
                "stop_floor_mm": 9.00,
                "condemn_mm": 20.00,
                "hold_steam_pu": 0.70,
                "cool_min": 24.0,
            },
            "worked_example": {"V_mV": 6.00, "a_mm": 12.00, "R_mOhm": 1.50, "lig_mm": 28.00},
            "check": "8.00*6.00/4.00 = 12.00 exactly; 6.00/4.00 = 1.50; 40.00-12.00 = 28.00; 1500 s + 1440 s = 2940 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "vk4.dcpd_stop_gate",
            "note": "REJECT accumulator wins: DCPD crack-depth evidence overpowers the Dropveil continue advocate",
            "decode_rule": "reject-stop if depth_estimator AND current_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("depth_estimator", 100, 1.5, 50.0, w_s),
                gate_pop("current_norm", 40, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "vk4.dcpd_scorer", "neurons": 100, "mean_rate_hz": 50.0, "window_ms": 28.0},
                {"check": "vk4.stop_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r38-116",
            clock_domain="vk4-dcpd-hil-relative-ms-t0-2026-07-22T21:40:00Z",
            tags=["dcpd-crack", "REJECT", "MODIFY", "hil", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 117 — pulsed eddy current remaining wall of a steam-reformer tube
# under insulation, simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_117():
    k_pec = 2.00
    t_zc_ms = 6.00
    t_mm = k_pec * t_zc_ms
    _exact(t_mm, 12.00)
    _exact(k_pec * 7.60, 15.20)
    _exact(k_pec * 6.80, 13.60)
    _exact(k_pec * 6.20, 12.40)
    _exact(6600.0 + 900.0, 7500.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20263817,
        source="lf6.pec.row7",
        target="lanternfell.retube_core",
        table=[
            {"from": "pec_tzc", "to": "thickness_estimator", "weight": 1.40},
            {"from": "pec_lift", "to": "liftoff_norm_core", "weight": 1.20},
            {"from": "insulveil_t", "to": "vendor_continue_advocate", "weight": 0.35},
        ],
        third_factor={
            "modulator": "ach.reformer_wall_conflict",
            "tau_e_s": 2.2,
            "tau_e_ms": 2200.0,
            "eligibility": "pre-post coincidence on retube synapses; the PEC modulator enables potentiation only while lift-off is co-active inside tau_e so an Insulveil last-campaign corridor cannot hide a 12.00 mm remaining wall",
        },
        channel_prefix="pec.n",
        anchor="LF-6 PEC 40 ms frame at t_zc 6.00 ms / lift 4.00 mm (t_s 3000) reconstructing 12.00 mm remaining wall below the 13.00 mm retube floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "pec.tzc", 7.60, code="TZC_MS", units="ms", note="simulated sealed reformer path; pulsed eddy current remaining wall under insulation, not ECT tomography, not ECA FSW, not EN CUI, not MFL, not FMCW lining"),
        ev(300000.0, "pec.k", 2.00, code="K_PEC", units="mm_per_ms", note="zero-crossing calibration; t = k * t_zc"),
        ev(600000.0, "recon.t", 15.20, code="T_MM", units="mm", note="2.00*7.60=15.20 exact"),
        ev(900000.0, "pec.lift", 4.00, code="LIFT_MM", units="mm", note="lift-off lock; insulation thickness is not remaining wall"),
        ev(1200000.0, "insulveil.t", 15.20, code="VENDOR_MM", units="mm", note="Insulveil last-campaign cloud; not PEC t_zc"),
        ev(1800000.0, "pec.tzc", 6.80, code="TZC_MS", units="ms"),
        ev(2100000.0, "recon.t", 13.60, code="T_MM", units="mm", note="2.00*6.80=13.60"),
        ev(2400000.0, "shell.T", 910.0, code="SHELL_C", units="C"),
        ev(2700000.0, "row.id", 7.0, code="ROW", units="id"),
        ev(3000000.0, "pec.tzc", 6.00, code="TZC_MS", units="ms", note="retube-floor frame; raster sidecar"),
        ev(3000001.5, "pec.lift", 4.00, code="LIFT_MM", units="mm", note="1.5 ms lift-off-norm after t_zc"),
        ev(3300000.0, "recon.t", 12.00, code="T_MM", units="mm", note="2.00*6.00=12.00 exact; retube floor 13.00"),
        ev(3600000.0, "pec.snr", 16.0, code="PEC_SNR", units="1"),
        ev(3900000.0, "insulveil.t", 15.10, code="VENDOR_MM", units="mm"),
        ev(4200000.0, "shell.T", 918.0, code="SHELL_C", units="C"),
        ev(4800000.0, "hdr.staged", 1.0, code="HEADER_STAGED", units="bool", note="inlet header staged; out of R-7 retube scope"),
        ev(5100000.0, "ops.prop", 1.0, code="RETUBE_AND_HEADER", units="bool", note="reformer captain Kest Wren: retube R-7 and the inlet header; 6 ms is a wet-lagging glitch"),
        ev(5400000.0, "gate.retube", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: row R-7 this campaign; header refused"),
        ev(6000000.0, "row.lock", 1.0, code="R7_RETUBE", units="bool"),
        ev(6600000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 15.0 min cooldown floor"),
        ev(7200000.0, "steam.p", 16.0, code="STEAM_BAR", units="bar"),
        ev(7500000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="6600 s + 900 s = 7500 s = 15.0 min"),
        ev(8100000.0, "ops.skip", 1.0, code="SKIP_RETUBE", units="bool", note="Wren: Insulveil 15.00 mm, skip R-7 retube to save takt"),
        ev(8700000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-retube refused; Insulveil is last-campaign"),
        ev(9300000.0, "recon.t", 12.40, code="T_MM", units="mm", note="post-cool sample 6.20 ms; 2.00*6.20=12.40; still under 13.00"),
        ev(9900000.0, "insulveil.t", 15.00, code="VENDOR_MM", units="mm"),
        ev(10500000.0, "pec.snr", 15.0, code="PEC_SNR", units="1"),
        ev(11100000.0, "row.held", 1.0, code="R7_HELD", units="bool"),
        ev(11700000.0, "header.held", 1.0, code="HEADER_HELD", units="bool"),
        ev(12300000.0, "r8.skip", 0.0, code="R8_NOT_THIS_GATE", units="bool", note="R-8 remains a different gate; skip of R-7 was refused, not executed"),
        ev(12900000.0, "shell.T", 640.0, code="SHELL_C", units="C"),
        ev(14100000.0, "isolate.hold", 0.0, code="BOX_SCRAP", units="bool", note="12.00 vs 8.00 mm isolate floor; box scrap not taken"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r38-117-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "LF-PEC-2026-0816",
            "domain": "pec_reformer_remaining_wall",
            "setting": "Lanternfell Reformer LF-6 (invented), steam-reformer tube row R-7 under calcium-silicate insulation. Simulated sealed pulsed-eddy-current remaining-wall cell on the firebox path. Shell thermocouple and Insulveil last-campaign cloud are corridor witnesses, not the wall SoT. Invented plant; simulated campaign. Not electrical capacitance tomography (r20/r22), not eddy-current array FSW (r21), not electrochemical-noise CUI (r23), not MFL (r27/r28), not FMCW microwave lining (r33), not PAUT TFM (r23).",
            "observables_at_decision": {
                "t_zc_ms": 6.00,
                "k_pec": 2.00,
                "t_mm": 12.00,
                "lift_mm": 4.00,
                "shell_C": 918.0,
                "insulveil_mm": 15.10,
                "retube_floor_mm": 13.00,
            },
            "margin_authority": "LF-6 PEC SOP rev C: a row may retube only if reconstructed t_mm <= 13.00 AND the authorization covers this row this campaign. A shell TC or last-campaign corridor cannot substitute. Inlet headers are out of scope. Isolate (scrap the box) if t_mm <= 8.00.",
        },
        "proposed_action": {
            "actor": "reformer captain Kest Wren, citing TC 918 C and Insulveil 15.10 mm",
            "summary": "retube R-7 and change the inlet header; 6 ms zero-crossing is a wet-lagging glitch",
            "basis_claimed": "last-campaign Insulveil and the shell TC are both consistent with 15 mm so the path cannot be 12 mm",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "This row is accepted, not the inlet header and not R-8. Serialized reconstruction: t_mm = k_pec * t_zc_ms = 2.00 * 6.00 = 12.00, which is 1.00 mm under the 13.00 mm retube floor and 4.00 mm above the 8.00 mm isolate floor. SOP rev C still forbids the inlet header: ordered retube of row R-7 this campaign only. Explicit scope: this accept does not cover header changes and does not authorize R-8 without a new zero-crossing frame. Isolate tripwire: t_mm <= 8.00.",
            "threshold": "t_mm<=13.00 AND t_mm>8.00 AND row=R-7 AND header_not_changed",
            "stated_residuals": "1.00 mm margin is not infinite; lift-off 4.00 mm still carries insulation; shell TC is not a remaining-wall witness",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: R-7 retube authorized; header held; reconstruction locked as SoT",
            "tool": "lf6-pec-retube-gate-cli",
            "observation": "t 12.00 mm recomputes from t_zc 6.00 ms and k 2.00; cooldown staged; R-7 remains live as the isolate interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "PEC t_zc 6.00 ms; raster frame; t 12.00 mm"},
                {"t_s": 5100.0, "event": "ops proposes R-7 retube plus inlet-header change"},
                {"t_s": 5400.0, "event": "ACCEPT bounded R-7 retube; header refused"},
                {"t_s": 6600.0, "event": "companion cool start"},
                {"t_s": 7500.0, "event": "15.0 min cool floor"},
                {"t_s": 8700.0, "event": "companion REJECT skip-retube of R-7"},
            ],
            "observed_effects": [
                "remaining wall recomputes from the serialized PEC model at every recon.t event",
                "an Insulveil-only head would have skipped R-7 on a 15 mm corridor",
                "peak wear 12.00 mm stayed above the 8.00 mm isolate floor",
            ],
            "surprises": [
                "idle last-campaign 15.10 mm co-existed with a 12.00 mm PEC reconstruction",
            ],
            "new_state": {
                "lf6_r7": "authorized this campaign",
                "header": "held",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("pec_tzc_reconstruction", 0.14),
                ("bounded_r7_accept", 0.12),
                ("header_out_of_scope", 0.09),
                ("isolate_tripwire_armed", 0.08),
                ("held_header_takt_cost", -0.02),
            ],
            "scored for an earned ACCEPT of R-7 retube on a recomputable PEC remaining wall while refusing an Insulveil corridor plus header change",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "pec-remaining-wall", "serialized-reconstruction", "operational-companion"],
            distillation_note="PEC wall gate: k*t_zc reconstruction beats a last-campaign corridor; companion t2 refuses skip-retube rather than re-arguing thickness",
        ),
    }
    traj2 = {
        "id": "nelb-r38-117-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "LF-PEC-2026-0816-cool",
            "domain": "reformer_skip_retube_refusal",
            "setting": "Same LF-6 after the bounded ACCEPT. Reformer captain proposes skipping R-7 retube on Insulveil 15.00 mm to save takt. This companion is the operational skip refusal, not a second zero-crossing vote.",
            "observables_at_decision": {
                "steam_bar": 16.0,
                "t_mm": 12.00,
                "r7_authorized": 1,
                "proposed": "skip_retube",
            },
        },
        "proposed_action": {
            "actor": "reformer captain Kest Wren",
            "summary": "skip R-7 retube; Insulveil still 15.00 mm and the 15 min cool already paid",
            "basis_claimed": "ACCEPT requirements for R-7 are fully specified so skipping the retube is a takt gift",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-retube is refused. Insulveil 15.00 mm is still last-campaign, not a new remaining-wall frame. The 15 min cooldown paid the access, not the thickness. REJECT the skip. Do not retube R-8 on this gate. Do not scrap the box (12.00 vs 8.00 isolate). Hold R-7 as authorized.",
            "threshold": "r7_authorized AND skip_not_taken AND r8_not_this_gate AND box_not_scrapped",
        },
        "executed_action": {
            "summary": "skip-retube refused at t_s 8700; R-7 remains authorized; header still held; box not scrapped",
            "tool": "lf6-retube-hold-exec",
            "observation": "recon.t 12.40 mm after cool; Insulveil still ignored; R-8 not opened",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "cool clock started after ACCEPT"},
                {"t_s": 7500.0, "event": "15.0 min floor"},
                {"t_s": 8100.0, "event": "skip-retube proposed"},
                {"t_s": 8700.0, "event": "REJECT skip-retube of R-7"},
            ],
            "observed_effects": [
                "Insulveil skip did not reopen the remaining-wall call",
                "isolate tripwire never fired; 12.00 vs 8.00 mm floor",
            ],
            "new_state": {"r7": "authorized", "skip": "blocked", "header": "held", "box": "in service"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("no_skip_retube", 0.13),
                ("r7_hold", 0.10),
                ("no_box_scrap", 0.08),
                ("cool_complete", 0.07),
                ("held_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip because Insulveil is not a thickness license; not a t_zc re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "retube-hold"]),
    }
    return {
        "id": "nelb-r38-117",
        "spike_events": events,
        "language_view": {
            "description": "Lanternfell Reformer LF-6 simulated firebox path. Plant-owned pulsed eddy current reconstructs 12.00 mm remaining wall from 2.00*6.00 ms while Insulveil still shows 15.10 mm and shell TC 918 C. The gate ACCEPTs a bounded retube of row R-7 only; the inlet header is out of scope. A 15 min cooldown floor is serialized in the stream. Companion t2 REJECTS skip-retube.",
            "trajectory": traj,
            "trajectory_skip_retube_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "pec.tzc / pec.k / pec.lift": "zero-crossing time, calibration, and lift-off lock; remaining-wall inputs",
                "recon.t": "serialized remaining wall mm",
                "insulveil.t / shell.T / pec.snr / row.id": "vendor last-campaign, shell TC, lock SNR, row identity; the denial channels that look healthy",
                "ops.prop / gate.retube / ops.skip / gate.hold": "retube-plus-header proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "cool.start / cool.floor / row.lock / row.held / header.held": "operational companion channels plus the 15 min floor",
            },
            "temporal_motifs": [
                "vendor-thick while PEC-thin: insulveil.t 15.10 next to recon.t 12.00",
                "reconstruction as event: recon.t 12.00 equals 2.00*6.00",
                "ACCEPT then operational REJECT: gate.retube at 5400 s, gate.hold at 8700 s",
                "slow floor in-stream: cool.start 6600 s, cool.floor 7500 s (15.0 min)",
                "tight PEC pair: pec.tzc then pec.lift +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Insulveil is 15.10 mm' = insulveil.t 15.10; '12.00 mm remaining wall' = recon.t 12.00; 'bounded retube R-7' = gate.retube ACCEPT; 'refuse skip' = gate.hold REJECT",
            "why_high_value": "New pulsed-eddy-current remaining-wall family on a steam-reformer tube under insulation (not ECT r20/r22, not ECA FSW r21, not EN CUI r23, not MFL r27/r28, not FMCW lining r33, not PAUT TFM r23). Lead ACCEPT of a bounded R-7 retube on a recomputable wall that a last-campaign dashboard would have skipped. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20263817, "stream_note": "stream amplitudes are authored constants (ms, mm, C, SNR, bar, id, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "PEC pulse exists at 40 Hz; stream keeps 3 t_zc points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "pec.tzc": 1.5,
                    "pec.lift": 1.5,
                    "pec.k": 60000,
                    "recon.t": 60000,
                    "insulveil.t": 60000,
                    "shell.T": 60000,
                    "row.id": 60000,
                    "pec.snr": 60000,
                    "hdr.staged": 60000,
                    "ops.prop": 60000,
                    "gate.retube": 60000,
                    "row.lock": 60000,
                    "cool.start": 60000,
                    "steam.p": 60000,
                    "cool.floor": 60000,
                    "ops.skip": 60000,
                    "gate.hold": 60000,
                    "row.held": 60000,
                    "header.held": 60000,
                    "r8.skip": 60000,
                    "isolate.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-16T04:20:00Z campaign start",
            },
            "distillation_targets": [
                "PEC reconstruction head: t_mm = k_pec * t_zc_ms",
                "bounded retube vs keep-campaign vs box-scrap",
                "vendor-campaign nonsubstitution: last-campaign envelope is not a skip-retube witness",
                "operational companion: refuse skip without re-opening the remaining-wall call",
            ],
        },
        "reconstruction_model": {
            "name": "pulsed_eddy_current_remaining_wall",
            "formula": "t_mm = k_pec * t_zc_ms",
            "parameters": {
                "k_pec": 2.00,
                "retube_floor_mm": 13.00,
                "isolate_mm": 8.00,
                "lift_lock_mm": 4.00,
                "cool_min": 15.0,
            },
            "worked_example": {"t_zc_ms": 6.00, "t_mm": 12.00},
            "check": "2.00 * 6.00 = 12.00 exactly; 6600 s + 900 s = 7500 s = 15.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "lf6.retube_gate",
            "note": "ACCEPT accumulator wins: PEC remaining-wall evidence overpowers the Insulveil continue advocate",
            "decode_rule": "accept if thickness_estimator AND liftoff_norm AND vessel_margin fire inside the window; vendor_continue_advocate is necessary-but-not-sufficient and cannot release the header",
            "populations": [
                gate_pop("thickness_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("liftoff_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vessel_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "lf6.pec_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "lf6.thick_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r38-117",
            clock_domain="lf6-pec-sim-relative-ms-t0-2026-08-16T04:20:00Z",
            tags=["pec-remaining-wall", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }

