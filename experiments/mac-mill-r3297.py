#!/usr/bin/env python3
"""MAC mill r3297+. Hop SSR r554+ if MAC reserved. Never sbox if reserved/writing."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205b", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

AGENTIC = REPO / "outputs/raw/2026-08-19-agentic"
FACTORY = AGENTIC / "multi-agent-coordination-factory"
SSR = AGENTIC / "secret-scan-remediation-factory"
SBOX = AGENTIC / "sandbox-refusal-factory"
SSR_MILL = REPO / "experiments/ssr-mill-r554.py"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("cyclohexanol-dehydro-vs-h2", "cyclohexanol dehydro", "conv", "82%", "88%", "87.4%", "12 K", "phenol", "H2 +5%", 10, 1, "KA tank", "recycle", "78%", "H2 0.3 bar extra", "adiponitrile vs HCN", "cyol_op", "h2_cyol", "cyol_lab", 84),
    A("adiponitrile-butadiene-vs-hcn", "adiponitrile", "HCN leftover", "28 ppm", "10 ppm", "9.5 ppm", "14 K", "COx", "HCN +3%", 11, 1, "ADN tank", "nylon", "40 ppm", "HCN 0.4 t extra", "HMDI NCO vs H12", "adn_op", "hcn_adn", "hcn_adnlab", 83),
    A("hmdi-h12mdi-vs-nco", "H12MDI", "NCO", "31.2%", "31.8%", "31.75%", "9 K", "color", "phosgene +3%", 12, 1, "H12 tank", "elastomer", "30.8%", "phosgene 0.6 t extra", "IPDI IPDA vs NCO", "h12_op", "phos_h12", "nco_h12", 82),
    A("ipdi-ipda-vs-nco", "IPDI", "NCO", "37.1%", "37.5%", "37.45%", "8 K", "color", "phosgene +2.5%", 10, 1, "IPDI tank", "coating", "36.6%", "phosgene 0.5 t extra", "HDI biuret vs NCO", "ipdi_op", "phos_ipdi", "nco_ipdi", 81),
    A("hdi-biuret-vs-nco", "HDI biuret", "NCO", "21.4%", "22.0%", "21.9%", "7 K", "gel", "HDI +3%", 9, 1, "biuret tank", "clearcoat", "20.8%", "HDI 0.4 t extra", "TMXDI TMI vs NCO", "hdi_op", "hdi_biu", "nco_hdi", 80),
    A("tmxdi-tmi-vs-nco", "TMXDI", "NCO", "33.8%", "34.4%", "34.3%", "8 K", "yellow", "phosgene +2%", 11, 1, "TMXDI tank", "sealant", "33.2%", "phosgene 0.3 t extra", "MOCA cast vs NH2", "tmx_op", "phos_tmx", "nco_tmx", 79),
    A("moca-cast-vs-nh2", "MOCA", "NH2", "24.8%", "25.5%", "25.4%", "6 K", "color", "H2 +4%", 13, 1, "MOCA melt", "cast-PU", "24.2%", "H2 0.2 bar extra", "DETDA gel vs NCO", "moca_op", "h2_moca", "nh2_lab", 78),
    A("detda-gel-vs-nco", "DETDA", "amine", "98.2%", "99.0%", "98.9%", "7 K", "gel", "H2 +3%", 8, 1, "DETDA tank", "RIM", "97.5%", "H2 0.2 bar extra", "PTMEG THF vs OH", "det_op", "h2_det", "am_lab", 77),
    A("ptmeg-thf-vs-oh", "PTMEG", "OH#", "108", "112", "111.5", "10 K", "THF", "THF +3%", 14, 1, "PTMEG tank", "spandex", "104", "THF 1 t extra", "PPG PO vs unsat", "ptmeg_op", "thf_ptmeg", "oh_ptmeg", 76),
    A("ppg-po-vs-unsat", "PPG", "unsat", "0.032", "0.018", "0.017", "9 K", "allyl", "PO +3%", 12, 1, "PPG tank", "flex-foam", "0.040", "PO 0.8 t extra", "POP EO vs OH", "ppg_op", "po_ppg", "unsat_lab", 75),
    A("pop-eo-vs-oh", "POP", "OH#", "54", "56", "55.8", "8 K", "unsat", "EO +3%", 10, 1, "POP tank", "slabstock", "52", "EO 0.6 t extra", "caprolactone polyol vs OH", "pop_op", "eo_pop", "oh_pop", 74),
    A("caprolactone-polyol-vs-oh", "PCL polyol", "OH#", "108", "112", "111.6", "11 K", "acid", "CL +3%", 15, 1, "PCL tank", "TPU", "104", "CL 0.5 t extra", "polyester adipate vs AV", "pclp_op", "cl_pclp", "oh_pclp", 73),
    A("polyester-adipate-vs-av", "polyester polyol", "AV", "1.4", "0.5", "0.48", "12 K", "color", "adipic +3%", 13, 1, "PES tank", "foam", "1.8", "adipic 0.4 t extra", "PCD OH vs visc", "pesp_op", "ad_pesp", "av_pesp", 72),
    A("polycarbonate-diol-vs-oh", "PCD", "OH#", "54", "56", "55.7", "10 K", "phenol", "DPC +2%", 16, 1, "PCD tank", "TPU-coat", "52", "DPC 40 kg extra", "castor OH vs IV", "pcd_op", "dpc_pcd", "oh_pcd", 71),
    A("castor-oh-vs-iv", "castor oil", "OH#", "158", "164", "163", "8 K", "color", "steam +4%", 9, 1, "castor tank", "alkyd", "152", "steam 0.6 t extra", "dimer acid vs AV", "cas_op", "stm_cas", "oh_cas", 70),
    A("dimer-acid-vs-av", "dimer acid", "AV", "188", "192", "191.5", "14 K", "monomer", "vacuum +5%", 12, 1, "dimer tank", "PA", "184", "vacuum 3% extra", "tall oil vs AV", "dim_op", "vac_dim", "av_dim", 69),
    A("tall-oil-vs-av", "TOFA", "AV", "188", "194", "193", "11 K", "rosin", "steam +4%", 10, 1, "TOFA tank", "alkyd", "182", "steam 0.5 t extra", "rosin acid vs AV", "tofa_op", "stm_tofa", "av_tofa", 68),
    A("rosin-acid-vs-av", "rosin", "AV", "158", "165", "164", "13 K", "color", "vacuum +5%", 11, 1, "rosin kettle", "ink", "150", "vacuum 4% extra", "terpene resin vs soften", "ros_op", "vac_ros", "av_ros", 67),
    A("terpene-resin-vs-soften", "terpene resin", "SP", "92 C", "100 C", "99 C", "12 K", "color", "catalyst +3%", 14, 1, "resin kettle", "hotmelt", "86 C", "cat 8 kg extra", "C5 resin vs soften", "ter_op", "cat_ter", "sp_lab", 66),
    A("c5-resin-vs-soften", "C5 resin", "SP", "88 C", "95 C", "94.5 C", "11 K", "color", "piperylene +3%", 13, 1, "C5 kettle", "PSA", "82 C", "C5 0.6 t extra", "C9 resin vs color", "c5_op", "pip_c5", "sp_c5", 65),
    A("c9-resin-vs-color", "C9 resin", "Gardner", "8", "5", "5.2", "15 K", "gel", "hydrogen +6%", 16, 1, "C9 kettle", "adhesive", "10", "H2 0.3 bar extra", "DCPD resin vs soften", "c9_op", "h2_c9", "gd_lab", 64),
    A("dcpd-resin-vs-soften", "DCPD resin", "SP", "102 C", "110 C", "109 C", "14 K", "gel", "DCPD +3%", 12, 1, "DCPD kettle", "ink", "96 C", "DCPD 0.5 t extra", "coumarone vs soften", "dcpd_op", "dcpd_feed", "sp_dcpd", 63),
    A("coumarone-vs-soften", "coumarone", "SP", "96 C", "105 C", "104 C", "13 K", "color", "indene +3%", 11, 1, "CI kettle", "rubber", "90 C", "indene 0.4 t extra", "petroleum resin vs GA", "ci_op", "ind_ci", "sp_ci", 62),
    A("petroleum-resin-vs-ga", "HC resin", "GA", "8", "4", "4.2", "16 K", "gel", "H2 +5%", 15, 1, "HC kettle", "hotmelt", "10", "H2 0.3 bar extra", "bitumen pen vs RTOF", "hc_op", "h2_hc", "ga_lab", 61),
    A("bitumen-pen-vs-rtof", "bitumen", "pen", "68", "50", "51", "18 K", "fume", "air-blow +6%", 20, 1, "bit tank", "paving", "80", "air 5% extra", "asphalt PGI vs MSCR", "bit_op", "air_bit", "pen_lab", 60),
    A("asphalt-pgi-vs-msct", "PG binder", "Jnr", "4.8", "3.0", "3.1", "16 K", "aging", "PPA +3%", 14, 1, "PG tank", "mix", "5.5", "PPA 40 kg extra", "wax oil vs congeal", "pgb_op", "ppa_pgb", "jnr_lab", 59),
    A("wax-oil-vs-congeal", "paraffin", "oil", "1.8%", "0.5%", "0.48%", "12 K", "odor", "sweat +5%", 18, 1, "wax kettle", "candle", "2.2%", "sweat 2 h extra", "microcrystal pen vs oil", "wax_op", "swt_wax", "oil_wax", 58),
    A("microcrystal-pen-vs-oil", "microcrystalline", "pen", "28", "22", "22.4", "11 K", "oil", "deoil +4%", 16, 1, "MC kettle", "polish", "32", "MEK 0.4 t extra", "petrolatum cone vs drop", "mc_op", "deo_mc", "pen_mc", 57),
    A("petrolatum-cone-vs-drop", "petrolatum", "cone", "210", "180", "182", "9 K", "oil-bleed", "blend +3%", 10, 1, "pet kettle", "ointment", "230", "wax 0.3 t extra", "slack wax vs oil", "pet_op", "bl_pet", "cone_lab", 56),
    A("slack-wax-vs-oil", "slack wax", "oil", "8.4%", "3.0%", "3.1%", "13 K", "color", "deoil +5%", 14, 1, "slack tank", "board", "10%", "MEK 0.6 t extra", "FT wax vs congeal", "slk_op", "deo_slk", "oil_slk", 55),
    A("ft-wax-vs-congeal", "FT wax", "congeal", "96 C", "102 C", "101.5 C", "15 K", "odor", "H2 +4%", 12, 1, "FT kettle", "hotmelt", "92 C", "H2 3% extra", "PE wax vs Mv", "ft_op", "h2_ft", "cg_lab", 54),
    A("pe-wax-vs-mv", "PE wax", "Mv", "1800", "2200", "2180", "14 K", "color", "perox +3%", 11, 1, "PE wax silo", "PVC", "1600", "perox 8 kg extra", "PP wax vs MFR", "pew_op", "pox_pew", "mv_pew", 53),
    A("pp-wax-vs-mfr", "PP wax", "MFR", "420", "380", "385", "13 K", "yellow", "H2 +4%", 10, 1, "PP wax silo", "masterbatch", "480", "H2 3% extra", "amide wax vs MP", "ppw_op", "h2_ppw", "mfr_ppw", 52),
    A("amide-wax-vs-mp", "EBS", "MP", "138 C", "144 C", "143.5 C", "8 K", "acid", "steam +4%", 9, 1, "EBS hopper", "ABS", "132 C", "steam 0.4 t extra", "ester wax vs AV", "ebs_op", "stm_ebs", "mp_ebs", 51),
    A("ester-wax-vs-av", "ester wax", "AV", "8.4", "4.0", "4.1", "10 K", "color", "polyol +3%", 12, 1, "ester kettle", "polish", "10", "polyol 20 kg extra", "montan vs acid", "est_op", "pol_est", "av_est", 50),
    A("montan-vs-acid", "montan", "AV", "28", "18", "18.4", "14 K", "ash", "bleach +5%", 15, 1, "montan kettle", "carbon-paper", "32", "CrO3 8 kg extra", "carnauba vs MP", "mon_op", "bl_mon", "av_mon", 49),
    A("carnauba-vs-mp", "carnauba", "MP", "78 C", "83 C", "82.5 C", "7 K", "dirt", "filter +4%", 8, 1, "carnauba kettle", "polish", "74 C", "filter-aid 10 kg extra", "beeswax vs AV", "car_op", "fil_car", "mp_car", 48),
    A("beeswax-vs-av", "beeswax", "AV", "22", "18", "18.2", "6 K", "color", "bleach +4%", 9, 1, "bees kettle", "cosmetic", "26", "perox 4 kg extra", "lanolin vs OH", "bee_op", "bl_bee", "av_bee", 47),
    A("lanolin-vs-oh", "lanolin", "OH#", "18", "14", "14.2", "8 K", "odor", "deodor +5%", 11, 1, "lan kettle", "ointment", "22", "steam 0.3 t extra", "sterol vs GC", "lan_op", "deo_lan", "oh_lan", 46),
    A("sterol-vs-gc", "phytosterol", "beta-sito", "38%", "42%", "41.8%", "9 K", "oxidate", "vacuum +4%", 13, 1, "sterol hopper", "food", "35%", "vacuum 3% extra", "tocopherol vs assay", "ste_op", "vac_ste", "sito_lab", 45),
    A("tocopherol-vs-assay", "tocopherol", "d-alpha", "92%", "96%", "95.7%", "7 K", "oxidate", "N2 +6%", 10, 1, "toco tank", "supplement", "88%", "N2 4% extra", "ascorbate vs assay", "toc_op", "n2_toc", "da_lab", 44),
    A("ascorbate-vs-assay", "ascorbic", "assay", "98.2%", "99.0%", "98.9%", "5 K", "oxidate", "N2 +5%", 8, 1, "AA hopper", "food", "97.0%", "N2 3% extra", "citrate vs assay", "asc_op", "n2_asc", "as_lab", 43),
    A("citrate-vs-assay", "citric", "assay", "99.1%", "99.5%", "99.45%", "6 K", "color", "carbon +4%", 9, 1, "citric hopper", "beverage", "98.6%", "carbon 20 kg extra", "lactate vs assay", "cit_op", "c_cit", "as_cit", 42),
    A("lactate-vs-assay", "lactic", "assay", "87.4%", "88.0%", "87.9%", "7 K", "color", "carbon +3%", 8, 1, "lactic tank", "food", "86.5%", "carbon 15 kg extra", "gluconate vs assay", "lac_op", "c_lac", "as_lac", 41),
    A("gluconate-vs-assay", "gluconate", "assay", "98.0%", "99.0%", "98.8%", "8 K", "color", "H2O2 +3%", 10, 1, "glu hopper", "chelant", "97.0%", "H2O2 20 kg extra", "sorbate vs assay", "glu_op", "h2o2_glu", "as_glu", 40),
    A("sorbate-vs-assay", "K-sorbate", "assay", "98.4%", "99.0%", "98.95%", "6 K", "color", "carbon +4%", 7, 1, "sorbate hopper", "preserve", "97.5%", "carbon 10 kg extra", "benzoate vs assay", "sor_op", "c_sor", "as_sor", 39),
    A("benzoate-vs-assay", "Na-benzoate", "assay", "99.0%", "99.5%", "99.45%", "7 K", "odor", "steam +4%", 8, 1, "benzo hopper", "beverage", "98.4%", "steam 0.3 t extra", "paraben vs assay", "bz_op", "stm_bz", "as_bz", 38),
    A("paraben-vs-assay", "methylparaben", "assay", "98.6%", "99.0%", "98.95%", "6 K", "color", "recryst +4%", 12, 1, "paraben hopper", "cosmetic", "98.0%", "MeOH 0.2 t extra", "phenoxyethanol vs assay", "par_op", "rc_par", "as_par", 37),
    A("phenoxyethanol-vs-assay", "phenoxyethanol", "assay", "98.8%", "99.5%", "99.4%", "8 K", "phenol", "vacuum +4%", 9, 1, "POE tank", "cosmetic", "98.2%", "vacuum 3% extra", "isothiazolinone vs assay", "poe_op", "vac_poe", "as_poe", 36),
    A("isothiazolinone-vs-assay", "MIT", "assay", "9.2%", "9.5%", "9.48%", "5 K", "color", "diluent +3%", 6, 1, "MIT tank", "in-can", "8.8%", "water 40 kg extra", "quat vs active", "mit_op", "dil_mit", "as_mit", 35),
    A("quat-vs-active", "BAC", "active", "48.2%", "50.0%", "49.8%", "7 K", "amine", "alkyl +3%", 10, 1, "BAC tank", "hard-surface", "47.0%", "alkyl 0.3 t extra", "amine oxide vs amine", "bac_op", "alk_bac", "act_bac", 34),
    A("amine-oxide-vs-amine", "LAO", "free amine", "1.8%", "0.5%", "0.48%", "8 K", "nitrosa", "H2O2 +4%", 11, 1, "AO tank", "dish", "2.2%", "H2O2 40 kg extra", "betaine vs solids", "ao_op", "h2o2_ao", "am_ao", 33),
    A("betaine-vs-solids", "CAPB", "solids", "28.4%", "30.0%", "29.8%", "6 K", "NaCl", "steam-cut 4%", 8, 1, "CAPB tank", "shampoo", "27.0%", "steam 0.4 t extra", "sultaine vs solids", "capb_op", "stm_capb", "sol_capb", 32),
    A("sultaine-vs-solids", "sultaine", "solids", "38.2%", "40.0%", "39.7%", "7 K", "salt", "steam-cut 3%", 9, 1, "sultaine tank", "bodywash", "36.5%", "steam 0.3 t extra", "APG vs DP", "sul_op", "stm_sul", "sol_sul", 31),
    A("apg-vs-dp", "APG", "DP", "1.32", "1.40", "1.39", "9 K", "glucose", "fatty +3%", 12, 1, "APG tank", "dish", "1.25", "alcohol 0.4 t extra", "SCI vs active", "apg_op", "fa_apg", "dp_lab", 30),
    A("sci-vs-active", "SCI", "active", "83%", "85%", "84.8%", "8 K", "salt", "isethionate +3%", 10, 1, "SCI hopper", "syndet", "81%", "SCI 40 kg extra", "SLES dioxane vs active", "sci_op", "ise_sci", "act_sci", 29),
    A("sles-vs-dioxane", "SLES", "dioxane", "28 ppm", "10 ppm", "9.5 ppm", "7 K", "color", "steam-strip +5%", 11, 1, "SLES tank", "shampoo", "40 ppm", "steam 0.5 t extra", "SLES-1EO vs active", "sles_op", "stm_sles", "dx_lab", 28),
    A("sles-1eo-vs-active", "SLES 1EO", "active", "68.4%", "70.0%", "69.7%", "6 K", "unsulf", "SO3 +2%", 8, 1, "SLES tank", "dish", "66.0%", "SO3 0.3 t extra", "ALS vs active", "sles1_op", "so3_sles1", "act_sles1", 27),
    A("als-vs-active", "ALS", "active", "28.2%", "30.0%", "29.8%", "7 K", "unsulf", "SO3 +2.5%", 9, 1, "ALS tank", "shampoo", "26.5%", "SO3 0.2 t extra", "AOSS vs active", "als_op", "so3_als", "act_als", 26),
    A("aoss-vs-active", "AOS", "active", "38.4%", "40.0%", "39.7%", "8 K", "sultone", "SO3 +3%", 10, 1, "AOS tank", "powder", "36.5%", "SO3 0.3 t extra", "LABS vs active", "aos_op", "so3_aos", "act_aos", 25),
    A("labs-vs-active", "LABS", "active", "95.2%", "96.0%", "95.9%", "9 K", "unsulf", "SO3 +2%", 8, 1, "LABS tank", "powder", "94.0%", "SO3 0.4 t extra", "MES vs active", "labs_op", "so3_labs", "act_labs", 24),
    A("mes-vs-active", "MES", "active", "82%", "85%", "84.6%", "10 K", "disalt", "MeOH +4%", 12, 1, "MES hopper", "powder", "80%", "MeOH 0.3 t extra", "SAS vs active", "mes_op", "meoh_mes", "act_mes", 23),
    A("sas-vs-active", "SAS", "active", "92.4%", "93.0%", "92.9%", "8 K", "unsulf", "SO3 +2%", 9, 1, "SAS tank", "liquid", "91.5%", "SO3 0.2 t extra", "lauryl glucoside vs DP", "sas_op", "so3_sas", "act_sas", 22),
    A("lauryl-glucoside-vs-dp", "lauryl glucoside", "DP", "1.28", "1.40", "1.38", "9 K", "glucose", "lauryl +3%", 11, 1, "LG tank", "baby", "1.20", "alcohol 0.3 t extra", "decyl glucoside vs DP", "lg_op", "lau_lg", "dp_lg", 21),
    A("decyl-glucoside-vs-dp", "decyl glucoside", "DP", "1.30", "1.42", "1.40", "8 K", "glucose", "decyl +3%", 10, 1, "DG tank", "baby", "1.22", "alcohol 0.25 t extra", "coco glucoside vs DP", "dg_op", "dec_dg", "dp_dg", 20),
    A("coco-glucoside-vs-dp", "coco glucoside", "DP", "1.34", "1.45", "1.43", "9 K", "glucose", "coco +3%", 12, 1, "CG tank", "bodywash", "1.25", "alcohol 0.3 t extra", "glyceryl stearate vs AV", "cg_op", "co_cg", "dp_cg", 19),
    A("glyceryl-stearate-vs-av", "GMS", "AV", "4.2", "1.5", "1.55", "8 K", "color", "glycerin +3%", 10, 1, "GMS hopper", "cream", "5.0", "glycerin 20 kg extra", "PEG stearate vs OH", "gms_op", "gly_gms", "av_gms", 18),
    A("peg-stearate-vs-oh", "PEG-100 stearate", "OH#", "22", "18", "18.3", "9 K", "color", "PEG +3%", 11, 1, "PEG-st hopper", "lotion", "26", "PEG 15 kg extra", "sorbitan stearate vs OH", "pegs_op", "peg_pegs", "oh_pegs", 17),
    A("sorbitan-stearate-vs-oh", "span-60", "OH#", "235", "245", "243", "8 K", "color", "sorbitol +3%", 12, 1, "span hopper", "food", "225", "sorbitol 12 kg extra", "polysorbate vs OH", "sp_op", "sorb_sp", "oh_sp", 16),
    A("polysorbate-vs-oh", "tween-80", "OH#", "68", "72", "71.5", "7 K", "perox", "EO +3%", 10, 1, "tween tank", "pharma", "64", "EO 0.2 t extra", "lecithin vs AI", "tw_op", "eo_tw", "oh_tw", 15),
    A("lecithin-vs-ai", "lecithin", "AI", "62%", "65%", "64.7%", "6 K", "color", "acetone +4%", 13, 1, "lec hopper", "food", "59%", "acetone 0.3 t extra", "ceramide vs assay", "lec_op", "ac_lec", "ai_lab", 14),
    A("ceramide-vs-assay", "ceramide NP", "assay", "92%", "95%", "94.8%", "5 K", "oxidate", "N2 +5%", 9, 1, "cer hopper", "serum", "88%", "N2 3% extra", "hyaluronate vs MW", "cer_op", "n2_cer", "as_cer", 13),
    A("hyaluronate-vs-mw", "HA", "Mw", "0.82 MDa", "1.10 MDa", "1.08 MDa", "4 K", "depoly", "EtOH +4%", 14, 1, "HA hopper", "serum", "0.60", "EtOH 0.2 t extra", "carbomer vs visc", "ha_op", "etoh_ha", "mw_ha", 12),
    A("carbomer-vs-visc", "carbomer", "visc", "42k cP", "55k cP", "54k cP", "5 K", "grit", "AA +3%", 11, 1, "carb hopper", "gel", "35k", "AA 20 kg extra", "xanthan vs visc", "carb_op", "aa_carb", "vis_carb", 11),
    A("xanthan-vs-visc", "xanthan", "visc", "1200 cP", "1400 cP", "1380 cP", "6 K", "pyruvate", "DO +5%", 16, 1, "xanthan hopper", "sauce", "1100", "air 4% extra", "guar vs visc", "xan_op", "do_xan", "vis_xan", 10),
    A("guar-vs-visc", "guar", "visc", "3800 cP", "4500 cP", "4450 cP", "7 K", "insol", "hydrate +4%", 12, 1, "guar hopper", "frac", "3200", "water 0.4 t extra", "HPC vs visc", "gu_op", "hyd_gu", "vis_gu", 9),
    A("hpc-vs-visc", "HPC", "visc", "220 cP", "280 cP", "275 cP", "8 K", "DS", "PO +3%", 13, 1, "HPC hopper", "tablet", "180", "PO 15 kg extra", "HPMC vs visc", "hpc_op", "po_hpc", "vis_hpc", 8),
    A("hpmc-vs-visc", "HPMC", "visc", "3200 cP", "4000 cP", "3950 cP", "9 K", "DS", "MeCl +3%", 14, 1, "HPMC hopper", "tablet", "2800", "MeCl 20 kg extra", "CMC vs DS", "hpmc_op", "mecl_hpmc", "vis_hpmc", 7),
    A("cmc-vs-ds", "CMC", "DS", "0.72", "0.80", "0.79", "8 K", "glycolate", "MCA +3%", 12, 1, "CMC hopper", "food", "0.65", "MCA 25 kg extra", "acrylates copolymer vs solids", "cmc_op", "mca_cmc", "ds_lab", 6),
    A("acrylates-copolymer-vs-solids", "ASE", "solids", "28.4%", "30.0%", "29.8%", "6 K", "grit", "AA +3%", 9, 1, "ASE tank", "paint", "27.0%", "AA 30 kg extra", "cyclohexanol next", "ase_op", "aa_ase", "sol_ase", 5),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(3297, s)
        if len(rec["transcript"]) < 8 or len(s["agents"]) != 3:
            raise SystemExit(s["slug"])
    print(f"self_check ok: {len(SCENARIOS)} plants", flush=True)


def mill_ssr(rnd: int, stage: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(SSR_MILL), "--round", str(rnd), "--staging", str(stage)],
        cwd=REPO, text=True, capture_output=True, check=False,
    )
    sys.stderr.write(proc.stderr or "")
    print(proc.stdout, flush=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ssr mill r{rnd}: {proc.stderr}")


def hop_ssr() -> bool:
    if busy(SBOX):
        print("sandbox-refusal reserved/writing; never hop there", flush=True)
    if busy(SSR):
        print("HOP skip ssr: reserved/writing", flush=True)
        return False
    n = round_txn.frontier_status(SSR)["next_round"]
    if n < 554 or n > 669:
        print(f"HOP skip ssr: r{n} outside 554-669", flush=True)
        return False
    try:
        reservation = round_txn.reserve(SSR, n, 2)
    except (round_txn.TransactionError, FileExistsError, OSError) as exc:
        print(f"HOP ssr reserve fail r{n}: {exc}", flush=True)
        return False
    token = reservation["token"]
    stage = Path(reservation["staging_dir"])
    try:
        mill_ssr(n, stage)
        pub = round_txn.publish(SSR, n, token)
    except Exception as exc:
        print(f"HOP ssr mill/publish fail r{n}: {exc}", flush=True)
        try:
            round_txn.abort(SSR, n, token)
        except round_txn.TransactionError:
            pass
        return False
    print(json.dumps({"hop": "secret-scan-remediation-factory", "round": n, "records": pub.get("records")}), flush=True)
    return True


def main() -> int:
    self_check()
    published = []
    idx = 0
    start = time.monotonic()
    while time.monotonic() - start < DEADLINE_S:
        n = round_txn.frontier_status(FACTORY)["next_round"]
        if busy(FACTORY):
            print(f"MAC r{n} reserved/writing; hopping", flush=True)
            if not hop_ssr():
                time.sleep(2)
            continue
        if idx >= len(SCENARIOS):
            print(f"MAC catalog exhausted at r{n}; hopping", flush=True)
            if not hop_ssr():
                time.sleep(3)
                if not busy(FACTORY):
                    print("no hop fuel and MAC free but catalog empty", flush=True)
                    break
            continue
        spec = SCENARIOS[idx]
        idx += 1
        try:
            reservation = round_txn.reserve(FACTORY, n, 1)
        except (round_txn.TransactionError, FileExistsError, OSError) as exc:
            print(f"HOP reserve r{n}: {exc}", flush=True)
            idx -= 1
            if not hop_ssr():
                time.sleep(1)
            continue
        rec = build_record(n, spec)
        line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
        nbytes = len(line.encode())
        stage = Path(reservation["staging_dir"])
        (stage / reservation["batch_file"]).write_text(line + "\n")
        (stage / reservation["notes_file"]).write_text(notes_text(spec, nbytes, n))
        print(f"STAGED r{n} {rec['id']} {nbytes}B", flush=True)
        try:
            round_txn.publish(FACTORY, n, reservation["token"])
        except round_txn.TransactionError as exc:
            print(f"PUBLISH FAIL r{n}: {exc}", flush=True)
            try:
                round_txn.abort(FACTORY, n, reservation["token"])
            except round_txn.TransactionError:
                pass
            return 1
        published.append((n, rec["id"], nbytes))
        print(f"PUBLISHED r{n} {rec['id']} {nbytes}B", flush=True)
    print(json.dumps({"published": published, "count": len(published),
                      "frontier": round_txn.frontier_status(FACTORY)["next_round"]}), flush=True)
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
