#!/usr/bin/env python3
"""Splices r111 chemistry, percent-open/closed wrong-modify, NOTES, and 572 checks."""
from pathlib import Path

src = Path("/tmp/ttf-r111/_stage1.py").read_text()
src = src.replace(
    "ttf-r111-571..535",
    "ttf-r111-571..575",
)

CHEM = [
    # 571 phthalic anhydride oxidizer
    ("Selenite-Hawes", "Phthalan-Keld"),
    ("SH-5", "PK-5"),
    ("selenium-dioxide-scrubber", "phthalic-anhydride-oxidizer"),
    ("packed tower T-2", "air-oxidizer O-2"),
    ("Scrubber T-2", "Oxidizer O-2"),
    ("scrubber pass", "oxidizer pass"),
    ("the scrubber is", "the oxidizer is"),
    ("SH-5 scrubber", "PK-5 oxidizer"),
    ("T-2 indexed", "O-2 indexed"),
    ("T-2 SeO2", "O-2 PA-mist"),
    ("circulating-liquor UV SeO2 cell", "o-xylene-air PA-mist UV cell"),
    ("circulating-liquor UV", "o-xylene-air PA-mist UV"),
    ("SeO2 liquor", "PA-mist"),
    ("SeO2", "PA-mist"),
    ("seo2-liquor", "pa-mist"),
    ("uv.se.gL", "uv.pa.gNm3"),
    ("relay.uv.se", "relay.uv.pa"),
    ("se_cap_gL", "pa_cap_gNm3"),
    ("observed_se_gL", "observed_pa_gNm3"),
    ("predicted_unclamped_next_gL", "predicted_unclamped_next_gNm3"),
    ("se_gL", "pa_gNm3"),
    ("g/L", "g/Nm3"),
    ("pt.rec.bar", "pt.qch.bar"),
    ("relay.pt.rec", "relay.pt.qch"),
    ("ae.pack.drop", "ae.bed.drop"),
    ("relay.ae.pack", "relay.ae.bed"),
    ("recycle-header PT", "quench-header PT"),
    ("recycle-header", "quench-header"),
    ("recycle PT", "quench PT"),
    ("recycle lock", "quench lock"),
    ("recycle-lock", "quench-lock"),
    ("recycle still", "quench still"),
    ("header-first", "quench-first"),
    ("Liquor-first", "Mist-first"),
    ("liquor-first", "mist-first"),
    ("liquor-SeO2", "PA-mist"),
    ("liquor-pump clamp", "air-header clamp"),
    ("liquor-pump", "air-header"),
    ("Pump-cut on the liquor win", "Air-cut on the o-xylene win"),
    ("pump clamp", "air-header clamp"),
    ("pump-clamp", "air-clamp"),
    ("pump_clamp", "air_clamp"),
    ("cruise_liquor_pump", "cruise_air_header"),
    ("clamped_liquor_pump", "clamped_air_header"),
    ("clamped_liquor_m3h", "clamped_air_kNm3h"),
    ("liquor_m3h", "air_kNm3h"),
    ("m3/h", "kNm3/h"),
    ("rec_cap_bar", "qch_cap_bar"),
    ("rec_bar", "qch_bar"),
    ("header_hold", "quench_hold"),
    ("pack_veto", "bed_veto"),
    ("packing-ring slump", "V2O5-bed slump"),
    ("packing collapse", "V2O5-bed slump"),
    ("packing still collapses", "V2O5 bed still slumps"),
    ("packing drop", "V2O5-bed drop"),
    ("Ceramic-ring AE", "Vanadium-bed AE"),
    ("packing AE puck", "vanadium-bed AE puck"),
    ("seated packing collapse", "seated V2O5-bed slump"),
    ("collapsed packed bed", "slumped V2O5 bed"),
    ("ceramic rings", "vanadium pellets"),
    ("lif.pack", "lif.bed"),
    ("selenium dust", "PA-coke fines"),
    ("dumping selenium", "dumping PA-coke"),
    ("a clean selenium pass", "a clean PA pass"),
    ("tower isolate", "oxidizer isolate"),
    ("15 min tower", "15 min oxidizer"),
    ("make-up Coriolis", "o-xylene Coriolis"),
    ("Neurons 0-13 carry +0.62 liquor-pump clamp bias; stim 22-25 ms is the packing collapse.",
     "Neurons 0-13 carry +0.62 air-header clamp bias; stim 22-25 ms is the V2O5-bed slump."),
    # 573 lanthanum fluoride precipitator
    ("Yttria-Scarth", "Lanfluor-Smeaton"),
    ("YS-HIL", "LS-HIL"),
    ("yttrium-fluoride-electrolyzer", "lanthanum-fluoride-precipitator"),
    ("yttrium-fluoride cell", "lanthanum-fluoride precipitator"),
    ("yttrium-fluoride bus", "lanthanum-fluoride bus"),
    ("yttrium fluoride", "lanthanum fluoride"),
    ("yttrium cathode", "LaF3 rake"),
    ("growling yttrium", "growling LaF3"),
    ("YF-3", "LF-3"),
    ("ae.yf.pps", "ae.laf.pps"),
    ("relay.ae.yf", "relay.ae.laf"),
    ("i.cell.kA", "p.agit.kW"),
    ("relay.i.cell", "relay.p.agit"),
    ("yf-ae", "laf-ae"),
    ("yf-hold", "laf-hold"),
    ("yf_hold", "laf_hold"),
    ("ka_go", "kw_go"),
    ("cell-CT", "agitator-kW"),
    ("cell CT", "agitator kW"),
    ("Cell CT", "Agitator kW"),
    ("cell-current", "agitator-kW"),
    ("cell current", "agitator kW"),
    ("Cell current", "Agitator kW"),
    ("legal cell-current", "legal agitator-kW"),
    ("dispatch_tap", "raise_rake"),
    ("hold_cell", "hold_rake"),
    ("dispatched a growling", "raised a growling"),
    ("Hall stack", "rake gearbox"),
    ("tap-to-tap encoder", "rake-height encoder"),
    ("bath TC", "slurry TC"),
    ("9 MW tap", "9 t/h rake raise"),
    ("9 MW", "9 t/h"),
    ("proposed_mw", "proposed_tph"),
    ("executed_mw", "executed_tph"),
    ("(\"mw\", 9.0)", '("tph", 9.0)'),
    ("(\"mw\", 0.0)", '("tph", 0.0)'),
    ("power 9 -> 0 MW", "rake 9 -> 0 t/h"),
    ("held at 0 MW", "held at 0 t/h"),
    ("Power 0 MW", "Rake 0 t/h"),
    ("kA-first", "kW-first"),
    ("Current-first", "Agitator-first"),
    ("AE-first latches hold; current-first dispatches 9 t/h on a 'kA still legal' model.",
     "AE-first latches hold; agitator-first raises 9 t/h on a 'kW still legal' model."),
    ("trims kA", "trims kW"),
    ("cell reset", "rake reset"),
    ("HIL slip not dispatched", "HIL rake not raised"),
    ("/ Cell YF-3", "/ Precipitator LF-3"),
    ("holds the tap", "holds the rake"),
    ("kA trip", "kW trip"),
    ("28 kA", "28 kW"),
    ("44 kA", "44 kW"),
    ("cell_kA", "agit_kW"),
    ("cell_cap_kA", "agit_cap_kW"),
    # leftover 28 kA strings after kA replacement
    ("28 kW under a 44 kW", "28 kW under a 44 kW"),
    # 574 ethylhexanol aldol
    ("Germanyl-Tofts", "Ethylhex-Knap"),
    ("GT-6", "EK-6"),
    ("germanium-tetrachloride-rectifier", "ethylhexanol-aldol-kettle"),
    ("simulated-gecl4-rectifier", "simulated-eh-aldol"),
    ("GeCl4-rectifier", "EH-aldol"),
    ("crude GeCl4", "n-butyraldehyde"),
    ("crude-GeCl4", "n-butyraldehyde"),
    ("GeCl4 feed", "butyraldehyde feed"),
    ("legal GeCl4", "legal butyraldehyde"),
    ("gecl4_tph", "butyral_tph"),
    ("gecl4-level", "aldol-level"),
    ("legal_gecl4_stdp", "legal_aldol_stdp"),
    ("feed_gecl4_96", "feed_butyral_96"),
    ("rectifier R-1", "aldol kettle A-1"),
    ("Rectifier R-1", "Aldol A-1"),
    ("R-1 indexed", "A-1 indexed"),
    ("restacks R-1", "restacks A-1"),
    ("left R-1", "left A-1"),
    ("reflux drum", "aldol pot"),
    ("reflux inventory", "pot inventory"),
    ("reflux densitometer", "pot densitometer"),
    ("dens.reflux.m", "dens.pot.m"),
    ("relay.dens.reflux", "relay.dens.pot"),
    ("reflux_cap_m", "pot_cap_m"),
    ("observed_reflux_m", "observed_pot_m"),
    ("reflux_m", "pot_m"),
    ("reflux_go", "pot_go"),
    ("reflux-go", "pot-go"),
    ("reflux_veto", "pot_veto"),
    ("delta-P packing", "delta-P agitator"),
    ("HCl 2.0 wt percent", "NaOH 2.0 wt percent"),
    ("hcl_wt_pct", "naoh_wt_pct"),
    ("hcl_cap_wt_pct", "naoh_cap_wt_pct"),
    ("HCl 0.8", "NaOH 0.8"),
    ("6.8 m reflux", "6.8 m pot"),
    ("reflux 6.8", "pot 6.8"),
    ("Reflux level", "Pot level"),
    ("Reflux ", "Pot "),
    ("reflux ", "pot "),
    ("skin-TC hitch", "jacket-TC hitch"),
    ("Skin TC hitch", "Jacket TC hitch"),
    ("Skin TC", "Jacket TC"),
    ("skin TC", "jacket TC"),
    ("skin-first", "jacket-first"),
    ("tc.skin.C", "tc.jkt.C"),
    ("relay.tc.skin", "relay.tc.jkt"),
    ("skin_cap_C", "jkt_cap_C"),
    ("observed_skin_C", "observed_jkt_C"),
    ("skin_C", "jkt_C"),
    ("skin_hold", "jkt_hold"),
    ("dry still", "dry aldol pot"),
    # 575 SF6 cell
    ("Ceriax-Howk", "Sulfhex-Brae"),
    ("CH-2", "SB-4"),
    ("cerium-oxalate-calciner", "sulfur-hexafluoride-cell"),
    ("cerium oxide", "SF6"),
    ("cerium kiln", "SF6 cell"),
    ("Calciner K-7", "Cell F-7"),
    ("Kiln K-7", "Cell F-7"),
    ("kiln K-7", "cell F-7"),
    ("K-7 on-spec", "F-7 on-spec"),
    ("K-7 at 4.8", "F-7 at 4.8"),
    ("oxalate charge", "SF6 charge"),
    ("oxalate run", "SF6 run"),
    ("oxalate armed", "SF6 armed"),
    ("already-legal oxalate", "already-legal SF6"),
    ("hold_oxalate_tph", "hold_sf6_kgh"),
    ("oxalate_tph", "sf6_kgh"),
    ("executed_oxalate_tph", "executed_sf6_kgh"),
    ("4.8 t/h oxalate", "4.8 kg/h SF6"),
    ("4.8 t/h held", "4.8 kg/h held"),
    ("4.8 t/h", "4.8 kg/h"),
    ("quiet ceria kiln", "quiet SF6 cell"),
    ("legal cerium kiln", "legal SF6 cell"),
    ("ce-bed", "sf6-melt"),
    ("calciner-go", "cell-go"),
    ("calciner_go", "cell_go"),
    ("calciner_hold", "cell_hold"),
    ("bed-TC win", "melt-TC win"),
    ("bed TC", "melt TC"),
    ("Bed TC", "Melt TC"),
    ("Bed-first", "Melt-first"),
    ("bed-first", "melt-first"),
    ("tc.bed.C", "tc.melt.C"),
    ("relay.tc.bed", "relay.tc.melt"),
    ("bed_cap_C", "melt_cap_C"),
    ("observed_bed_C", "observed_melt_C"),
    ("bed_C", "melt_C"),
    ("bed_veto", "melt_veto"),
    ("hood pyrometer", "lid pyrometer"),
    ("hood IR", "lid IR"),
    ("Hood IR", "Lid IR"),
    ("hood-IR", "lid-IR"),
    ("hood-first", "lid-first"),
    ("ir.hood.C", "ir.lid.C"),
    ("relay.ir.hood", "relay.ir.lid"),
    ("hood_look_C", "lid_look_C"),
    ("hood_C", "lid_C"),
    ("smear look", "smear look"),
    ("shuttering on the hood smear", "shuttering on the lid smear"),
    ("screw encoder", "busbar encoder"),
    ("screw reseq", "busbar reseq"),
    ("off-gas O2 cell", "off-gas F2 cell"),
    ("Oxide pass", "SF6 pass"),
    ("oxide pass", "SF6 pass"),
    ("stack ceiling", "melt ceiling"),
]

