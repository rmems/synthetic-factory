#!/usr/bin/env python3
"""MAC mill r3391+. Unique food-process plants. Hop if reserved. Never sbox if reserved/writing."""
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

_b = SourceFileLoader("mac3205c", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

AGENTIC = REPO / "outputs/raw/2026-08-19-agentic"
FACTORY = AGENTIC / "multi-agent-coordination-factory"
OBS = AGENTIC / "observability-debug-factory"
SBOX = AGENTIC / "sandbox-refusal-factory"
OBS_MILL = REPO / "experiments/obs-mill-r401.py"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("yogurt-ph-vs-set", "yogurt", "pH", "4.72", "4.55", "4.56", "3 K", "whey", "hold +20 min", 20, 1, "vat", "stirred", "4.85", "hold 20 min extra", "cheese moisture vs vat", "yog_op", "hold_yog", "ph_lab", 72),
    A("cheese-moisture-vs-vat", "cheddar", "moisture", "39.4%", "38.0%", "38.1%", "4 K", "oil-off", "cut +8 min", 8, 1, "vat", "process", "40.5%", "steam 0.3 t extra", "butter moisture vs churn", "chz_op", "cut_chz", "moi_chz", 71),
    A("butter-moisture-vs-churn", "butter", "moisture", "16.8%", "16.0%", "16.05%", "2 K", "free-water", "work +4 min", 4, 1, "churn", "print", "17.2%", "work 4 min extra", "ice cream overrun vs draw", "but_op", "wrk_but", "moi_but", 70),
    A("ice-cream-overrun-vs-draw", "ice cream", "overrun", "82%", "90%", "89%", "3 K", "icy", "draw -2 C", 6, 1, "freezer", "novelty", "75%", "ammonia 0.2 bar extra", "chocolate visc vs conche", "ic_op", "drw_ic", "ov_lab", 69),
    A("chocolate-visc-vs-conche", "chocolate", "visc", "4.8 Pa.s", "3.5 Pa.s", "3.55", "4 K", "grit", "conche +40 min", 40, 1, "conche", "coating", "5.5", "lecithin 4 kg extra", "cocoa butter vs temp", "choc_op", "cnc_choc", "vis_choc", 68),
    A("cocoa-butter-vs-temp", "cocoa butter", "IV", "36.8", "35.0", "35.1", "6 K", "bloom", "seed +3%", 12, 1, "CB tank", "compound", "38.0", "seed 8 kg extra", "coffee roast vs agtron", "cb_op", "sd_cb", "iv_cb", 67),
    A("coffee-roast-vs-agtron", "coffee", "Agtron", "62", "55", "55.5", "8 K", "bake", "air +5%", 8, 1, "roast", "espresso", "68", "air 4% extra", "tea theaflavin vs oxid", "cof_op", "air_cof", "ag_lab", 66),
    A("tea-theaflavin-vs-oxid", "black tea", "TF", "0.72%", "0.90%", "0.88%", "5 K", "brisk", "oxid +12 min", 12, 1, "oxid floor", "blend", "0.60%", "rh 3% extra", "cocoa nibs vs fat", "tea_op", "ox_tea", "tf_lab", 65),
    A("cocoa-nibs-vs-fat", "cocoa liquor", "fat", "52.4%", "54.0%", "53.8%", "7 K", "grit", "press -4%", 10, 1, "liquor tank", "powder", "51.0%", "press 4% extra", "malt extract vs color", "nib_op", "pr_nib", "fat_lab", 64),
    A("malt-extract-vs-color", "malt extract", "EBC", "18", "12", "12.4", "8 K", "HMF", "vacuum +5%", 11, 1, "extract tank", "bakery", "22", "vacuum 3% extra", "wort gravity vs boil", "malt_op", "vac_malt", "ebc_lab", 63),
    A("wort-gravity-vs-boil", "wort", "OG", "1.048", "1.052", "1.0518", "4 K", "DMS", "boil +8 min", 8, 1, "kettle", "ferment", "1.044", "steam 0.4 t extra", "wine VA vs SO2", "wort_op", "bl_wort", "og_lab", 62),
    A("wine-va-vs-so2", "wine", "VA", "0.72 g/L", "0.50 g/L", "0.51", "3 K", "oxidation", "SO2 +8 ppm", 6, 1, "tank", "blend", "0.85", "SO2 8 ppm extra", "cider SO2 vs VA", "wn_op", "so2_wn", "va_lab", 61),
    A("cider-so2-vs-va", "cider", "VA", "0.68 g/L", "0.50 g/L", "0.52", "2 K", "acetobacter", "SO2 +10 ppm", 5, 1, "cider tank", "blend", "0.80", "SO2 10 ppm extra", "vinegar acetic vs mother", "cid_op", "so2_cid", "va_cid", 60),
    A("vinegar-acetic-vs-mother", "vinegar", "acetic", "4.8%", "5.0%", "4.98%", "4 K", "overox", "air +6%", 10, 1, "acetator", "food", "4.5%", "air 5% extra", "soy sauce NaCl vs TN", "vin_op", "air_vin", "ac_vin", 59),
    A("soy-sauce-nacl-vs-tn", "soy sauce", "TN", "1.42%", "1.55%", "1.54%", "5 K", "salt", "koji +4%", 48, 1, "moromi", "light", "1.30%", "koji 20 kg extra", "miso salt vs protease", "soy_op", "kj_soy", "tn_lab", 58),
    A("miso-salt-vs-protease", "miso", "salt", "12.8%", "11.5%", "11.6%", "3 K", "bitter", "koji +5%", 24, 1, "vat", "white", "13.5%", "koji 15 kg extra", "tofu coag vs yield", "miso_op", "kj_miso", "salt_miso", 57),
    A("tofu-coag-vs-yield", "tofu", "yield", "2.8 kg", "3.2 kg", "3.15 kg", "4 K", "soft", "nigari +3%", 6, 1, "vat", "firm", "2.5 kg", "nigari 2 kg extra", "tempeh temp vs RH", "tf_op", "nig_tf", "yld_lab", 56),
    A("tempeh-temp-vs-rh", "tempeh", "RH", "82%", "90%", "89%", "3 K", "spoil", "steam +4%", 8, 1, "incubator", "fresh", "75%", "steam 0.2 t extra", "kimchi salt vs pH", "tem_op", "stm_tem", "rh_lab", 55),
    A("kimchi-salt-vs-ph", "kimchi", "pH", "4.62", "4.40", "4.42", "2 K", "soft", "salt +0.3%", 12, 1, "crock", "jar", "4.80", "salt 2 kg extra", "sauerkraut salt vs pH", "kim_op", "nacl_kim", "ph_kim", 54),
    A("sauerkraut-salt-vs-ph", "sauerkraut", "pH", "4.18", "3.90", "3.92", "2 K", "pink", "salt +0.2%", 10, 1, "silo", "can", "4.40", "salt 3 kg extra", "pickle brine vs acid", "skr_op", "nacl_skr", "ph_skr", 53),
    A("pickle-brine-vs-acid", "pickle", "acid", "0.62%", "0.80%", "0.78%", "3 K", "bloater", "vinegar +4%", 8, 1, "tank", "spear", "0.50%", "vinegar 40 L extra", "olive NaCl vs pH", "pkl_op", "vin_pkl", "ac_pkl", 52),
    A("olive-nacl-vs-ph", "olive", "NaCl", "7.8%", "8.5%", "8.45%", "2 K", "gas", "brine +4%", 14, 1, "fermenter", "table", "7.2%", "salt 8 kg extra", "capers salt vs size", "olv_op", "br_olv", "nacl_olv", 51),
    A("capers-salt-vs-size", "capers", "NaCl", "18%", "22%", "21.6%", "2 K", "soft", "salt +4%", 9, 1, "barrel", "nonpareil", "16%", "salt 5 kg extra", "honey HMF vs heat", "cap_op", "nacl_cap", "nacl_caplab", 50),
    A("honey-hmf-vs-heat", "honey", "HMF", "28 ppm", "15 ppm", "14.5 ppm", "6 K", "dark", "vacuum +5%", 10, 1, "tank", "creamed", "40 ppm", "vacuum 3% extra", "maple brix vs color", "hon_op", "vac_hon", "hmf_lab", 49),
    A("maple-brix-vs-color", "maple", "brix", "64.8", "66.0", "65.9", "8 K", "dark", "vacuum +4%", 9, 1, "evap", "grade-A", "63.5", "vacuum 3% extra", "molasses brix vs ash", "map_op", "vac_map", "bx_map", 48),
    A("molasses-brix-vs-ash", "molasses", "ash", "12.4%", "10.0%", "10.1%", "10 K", "color", "centrif +5%", 8, 1, "tank", "feed", "13.5%", "wash 0.4 t extra", "starch moisture vs visc", "mol_op", "cf_mol", "ash_lab", 47),
    A("starch-moisture-vs-visc", "starch", "moisture", "14.2%", "13.0%", "13.05%", "9 K", "retro", "flash +4%", 7, 1, "silo", "food", "15.0%", "air 5% extra", "dextrose DE vs color", "st_op", "fl_st", "moi_st", 46),
    A("dextrose-de-vs-color", "dextrose", "DE", "94.2", "95.0", "94.9", "8 K", "color", "carbon +4%", 10, 1, "crystallizer", "pharma", "93.5", "carbon 15 kg extra", "maltose DE vs ash", "dex_op", "c_dex", "de_lab", 45),
    A("maltose-de-vs-ash", "maltose", "ash", "0.18%", "0.08%", "0.082%", "7 K", "color", "ix +5%", 12, 1, "tank", "confection", "0.22%", "resin 0.2 CV extra", "fructose DE vs color", "mal_op", "ix_mal", "ash_mal", 44),
    A("fructose-de-vs-color", "HFCS", "color", "28 IU", "15 IU", "14.5 IU", "6 K", "HMF", "carbon +4%", 9, 1, "tank", "beverage", "35 IU", "carbon 12 kg extra", "inulin DP vs ash", "hfcs_op", "c_hfcs", "iu_lab", 43),
    A("inulin-dp-vs-ash", "inulin", "DP", "9.2", "10.0", "9.9", "8 K", "hydrolysis", "spray +4%", 11, 1, "silo", "fiber", "8.5", "inlet 4 K extra", "pectin DE vs visc", "inu_op", "sd_inu", "dp_inu", 42),
    A("pectin-de-vs-visc", "pectin", "DE", "68%", "72%", "71.6%", "7 K", "set", "acid +3%", 10, 1, "hopper", "jam", "64%", "HCl 8 kg extra", "gelatin bloom vs visc", "pec_op", "ac_pec", "de_pec", 41),
    A("gelatin-bloom-vs-visc", "gelatin", "bloom", "220", "250", "248", "5 K", "color", "extract +4%", 14, 1, "hopper", "gummy", "200", "acid 10 kg extra", "agar gel vs ash", "gel_op", "ex_gel", "bl_lab", 40),
    A("agar-gel-vs-ash", "agar", "gel", "780 g/cm2", "900 g/cm2", "890", "8 K", "ash", "wash +5%", 12, 1, "hopper", "micro", "700", "water 0.3 t extra", "carrageenan gel vs K", "ag_op", "w_ag", "gel_ag", 39),
    A("carrageenan-gel-vs-k", "carrageenan", "gel", "420 g", "500 g", "495 g", "6 K", "syneresis", "KCl +3%", 9, 1, "hopper", "dairy", "380 g", "KCl 8 kg extra", "alginate M vs G", "car_op", "kcl_car", "gel_car", 38),
    A("alginate-m-vs-g", "alginate", "G-block", "38%", "42%", "41.7%", "7 K", "visc", "Ca +3%", 10, 1, "hopper", "bead", "34%", "CaCl2 6 kg extra", "chitosan DD vs visc", "alg_op", "ca_alg", "g_lab", 37),
    A("chitosan-dd-vs-visc", "chitosan", "DD", "82%", "88%", "87.5%", "8 K", "color", "NaOH +4%", 12, 1, "hopper", "wound", "78%", "NaOH 15 kg extra", "collagen MW vs OH", "chi_op", "naoh_chi", "dd_lab", 36),
    A("collagen-mw-vs-oh", "collagen", "Mw", "280 kDa", "320 kDa", "315 kDa", "5 K", "hydrolysis", "pepsin +3%", 14, 1, "tank", "capsule", "250 kDa", "enzyme 2 kg extra", "casein N vs ash", "col_op", "pep_col", "mw_col", 35),
    A("casein-n-vs-ash", "casein", "N", "14.8%", "15.5%", "15.4%", "6 K", "ash", "wash +4%", 11, 1, "hopper", "cheese-analog", "14.2%", "water 0.4 t extra", "whey protein vs ash", "cas_op", "w_cas", "n_cas", 34),
    A("whey-protein-vs-ash", "WPC", "protein", "78.4%", "80.0%", "79.8%", "5 K", "denature", "UF +4%", 10, 1, "silo", "bar", "76.0%", "diafil 0.3 t extra", "isolate protein vs N", "wpc_op", "uf_wpc", "pr_wpc", 33),
    A("isolate-protein-vs-n", "WPI", "protein", "88.2%", "90.0%", "89.7%", "4 K", "denature", "IX +4%", 12, 1, "silo", "rtd", "86.0%", "resin 0.2 CV extra", "soy isolate vs N", "wpi_op", "ix_wpi", "pr_wpi", 32),
    A("soy-isolate-vs-n", "SPI", "protein", "88.4%", "90.0%", "89.8%", "7 K", "NSI", "pH +0.2", 9, 1, "hopper", "meat-analog", "86.5%", "NaOH 8 kg extra", "pea protein vs N", "spi_op", "ph_spi", "pr_spi", 31),
    A("pea-protein-vs-n", "PPI", "protein", "78.6%", "80.0%", "79.7%", "6 K", "beany", "UF +4%", 11, 1, "hopper", "bar", "76.5%", "diafil 0.3 t extra", "wheat gluten vs protein", "ppi_op", "uf_ppi", "pr_ppi", 30),
    A("wheat-gluten-vs-protein", "gluten", "protein", "75.2%", "77.0%", "76.8%", "8 K", "color", "wash +4%", 10, 1, "hopper", "bread", "73.5%", "water 0.4 t extra", "corn gluten vs protein", "wg_op", "w_wg", "pr_wg", 29),
    A("corn-gluten-vs-protein", "corn gluten", "protein", "58.4%", "60.0%", "59.8%", "9 K", "color", "steep +4%", 12, 1, "hopper", "feed", "56.5%", "SO2 0.2 t extra", "rice protein vs N", "cg_op", "st_cg", "pr_cg", 28),
    A("rice-protein-vs-n", "rice protein", "protein", "78.2%", "80.0%", "79.7%", "7 K", "ash", "enzyme +4%", 14, 1, "hopper", "hypoallergenic", "76.0%", "enzyme 3 kg extra", "oat beta vs visc", "rp_op", "enz_rp", "pr_rp", 27),
    A("oat-beta-vs-visc", "oat beta-glucan", "beta", "18.4%", "20.0%", "19.8%", "6 K", "visc", "extract +4%", 13, 1, "hopper", "cereal", "16.5%", "water 0.3 t extra", "flour ash vs protein", "oat_op", "ex_oat", "bg_lab", 26),
    A("flour-ash-vs-protein", "flour", "ash", "0.62%", "0.55%", "0.552%", "5 K", "speck", "mill +4%", 8, 1, "silo", "cake", "0.70%", "streams 4% extra", "semolina ash vs gran", "fl_op", "ml_fl", "ash_fl", 25),
    A("semolina-ash-vs-gran", "semolina", "gran", "320 µm", "280 µm", "282 µm", "4 K", "speck", "sift +4%", 7, 1, "silo", "pasta", "360 µm", "sift 4% extra", "pasta moisture vs color", "sem_op", "sf_sem", "gr_lab", 24),
    A("pasta-moisture-vs-color", "pasta", "moisture", "13.2%", "12.5%", "12.52%", "8 K", "check", "dry +6%", 12, 1, "dryer", "long-cut", "13.8%", "air 5% extra", "noodle alkali vs color", "pst_op", "dry_pst", "moi_pst", 23),
    A("noodle-alkali-vs-color", "noodle", "kansui", "0.82%", "1.00%", "0.98%", "3 K", "yellow", "kansui +3%", 6, 1, "mixer", "ramen", "0.70%", "kansui 2 kg extra", "bread volume vs proof", "ndl_op", "kan_ndl", "alk_lab", 22),
    A("bread-volume-vs-proof", "bread", "volume", "820 mL", "900 mL", "890 mL", "2 K", "collapse", "proof +8 min", 8, 1, "proofer", "tin", "760 mL", "steam 0.1 t extra", "cracker moisture vs oven", "brd_op", "prf_brd", "vol_lab", 21),
    A("cracker-moisture-vs-oven", "cracker", "moisture", "4.8%", "3.5%", "3.55%", "12 K", "color", "zone3 +4%", 7, 1, "oven", "snack", "5.5%", "gas 3% extra", "biscuit spread vs fat", "crk_op", "z3_crk", "moi_crk", 20),
    A("biscuit-spread-vs-fat", "biscuit", "spread", "48 mm", "52 mm", "51.6 mm", "8 K", "spread", "fat +3%", 6, 1, "oven", "wirecut", "44 mm", "fat 8 kg extra", "cake volume vs SG", "bis_op", "fat_bis", "sp_lab", 19),
    A("cake-volume-vs-sg", "cake", "SG", "0.92", "0.85", "0.852", "5 K", "tunnel", "mix +20 s", 5, 1, "mixer", "layer", "0.98", "air 3% extra", "cookie spread vs sugar", "ck_op", "mx_ck", "sg_lab", 18),
    A("cookie-spread-vs-sugar", "cookie", "spread", "52 mm", "56 mm", "55.7 mm", "7 K", "spread", "sugar +3%", 6, 1, "oven", "rotary", "48 mm", "sugar 6 kg extra", "pretzel alkali vs color", "coo_op", "sug_coo", "sp_coo", 17),
    A("pretzel-alkali-vs-color", "pretzel", "L*", "52", "48", "48.4", "9 K", "blister", "lye +3%", 4, 1, "oven", "hard", "56", "NaOH 3 kg extra", "chip moisture vs fry", "prz_op", "lye_prz", "l_lab", 16),
    A("chip-moisture-vs-fry", "chip", "moisture", "2.4%", "1.8%", "1.82%", "10 K", "oil", "fry -4 C", 5, 1, "fryer", "kettle", "2.8%", "oil 0.2 t extra", "fry FFA vs color", "chp_op", "fr_chp", "moi_chp", 15),
    A("fry-ffa-vs-color", "fry oil", "FFA", "0.82%", "0.50%", "0.51%", "8 K", "color", "filter +4%", 8, 1, "fryer", "dump", "1.00%", "filter-aid 4 kg extra", "oil PV vs AV", "fry_op", "fil_fry", "ffa_fry", 14),
    A("oil-pv-vs-av", "veg oil", "PV", "4.8", "2.0", "2.1", "7 K", "rancid", "N2 +5%", 10, 1, "tank", "bottle", "6.0", "N2 4% extra", "shortening SFI vs IV", "oil_op", "n2_oil", "pv_lab", 13),
    A("shortening-sfi-vs-iv", "shortening", "SFI20", "22", "18", "18.2", "9 K", "grain", "N2 +4%", 11, 1, "votator", "bakery", "26", "N2 3% extra", "margarine SFI vs drop", "sh_op", "n2_sh", "sfi_lab", 12),
    A("margarine-sfi-vs-drop", "margarine", "drop", "32.4 C", "34.0 C", "33.8 C", "6 K", "oil-off", "hardstock +3%", 8, 1, "votator", "table", "31.0 C", "hard 8 kg extra", "mayonnaise visc vs oil", "mar_op", "hs_mar", "dp_mar", 11),
    A("mayonnaise-visc-vs-oil", "mayo", "visc", "18 Pa.s", "22 Pa.s", "21.6", "3 K", "break", "oil +3%", 6, 1, "colloid", "jar", "15", "oil 12 kg extra", "dressing visc vs acid", "mayo_op", "oil_mayo", "vis_mayo", 10),
    A("dressing-visc-vs-acid", "dressing", "visc", "2.8 Pa.s", "3.5 Pa.s", "3.45", "3 K", "split", "gum +4%", 5, 1, "tank", "bottle", "2.2", "xanthan 1 kg extra", "ketchup brix vs Bostwick", "drs_op", "gum_drs", "vis_drs", 9),
    A("ketchup-brix-vs-bostwick", "ketchup", "Bostwick", "9.4 cm", "7.5 cm", "7.6 cm", "5 K", "syneresis", "evap +4%", 8, 1, "kettle", "bottle", "10.5 cm", "steam 0.3 t extra", "mustard acid vs heat", "ket_op", "ev_ket", "bs_lab", 8),
    A("mustard-acid-vs-heat", "mustard", "acid", "1.8%", "2.2%", "2.18%", "4 K", "heat", "vinegar +4%", 7, 1, "tank", "jar", "1.5%", "vinegar 20 L extra", "salsa brix vs pH", "mus_op", "vin_mus", "ac_mus", 7),
    A("salsa-brix-vs-ph", "salsa", "pH", "4.28", "4.10", "4.12", "5 K", "gas", "acid +4%", 6, 1, "kettle", "jar", "4.40", "citric 3 kg extra", "soup salt vs solids", "sal_op", "ac_sal", "ph_sal", 6),
    A("soup-salt-vs-solids", "soup", "solids", "8.4%", "9.0%", "8.95%", "6 K", "scorch", "reduce +5%", 9, 1, "kettle", "can", "7.8%", "steam 0.3 t extra", "broth N vs salt", "soup_op", "rd_soup", "sol_soup", 5),
    A("broth-n-vs-salt", "broth", "N", "0.82%", "0.95%", "0.94%", "7 K", "salt", "reduce +4%", 10, 1, "kettle", "carton", "0.70%", "steam 0.4 t extra", "sauce brix vs visc", "br_op", "rd_br", "n_br", 4),
    A("sauce-brix-vs-visc", "sauce", "brix", "22.4", "24.0", "23.8", "8 K", "scorch", "evap +4%", 8, 1, "kettle", "jar", "21.0", "steam 0.3 t extra", "jam brix vs set", "sau_op", "ev_sau", "bx_sau", 3),
    A("jam-brix-vs-set", "jam", "brix", "64.2", "65.0", "64.9", "7 K", "weep", "boil +4 min", 4, 1, "pan", "jar", "63.0", "steam 0.2 t extra", "jelly brix vs set", "jam_op", "bl_jam", "bx_jam", 2),
    A("jelly-brix-vs-set", "jelly", "brix", "64.4", "65.0", "64.95", "6 K", "syneresis", "boil +3 min", 3, 1, "pan", "jar", "63.2", "pectin 2 kg extra", "preserve brix vs Aw", "jel_op", "bl_jel", "bx_jel", 73),
    A("preserve-brix-vs-aw", "preserve", "Aw", "0.84", "0.80", "0.802", "6 K", "mold", "sugar +3%", 5, 1, "pan", "jar", "0.86", "sugar 8 kg extra", "syrup brix vs color", "prv_op", "sug_prv", "aw_lab", 72),
    A("syrup-brix-vs-color", "syrup", "color", "38 IU", "25 IU", "24.5 IU", "8 K", "HMF", "carbon +4%", 9, 1, "tank", "bottle", "45 IU", "carbon 10 kg extra", "fondant SS vs crystal", "syr_op", "c_syr", "iu_syr", 71),
    A("fondant-ss-vs-crystal", "fondant", "SS", "88.2%", "89.0%", "88.9%", "5 K", "grit", "cool +4%", 6, 1, "beater", "center", "87.0%", "seed 2 kg extra", "yogurt next densify", "fon_op", "cl_fon", "ss_lab", 70),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(3391, s)
        if len(rec["transcript"]) < 8 or len(s["agents"]) != 3:
            raise SystemExit(s["slug"])
    print(f"self_check ok: {len(SCENARIOS)} plants", flush=True)


def hop_obs() -> bool:
    if busy(SBOX):
        print("sandbox-refusal reserved/writing; never hop there", flush=True)
    if not OBS_MILL.exists() or busy(OBS):
        return False
    n = round_txn.frontier_status(OBS)["next_round"]
    try:
        reservation = round_txn.reserve(OBS, n, 2)
    except (round_txn.TransactionError, FileExistsError, OSError) as exc:
        print(f"HOP obs reserve fail r{n}: {exc}", flush=True)
        return False
    token = reservation["token"]
    stage = Path(reservation["staging_dir"])
    try:
        proc = subprocess.run(
            [sys.executable, str(OBS_MILL), "--round", str(n), "--staging", str(stage)],
            cwd=REPO, text=True, capture_output=True, check=False,
        )
        print(proc.stdout, flush=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)
        pub = round_txn.publish(OBS, n, token)
    except Exception as exc:
        print(f"HOP obs fail r{n}: {exc}", flush=True)
        try:
            round_txn.abort(OBS, n, token)
        except round_txn.TransactionError:
            pass
        return False
    print(json.dumps({"hop": "observability-debug-factory", "round": n, "records": pub.get("records")}), flush=True)
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
            if not hop_obs():
                time.sleep(2)
            continue
        if idx >= len(SCENARIOS):
            print(f"MAC catalog exhausted at r{n}; hopping", flush=True)
            if not hop_obs():
                time.sleep(2)
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
            if not hop_obs():
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
