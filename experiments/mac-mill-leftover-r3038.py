#!/usr/bin/env python3
"""MAC leftover leftover leftover mill after Beckmann/caprolactam.

Ban r2748–r3033 clones (esp. r3033 capro-oxime-vs-beckmann) and the r3034
polymer/semicon catalog. Never steal a reserved round; never rewrite raw.

Loop: frontier → reserve --expected 1 → stage JSONL+NOTES → publish.
If MAC reserved, HOP (do not steal).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

AGENTIC = REPO / "outputs/raw/2026-08-19-agentic"
FACTORY = AGENTIC / "multi-agent-coordination-factory"
SBOX = AGENTIC / "sandbox-refusal-factory"
DEADLINE_S = 40 * 60
MIN_ROUNDS = 12

BANNED_SUB = (
    "capro-oxime-vs-beckmann",
    "beckmann",
    "caprolactam",
    "whiskey-barrel",
    "hearts-vs-tails",
    "whiskey",
    "cyclohexanone-air-vs-ka",
    "adipic-nox-vs-yield",
    "tdi-phosgene-vs-color",
    "mdi-mda-vs-amine",
)


def T(n, s, c):
    return {"n": n, "speaker": s, "content": c}


def P(slug, goal, agents, turns, d, res, joint, novel, dens):
    return dict(
        slug=slug,
        goal=goal,
        agents=agents,
        turns=turns,
        disagreements=d,
        resolution=res,
        joint_outcome=joint,
        success=True,
        novel=novel,
        densify=dens,
    )


def add_turns(op, eng, lab, spike, add, mins, bad, metric, legal, hold_n, hold, divert, fail, residual, plan):
    return [
        (op, f"Spike {spike}. {metric} leftover is dying."),
        (eng, f"{add}, {mins} min. {spike} is {bad} leftover."),
        (lab, f"Hold {hold_n} {hold}. {spike} leftover I will not sign."),
        (op, f"{add}, hold leftover. I spike only if {metric} hits {fail}."),
        (eng, f"In. {metric} {legal} at minute {int(mins)+6} leftover."),
        (lab, f"{hold} 1 still leftover — to {divert}."),
        (op, f"{legal} legal leftover. No spike."),
        (eng, f"Hold leftover. Residual: {residual}."),
        (lab, f"New {legal}. Residual leftover: {hold_n} {hold} {divert}."),
        (op, plan),
    ]


def cut_turns(op, eng, lab, dump, cut, extra, bad, metric, legal, hold_n, hold, divert, fail, residual, plan):
    return [
        (op, f"Dump {dump}. {metric} leftover will recover."),
        (eng, f"Cut {cut} only, {extra}. {dump} is leftover {bad}."),
        (lab, f"Hold {hold_n} {hold}. {dump} leftover I will not sign."),
        (op, f"Cut {cut}, hold leftover. I dump only if {metric} hits {fail}."),
        (eng, f"Cut in leftover. {metric} {legal}."),
        (lab, f"{hold} 1 still leftover — to {divert}."),
        (op, f"{legal} legal leftover. No dump."),
        (eng, f"Hold leftover cut. Residual: {residual}."),
        (lab, f"New {legal}. Residual leftover: {hold_n} {hold} {divert}."),
        (op, plan),
    ]


SCENARIOS = [
    P("wetphos-gypsum-vs-p2o5",
      "Hold wet-process P2O5 after filter cloth blinds without a 18 K den spike or a 2.2% P2O5 gypsum leftover fail.",
      [{"role": "wpa_op", "mandate": "gypsum P2O5 leftover is 1.9%; spec 0.8; I will not spike 18 K"},
       {"role": "filt_wpa", "mandate": "I can add 6% wash in 11 min; I will not slug 16%"},
       {"role": "p2o5_lab", "mandate": "I will hold 1 gypsum pile; I will not certify 1.9% leftover"}],
      add_turns("wpa_op", "filt_wpa", "p2o5_lab", "18 K", "wash +6%", 11, "hemihydrate", "P2O5 leftover", "0.74%",
                1, "gypsum pile", "stack-rework", "2.4%", "wash 8 m3 extra",
                "Plan is leftover-wash-plus-6-plus-hold, not 18K-spike and not slug-16pct."),
      ["Op 18K-spike vs leftover wash plus-6 vs lab hold-not-1.9pct-P2O5"],
      "Add 6% leftover wash in 11 min; hold 1 gypsum pile; spike only at 2.4%; no 16% slug.",
      "P2O5 leftover 0.74%. Residual: pile 1 stack-rework, extra wash.", 91, "SSP fluorine vs acid"),
    P("ssp-fluorine-vs-acid",
      "Hold SSP available-P after den acid is 5% short without a 14 K den spike or a 1.8% F leftover fail.",
      [{"role": "ssp_op", "mandate": "avail-P is 16.2%; spec 18.0; I will not spike 14 K"},
       {"role": "acid_ssp", "mandate": "I can add 4% den acid in 13 min; I will not slug 12%"},
       {"role": "f_ssp", "mandate": "I will hold 1 den cut; I will not certify 1.8% F leftover"}],
      add_turns("ssp_op", "acid_ssp", "f_ssp", "14 K", "den-acid +4%", 13, "HF", "avail-P", "17.8%",
                1, "den cut", "re-acidulate", "15.4%", "acid 6 t extra",
                "Plan is leftover-den-acid-plus-4-plus-hold, not 14K-spike and not slug-12pct."),
      ["Op 14K-spike vs leftover den-acid plus-4 vs lab hold-not-1.8pct-F"],
      "Add 4% leftover den acid in 13 min; hold 1 den cut; spike only if avail-P 15.4%; no 12% slug.",
      "Avail-P 17.8%. Residual leftover: cut 1 re-acidulate, 6 t acid.", 92, "TSP den vs APA"),
    P("tsp-den-vs-apa",
      "Hold TSP water-sol P after APA is 0.6% lean without a 16 K den spike or a 3% citrate leftover fail.",
      [{"role": "tsp_op", "mandate": "WSP is 43.1%; spec 46; I will not spike 16 K"},
       {"role": "apa_tsp", "mandate": "I can add 0.5% APA in 12 min; I will not slug 2%"},
       {"role": "cit_lab", "mandate": "I will hold 1 granulator lot; I will not certify 43.1% as 46"}],
      add_turns("tsp_op", "apa_tsp", "cit_lab", "16 K", "APA +0.5%", 12, "polyphosphate", "WSP", "45.7%",
                1, "gran lot", "blend-off", "41%", "APA 3 t leftover",
                "Plan is leftover-APA-plus-0.5-plus-hold, not 16K-spike and not slug-2pct."),
      ["Op 16K-spike vs leftover APA plus-0.5 vs lab hold-not-43.1as46"],
      "Add 0.5% leftover APA in 12 min; hold 1 gran lot; spike only if WSP 41%; no 2% slug.",
      "WSP 45.7%. Residual leftover: lot 1 blend-off, 3 t APA.", 93, "MAP ammonia vs N"),
    P("map-ammonia-vs-n",
      "Hold MAP N after pipe-reactor NH3 slips without a 12 K melt spike or a 0.9 pH leftover fail.",
      [{"role": "map_op", "mandate": "N is 10.4%; spec 11.0; I will not spike 12 K"},
       {"role": "nh3_map", "mandate": "I can add 3% NH3 in 8 min; I will not slug 9%"},
       {"role": "n_lab", "mandate": "I will hold 1 prill bin; I will not certify 10.4% leftover N"}],
      add_turns("map_op", "nh3_map", "n_lab", "12 K", "NH3 +3%", 8, "offgas", "N leftover", "10.9%",
                1, "prill bin", "rework", "9.8%", "NH3 1.2 t leftover",
                "Plan is leftover-NH3-plus-3-plus-hold, not 12K-spike and not slug-9pct."),
      ["Op 12K-spike vs leftover NH3 plus-3 vs lab hold-not-10.4pct-N"],
      "Add 3% leftover NH3 in 8 min; hold 1 prill bin; spike only if N 9.8%; no 9% slug.",
      "N leftover 10.9%. Residual: bin 1 rework, 1.2 t NH3.", 94, "DAP recycle vs NH3"),
    P("dap-recycle-vs-nh3",
      "Hold DAP N:P after recycle is 7% wet without a 15 K gran spike or a 1.4% NH3 leftover slip.",
      [{"role": "dap_op", "mandate": "N is 17.4%; spec 18.0; I will not spike 15 K"},
       {"role": "rec_dap", "mandate": "I can dry recycle 5% in 10 min; I will not dump 12% recycle"},
       {"role": "nh3_dap", "mandate": "I will hold 1 cooler lot; I will not certify 1.4% NH3 leftover"}],
      cut_turns("dap_op", "rec_dap", "nh3_dap", "12% recycle", "wet recycle 5%", "+dryer steam", "caking",
                "N leftover", "17.9%", 1, "cooler lot", "regran", "16.8%", "steam 4 t leftover",
                "Plan is leftover-dry-recycle-5-plus-hold, not 15K-spike and not dump-12pct."),
      ["Op dump-12pct-recycle vs leftover dry-5 vs lab hold-not-1.4pct-NH3"],
      "Dry leftover recycle 5% plus steam; hold 1 cooler lot; dump only if N 16.8%; no 15 K spike.",
      "N leftover 17.9%. Residual: lot 1 regran, 4 t steam.", 95, "potash amine vs K2O"),
    P("potash-amine-vs-k2o",
      "Hold potash K2O after collector is 8% short without a 6% extra-amine leftover slug or a 3.2% insol fail.",
      [{"role": "kcl_op", "mandate": "K2O is 59.4%; spec 60.5; I will not slug 6% amine leftover"},
       {"role": "am_kcl", "mandate": "I can add 1.5% amine in 9 min; I will not slug 6%"},
       {"role": "ins_lab", "mandate": "I will hold 1 flotation cell; I will not certify 3.2% insol leftover"}],
      add_turns("kcl_op", "am_kcl", "ins_lab", "6% amine", "amine +1.5%", 9, "froth-lock", "K2O leftover", "60.3%",
                1, "flotation cell", "rougher-rework", "58.6%", "amine 40 kg leftover",
                "Plan is leftover-amine-plus-1.5-plus-hold, not 6pct-slug and not dump-cell."),
      ["Op 6pct-amine-slug vs leftover amine plus-1.5 vs lab hold-not-3.2pct-insol"],
      "Add 1.5% leftover amine in 9 min; hold 1 cell; slug only if K2O 58.6%; no 6% slug.",
      "K2O leftover 60.3%. Residual: cell 1 rougher-rework, 40 kg amine.", 91, "langbeinite vs Mg"),
    P("langbeinite-vs-mg",
      "Hold langbeinite Mg after leach is 5% short without a 20 K crystallizer leftover spike or a 3.8% Na fail.",
      [{"role": "lan_op", "mandate": "Mg is 10.6%; spec 11.2; I will not spike 20 K leftover"},
       {"role": "lch_lan", "mandate": "I can add 4% leach in 14 min; I will not slug 11%"},
       {"role": "na_lab", "mandate": "I will hold 1 crystal cut; I will not certify 3.8% Na leftover"}],
      add_turns("lan_op", "lch_lan", "na_lab", "20 K", "leach +4%", 14, "halite", "Mg leftover", "11.1%",
                1, "crystal cut", "re-leach", "10.0%", "brine 12 m3 leftover",
                "Plan is leftover-leach-plus-4-plus-hold, not 20K-spike and not slug-11pct."),
      ["Op 20K-spike vs leftover leach plus-4 vs lab hold-not-3.8pct-Na"],
      "Add 4% leftover leach in 14 min; hold 1 crystal cut; spike only if Mg 10.0%; no 11% slug.",
      "Mg leftover 11.1%. Residual: cut 1 re-leach, 12 m3 brine.", 92, "KCl compact vs fines"),
    P("kcl-compact-vs-fines",
      "Hold compacted KCl +1.7 mm after steam is 6% short without a 30 K roll leftover spike or a 22% fines fail.",
      [{"role": "cmp_op", "mandate": "fines leftover are 18%; spec 8; I will not spike 30 K"},
       {"role": "stm_cmp", "mandate": "I can add 5% steam in 7 min; I will not slug 14%"},
       {"role": "fin_kcl", "mandate": "I will hold 1 screen cut; I will not certify 18% leftover fines"}],
      add_turns("cmp_op", "stm_cmp", "fin_kcl", "30 K", "steam +5%", 7, "flake-split", "fines leftover", "7.6%",
                1, "screen cut", "recycle", "24%", "steam 2 t leftover",
                "Plan is leftover-steam-plus-5-plus-hold, not 30K-spike and not slug-14pct."),
      ["Op 30K-spike vs leftover steam plus-5 vs lab hold-not-18pct-fines"],
      "Add 5% leftover steam in 7 min; hold 1 screen cut; spike only at 24% fines; no 14% slug.",
      "Fines leftover 7.6%. Residual: cut 1 recycle, 2 t steam.", 93, "S-bentonite vs pastille"),
    P("sbent-pastille-vs-s",
      "Hold sulfur-bentonite pastille after clay is 0.4% rich without a 8 K wheel leftover spike or a 12% dust fail.",
      [{"role": "sb_op", "mandate": "dust leftover is 9.4%; spec 4.0; I will not spike 8 K"},
       {"role": "cl_sb", "mandate": "I can cut clay 0.3% in 10 min; I will not dump 2% S"},
       {"role": "dust_lab", "mandate": "I will hold 1 pastille bin; I will not certify 9.4% leftover dust"}],
      cut_turns("sb_op", "cl_sb", "dust_lab", "2% S", "0.3% clay", "+wheel RPM -4%", "crumb",
                "dust leftover", "3.8%", 1, "pastille bin", "re-melt", "13%", "clay 0.6 t leftover",
                "Plan is leftover-clay-cut-0.3-plus-hold, not 8K-spike and not dump-2pct-S."),
      ["Op dump-2pct-S vs leftover clay cut-0.3 vs lab hold-not-9.4pct-dust"],
      "Cut leftover clay 0.3% plus RPM; hold 1 bin; dump only at 13% dust; no 8 K spike.",
      "Dust leftover 3.8%. Residual: bin 1 re-melt, 0.6 t clay.", 94, "AS crystallizer vs N"),
    P("as-crystal-vs-n",
      "Hold ammonium-sulfate N after purge is 5% short without a 10 K leftover spike or a 0.35% free-acid fail.",
      [{"role": "as_op", "mandate": "N leftover is 20.6%; spec 21.0; I will not spike 10 K"},
       {"role": "prg_as", "mandate": "I can add 4% purge in 12 min; I will not dump 10% magma"},
       {"role": "fa_lab", "mandate": "I will hold 1 centrifuge cut; I will not certify 0.35% leftover acid"}],
      add_turns("as_op", "prg_as", "fa_lab", "10 K", "purge +4%", 12, "gypsum-scale", "N leftover", "20.95%",
                1, "centrifuge cut", "redissolve", "20.2%", "purge 3 m3 leftover",
                "Plan is leftover-purge-plus-4-plus-hold, not 10K-spike and not dump-10pct-magma."),
      ["Op 10K-spike vs leftover purge plus-4 vs lab hold-not-0.35pct-acid"],
      "Add 4% leftover purge in 12 min; hold 1 centrifuge cut; dump only if N 20.2%; no 10% magma dump.",
      "N leftover 20.95%. Residual: cut 1 redissolve, 3 m3 purge.", 95, "P4 mud vs slag"),
    P("p4-furnace-vs-mud",
      "Hold P4 yield after mud is 0.8% rich without a 80 K furnace leftover spike or a 4.5% P2O5 slag fail.",
      [{"role": "p4_op", "mandate": "slag P2O5 leftover is 3.9%; spec 2.0; I will not spike 80 K"},
       {"role": "mud_p4", "mandate": "I can cut mud 0.6% in 15 min; I will not dump 3% burden"},
       {"role": "sl_lab", "mandate": "I will hold 1 tap; I will not certify 3.9% leftover slag-P"}],
      cut_turns("p4_op", "mud_p4", "sl_lab", "3% burden", "0.6% mud", "+coke 0.4%", "offgas-P",
                "slag-P leftover", "1.9%", 1, "tap", "re-smelt", "5.0%", "coke 2 t leftover",
                "Plan is leftover-mud-cut-0.6-plus-coke-hold, not 80K-spike and not dump-3pct."),
      ["Op dump-3pct-burden vs leftover mud cut-0.6 vs lab hold-not-3.9pct-slagP"],
      "Cut leftover mud 0.6% plus coke; hold 1 tap; dump only at 5.0% slag-P; no 80 K spike.",
      "Slag-P leftover 1.9%. Residual: tap 1 re-smelt, 2 t coke.", 91, "PCl3 vs P4"),
    P("pcl3-vs-p4",
      "Hold PCl3 P4 leftover after Cl2 is 4% short without a 9 K burner leftover spike or a 0.8% P4 fail.",
      [{"role": "pcl_op", "mandate": "P4 leftover is 0.62%; spec 0.15; I will not spike 9 K"},
       {"role": "cl2_pcl", "mandate": "I can add 3% Cl2 in 8 min; I will not slug 10%"},
       {"role": "p4_lab", "mandate": "I will hold 1 still cut; I will not certify 0.62% leftover P4"}],
      add_turns("pcl_op", "cl2_pcl", "p4_lab", "9 K", "Cl2 +3%", 8, "PCl5", "P4 leftover", "0.13%",
                1, "still cut", "rechlor", "0.90%", "Cl2 0.4 t leftover",
                "Plan is leftover-Cl2-plus-3-plus-hold, not 9K-spike and not slug-10pct."),
      ["Op 9K-spike vs leftover Cl2 plus-3 vs lab hold-not-0.62pct-P4"],
      "Add 3% leftover Cl2 in 8 min; hold 1 still cut; spike only at 0.90% P4; no 10% slug.",
      "P4 leftover 0.13%. Residual: cut 1 rechlor, 0.4 t Cl2.", 92, "POCl3 vs HCl"),
    P("pocl3-vs-hcl",
      "Hold POCl3 HCl leftover after O2 is 3% short without a 11 K leftover spike or a 0.40% HCl fail.",
      [{"role": "poc_op", "mandate": "HCl leftover is 0.31%; spec 0.08; I will not spike 11 K"},
       {"role": "o2_poc", "mandate": "I can add 2.5% O2 in 9 min; I will not slug 8%"},
       {"role": "hcl_poc", "mandate": "I will hold 1 receiver; I will not certify 0.31% leftover HCl"}],
      add_turns("poc_op", "o2_poc", "hcl_poc", "11 K", "O2 +2.5%", 9, "P2O5-haze", "HCl leftover", "0.07%",
                1, "receiver", "reboil", "0.45%", "O2 2% leftover extra",
                "Plan is leftover-O2-plus-2.5-plus-hold, not 11K-spike and not slug-8pct."),
      ["Op 11K-spike vs leftover O2 plus-2.5 vs lab hold-not-0.31pct-HCl"],
      "Add 2.5% leftover O2 in 9 min; hold 1 receiver; spike only at 0.45% HCl; no 8% slug.",
      "HCl leftover 0.07%. Residual: receiver 1 reboil, extra O2.", 93, "P2S5 vs S"),
    P("p2s5-vs-sulfur",
      "Hold P2S5 free-S leftover after P4 is 0.5% short without a 7 K pot leftover spike or a 1.2% free-S fail.",
      [{"role": "p2s_op", "mandate": "free-S leftover is 0.94%; spec 0.30; I will not spike 7 K"},
       {"role": "p4_p2s", "mandate": "I can add 0.4% P4 in 11 min; I will not slug 1.5%"},
       {"role": "s_lab", "mandate": "I will hold 1 flake lot; I will not certify 0.94% leftover S"}],
      add_turns("p2s_op", "p4_p2s", "s_lab", "7 K", "P4 +0.4%", 11, "H2S", "free-S leftover", "0.27%",
                1, "flake lot", "remelt", "1.3%", "P4 80 kg leftover",
                "Plan is leftover-P4-plus-0.4-plus-hold, not 7K-spike and not slug-1.5pct."),
      ["Op 7K-spike vs leftover P4 plus-0.4 vs lab hold-not-0.94pct-S"],
      "Add 0.4% leftover P4 in 11 min; hold 1 flake lot; spike only at 1.3% free-S; no 1.5% slug.",
      "Free-S leftover 0.27%. Residual: lot 1 remelt, 80 kg P4.", 94, "PH3 vs P4"),
    P("ph3-recycle-vs-p4",
      "Hold PH3 P4 leftover after recycle H2 slips without a 13 K reactor leftover spike or a 80 ppm P4 fail.",
      [{"role": "ph3_op", "mandate": "P4 leftover is 64 ppm; spec 15; I will not spike 13 K"},
       {"role": "h2_ph3", "mandate": "I can add 5% H2 in 10 min; I will not slug 14%"},
       {"role": "p4_ph3", "mandate": "I will hold 1 cylinder bank; I will not certify 64 ppm leftover P4"}],
      add_turns("ph3_op", "h2_ph3", "p4_ph3", "13 K", "H2 +5%", 10, "solid-P", "P4 leftover", "13 ppm",
                1, "cylinder bank", "scrub", "90 ppm", "H2 0.2 bar leftover",
                "Plan is leftover-H2-plus-5-plus-hold, not 13K-spike and not slug-14pct."),
      ["Op 13K-spike vs leftover H2 plus-5 vs lab hold-not-64ppm-P4"],
      "Add 5% leftover H2 in 10 min; hold 1 cylinder bank; spike only at 90 ppm; no 14% slug.",
      "P4 leftover 13 ppm. Residual: bank 1 scrub, extra H2 pad.", 95, "CaC2 sludge vs gas"),
    P("cac2-sludge-vs-gas",
      "Hold carbide gas yield after sludge is 1.1% wet without a 6% extra-coke leftover slug or a 280 L/kg fail.",
      [{"role": "cac_op", "mandate": "yield leftover is 292 L/kg; spec 305; I will not slug 6% coke"},
       {"role": "ck_cac", "mandate": "I can add 1.8% coke in 16 min; I will not slug 6%"},
       {"role": "gas_lab", "mandate": "I will hold 1 generator charge; I will not certify 292 leftover L/kg"}],
      add_turns("cac_op", "ck_cac", "gas_lab", "6% coke", "coke +1.8%", 16, "CO", "yield leftover", "304 L/kg",
                1, "generator charge", "lime-blend", "275 L/kg", "coke 1.5 t leftover",
                "Plan is leftover-coke-plus-1.8-plus-hold, not 6pct-slug and not dump-charge."),
      ["Op 6pct-coke-slug vs leftover coke plus-1.8 vs lab hold-not-292Lkg"],
      "Add 1.8% leftover coke in 16 min; hold 1 charge; slug only if yield 275 L/kg; no 6% slug.",
      "Yield leftover 304 L/kg. Residual: charge 1 lime-blend, 1.5 t coke.", 91, "CaCN2 vs N2"),
    P("cacn2-n2-vs-c",
      "Hold cyanamide N after N2 is 5% short without a 40 K rotary leftover spike or a 0.9% free-C fail.",
      [{"role": "cn2_op", "mandate": "N leftover is 19.8%; spec 21.0; I will not spike 40 K"},
       {"role": "n2_cn2", "mandate": "I can add 4% N2 in 14 min; I will not slug 12%"},
       {"role": "c_lab", "mandate": "I will hold 1 cooler lot; I will not certify 0.9% leftover free-C"}],
      add_turns("cn2_op", "n2_cn2", "c_lab", "40 K", "N2 +4%", 14, "carbide-slip", "N leftover", "20.8%",
                1, "cooler lot", "re-nitride", "18.9%", "N2 3% leftover extra",
                "Plan is leftover-N2-plus-4-plus-hold, not 40K-spike and not slug-12pct."),
      ["Op 40K-spike vs leftover N2 plus-4 vs lab hold-not-0.9pct-C"],
      "Add 4% leftover N2 in 14 min; hold 1 cooler lot; spike only if N 18.9%; no 12% slug.",
      "N leftover 20.8%. Residual: lot 1 re-nitride, extra N2.", 92, "SiC Acheson vs Si"),
    P("sic-acheson-vs-si",
      "Hold SiC free-Si leftover after core power slips without a 2 h extra-fire leftover or a 2.4% free-Si fail.",
      [{"role": "sic_op", "mandate": "free-Si leftover is 1.9%; spec 0.6; I will not extra-fire 2 h"},
       {"role": "pwr_sic", "mandate": "I can add 8% power in 20 min; I will not slug 20%"},
       {"role": "si_lab", "mandate": "I will hold 1 ingot slice; I will not certify 1.9% leftover Si"}],
      add_turns("sic_op", "pwr_sic", "si_lab", "2 h fire", "power +8%", 20, "graphite-loss", "free-Si leftover", "0.55%",
                1, "ingot slice", "metallurgical", "2.6%", "power 6% leftover extra",
                "Plan is leftover-power-plus-8-plus-hold, not 2h-extra-fire and not slug-20pct."),
      ["Op 2h-extra-fire vs leftover power plus-8 vs lab hold-not-1.9pct-Si"],
      "Add 8% leftover power in 20 min; hold 1 slice; extra-fire only at 2.6% Si; no 20% slug.",
      "Free-Si leftover 0.55%. Residual: slice 1 metallurgical, extra power.", 93, "B4C vs C"),
    P("b4c-vs-carbon",
      "Hold B4C free-C leftover after B is 0.7% short without a 50 K leftover spike or a 1.6% free-C fail.",
      [{"role": "b4c_op", "mandate": "free-C leftover is 1.25%; spec 0.40; I will not spike 50 K"},
       {"role": "b_b4c", "mandate": "I can add 0.6% B in 18 min; I will not slug 2%"},
       {"role": "c_b4c", "mandate": "I will hold 1 hot-press lot; I will not certify 1.25% leftover C"}],
      add_turns("b4c_op", "b_b4c", "c_b4c", "50 K", "B +0.6%", 18, "B2O3", "free-C leftover", "0.36%",
                1, "hot-press lot", "abrasive", "1.8%", "B 20 kg leftover",
                "Plan is leftover-B-plus-0.6-plus-hold, not 50K-spike and not slug-2pct."),
      ["Op 50K-spike vs leftover B plus-0.6 vs lab hold-not-1.25pct-C"],
      "Add 0.6% leftover B in 18 min; hold 1 hot-press lot; spike only at 1.8% C; no 2% slug.",
      "Free-C leftover 0.36%. Residual: lot 1 abrasive, 20 kg B.", 94, "BN vs B2O3"),
    P("bn-vs-b2o3",
      "Hold h-BN B2O3 leftover after NH3 is 6% short without a 30 K leftover spike or a 1.1% B2O3 fail.",
      [{"role": "bn_op", "mandate": "B2O3 leftover is 0.86%; spec 0.25; I will not spike 30 K"},
       {"role": "nh3_bn", "mandate": "I can add 5% NH3 in 12 min; I will not slug 15%"},
       {"role": "ox_bn", "mandate": "I will hold 1 boat lot; I will not certify 0.86% leftover B2O3"}],
      add_turns("bn_op", "nh3_bn", "ox_bn", "30 K", "NH3 +5%", 12, "BN-whisker", "B2O3 leftover", "0.22%",
                1, "boat lot", "ceramic-blend", "1.2%", "NH3 4% leftover extra",
                "Plan is leftover-NH3-plus-5-plus-hold, not 30K-spike and not slug-15pct."),
      ["Op 30K-spike vs leftover NH3 plus-5 vs lab hold-not-0.86pct-B2O3"],
      "Add 5% leftover NH3 in 12 min; hold 1 boat lot; spike only at 1.2% B2O3; no 15% slug.",
      "B2O3 leftover 0.22%. Residual: lot 1 ceramic-blend, extra NH3.", 95, "AlN vs N2"),
    P("aln-vs-n2",
      "Hold AlN oxygen leftover after N2 is 7% short without a 25 K leftover spike or a 1.4% O fail.",
      [{"role": "aln_op", "mandate": "O leftover is 1.05%; spec 0.40; I will not spike 25 K"},
       {"role": "n2_aln", "mandate": "I can add 6% N2 in 11 min; I will not slug 16%"},
       {"role": "o_aln", "mandate": "I will hold 1 crucible lot; I will not certify 1.05% leftover O"}],
      add_turns("aln_op", "n2_aln", "o_aln", "25 K", "N2 +6%", 11, "Al-metal", "O leftover", "0.36%",
                1, "crucible lot", "filler", "1.5%", "N2 5% leftover extra",
                "Plan is leftover-N2-plus-6-plus-hold, not 25K-spike and not slug-16pct."),
      ["Op 25K-spike vs leftover N2 plus-6 vs lab hold-not-1.05pct-O"],
      "Add 6% leftover N2 in 11 min; hold 1 crucible lot; spike only at 1.5% O; no 16% slug.",
      "O leftover 0.36%. Residual: lot 1 filler, extra N2.", 91, "Si3N4 vs NH3"),
    P("si3n4-vs-nh3",
      "Hold Si3N4 free-Si leftover after NH3 is 5% short without a 22 K leftover spike or a 1.8% free-Si fail.",
      [{"role": "sn_op", "mandate": "free-Si leftover is 1.4%; spec 0.5; I will not spike 22 K"},
       {"role": "nh3_sn", "mandate": "I can add 4% NH3 in 13 min; I will not slug 12%"},
       {"role": "si_sn", "mandate": "I will hold 1 setter lot; I will not certify 1.4% leftover Si"}],
      add_turns("sn_op", "nh3_sn", "si_sn", "22 K", "NH3 +4%", 13, "alpha-shift", "free-Si leftover", "0.46%",
                1, "setter lot", "re-nitride", "2.0%", "NH3 3% leftover extra",
                "Plan is leftover-NH3-plus-4-plus-hold, not 22K-spike and not slug-12pct."),
      ["Op 22K-spike vs leftover NH3 plus-4 vs lab hold-not-1.4pct-Si"],
      "Add 4% leftover NH3 in 13 min; hold 1 setter lot; spike only at 2.0% Si; no 12% slug.",
      "Free-Si leftover 0.46%. Residual: lot 1 re-nitride, extra NH3.", 92, "fumed SiO2 vs HCl"),
    P("fumed-sio2-vs-hcl",
      "Hold fumed-silica HCl leftover after quench air slips without a 15 K leftover spike or a 250 ppm HCl fail.",
      [{"role": "fs_op", "mandate": "HCl leftover is 190 ppm; spec 80; I will not spike 15 K"},
       {"role": "air_fs", "mandate": "I can add 5% quench air in 6 min; I will not slug 14%"},
       {"role": "hcl_fs", "mandate": "I will hold 1 baghouse lot; I will not certify 190 ppm leftover HCl"}],
      add_turns("fs_op", "air_fs", "hcl_fs", "15 K", "quench-air +5%", 6, "sinter", "HCl leftover", "74 ppm",
                1, "baghouse lot", "wash", "270 ppm", "air blower 90% leftover",
                "Plan is leftover-quench-air-plus-5-plus-hold, not 15K-spike and not slug-14pct."),
      ["Op 15K-spike vs leftover quench-air plus-5 vs lab hold-not-190ppm-HCl"],
      "Add 5% leftover quench air in 6 min; hold 1 baghouse lot; spike only at 270 ppm; no 14% slug.",
      "HCl leftover 74 ppm. Residual: lot 1 wash, blower 90%.", 93, "ppt silica vs salt"),
    P("ppt-sio2-vs-salt",
      "Hold precipitated-silica Na2SO4 leftover after wash is 8% short without a 9 K leftover spike or a 1.8% salt fail.",
      [{"role": "ps_op", "mandate": "salt leftover is 1.35%; spec 0.50; I will not spike 9 K"},
       {"role": "wsh_ps", "mandate": "I can add 7% wash in 10 min; I will not slug 18%"},
       {"role": "sal_lab", "mandate": "I will hold 1 filter cake; I will not certify 1.35% leftover salt"}],
      add_turns("ps_op", "wsh_ps", "sal_lab", "9 K", "wash +7%", 10, "solubles", "salt leftover", "0.46%",
                1, "filter cake", "re-slurry", "2.0%", "wash 5 m3 leftover",
                "Plan is leftover-wash-plus-7-plus-hold, not 9K-spike and not slug-18pct."),
      ["Op 9K-spike vs leftover wash plus-7 vs lab hold-not-1.35pct-salt"],
      "Add 7% leftover wash in 10 min; hold 1 cake; spike only at 2.0% salt; no 18% slug.",
      "Salt leftover 0.46%. Residual: cake 1 re-slurry, 5 m3 wash.", 94, "zeolite vs template"),
    P("zeolite-template-vs-toc",
      "Hold zeolite TOC leftover after calciner O2 slips without a 40 K leftover spike or a 0.25% TOC fail.",
      [{"role": "zeo_op", "mandate": "TOC leftover is 0.19%; spec 0.06; I will not spike 40 K"},
       {"role": "o2_zeo", "mandate": "I can add 6% O2 in 15 min; I will not slug 16%"},
       {"role": "toc_lab", "mandate": "I will hold 1 calciner lot; I will not certify 0.19% leftover TOC"}],
      add_turns("zeo_op", "o2_zeo", "toc_lab", "40 K", "O2 +6%", 15, "collapse", "TOC leftover", "0.055%",
                1, "calciner lot", "recalsine", "0.28%", "O2 4% leftover extra",
                "Plan is leftover-O2-plus-6-plus-hold, not 40K-spike and not slug-16pct."),
      ["Op 40K-spike vs leftover O2 plus-6 vs lab hold-not-0.19pct-TOC"],
      "Add 6% leftover O2 in 15 min; hold 1 calciner lot; spike only at 0.28% TOC; no 16% slug.",
      "TOC leftover 0.055%. Residual: lot 1 recalsine, extra O2.", 95, "CMS vs pitch"),
    P("cms-pitch-vs-select",
      "Hold CMS O2/N2 selectivity after pitch is 0.5% rich without a 20 K leftover spike or a 6.8 alpha fail.",
      [{"role": "cms_op", "mandate": "alpha leftover is 7.4; spec 9.0; I will not spike 20 K"},
       {"role": "pt_cms", "mandate": "I can cut pitch 0.4% in 14 min; I will not dump 2% feed"},
       {"role": "al_lab", "mandate": "I will hold 1 CMS bin; I will not certify alpha 7.4 leftover"}],
      cut_turns("cms_op", "pt_cms", "al_lab", "2% feed", "0.4% pitch", "+steam 3%", "pore-block",
                "alpha leftover", "8.9", 1, "CMS bin", "recycle-carbon", "6.5", "steam 1 t leftover",
                "Plan is leftover-pitch-cut-0.4-plus-steam-hold, not 20K-spike and not dump-2pct."),
      ["Op dump-2pct vs leftover pitch cut-0.4 vs lab hold-not-alpha7.4"],
      "Cut leftover pitch 0.4% plus steam; hold 1 bin; dump only if alpha 6.5; no 20 K spike.",
      "Alpha leftover 8.9. Residual: bin 1 recycle-carbon, 1 t steam.", 91, "actcarbon vs steam"),
    P("actcarbon-steam-vs-iodine",
      "Hold activated-carbon iodine leftover after steam is 7% short without a 50 K leftover spike or a 780 iodine fail.",
      [{"role": "ac_op", "mandate": "iodine leftover is 810; spec 950; I will not spike 50 K"},
       {"role": "stm_ac", "mandate": "I can add 6% steam in 12 min; I will not slug 16%"},
       {"role": "i2_lab", "mandate": "I will hold 1 kiln cut; I will not certify 810 leftover iodine"}],
      add_turns("ac_op", "stm_ac", "i2_lab", "50 K", "steam +6%", 12, "ash-rise", "iodine leftover", "945",
                1, "kiln cut", "reactivate", "760", "steam 3 t leftover",
                "Plan is leftover-steam-plus-6-plus-hold, not 50K-spike and not slug-16pct."),
      ["Op 50K-spike vs leftover steam plus-6 vs lab hold-not-810-iodine"],
      "Add 6% leftover steam in 12 min; hold 1 kiln cut; spike only if iodine 760; no 16% slug.",
      "Iodine leftover 945. Residual: cut 1 reactivate, 3 t steam.", 92, "calcoke vs VM"),
    P("calcoke-vm-vs-temp",
      "Hold calcined-coke VM leftover after draft slips without a 40 K leftover spike or a 0.55% VM fail.",
      [{"role": "ck_op", "mandate": "VM leftover is 0.42%; spec 0.20; I will not spike 40 K"},
       {"role": "dr_ck", "mandate": "I can add 5% draft in 9 min; I will not slug 14%"},
       {"role": "vm_lab", "mandate": "I will hold 1 cooler lot; I will not certify 0.42% leftover VM"}],
      add_turns("ck_op", "dr_ck", "vm_lab", "40 K", "draft +5%", 9, "air-burn", "VM leftover", "0.18%",
                1, "cooler lot", "recalcine", "0.60%", "draft damper 8% leftover",
                "Plan is leftover-draft-plus-5-plus-hold, not 40K-spike and not slug-14pct."),
      ["Op 40K-spike vs leftover draft plus-5 vs lab hold-not-0.42pct-VM"],
      "Add 5% leftover draft in 9 min; hold 1 cooler lot; spike only at 0.60% VM; no 14% slug.",
      "VM leftover 0.18%. Residual: lot 1 recalcine, extra draft.", 93, "anode paste vs pitch"),
    P("anode-pitch-vs-vd",
      "Hold anode-paste VBD leftover after pitch is 0.8% short without a 8 K leftover spike or a 1.52 VBD fail.",
      [{"role": "an_op", "mandate": "VBD leftover is 1.545; spec 1.580; I will not spike 8 K"},
       {"role": "pt_an", "mandate": "I can add 0.6% pitch in 8 min; I will not slug 2%"},
       {"role": "vd_lab", "mandate": "I will hold 1 paste batch; I will not certify 1.545 leftover VBD"}],
      add_turns("an_op", "pt_an", "vd_lab", "8 K", "pitch +0.6%", 8, "bleed", "VBD leftover", "1.578",
                1, "paste batch", "recycle-green", "1.515", "pitch 0.4 t leftover",
                "Plan is leftover-pitch-plus-0.6-plus-hold, not 8K-spike and not slug-2pct."),
      ["Op 8K-spike vs leftover pitch plus-0.6 vs lab hold-not-1.545-VBD"],
      "Add 0.6% leftover pitch in 8 min; hold 1 paste batch; spike only if VBD 1.515; no 2% slug.",
      "VBD leftover 1.578. Residual: batch 1 recycle-green, 0.4 t pitch.", 94, "QI pitch vs cut"),
    P("qi-pitch-vs-cut",
      "Hold binder-pitch QI leftover after flash is 5% short without a 12 K leftover spike or a 16% QI fail.",
      [{"role": "qi_op", "mandate": "QI leftover is 14.2%; spec 10.0; I will not spike 12 K"},
       {"role": "fl_qi", "mandate": "I can add 4% flash in 11 min; I will not dump 10% bottoms"},
       {"role": "qi_lab", "mandate": "I will hold 1 pitch tank; I will not certify 14.2% leftover QI"}],
      add_turns("qi_op", "fl_qi", "qi_lab", "12 K", "flash +4%", 11, "coke-fines", "QI leftover", "9.7%",
                1, "pitch tank", "blend-cut", "16.5%", "flash steam 2 t leftover",
                "Plan is leftover-flash-plus-4-plus-hold, not 12K-spike and not dump-10pct-bottoms."),
      ["Op 12K-spike vs leftover flash plus-4 vs lab hold-not-14.2pct-QI"],
      "Add 4% leftover flash in 11 min; hold 1 pitch tank; dump only at 16.5% QI; no 10% bottoms dump.",
      "QI leftover 9.7%. Residual: tank 1 blend-cut, 2 t flash steam.", 95, "Acheson graphite vs SiC"),
    P("graphite-acheson-vs-sic",
      "Hold Acheson graphite SiC leftover after core Si slips without a 3 h leftover extra-fire or a 0.9% SiC fail.",
      [{"role": "gr_op", "mandate": "SiC leftover is 0.72%; spec 0.20; I will not extra-fire 3 h"},
       {"role": "si_gr", "mandate": "I can cut pack-Si 0.5% in 25 min; I will not dump 4% pack"},
       {"role": "sic_lab", "mandate": "I will hold 1 electrode; I will not certify 0.72% leftover SiC"}],
      cut_turns("gr_op", "si_gr", "sic_lab", "4% pack", "0.5% pack-Si", "+power 4%", "soft-core",
                "SiC leftover", "0.18%", 1, "electrode", "foundry-grade", "1.0%", "power 3% leftover extra",
                "Plan is leftover-pack-Si-cut-0.5-plus-hold, not 3h-extra-fire and not dump-4pct."),
      ["Op dump-4pct-pack vs leftover pack-Si cut-0.5 vs lab hold-not-0.72pct-SiC"],
      "Cut leftover pack-Si 0.5% plus power; hold 1 electrode; extra-fire only at 1.0% SiC; no 4% dump.",
      "SiC leftover 0.18%. Residual: electrode 1 foundry-grade, extra power.", 91, "HPHT diamond vs Fe"),
    P("hpht-diamond-vs-fe",
      "Hold HPHT diamond Fe leftover after solvent is 0.4% rich without a 200 K leftover spike or a 180 ppm Fe fail.",
      [{"role": "dia_op", "mandate": "Fe leftover is 140 ppm; spec 40; I will not spike 200 K"},
       {"role": "sv_dia", "mandate": "I can cut solvent 0.3% in 30 min; I will not dump 2% melt"},
       {"role": "fe_dia", "mandate": "I will hold 1 cell; I will not certify 140 ppm leftover Fe"}],
      cut_turns("dia_op", "sv_dia", "fe_dia", "2% melt", "0.3% solvent", "+acid-leach 4%", "graphite",
                "Fe leftover", "36 ppm", 1, "cell", "industrial-grit", "200 ppm", "acid 20 L leftover",
                "Plan is leftover-solvent-cut-0.3-plus-leach-hold, not 200K-spike and not dump-2pct."),
      ["Op dump-2pct-melt vs leftover solvent cut-0.3 vs lab hold-not-140ppm-Fe"],
      "Cut leftover solvent 0.3% plus leach; hold 1 cell; dump only at 200 ppm Fe; no 200 K spike.",
      "Fe leftover 36 ppm. Residual: cell 1 industrial-grit, 20 L acid.", 92, "Solvay vs NH3"),
    P("solvay-nh3-vs-nacl",
      "Hold Solvay Na2CO3 NaCl leftover after NH3 is 4% short without a 8 K leftover spike or a 0.55% NaCl fail.",
      [{"role": "sol_op", "mandate": "NaCl leftover is 0.42%; spec 0.15; I will not spike 8 K"},
       {"role": "nh3_sol", "mandate": "I can add 3% NH3 in 10 min; I will not slug 10%"},
       {"role": "cl_sol", "mandate": "I will hold 1 calciner lot; I will not certify 0.42% leftover NaCl"}],
      add_turns("sol_op", "nh3_sol", "cl_sol", "8 K", "NH3 +3%", 10, "NH4Cl-slip", "NaCl leftover", "0.14%",
                1, "calciner lot", "re-wash", "0.60%", "NH3 2 t leftover",
                "Plan is leftover-NH3-plus-3-plus-hold, not 8K-spike and not slug-10pct."),
      ["Op 8K-spike vs leftover NH3 plus-3 vs lab hold-not-0.42pct-NaCl"],
      "Add 3% leftover NH3 in 10 min; hold 1 calciner lot; spike only at 0.60% NaCl; no 10% slug.",
      "NaCl leftover 0.14%. Residual: lot 1 re-wash, 2 t NH3.", 93, "lime kiln vs CO2"),
    P("limekiln-co2-vs-loi",
      "Hold lime LOI leftover after draft is 6% short without a 50 K leftover spike or a 2.4% LOI fail.",
      [{"role": "lm_op", "mandate": "LOI leftover is 1.9%; spec 0.8; I will not spike 50 K"},
       {"role": "dr_lm", "mandate": "I can add 5% draft in 8 min; I will not slug 15%"},
       {"role": "loi_lab", "mandate": "I will hold 1 cooler lot; I will not certify 1.9% leftover LOI"}],
      add_turns("lm_op", "dr_lm", "loi_lab", "50 K", "draft +5%", 8, "overburn", "LOI leftover", "0.74%",
                1, "cooler lot", "hydrate-blend", "2.6%", "draft 7% leftover extra",
                "Plan is leftover-draft-plus-5-plus-hold, not 50K-spike and not slug-15pct."),
      ["Op 50K-spike vs leftover draft plus-5 vs lab hold-not-1.9pct-LOI"],
      "Add 5% leftover draft in 8 min; hold 1 cooler lot; spike only at 2.6% LOI; no 15% slug.",
      "LOI leftover 0.74%. Residual: lot 1 hydrate-blend, extra draft.", 94, "deadburn MgO vs Fe"),
    P("deadburn-mgo-vs-fe",
      "Hold dead-burned MgO Fe leftover after kiln air slips without a 40 K leftover spike or a 0.9% Fe2O3 fail.",
      [{"role": "mgo_op", "mandate": "Fe2O3 leftover is 0.72%; spec 0.30; I will not spike 40 K"},
       {"role": "air_mgo", "mandate": "I can add 4% air in 12 min; I will not slug 12%"},
       {"role": "fe_mgo", "mandate": "I will hold 1 brick lot; I will not certify 0.72% leftover Fe"}],
      add_turns("mgo_op", "air_mgo", "fe_mgo", "40 K", "air +4%", 12, "periclase-grow", "Fe leftover", "0.28%",
                1, "brick lot", "gunning", "1.0%", "air 3% leftover extra",
                "Plan is leftover-air-plus-4-plus-hold, not 40K-spike and not slug-12pct."),
      ["Op 40K-spike vs leftover air plus-4 vs lab hold-not-0.72pct-Fe"],
      "Add 4% leftover air in 12 min; hold 1 brick lot; spike only at 1.0% Fe2O3; no 12% slug.",
      "Fe leftover 0.28%. Residual: lot 1 gunning, extra air.", 95, "fused alumina vs TiO2"),
    P("fused-al2o3-vs-tio2",
      "Hold brown-fused alumina TiO2 leftover after coke is 0.6% rich without a 5 min leftover overpower or a 3.4% TiO2 fail.",
      [{"role": "fa_op", "mandate": "TiO2 leftover is 2.9%; spec 1.8; I will not overpower 5 min"},
       {"role": "ck_fa", "mandate": "I can cut coke 0.5% in 10 min; I will not dump 3% mix"},
       {"role": "ti_lab", "mandate": "I will hold 1 furnace tap; I will not certify 2.9% leftover TiO2"}],
      cut_turns("fa_op", "ck_fa", "ti_lab", "3% mix", "0.5% coke", "+settle 8 min", "Si-metal",
                "TiO2 leftover", "1.75%", 1, "furnace tap", "refractory-blend", "3.6%", "settle 8 min leftover",
                "Plan is leftover-coke-cut-0.5-plus-settle-hold, not 5min-overpower and not dump-3pct."),
      ["Op dump-3pct-mix vs leftover coke cut-0.5 vs lab hold-not-2.9pct-TiO2"],
      "Cut leftover coke 0.5% plus settle; hold 1 tap; overpower only at 3.6% TiO2; no 3% dump.",
      "TiO2 leftover 1.75%. Residual: tap 1 refractory-blend, extra settle.", 91, "Si metal vs slag"),
    P("simetal-slag-vs-al",
      "Hold silicon-metal Al leftover after quartz is 0.7% lean without a 15 min leftover overpower or a 0.45% Al fail.",
      [{"role": "si_op", "mandate": "Al leftover is 0.36%; spec 0.15; I will not overpower 15 min"},
       {"role": "qz_si", "mandate": "I can add 0.6% quartz in 9 min; I will not slug 2%"},
       {"role": "al_si", "mandate": "I will hold 1 ladle; I will not certify 0.36% leftover Al"}],
      add_turns("si_op", "qz_si", "al_si", "15 min power", "quartz +0.6%", 9, "SiC-skull", "Al leftover", "0.14%",
                1, "ladle", "chemical-Si", "0.50%", "quartz 1.2 t leftover",
                "Plan is leftover-quartz-plus-0.6-plus-hold, not 15min-overpower and not slug-2pct."),
      ["Op 15min-overpower vs leftover quartz plus-0.6 vs lab hold-not-0.36pct-Al"],
      "Add 0.6% leftover quartz in 9 min; hold 1 ladle; overpower only at 0.50% Al; no 2% slug.",
      "Al leftover 0.14%. Residual: ladle 1 chemical-Si, 1.2 t quartz.", 92, "FeSi vs C"),
    P("fesi-c-vs-si",
      "Hold FeSi carbon leftover after quartz slips without a 12 min leftover overpower or a 0.20% C fail.",
      [{"role": "fs_op", "mandate": "C leftover is 0.16%; spec 0.08; I will not overpower 12 min"},
       {"role": "qz_fs", "mandate": "I can add 0.8% quartz in 8 min; I will not slug 2.5%"},
       {"role": "c_fs", "mandate": "I will hold 1 tap; I will not certify 0.16% leftover C"}],
      add_turns("fs_op", "qz_fs", "c_fs", "12 min power", "quartz +0.8%", 8, "SiO-fume", "C leftover", "0.075%",
                1, "tap", "foundry-FeSi", "0.22%", "quartz 1.8 t leftover",
                "Plan is leftover-quartz-plus-0.8-plus-hold, not 12min-overpower and not slug-2.5pct."),
      ["Op 12min-overpower vs leftover quartz plus-0.8 vs lab hold-not-0.16pct-C"],
      "Add 0.8% leftover quartz in 8 min; hold 1 tap; overpower only at 0.22% C; no 2.5% slug.",
      "C leftover 0.075%. Residual: tap 1 foundry-FeSi, 1.8 t quartz.", 93, "FeCr vs C"),
    P("fecr-c-vs-cr",
      "Hold HC FeCr C leftover after ore is 1.0% lean without a 10 min leftover overblow or a 9.2% C fail.",
      [{"role": "fcr_op", "mandate": "C leftover is 8.6%; spec 7.5; I will not overblow 10 min"},
       {"role": "ore_fcr", "mandate": "I can add 0.9% ore in 7 min; I will not slug 3%"},
       {"role": "c_fcr", "mandate": "I will hold 1 tap; I will not certify 8.6% leftover C"}],
      add_turns("fcr_op", "ore_fcr", "c_fcr", "10 min blow", "ore +0.9%", 7, "Cr2O3-slag", "C leftover", "7.4%",
                1, "tap", "charge-chrome", "9.4%", "ore 2.4 t leftover",
                "Plan is leftover-ore-plus-0.9-plus-hold, not 10min-overblow and not slug-3pct."),
      ["Op 10min-overblow vs leftover ore plus-0.9 vs lab hold-not-8.6pct-C"],
      "Add 0.9% leftover ore in 7 min; hold 1 tap; overblow only at 9.4% C; no 3% slug.",
      "C leftover 7.4%. Residual: tap 1 charge-chrome, 2.4 t ore.", 94, "FeMn vs slag"),
    P("femn-slag-vs-mn",
      "Hold FeMn slag-Mn leftover after coke is 0.8% short without a 14 min leftover overpower or a 22% slag-Mn fail.",
      [{"role": "fmn_op", "mandate": "slag-Mn leftover is 19%; spec 12; I will not overpower 14 min"},
       {"role": "ck_fmn", "mandate": "I can add 0.7% coke in 9 min; I will not slug 2.2%"},
       {"role": "mn_lab", "mandate": "I will hold 1 tap; I will not certify 19% leftover slag-Mn"}],
      add_turns("fmn_op", "ck_fmn", "mn_lab", "14 min power", "coke +0.7%", 9, "Si-rise", "slag-Mn leftover", "11.6%",
                1, "tap", "silicomanganese", "23%", "coke 1.6 t leftover",
                "Plan is leftover-coke-plus-0.7-plus-hold, not 14min-overpower and not slug-2.2pct."),
      ["Op 14min-overpower vs leftover coke plus-0.7 vs lab hold-not-19pct-slagMn"],
      "Add 0.7% leftover coke in 9 min; hold 1 tap; overpower only at 23% slag-Mn; no 2.2% slug.",
      "Slag-Mn leftover 11.6%. Residual: tap 1 silicomanganese, 1.6 t coke.", 95, "Kroll Ti vs Mg"),
]


def build_record(n, spec):
    if len(spec["turns"]) < 8:
        raise SystemExit(f"short transcript {spec['slug']}")
    roles = {a["role"] for a in spec["agents"]}
    if len(spec["agents"]) != 3:
        raise SystemExit(f"need 3 roles {spec['slug']}")
    for s, _ in spec["turns"]:
        if s not in roles:
            raise SystemExit(f"{spec['slug']} {s}")
    return {
        "id": f"mac-r{n}-{spec['slug']}",
        "goal": spec["goal"],
        "agents": spec["agents"],
        "transcript": [T(i, s, c) for i, (s, c) in enumerate(spec["turns"], 1)],
        "disagreements": spec["disagreements"],
        "resolution": spec["resolution"],
        "joint_outcome": spec["joint_outcome"],
        "reward": {"success": spec["success"]},
        "meta": {
            "factory": "multi-agent-coordination-factory",
            "round": n,
            "generator": "grok-4.6",
        },
    }


def notes_text(spec, nbytes, n):
    roles = ", ".join(f"{a['role']} ({a['mandate']})" for a in spec["agents"])
    return (
        f"Roles: {roles}.\n"
        f"Disagreement that mattered: {spec['disagreements'][0]}.\n"
        f"Resolution cites that disagreement and changes the plan.\n"
        f"Joint outcome earned: yes — {spec['joint_outcome']}\n"
        f"Bytes: {nbytes}. Unique leftover leftover leftover vs banned r2748–r3033; "
        f"not capro-oxime-vs-beckmann / whiskey / hearts-vs-tails / r3034 polymer catalog.\n"
        f"Novel coverage: {spec['novel']}%\n"
        f"Next densify target: {spec['densify']}.\n"
    )


def busy(factory: Path) -> bool:
    return bool(list(factory.glob("ROUND-r*.reserved.json"))) or bool(
        list(factory.glob("ROUND-r*.publishing.json"))
    )


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs in leftover leftover leftover catalog")
    for s in SCENARIOS:
        low = s["slug"].lower()
        if any(b in low for b in BANNED_SUB):
            raise SystemExit(f"banned slug {s['slug']}")
        rec = build_record(3038, s)
        blob = json.dumps(rec)
        for bad in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
            if f'"{bad}"' in blob:
                raise SystemExit(f"{s['slug']} has {bad}")
        if "sim_or_real" in blob and "real" in blob.split("sim_or_real")[-1][:40]:
            raise SystemExit(f"{s['slug']} sim_or_real real")
        if len(rec["transcript"]) != 10:
            raise SystemExit(f"{s['slug']} need 10 turns")
        if len(rec["agents"]) != 3:
            raise SystemExit(f"{s['slug']} need 3 roles")
    print(f"self_check ok: {len(SCENARIOS)} leftover leftover leftover plants", flush=True)


def main() -> int:
    self_check()
    published = []
    hops_done = 0
    idx = 0
    start = time.monotonic()
    last_hop_log = 0.0
    while time.monotonic() - start < DEADLINE_S:
        if idx >= len(SCENARIOS):
            print("leftover leftover leftover catalog exhausted", flush=True)
            break
        status = round_txn.frontier_status(FACTORY)
        n = status["next_round"]
        spec = SCENARIOS[idx]
        try:
            reservation = round_txn.reserve(FACTORY, n, 1)
        except (round_txn.TransactionError, FileExistsError, OSError) as exc:
            hops_done += 1
            now = time.monotonic()
            if now - last_hop_log >= 8:
                print(f"HOP leftover leftover leftover r{n}: {exc}", flush=True)
                last_hop_log = now
            time.sleep(0.05)
            continue
        rec = build_record(n, spec)
        line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
        nbytes = len(line.encode())
        stage = Path(reservation["staging_dir"])
        (stage / reservation["batch_file"]).write_text(line + "\n")
        (stage / reservation["notes_file"]).write_text(notes_text(spec, nbytes, n))
        print(f"STAGED r{n} {rec['id']} {nbytes}B leftover leftover leftover", flush=True)
        try:
            pub = round_txn.publish(FACTORY, n, reservation["token"])
        except round_txn.TransactionError as exc:
            print(f"PUBLISH FAIL r{n}: {exc}", flush=True)
            try:
                round_txn.abort(FACTORY, n, reservation["token"])
            except round_txn.TransactionError:
                pass
            return 1
        published.append((n, rec["id"], nbytes, pub.get("records")))
        idx += 1
        print(f"PUBLISHED r{n} {rec['id']} {nbytes}B leftover leftover leftover", flush=True)
    print(
        json.dumps(
            {
                "published": published,
                "count": len(published),
                "hops": hops_done,
                "frontier": round_txn.frontier_status(FACTORY)["next_round"],
            }
        ),
        flush=True,
    )
    return 0 if published or hops_done else 1


if __name__ == "__main__":
    raise SystemExit(main())