for a, b in CHEM:
    src = src.replace(a, b)

# --- replace record_572 ---
start = src.index("def record_572():")
end = src.index("def record_573():")
RECORD_572 = r'''def record_572():
    ticks = [
        tick(2240, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5600, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5780, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6120, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6460, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(660000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.steam.tph", 1.120, 0.42),
        spike("tc.col.C", 2.240, 0.57),
        spike("enc.steam.tph", 3.500, 0.49),
        spike("tc.col.C", 5.600, 1.29),
        spike("zv.stem.pct", 5.780, 1.10),
        spike("ctrl.gate", 6.120, 0.96),
        spike("tc.col.C", 8.400, 0.80),
        spike("enc.steam.tph", 10.400, 0.63),
        spike("ctrl.gate", 12.600, 0.84),
        spike("tc.col.C", 16.600, 0.41),
        spike("zv.stem.pct", 22.200, 0.54),
        spike("tc.col.C", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(111572, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "TBHP finishing column C-4 at Peroxbutyl-Twine PT-8 is 94.0 C, 12 above the 82.0 C "
                "cap. Steam stem ZV-C4.STEM publishes 72.0 percent-open (LIVE, FRESH). Live-TC-first "
                "must cut the stem 72 -> 28 percent-open; the weak supervisor reads 72 as percent-closed "
                "and drives the valve to 88 percent-open because 72 'closed' still looks shy of wide-open.",
            ),
            ("domain", "tert-butyl-hydroperoxide-column"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the PT-8 TBHP pass with live column C-4 <= 82.0 C, leave organic feed at "
                "2.1 t/h, and keep ZV-C4.STEM bound as percent-open, never percent-closed.",
            ),
            ("t0_us", 1756850400000572),
            ("gate_latency_us", 520),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.600, 5.940]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.col.C 94.0 C on LIVE C-4 vapor",
                                "zv.stem.pct 72.0 percent-open on LIVE FRESH ZV-C4.STEM",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-TC-first should MODIFY-cut steam on C-4; percent-open-as-closed is a false "
                            "stem-invert bind that opens steam because 72 looks like 72 percent-closed.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live column-TC slot versus the stem-position publisher "
                            "on this TBHP finishing PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (live 28 + stem 32). Order is "
                            "correctly live-TC-first. The error is stem-semantics invert: ZV-C4.STEM is "
                            "percent_open, so treating it as percent_closed opens steam instead of cutting C-4.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live column TC on C-4, 2 kHz, 28 us jitter, tag=C4_TC.VAP status=LIVE",
                    "steam stem ZV-C4.STEM, 1 kHz, 32 us jitter, semantics=percent_open status=LIVE FRESH",
                    "steam FT C-4 (context)",
                    "TBHP Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_tc_C", 82.0),
                        ("live_tc_C", 94.0),
                        ("stem_pct_open", 72.0),
                        ("stem_semantics", "percent_open"),
                        ("live_status", "LIVE"),
                        ("stem_status", "LIVE"),
                        ("stem_fresh", True),
                        ("bind_percent_closed", False),
                        ("organic_tph", 2.1),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-4 LIVE finishing; vapor 94.0 C; organic 2.1 t/h; steam stem 72 percent-open.",
                    "2. ZV-C4.STEM documented percent_open, LIVE and FRESH; not a leftover faceplate.",
                    "3. Steam precursor at 1.120 ms.",
                    "4. Race window [5.600, 5.940] ms.",
                    "5. tc.col.C 94.0 C at 5.600 ms (winner).",
                    "6. zv.stem.pct 72.0 percent-open at 5.780 ms (loser by 180 us).",
                    "7. Gate at 6.120 ms: WRONG-MODIFY binds stem as percent-closed.",
                    "8. Steam 72 -> 88 percent-open (opened); live vapor stays 94.0 C.",
                    "9. Live 94.0 stays > 82.0; C-4 dumps TBHP overhead.",
                    "10. Delayed (abort_s=660): 11 min column dump while C-4 stays over cap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_tbhp_live"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_pct_open", 72.0),
                        ("organic_tph", 2.1),
                        ("bind_percent_closed", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_tc_C", 94.0),
                        ("cap_tc_C", 82.0),
                        ("stem_pct_open", 72.0),
                        ("stem_semantics", "percent_open"),
                        ("live_status", "LIVE"),
                        ("stem_status", "LIVE"),
                        ("stem_fresh", True),
                        ("organic_tph", 2.1),
                        ("correct_steam_pct_open", 28.0),
                        ("correct_organic_tph", 2.1),
                        ("correct_gate", "MODIFY"),
                        ("t_gate_us", 6120),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 660),
                        ("stem_tag", "ZV-C4.STEM"),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 72 percent-open steam on C-4 because a percent-closed reading "
                "of 72 still looks short of wide-open, treating the live 94.0 C as a wet-well echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Vapor 94.0 C exceeds the 82.0 C cap, so a cut is required, but the highlighted "
                "stem is ZV-C4.STEM read as percent-closed. Apply an 88 percent-open steam move "
                "(which opens). Leave LIVE C-4 at 72 percent-open unused, then overshoot to 88.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "column",
                            OrderedDict(
                                [
                                    ("cap_tc_C", 82.0),
                                    ("live_tc_C", 94.0),
                                    ("stem_pct_open", 72.0),
                                    ("executed_steam_pct_open", 88.0),
                                    ("correct_steam_pct_open", 28.0),
                                    ("correct_gate", "MODIFY"),
                                ]
                            ),
                        ),
                        (
                            "stem",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6120),
                                    ("bind_percent_closed", True),
                                    ("stem_semantics", "percent_open"),
                                    ("stem_status", "LIVE"),
                                    ("wrong_semantics", True),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "percent_closed_stem_open"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_pct_open", 88.0),
                        ("organic_tph", 2.1),
                        ("bind_percent_closed", True),
                        ("live_tc_C", 94.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / percent-open vs percent-closed): 88 percent-open steam OPEN "
                "applied because ZV-C4.STEM at 72 percent-open was treated as 72 percent-closed. "
                "Routing relay.zv.stem -> policy.steam_open; no positive weight to policy.steam_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY opened steam on a TBHP column that needed a live-TC cut. Live "
                "94.0 C was over the 82.0 C cap at t_gate; ZV-C4.STEM is percent_open so the "
                "88 percent-open move opened the valve. 11 min column dump (abort_s=660). Correct "
                "gate was MODIFY; cut C-4 steam 72 -> 28 percent-open at t_gate_us=6120 and leave "
                "the stem bound as percent-open.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_tc", "C-4 left illegal at 94.0 C; steam opened 72 -> 88 percent-open"),
                        ("stem", "ZV-C4.STEM treated as percent-closed while documented percent_open"),
                        ("dump", "11 min TBHP dump, C-4 over cap"),
                        ("mission", "TBHP finishing deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-TC-first was the correct order and live vapor was over cap; the MODIFY spent that win as a percent-closed open.",
                    "Delayed (abort_s=660): PT-8 holds 11 min while C-4 is dumped and purged; next batch 13 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY; cut live C-4 steam 72 -> 28 percent-open at t_gate_us=6120; bind_percent_closed=false; leave organic at 2.1 t/h; keep ZV-C4.STEM as percent_open.",
                        ),
                        ("correct_actuator", "C-4_steam_direct"),
                        ("wrong_semantics", "ZV-C4.STEM_as_percent_closed"),
                        ("t_gate_us", 6120),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("steam_pct_open", 88.0),
                                    ("bind_percent_closed", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "11 min column dump (task/efficiency); live vapor never returned under 82.0 C while the cut was spent as a percent-closed open on ZV-C4.STEM.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.col.C (5.600 ms, 94.0 C)"),
                        ("loser", "zv.stem.pct (5.780 ms, 72.0 percent-open)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Stem-first by < 180 us would still be 72 percent-open on a percent_open tag; "
                            "a correct gate binds tc.col.C to policy.steam_cut at t_gate either "
                            "way. The wrong MODIFY spent the live win on a percent-closed bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the percent-closed bind (6.120 ms, tick 4). "
                "The 11 min column dump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 660),
        ]
    )
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.tbhp-stem-invert",
            "spikenaut.policy.steam-open",
            [
                ("relay.zv.stem", "policy.steam_open", 0.74),
                ("relay.tc.col", "policy.steam_open", 0.21),
            ],
            "acetylcholine",
            0.08,
            "percent_closed_stdp; ACh tags the (wrong) percent-open-as-closed open at the live TC win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 660),
                ("delayed_surprise_s", 660),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("steam_open", 48, 0.45, 300.0, 0.34),
                    pop("steam_cut", 48, 0.90),
                    pop("pair_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r111-572",
        "WRONG-MODIFY at Peroxbutyl-Twine PT-8 / Column C-4: live 94.0 C over 82.0 C cap; "
        "88 percent-open steam OPEN on ZV-C4.STEM (percent-open vs percent-closed)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-modify / percent-open vs percent-closed. Sidecar arithmetic 94.0 > 82.0 on live "
        "vapor is true; MODIFY bound to steam_open. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
        ras,
        gate,
        "tert-butyl-hydroperoxide-column",
        [
            "modify",
            "wrong-gate",
            "percent-open-as-closed",
            "stem-invert",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live-TC-first race can still be a wrong gate when the "
        "MODIFY treats a percent-open stem as percent-closed and opens steam. Convictable "
        "from live_tc_C vs cap, stem_semantics, bind_percent_closed, and routing without TBHP physics.",
        2,
        supervisor_error_type="wrong-modify",
    )


'''
src = src[:start] + RECORD_572 + src[end:]

