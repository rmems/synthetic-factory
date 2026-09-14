#!/usr/bin/env python3
"""MAC mill r3466+. Unique textile/paper/mineral/water plants. Never sbox if reserved/writing."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205d", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

AGENTIC = REPO / "outputs/raw/2026-08-19-agentic"
FACTORY = AGENTIC / "multi-agent-coordination-factory"
SBOX = AGENTIC / "sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("cotton-micronaire-vs-trash", "cotton", "micronaire", "5.2", "4.5", "4.55", "4 K", "neps", "clean +4%", 8, 1, "bale", "card", "5.6", "lint 0.3 t extra", "wool micron vs VM", "cot_op", "cl_cot", "mic_lab", 70),
    A("wool-micron-vs-vm", "wool", "VM", "2.4%", "1.2%", "1.22%", "5 K", "break", "scour +4%", 10, 1, "lot", "top", "3.0%", "detergent 8 kg extra", "silk denier vs sericin", "wl_op", "sc_wl", "vm_lab", 69),
    A("silk-denier-vs-sericin", "silk", "sericin", "22%", "18%", "18.2%", "3 K", "break", "degum +4%", 12, 1, "skein", "yarn", "25%", "soap 4 kg extra", "linen hackling vs length", "sk_op", "dg_sk", "ser_lab", 68),
    A("linen-hackling-vs-length", "linen", "length", "42 mm", "50 mm", "49 mm", "4 K", "tow", "hackling +4%", 9, 1, "lot", "yarn", "36 mm", "hack 4% extra", "denim indigo vs shade", "ln_op", "hk_ln", "len_lab", 67),
    A("denim-indigo-vs-shade", "denim", "K/S", "18.2", "22.0", "21.6", "6 K", "streak", "indigo +4%", 8, 1, "range", "garment", "16.0", "indigo 12 kg extra", "yarn count vs CSP", "dn_op", "ind_dn", "ks_lab", 66),
    A("yarn-count-vs-csp", "yarn", "CSP", "1820", "2100", "2080", "3 K", "ends", "twist +4%", 7, 1, "lot", "weave", "1650", "twist 3% extra", "fabric shrink vs sanfor", "yn_op", "tw_yn", "csp_lab", 65),
    A("fabric-shrink-vs-sanfor", "fabric", "shrink", "4.8%", "2.0%", "2.1%", "5 K", "hand", "sanfor +4%", 8, 1, "lot", "cut", "6.0%", "steam 0.3 t extra", "knit gsm vs loop", "fab_op", "sf_fab", "sh_fab", 64),
    A("knit-gsm-vs-loop", "knit", "gsm", "142", "160", "158", "3 K", "barre", "loop +4%", 6, 1, "roll", "dye", "130", "stitch 3% extra", "dye K/S vs level", "kn_op", "lp_kn", "gsm_lab", 63),
    A("dye-k-s-vs-level", "dye", "level", "3.8 DE", "1.0 DE", "1.1 DE", "4 K", "unlevel", "salt +4%", 9, 1, "lot", "print", "5.0 DE", "salt 8 kg extra", "print paste vs visc", "dy_op", "nacl_dy", "de_dy", 62),
    A("print-paste-vs-visc", "print paste", "visc", "18 Pa.s", "24 Pa.s", "23.5", "3 K", "bleed", "thickener +4%", 7, 1, "lot", "screen", "14", "alginate 3 kg extra", "finish resin vs hand", "pr_op", "th_pr", "vis_pr", 61),
    A("finish-resin-vs-hand", "resin finish", "DP", "3.2", "4.0", "3.95", "8 K", "harsh", "resin +4%", 8, 1, "lot", "shirt", "2.8", "resin 6 kg extra", "mercerize Baume vs luster", "fn_op", "rs_fn", "dp_fn", 60),
    A("mercerize-baume-vs-luster", "mercerize", "Baume", "26", "30", "29.6", "5 K", "tender", "NaOH +4%", 6, 1, "lot", "poplin", "22", "NaOH 0.2 t extra", "newsprint freeness vs caliper", "mer_op", "naoh_mer", "be_lab", 59),
    A("newsprint-freeness-vs-caliper", "newsprint", "CSF", "82 mL", "100 mL", "98 mL", "6 K", "lint", "refine +4%", 8, 1, "reel", "press", "70 mL", "kWh 4% extra", "linerboard STFI vs basis", "np_op", "rf_np", "csf_lab", 58),
    A("linerboard-stfi-vs-basis", "liner", "STFI", "18.2", "22.0", "21.6", "7 K", "crush", "starch +4%", 7, 1, "reel", "box", "16.0", "starch 20 kg extra", "tissue bulk vs tensile", "lnr_op", "st_lnr", "stfi_lab", 57),
    A("tissue-bulk-vs-tensile", "tissue", "bulk", "8.4 cm3/g", "10.0", "9.8", "5 K", "pinhole", "crepe +4%", 6, 1, "reel", "bath", "7.5", "crepe 3% extra", "fluting CMT vs moisture", "tis_op", "cr_tis", "bk_lab", 56),
    A("fluting-cmt-vs-moisture", "fluting", "CMT", "182 N", "220 N", "216 N", "6 K", "crush", "starch +4%", 8, 1, "reel", "corrugate", "160 N", "starch 15 kg extra", "coated paper gloss vs PPS", "flt_op", "st_flt", "cmt_lab", 55),
    A("coated-paper-gloss-vs-pps", "LWC", "gloss", "48", "55", "54.5", "5 K", "mottle", "coat +4%", 7, 1, "reel", "offset", "42", "coat 12 kg extra", "sack kraft vs TEA", "lwc_op", "ct_lwc", "gl_lab", 54),
    A("sack-kraft-vs-tea", "sack kraft", "TEA", "8.2 J/m2", "10.0", "9.8", "8 K", "break", "refine +4%", 9, 1, "reel", "sack", "7.0", "kWh 4% extra", "dissolving pulp vs alpha", "sk_op", "rf_sk", "tea_lab", 53),
    A("dissolving-pulp-vs-alpha", "dissolving", "alpha", "91.2%", "92.5%", "92.4%", "7 K", "ash", "cook +4%", 10, 1, "bale", "viscose", "90.0%", "EA 0.3 t extra", "TMP freeness vs shive", "dp_op", "ck_dp", "al_lab", 52),
    A("tmp-freeness-vs-shive", "TMP", "shive", "0.42%", "0.20%", "0.21%", "9 K", "speck", "energy +4%", 8, 1, "chest", "news", "0.55%", "kWh 5% extra", "lime kiln vs avails", "tmp_op", "en_tmp", "sh_lab", 51),
    A("lime-kiln-vs-avails", "lime kiln", "avail CaO", "88.4%", "92.0%", "91.7%", "40 K", "ring", "excess-air +4%", 12, 1, "silo", "recaust", "86.0%", "oil 0.4 t extra", "recaust TTA vs EA", "lk_op", "air_lk", "cao_lab", 50),
    A("recaust-tta-vs-ea", "recaust", "EA", "78 g/L", "85 g/L", "84.5 g/L", "8 K", "GR", "lime +4%", 9, 1, "tank", "cook", "74 g/L", "lime 0.5 t extra", "ClO2 gen vs yield", "rc_op", "lm_rc", "ea_lab", 49),
    A("cl02-gen-vs-yield", "ClO2", "yield", "88%", "94%", "93.6%", "6 K", "Cl2", "methanol +3%", 8, 1, "tower", "D1", "84%", "MeOH 40 kg extra", "gypsum purity vs H2O", "clo_op", "meoh_clo", "yld_clo", 48),
    A("gypsum-purity-vs-h2o", "gypsum", "purity", "92.4%", "95.0%", "94.8%", "10 K", "moisture", "calcine +4%", 11, 1, "silo", "board", "90.5%", "gas 4% extra", "lime LOI vs CaO", "gyp_op", "cl_gyp", "pur_lab", 47),
    A("lime-loi-vs-cao", "hydrated lime", "LOI", "24.8%", "24.0%", "24.05%", "8 K", "overburn", "hydrate +4%", 10, 1, "silo", "FGD", "25.5%", "water 0.3 t extra", "cement free lime vs fCaO", "hl_op", "hyd_hl", "loi_lab", 46),
    A("cement-free-lime-vs-fcao", "cement", "fCaO", "1.8%", "1.0%", "1.02%", "20 K", "expansion", "gypsum +3%", 8, 1, "silo", "type-I", "2.2%", "gypsum 0.4 t extra", "clinker LSF vs C3S", "cem_op", "gyp_cem", "fcao_lab", 45),
    A("clinker-lsf-vs-c3s", "clinker", "C3S", "52%", "58%", "57.6%", "30 K", "free-lime", "LSF +3%", 14, 1, "silo", "blend", "48%", "lime 0.6 t extra", "flyash LOI vs fineness", "clk_op", "lsf_clk", "c3s_lab", 44),
    A("flyash-loi-vs-fineness", "fly ash", "LOI", "4.8%", "3.0%", "3.05%", "12 K", "carbon", "classify +4%", 9, 1, "silo", "concrete", "5.5%", "air 4% extra", "slag Blaine vs activity", "fa_op", "cl_fa", "loi_fa", 43),
    A("slag-blaine-vs-activity", "GGBS", "Blaine", "380 m2/kg", "420", "416", "8 K", "moisture", "mill +4%", 10, 1, "silo", "blend", "350", "kWh 4% extra", "silica fume vs SiO2", "slg_op", "ml_slg", "bl_slg", 42),
    A("silica-fume-vs-sio2", "silica fume", "SiO2", "88.4%", "92.0%", "91.7%", "6 K", "carbon", "classify +4%", 8, 1, "silo", "HPC", "86.0%", "air 3% extra", "metakaolin vs activity", "sf_op", "cl_sf", "sio_lab", 41),
    A("metakaolin-vs-activity", "metakaolin", "activity", "108%", "115%", "114%", "15 K", "overcalcine", "temp -4 K", 10, 1, "silo", "white", "100%", "hold 8 min extra", "brick absorption vs firing", "mk_op", "t_mk", "act_lab", 40),
    A("brick-absorption-vs-firing", "brick", "abs", "8.4%", "6.0%", "6.1%", "40 K", "black-core", "soak +4%", 20, 1, "kiln", "facing", "9.5%", "gas 4% extra", "tile warpage vs shrink", "brk_op", "sk_brk", "abs_lab", 39),
    A("tile-warpage-vs-shrink", "tile", "warpage", "0.82 mm", "0.40 mm", "0.42 mm", "25 K", "bow", "profile +4%", 16, 1, "kiln", "floor", "1.10 mm", "cycle 4 min extra", "sanitary crazing vs glaze", "tl_op", "pr_tl", "wp_lab", 38),
    A("sanitary-crazing-vs-glaze", "sanitaryware", "crazing", "8%", "1%", "1.2%", "18 K", "dunt", "glaze +3%", 14, 1, "kiln", "rework", "12%", "glaze 8 kg extra", "refractory PCE vs porosity", "sw_op", "gl_sw", "cr_lab", 37),
    A("refractory-pce-vs-porosity", "refractory", "porosity", "18.4%", "14.0%", "14.2%", "30 K", "spall", "press +4%", 12, 1, "lot", "ladle", "20%", "pressure 4% extra", "glass seed vs fining", "rf_op", "pr_rf", "por_lab", 36),
    A("glass-seed-vs-fining", "container glass", "seeds", "8 /cm3", "2 /cm3", "2.1", "20 K", "stone", "sulfate +3%", 15, 1, "forehearth", "amber", "12", "sulfate 6 kg extra", "float tin vs bottom", "gl_op", "su_gl", "sd_lab", 35),
    A("float-tin-vs-bottom", "float glass", "tin", "28 µg/cm2", "15", "15.4", "12 K", "bloom", "N2 +4%", 10, 1, "lehr", "low-iron", "36", "N2 3% extra", "fiber glass vs tex", "ft_op", "n2_ft", "tin_lab", 34),
    A("fiber-glass-vs-tex", "E-glass", "tex", "620", "600", "602", "14 K", "bead", "bushing +3%", 8, 1, "creel", "roving", "650", "temp 3 K extra", "optical fiber vs OH", "eg_op", "bs_eg", "tex_lab", 33),
    A("optical-fiber-vs-oh", "SMF", "OH", "0.42 ppb", "0.20 ppb", "0.21", "18 K", "loss", "Cl2 +4%", 12, 1, "preform", "G.652", "0.55", "Cl2 4% extra", "anode coke vs VCM", "smf_op", "cl_smf", "oh_smf", 32),
    A("anode-coke-vs-vcm", "anode coke", "VCM", "0.62%", "0.40%", "0.41%", "16 K", "puffing", "calcine +4%", 14, 1, "silo", "anode", "0.75%", "gas 4% extra", "pitch QI vs SP", "ac_op", "cl_ac", "vcm_lab", 31),
    A("pitch-qi-vs-sp", "binder pitch", "QI", "8.4%", "6.0%", "6.1%", "12 K", "coke", "flash +4%", 11, 1, "tank", "Soderberg", "9.5%", "steam 0.3 t extra", "electrode resist vs bake", "pt_op", "fl_pt", "qi_lab", 30),
    A("electrode-resist-vs-bake", "graphite electrode", "resist", "6.8 µΩm", "5.5", "5.55", "20 K", "crack", "bake +4%", 18, 1, "lot", "EAF", "7.5", "cycle 20 min extra", "cathode sodium vs life", "el_op", "bk_el", "rs_lab", 29),
    A("cathode-sodium-vs-life", "Al cathode", "Na", "820 ppm", "400 ppm", "410 ppm", "15 K", "heave", "bake +4%", 16, 1, "lot", "pot", "1000 ppm", "pitch 8 kg extra", "copper cathode vs S", "ct_op", "bk_ct", "na_lab", 28),
    A("copper-cathode-vs-s", "Cu cathode", "S", "18 ppm", "8 ppm", "8.2 ppm", "8 K", "nodule", "glue +3%", 9, 1, "cell", "rod", "24 ppm", "glue 2 kg extra", "nickel cathode vs Co", "cu_op", "gl_cu", "s_cu", 27),
    A("nickel-cathode-vs-co", "Ni cathode", "Co", "0.18%", "0.08%", "0.082%", "7 K", "pinhole", "pH +0.2", 10, 1, "cell", "plating", "0.24%", "boric 4 kg extra", "cobalt hydroxide vs Mg", "ni_op", "ph_ni", "co_lab", 26),
    A("cobalt-hydroxide-vs-mg", "Co(OH)2", "Mg", "0.42%", "0.15%", "0.16%", "6 K", "filter", "wash +5%", 12, 1, "lot", "NMC", "0.55%", "water 0.4 t extra", "manganese SO4 vs K", "coh_op", "w_coh", "mg_lab", 25),
    A("manganese-so4-vs-k", "MnSO4", "K", "180 ppm", "80 ppm", "82 ppm", "8 K", "color", "recryst +4%", 14, 1, "hopper", "NMC", "240 ppm", "water 0.3 t extra", "rare earth Nd vs Pr", "mn_op", "rc_mn", "k_lab", 24),
    A("rare-earth-nd-vs-pr", "NdPr", "Nd", "74.2%", "75.5%", "75.4%", "10 K", "Ce", "SX +4%", 16, 1, "lot", "magnet", "73.0%", "extractant 8 L extra", "tungsten APT vs Mo", "nd_op", "sx_nd", "nd_lab", 23),
    A("tungsten-apt-vs-mo", "APT", "Mo", "42 ppm", "20 ppm", "21 ppm", "9 K", "color", "SX +4%", 13, 1, "hopper", "carbide", "55 ppm", "amine 4 L extra", "moly oxide vs Cu", "apt_op", "sx_apt", "mo_lab", 22),
    A("moly-oxide-vs-cu", "MoO3", "Cu", "0.18%", "0.05%", "0.052%", "14 K", "fume", "roast +4%", 12, 1, "lot", "steel", "0.24%", "air 4% extra", "vanadium V2O5 vs Si", "mo_op", "rs_mo", "cu_mo", 21),
    A("vanadium-v2o5-vs-si", "V2O5", "Si", "0.22%", "0.08%", "0.082%", "12 K", "insol", "leach +4%", 11, 1, "hopper", "ferro", "0.30%", "NaOH 0.2 t extra", "titanium sponge vs O", "v_op", "lc_v", "si_v", 20),
    A("titanium-sponge-vs-o", "Ti sponge", "O", "0.18%", "0.08%", "0.082%", "18 K", "nitride", "Mg +3%", 15, 1, "lot", "ingot", "0.24%", "Mg 8 kg extra", "zircon SiO2 vs Hf", "ti_op", "mg_ti", "o_lab", 19),
    A("zircon-sio2-vs-hf", "zircon", "Hf", "1.8%", "2.2%", "2.18%", "16 K", "Si", "chlorinate +4%", 14, 1, "lot", "Zr", "1.5%", "Cl2 0.3 t extra", "graphite FC vs ash", "zr_op", "cl_zr", "hf_lab", 18),
    A("graphite-fc-vs-ash", "graphite", "FC", "98.4%", "99.2%", "99.15%", "20 K", "ash", "purify +4%", 16, 1, "lot", "anode", "97.8%", "HF 8 kg extra", "petroleum coke vs S", "gr_op", "pur_gr", "fc_lab", 17),
    A("petroleum-coke-vs-s", "petcoke", "S", "4.8%", "3.5%", "3.55%", "18 K", "V", "calcine +4%", 12, 1, "silo", "fuel", "5.5%", "air 4% extra", "LNG Wobbe vs N2", "pc_op", "cl_pc", "s_pc", 16),
    A("lng-wobbe-vs-n2", "LNG", "Wobbe", "52.8", "54.0", "53.9", "10 K", "N2", "N2-reject +4%", 11, 1, "tank", "sendout", "51.5", "reject 3% extra", "LPG C3 vs C4", "lng_op", "n2_lng", "wb_lab", 15),
    A("lpg-c3-vs-c4", "LPG", "C3", "38%", "42%", "41.7%", "8 K", "C5", "reflux +4%", 9, 1, "sphere", "auto", "34%", "reflux 3% extra", "CNG methane vs inerts", "lpg_op", "rfx_lpg", "c3_lab", 14),
    A("cng-methane-vs-inerts", "CNG", "CH4", "92.4%", "96.0%", "95.7%", "6 K", "inerts", "PSA +4%", 10, 1, "cascade", "vehicle", "90.0%", "purge 3% extra", "hydrogen CO vs PSA", "cng_op", "psa_cng", "ch4_lab", 13),
    A("hydrogen-co-vs-psa", "H2", "CO", "8 ppm", "2 ppm", "2.1 ppm", "8 K", "CH4", "PSA +4%", 9, 1, "tube", "PEM", "12 ppm", "purge 3% extra", "ammonia storage vs O2", "h2_op", "psa_h2", "co_h2", 12),
    A("ammonia-storage-vs-o2", "NH3 storage", "O2", "8 ppm", "2 ppm", "2.2 ppm", "4 K", "oil", "N2 +4%", 8, 1, "tank", "export", "12 ppm", "N2 3% extra", "urea formal vs free", "nh3s_op", "n2_nh3s", "o2_lab", 11),
    A("urea-formal-vs-free", "UF concentrate", "free-F", "0.42%", "0.20%", "0.21%", "9 K", "gel", "urea +4%", 10, 1, "tank", "resin", "0.55%", "urea 0.3 t extra", "melamine purity vs ash", "ufc_op", "ur_ufc", "ff_ufc", 10),
    A("melamine-purity-vs-ash", "melamine", "purity", "99.42%", "99.80%", "99.78%", "12 K", "ash", "recryst +4%", 14, 1, "hopper", "laminate", "99.20%", "water 0.3 t extra", "cyanuric vs N", "mel_op", "rc_mel", "pur_mel", 9),
    A("cyanuric-vs-n", "cyanuric", "N", "31.8%", "32.4%", "32.35%", "10 K", "biuret", "acid +3%", 11, 1, "hopper", "pool", "31.2%", "acid 20 kg extra", "hydroxylamine vs SOx", "cya_op", "ac_cya", "n_cya", 8),
    A("hydroxylamine-vs-sox", "HAS", "SOx", "180 ppm", "50 ppm", "52 ppm", "6 K", "decomp", "air-cut 4%", 8, 1, "tank", "capro", "240 ppm", "N2 3% extra", "sodium chlorate vs NaCl", "has_op", "air_has", "sox_lab", 7),
    A("sodium-chlorate-vs-nacl", "NaClO3", "NaCl", "0.22%", "0.08%", "0.082%", "8 K", "moisture", "centrif +4%", 9, 1, "hopper", "ClO2", "0.30%", "wash 0.2 t extra", "sodium chlorite vs NaOH", "clo3_op", "cf_clo3", "nacl_clo3", 6),
    A("sodium-chlorite-vs-naoh", "NaClO2", "NaOH", "1.8%", "0.5%", "0.52%", "5 K", "ClO2", "SO2 +3%", 7, 1, "tank", "bleach", "2.4%", "SO2 8 kg extra", "peracetic vs H2O2", "clo2s_op", "so2_clo2s", "naoh_clo2s", 5),
    A("peracetic-vs-h2o2", "PAA", "H2O2", "4.8%", "3.0%", "3.05%", "4 K", "decomp", "acetic +3%", 6, 1, "tank", "CIP", "6.0%", "acetic 20 kg extra", "ozone dose vs ORP", "paa_op", "hoac_paa", "h2o2_paa", 4),
    A("ozone-dose-vs-orp", "ozone", "ORP", "620 mV", "750 mV", "745 mV", "3 K", "bromate", "O3 +4%", 5, 1, "contactor", "potable", "550 mV", "O2 4% extra", "UV fluence vs T10", "o3_op", "o3_dose", "orp_lab", 3),
    A("uv-fluence-vs-t10", "UV", "T10", "72%", "80%", "79%", "2 K", "sleeve", "wipe +4%", 6, 1, "channel", "reuse", "65%", "wipe 4 min extra", "RO permeate vs cond", "uv_op", "wp_uv", "t10_lab", 2),
    A("ro-permeate-vs-cond", "RO", "cond", "28 µS", "15 µS", "15.4 µS", "4 K", "silica", "CIP +4%", 10, 1, "tank", "boiler", "36 µS", "CIP 8 min extra", "EDI silica vs res", "ro_op", "cip_ro", "cd_lab", 73),
    A("edi-silica-vs-res", "EDI", "SiO2", "18 ppb", "5 ppb", "5.2 ppb", "3 K", "leakage", "current +4%", 8, 1, "stack", "UPW", "24 ppb", "A 3% extra", "IX leakage vs sodium", "edi_op", "i_edi", "si_edi", 72),
    A("ix-leakage-vs-sodium", "IX", "Na", "8 ppb", "2 ppb", "2.1 ppb", "2 K", "silica", "regen +4%", 12, 1, "bed", "polisher", "12 ppb", "HCl 20 L extra", "media NTU vs headloss", "ix_op", "rg_ix", "na_ix", 71),
    A("media-ntu-vs-headloss", "filter", "NTU", "0.42", "0.15", "0.16", "1 K", "breakthrough", "backwash +4%", 8, 1, "cell", "clearwell", "0.55", "air 4% extra", "DAF SS vs recycle", "md_op", "bw_md", "ntu_lab", 70),
    A("daf-ss-vs-recycle", "DAF", "SS", "18 mg/L", "8 mg/L", "8.2 mg/L", "2 K", "float", "recycle +4%", 7, 1, "basin", "filter", "24 mg/L", "air 4% extra", "clarifier sludge vs RAS", "daf_op", "rc_daf", "ss_lab", 69),
    A("clarifier-sludge-vs-ras", "clarifier", "ESS", "22 mg/L", "12 mg/L", "12.4 mg/L", "1 K", "blanket", "RAS +4%", 6, 1, "tank", "filter", "28 mg/L", "RAS 4% extra", "digester VFA vs alk", "cl_op", "ras_cl", "ess_lab", 68),
    A("digester-vfa-vs-alk", "digester", "VFA/alk", "0.42", "0.25", "0.26", "2 K", "foam", "feed-cut 4%", 10, 1, "digester", "dewater", "0.55", "hold 4 h extra", "dewater cake vs polymer", "dg_op", "fd_dg", "vfa_lab", 67),
    A("dewater-cake-vs-polymer", "centrifuge", "cake", "18.4%", "22.0%", "21.7%", "3 K", "capture", "polymer +4%", 8, 1, "hopper", "landfill", "16.5%", "polymer 4 kg extra", "cotton next densify", "dw_op", "pol_dw", "ck_lab", 66),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(3466, s)
        if len(rec["transcript"]) < 8 or len(s["agents"]) != 3:
            raise SystemExit(s["slug"])
    print(f"self_check ok: {len(SCENARIOS)} plants", flush=True)


def main() -> int:
    self_check()
    published = []
    idx = 0
    start = time.monotonic()
    while time.monotonic() - start < DEADLINE_S:
        n = round_txn.frontier_status(FACTORY)["next_round"]
        if busy(FACTORY):
            print(f"MAC r{n} reserved/writing; wait (sbox skipped if reserved/writing={busy(SBOX)})", flush=True)
            time.sleep(2)
            continue
        if idx >= len(SCENARIOS):
            print(f"MAC catalog exhausted at r{n}", flush=True)
            break
        spec = SCENARIOS[idx]
        idx += 1
        try:
            reservation = round_txn.reserve(FACTORY, n, 1)
        except (round_txn.TransactionError, FileExistsError, OSError) as exc:
            print(f"HOP reserve r{n}: {exc}", flush=True)
            idx -= 1
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