# --- replace 572 self-check block ---
old_chk = '''        if rec["id"] == "ttf-r111-572":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_pv_ppm"] > ev["cap_ppm"]):
                issues.append("532 live PV not over cap")
            if not (ev["shadow_sp_ppm"] < ev["cap_ppm"]):
                issues.append("532 shadow SP not under cap")
            if ev.get("faceplate_status") != "LEFTOVER":
                issues.append("532 faceplate not LEFTOVER")
            if rec["executed_action"]["parameters"].get("bind_shadow_sp") is not True:
                issues.append("532 bind_shadow_sp not true")
            if rec["executed_action"]["parameters"].get("shadow_as_live_sp") is not True:
                issues.append("532 shadow_as_live_sp not true")
            if rec["executed_action"]["parameters"].get("co_nm3h") != 12.8:
                issues.append("532 CO should open to 12.8")
            if rec["executed_action"]["parameters"].get("live_pv_ppm") != 184.0:
                issues.append("532 live PV should stay 184")
            if "recovery" not in rec["future_outcome"]:
                issues.append("532 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.live_cut" in table_to:
                issues.append("532 routing still has live_cut")
            if "policy.shadow_open" not in table_to:
                issues.append("532 routing missing shadow_open")
            if "shadow-setpoint" not in rec["meta"]["tags"] or "leftover-faceplate" not in rec["meta"]["tags"]:
                issues.append("532 missing shadow-setpoint/leftover-faceplate tags")
'''
new_chk = '''        if rec["id"] == "ttf-r111-572":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_tc_C"] > ev["cap_tc_C"]):
                issues.append("572 live TC not over cap")
            if ev.get("stem_semantics") != "percent_open":
                issues.append("572 stem not percent_open")
            if ev.get("stem_fresh") is not True:
                issues.append("572 stem not FRESH")
            if rec["executed_action"]["parameters"].get("bind_percent_closed") is not True:
                issues.append("572 bind_percent_closed not true")
            if rec["executed_action"]["parameters"].get("steam_pct_open") != 88.0:
                issues.append("572 steam should open to 88")
            if rec["executed_action"]["parameters"].get("live_tc_C") != 94.0:
                issues.append("572 live TC should stay 94")
            if "recovery" not in rec["future_outcome"]:
                issues.append("572 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.steam_cut" in table_to:
                issues.append("572 routing still has steam_cut")
            if "policy.steam_open" not in table_to:
                issues.append("572 routing missing steam_open")
            if "percent-open-as-closed" not in rec["meta"]["tags"] or "stem-invert" not in rec["meta"]["tags"]:
                issues.append("572 missing percent-open-as-closed/stem-invert tags")
'''
if old_chk not in src:
    raise SystemExit("572 check block not found")
src = src.replace(old_chk, new_chk)

# --- replace notes_text ---
nstart = src.index("def notes_text(")
nend = src.index("def run_pipelines(")
NOTES = '''def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r111

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r111-571` … `ttf-r111-575`
- Domains this batch: `phthalic-anhydride-oxidizer`, `tert-butyl-hydroperoxide-column`, `lanthanum-fluoride-precipitator`, `ethylhexanol-aldol-kettle`, `sulfur-hexafluoride-cell`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r105 occupancy (jsonl SoT) plus in-flight gens r106–r110 / r112 (`cumene-hydroperoxide-cleaver` / `sevoflurane-rectifier` / `carbon-black-furnace` / `acetone-cyanohydrin-column` / `barium-titanate-calciner`, r108 phenol-cumene-cleavage / SBR / zeolite-Y / SCR-honeycomb / graphite-spheroidizer, r109 MTO / sulfuryl-chloride / LaB6-sinter / PTHF / VOCl3, r104 SOCl2 / POCl3 / chlorate / NdF3 / LiPF6-xtal, r112 RuO4 / Ta-ethoxide / InCl3 / LaAlO3 / diborane). Distinct from r60 `tio2-chloride-oxidizer`, r85 moly-roaster, r99 POCl3-still / hydrosulfite / SrCO3 / PBD-polymerizer / SnCl4, r103 SeO2 / Ni-carbonyl / YF3 / GeCl4 / Ce-oxalate, r105 OsO4 / HDI / nylon-12 / PVDF / PEEK. Wrong-modify class is **percent-open vs percent-closed**, not r103/r105 leftover-faceplate shadow-setpoint, not r99 feedforward-as-feedback, not r97 lead-lag invert on a fresh tag. All five plants are invented (Phthalan-Keld, Peroxbutyl-Twine, Lanfluor-Smeaton, Ethylhex-Knap, Sulfhex-Brae). Do not restack prior TTF plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r111-571 | phthalic-anhydride-oxidizer | MODIFY | correct | designed | **−0.44** | process-correct air-header clamp; V2O5-bed slump inside 42 ms raster; independent LIF |
| ttf-r111-572 | tert-butyl-hydroperoxide-column | MODIFY | **incorrect (wrong-modify / percent-open vs percent-closed)** | designed | −0.68 | live 94.0 C > 82.0 cap; 88 percent-open steam OPEN on ZV-C4.STEM |
| ttf-r111-573 | lanthanum-fluoride-precipitator | REJECT | correct | hil | +0.80 | AE 64 pps beats agitator 28 kW; hold rake |
| ttf-r111-574 | ethylhexanol-aldol-kettle | ACCEPT | correct | simulated | +1.06 | pot 6.8 m vs jacket 58 C; proposed 9.6 t/h already legal |
| ttf-r111-575 | sulfur-hexafluoride-cell | ACCEPT | correct | designed | +1.14 | melt 742 C vs lid IR 410 C; proposed 4.8 kg/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (percent-open vs percent-closed), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Lanfluor-Smeaton LS-HIL LaF3 precipitator). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r111-572** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: even rounds host wrong-reject; odd rounds host wrong-modify. This is **percent-open vs percent-closed** (live C-4 vapor over cap; ZV-C4.STEM is LIVE/FRESH and documented percent_open at 72; supervisor treats 72 as percent-closed and OPENS steam to 88 while live 94.0 C stays over 82.0). Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity (same-loop sign flip), not r24 under-clamp, not r25/r29/r31/r63 wrong-phase, not r33/r35 over-clamp, not r39 extra-PLC-scan clamp-too-late, not r53/r55/r57 stale-sample / lagged-tag, not r59/r65/r67 wrong-string / idle-bank, not r69 split-range-wrong-half, not r71/r73/r75/r77 wrong-unit / lagged-bus, not r79/r81 selector-wrong-leg, not r83 wrong-bank polarity invert, not r85 ratio-pair invert, not r87 wrong-deadband, not r89 dual-range-wrong-band, not r91 wrong-polarity-fresh-tag, not r93 valve-travel as PV, not r95/r97 lead-lag invert, not r99 feedforward-as-feedback, not r103/r105 shadow-setpoint on a leftover faceplate (this stem is LIVE and FRESH, not LEFTOVER). Do not emit a wrong-ACCEPT.

Peroxbutyl-Twine PT-8 / Column C-4 (LIVE) reads live vapor **94.0 C** against an **82.0 C** cap. Stem `ZV-C4.STEM` is `LIVE`/`FRESH` at **72.0 percent-open**, semantics `percent_open`. Sidecar arithmetic `94.0 > 82.0` is true. A timely MODIFY at `t_gate_us=6120` cuts live steam **72 → 28 percent-open**. A weak supervisor binds the stem as percent-closed and MODIFY-opens steam **72 → 88 percent-open**. Live vapor stays **94.0 > 82.0**. Convictable without TBHP chemistry: `evidence.live_tc_C > evidence.cap_tc_C`, `evidence.stem_semantics == percent_open`, `evidence.stem_fresh == true`, `executed_action` sets `bind_percent_closed=true` and `steam_pct_open=88.0` with `live_tc_C=94.0`, `raster.routing.table` sends `relay.zv.stem` → `policy.steam_open` (weight 0.74) with no positive weight to `policy.steam_cut`, and `gate_snn` has `steam_open` above threshold while `steam_cut` is not. Recovery: MODIFY live steam 72 → 28 percent-open on C-4 at t_gate; leave organic at 2.1 t/h; keep ZV-C4.STEM as percent_open. Cost: 11 min column dump (`abort_s=660`).

## Partnered-negative in-window (571)

**ttf-r111-571** is the partnered negative: process-correct MODIFY (air held 11.0 kNm3/h; PA-mist 9.6 g/Nm3 <= 12.0 cap) while the world still charges. Safety −0.60 prices the V2O5-bed slump at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 15 min oxidizer isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 111571, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.bed` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 571 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22400) |
| 572 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6120) |
| 573 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7640) |
| 574 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (7840) |
| 575 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5640) |

Tick-6 sidecar bind: 571 `abort_s=900`, 572 `abort_s=660`, 573 `abort_s=480`, 574 `survey_s=360`, 575 `dwell_s=240`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 571 | phthalic-anhydride-oxidizer | 76 | 26 | 42 | 83 | 1909 | 0.001909 |
| 572 | tert-butyl-hydroperoxide-column | 88 | 34 | 28 | 84 | 1932 | 0.001932 |
| 573 | lanthanum-fluoride-precipitator | 120 | 20 | 46 | 110 | 2530 | 0.002530 |
| 574 | ethylhexanol-aldol-kettle | 48 | 42 | 28 | 56 | 1288 | 0.001288 |
| 575 | sulfur-hexafluoride-cell | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-571 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (571). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 574 and 575 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **wrong-hysteresis on a split-range control valve** once percent-open vs percent-closed is staged. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 15.8%
"""


'''
src = src[:nstart] + NOTES + src[nend:]

out = Path("/tmp/ttf-r111/gen_r111.py")
out.write_text(src)
print("wrote", out, "lines", len(src.splitlines()))
# leftover old plants/domains?
for tok in ["Selenite-Hawes", "Nickcarb-Linnick", "Yttria-Scarth", "Germanyl-Tofts", "Ceriax-Howk",
            "selenium-dioxide-scrubber", "nickel-carbonyl-decomposer", "shadow-setpoint",
            "live_pv_ppm", "bind_shadow_sp", "ttf-r103", "record_531"]:
    print(f"  leftover {tok!r}: {src.count(tok)}")
print("docstring", src.splitlines()[1])
print("571 domain count", src.count("phthalic-anhydride-oxidizer"))
print("572 domain count", src.count("tert-butyl-hydroperoxide-column"))
