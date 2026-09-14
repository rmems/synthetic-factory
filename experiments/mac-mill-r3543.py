#!/usr/bin/env python3
"""MAC mill r3543+. Unique energy/ag/electronics plants. Never sbox if reserved/writing."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205e", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
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
    A("solar-iv-vs-fill", "module", "FF", "74.2%", "76.5%", "76.3%", "8 K", "PID", "anneal +4%", 12, 1, "lot", "utility", "72.0%", "hold 8 min extra", "wind pitch vs power", "pv_op", "an_pv", "ff_lab", 68),
    A("wind-pitch-vs-power", "turbine", "Cp", "0.42", "0.47", "0.465", "3 K", "stall", "pitch +2 deg", 6, 1, "nacelle", "farm", "0.38", "pitch 2 deg extra", "hydro cavitation vs head", "wt_op", "pt_wt", "cp_lab", 67),
    A("hydro-cavitation-vs-head", "Francis", "sigma", "0.12", "0.18", "0.175", "2 K", "pitting", "head -4%", 8, 1, "unit", "peaking", "0.08", "gate 3% extra", "geothermal NCG vs steam", "hy_op", "hd_hy", "sg_lab", 66),
    A("geothermal-ncg-vs-steam", "geo steam", "NCG", "1.8%", "0.8%", "0.82%", "6 K", "NCG", "vent +4%", 9, 1, "well", "binary", "2.4%", "vent 3% extra", "biomass moisture vs steam", "geo_op", "vt_geo", "ncg_lab", 65),
    A("biomass-moisture-vs-steam", "boiler", "steam", "38 t/h", "42 t/h", "41.6 t/h", "12 K", "slag", "dry +4%", 10, 1, "pile", "CHP", "34 t/h", "air 4% extra", "CHP heat vs power", "bm_op", "dry_bm", "st_lab", 64),
    A("chp-heat-vs-power", "CHP", "heat", "18 MW", "22 MW", "21.6 MW", "8 K", "trip", "extract +4%", 7, 1, "unit", "district", "15 MW", "extract 3% extra", "district dT vs flow", "chp_op", "ex_chp", "ht_lab", 63),
    A("district-dt-vs-flow", "DH", "dT", "28 K", "35 K", "34.5 K", "4 K", "bypass", "flow-cut 4%", 8, 1, "loop", "substation", "22 K", "valve 4% extra", "boiler O2 vs CO", "dh_op", "fl_dh", "dt_lab", 62),
    A("boiler-o2-vs-co", "package boiler", "CO", "180 ppm", "50 ppm", "52 ppm", "10 K", "CO", "O2 +0.4%", 6, 1, "drum", "steam", "250 ppm", "air 0.4% extra", "turbine heatrate vs throttle", "bl_op", "o2_bl", "co_bl", 61),
    A("turbine-heatrate-vs-throttle", "ST", "HR", "9200", "8600", "8620", "5 K", "vib", "throttle +3%", 8, 1, "unit", "export", "9600", "load 3% extra", "HVAC COP vs approach", "st_op", "th_st", "hr_lab", 60),
    A("hvac-cop-vs-approach", "RTU", "COP", "2.8", "3.4", "3.35", "4 K", "icing", "charge +3%", 9, 1, "unit", "office", "2.4", "charge 0.2 kg extra", "chiller kW/ton vs lift", "rtu_op", "ch_rtu", "cop_lab", 59),
    A("chiller-kwton-vs-lift", "chiller", "kW/ton", "0.72", "0.58", "0.59", "3 K", "surge", "lift -4%", 7, 1, "plant", "campus", "0.82", "CW 3% extra", "cooling approach vs cycles", "ch_op", "lf_ch", "kw_lab", 58),
    A("cooling-approach-vs-cycles", "CT", "approach", "8.4 K", "5.0 K", "5.2 K", "2 K", "scale", "blowdown +4%", 8, 1, "basin", "chiller", "10 K", "blowdown 4% extra", "refrig superheat vs SH", "ct_op", "bd_ct", "ap_lab", 57),
    A("refrig-superheat-vs-sh", "DX", "SH", "18 K", "8 K", "8.4 K", "3 K", "flood", "TXV +3%", 6, 1, "rack", "case", "22 K", "TXV 3% extra", "heatpump COP vs defrost", "dx_op", "txv_dx", "sh_lab", 56),
    A("heatpump-cop-vs-defrost", "ASHP", "COP", "2.4", "3.1", "3.05", "4 K", "frost", "defrost +4%", 8, 1, "unit", "home", "2.0", "defrost 4 min extra", "AHU CO2 vs OA", "hp_op", "df_hp", "cop_hp", 55),
    A("ahus-co2-vs-oa", "AHU", "CO2", "1180 ppm", "850 ppm", "860 ppm", "2 K", "IAQ", "OA +8%", 6, 1, "AHU", "classroom", "1400 ppm", "OA 8% extra", "VAV static vs min", "ahu_op", "oa_ahu", "co2_lab", 54),
    A("vav-static-vs-min", "VAV", "static", "1.8 in", "1.2 in", "1.22 in", "1 K", "noise", "reset -0.3 in", 5, 1, "floor", "office", "2.2 in", "reset 0.3 extra", "fumehood sash vs face", "vav_op", "rs_vav", "st_vav", 53),
    A("fumehood-sash-vs-face", "hood", "face", "62 fpm", "80 fpm", "78 fpm", "1 K", "escape", "sash -4 in", 4, 1, "lab", "chem", "50 fpm", "sash 4 in extra", "cleanroom ACH vs ISO", "fh_op", "sash_fh", "fc_lab", 52),
    A("cleanroom-ach-vs-iso", "ISO7", "0.5µm", "280k", "150k", "155k", "2 K", "count", "ACH +12%", 6, 1, "suite", "fill", "360k", "fan 12% extra", "coldstore temp vs defrost", "cr_op", "ach_cr", "pt_cr", 51),
    A("coldstore-temp-vs-defrost", "coldstore", "T", "-16 C", "-18 C", "-17.8 C", "3 K", "frost", "defrost +4%", 8, 1, "room", "frozen", "-14 C", "defrost 4 min extra", "reefer set vs pulp", "cs_op", "df_cs", "t_cs", 50),
    A("reefer-set-vs-pulp", "reefer", "pulp", "5.8 C", "4.0 C", "4.1 C", "2 K", "hotspot", "set -1.5 K", 5, 1, "box", "export", "7.0 C", "air 4% extra", "ship bunker vs CSO", "rf_op", "st_rf", "pp_lab", 49),
    A("ship-bunker-vs-cso", "bunker", "CSO", "0.42%", "0.10%", "0.11%", "8 K", "compat", "blend +4%", 10, 1, "tank", "ECA", "0.55%", "MGO 8 t extra", "ballast BWTS vs TRO", "bn_op", "bl_bn", "cso_lab", 48),
    A("ballast-bwts-vs-tro", "BWTS", "TRO", "18 ppm", "8 ppm", "8.2 ppm", "3 K", "neutral", "dose-cut 4%", 7, 1, "tank", "port", "24 ppm", "neutral 4% extra", "scrubber SO2 vs alk", "bw_op", "ds_bw", "tro_lab", 47),
    A("scrubber-so2-vs-alk", "EGCS", "SO2/CO2", "8.4", "4.0", "4.1", "4 K", "pH", "alk +4%", 8, 1, "loop", "open", "10", "NaOH 20 kg extra", "EGCS PAH vs pH", "eg_op", "alk_eg", "so2_eg", 46),
    A("egcs-pah-vs-ph", "EGCS water", "PAH", "42 µg/L", "20 µg/L", "21 µg/L", "3 K", "pH", "bleed +4%", 6, 1, "loop", "closed", "55 µg/L", "bleed 4% extra", "hull fouling vs speed", "pah_op", "bl_pah", "pah_lab", 45),
    A("hull-fouling-vs-speed", "hull", "delta-P", "8.4%", "3.0%", "3.1%", "2 K", "foul", "clean +4%", 12, 1, "hull", "voyage", "11%", "clean 4 h extra", "prop cavitation vs rpm", "hl_op", "cl_hl", "dp_hl", 44),
    A("prop-cavitation-vs-rpm", "prop", "cav", "0.18", "0.08", "0.082", "2 K", "erosion", "rpm -4%", 5, 1, "shaft", "harbor", "0.24", "pitch 3% extra", "anchor scope vs hold", "pr_op", "rpm_pr", "cv_lab", 43),
    A("anchor-scope-vs-hold", "anchor", "hold", "0.62", "0.85", "0.84", "1 K", "drag", "scope +4%", 6, 1, "rode", "anchorage", "0.50", "chain 15 m extra", "cargo lashing vs GM", "an_op", "sc_an", "hd_lab", 42),
    A("cargo-lashing-vs-gm", "cargo", "GM", "0.42 m", "0.60 m", "0.58 m", "1 K", "shift", "lash +4%", 8, 1, "hold", "ro-ro", "0.30 m", "lash 4% extra", "grain moisture vs aflatoxin", "cg_op", "ls_cg", "gm_lab", 41),
    A("grain-moisture-vs-aflatoxin", "corn", "aflatoxin", "18 ppb", "8 ppb", "8.2 ppb", "6 K", "hotspot", "dry +4%", 10, 1, "bin", "feed", "24 ppb", "air 4% extra", "silage pH vs DM", "gr_op", "dry_gr", "af_lab", 40),
    A("silage-ph-vs-dm", "silage", "pH", "4.62", "4.20", "4.22", "3 K", "butyric", "inoc +4%", 8, 1, "bunker", "dairy", "4.80", "inoc 2 kg extra", "hay moisture vs heat", "si_op", "in_si", "ph_si", 39),
    A("hay-moisture-vs-heat", "hay", "moisture", "18.4%", "14.0%", "14.2%", "4 K", "heat", "ted +4%", 7, 1, "stack", "bale", "21%", "ted 4% extra", "feed protein vs urea", "hy_op", "td_hy", "moi_hy", 38),
    A("feed-protein-vs-urea", "feed", "CP", "14.8%", "16.0%", "15.9%", "5 K", "urea", "SBM +3%", 9, 1, "bin", "dairy", "13.5%", "SBM 0.4 t extra", "milk SCC vs bact", "fd_op", "sbm_fd", "cp_lab", 37),
    A("milk-scc-vs-bact", "milk", "SCC", "280k", "180k", "185k", "2 K", "bact", "pre-dip +4%", 6, 1, "bulk", "Grade-A", "350k", "dip 4% extra", "egg Haugh vs age", "mk_op", "pd_mk", "scc_lab", 36),
    A("egg-haugh-vs-age", "egg", "Haugh", "62", "72", "71", "3 K", "thin", "cool +4%", 8, 1, "cooler", "A", "55", "RH 3% extra", "poultry ammonia vs RH", "eg_op", "cl_eg", "hu_lab", 35),
    A("poultry-ammonia-vs-rh", "house", "NH3", "28 ppm", "15 ppm", "15.4 ppm", "2 K", "lesion", "vent +8%", 6, 1, "barn", "broiler", "36 ppm", "vent 8% extra", "swine ammonia vs pit", "pl_op", "vt_pl", "nh3_pl", 34),
    A("swine-ammonia-vs-pit", "barn", "NH3", "22 ppm", "12 ppm", "12.4 ppm", "2 K", "pit", "pull +4%", 7, 1, "room", "finisher", "28 ppm", "pull 4% extra", "aquaculture DO vs TAN", "sw_op", "pl_sw", "nh3_sw", 33),
    A("aquaculture-do-vs-tan", "pond", "TAN", "1.8 ppm", "0.8 ppm", "0.82 ppm", "3 K", "DO", "aerate +8%", 8, 1, "pond", "tilapia", "2.4 ppm", "air 8% extra", "hatchery salinity vs survival", "aq_op", "ae_aq", "tan_lab", 32),
    A("hatchery-salinity-vs-survival", "hatch", "survival", "78%", "88%", "87%", "2 K", "osmotic", "sal +3 ppt", 6, 1, "tank", "larvae", "70%", "salt 4 kg extra", "bees varroa vs brood", "ht_op", "sal_ht", "sv_lab", 31),
    A("bees-varroa-vs-brood", "hive", "varroa", "8%", "2%", "2.2%", "1 K", "brood", "OA +4%", 5, 1, "colony", "honey", "12%", "OA 4% extra", "greenhouse VPD vs CO2", "be_op", "oa_be", "vr_lab", 30),
    A("greenhouse-vpd-vs-co2", "GH", "VPD", "1.8 kPa", "1.1 kPa", "1.12 kPa", "3 K", "tipburn", "fog +4%", 7, 1, "bay", "tomato", "2.2 kPa", "fog 4% extra", "hydroponic EC vs pH", "gh_op", "fg_gh", "vpd_lab", 29),
    A("hydroponic-ec-vs-ph", "NFT", "EC", "3.2 mS", "2.4 mS", "2.42 mS", "2 K", "burn", "dilute +4%", 6, 1, "gutter", "leaf", "3.6 mS", "water 40 L extra", "aeroponic mist vs DO", "hy_op", "dl_hy", "ec_lab", 28),
    A("aeroponic-mist-vs-do", "aero", "DO", "4.8 ppm", "7.0 ppm", "6.9 ppm", "2 K", "root", "mist +4%", 5, 1, "tower", "herb", "3.5 ppm", "air 4% extra", "mushroom CO2 vs RH", "ae_op", "ms_ae", "do_ae", 27),
    A("mushroom-co2-vs-rh", "mushroom", "CO2", "1800 ppm", "900 ppm", "920 ppm", "2 K", "long-stem", "vent +8%", 6, 1, "room", "agaricus", "2400 ppm", "vent 8% extra", "compost temp vs C/N", "mu_op", "vt_mu", "co2_mu", 26),
    A("compost-temp-vs-c-n", "compost", "T", "72 C", "62 C", "62.5 C", "4 K", "N-loss", "turn +4%", 8, 1, "windrow", "soil", "78 C", "turn 4% extra", "biogas CH4 vs H2S", "cp_op", "tn_cp", "t_cp", 25),
    A("biogas-ch4-vs-h2s", "digester", "H2S", "1800 ppm", "200 ppm", "210 ppm", "5 K", "H2S", "FeCl3 +4%", 9, 1, "bag", "CHP", "2400 ppm", "FeCl3 8 kg extra", "landfill LFG vs O2", "bg_op", "fe_bg", "h2s_lab", 24),
    A("landfill-lfg-vs-o2", "LFG", "O2", "2.4%", "0.5%", "0.52%", "3 K", "air", "well +4%", 8, 1, "field", "flare", "3.5%", "vacuum 4% extra", "incinerator CO vs O2", "lf_op", "wl_lf", "o2_lf", 23),
    A("incinerator-co-vs-o2", "WTE", "CO", "180 ppm", "50 ppm", "52 ppm", "20 K", "CO", "O2 +0.4%", 7, 1, "grate", "steam", "250 ppm", "air 0.4% extra", "pyrolysis oil vs temp", "inc_op", "o2_inc", "co_inc", 22),
    A("pyrolysis-oil-vs-temp", "pyro", "oil", "48%", "55%", "54.6%", "18 K", "char", "T -8 K", 10, 1, "reactor", "fuel", "42%", "hold 8 min extra", "torrefy mass vs energy", "py_op", "t_py", "oil_py", 21),
    A("torrefy-mass-vs-energy", "torrefy", "mass", "72%", "78%", "77.6%", "14 K", "tar", "T -6 K", 9, 1, "kiln", "pellet", "66%", "hold 6 min extra", "pellet durability vs fines", "tf_op", "t_tf", "ms_lab", 20),
    A("pellet-durability-vs-fines", "pellet", "PDI", "92.4%", "96.0%", "95.7%", "8 K", "fines", "die +4%", 8, 1, "silo", "export", "90.0%", "steam 3% extra", "charcoal FC vs VM", "pl_op", "die_pl", "pdi_lab", 19),
    A("charcoal-fc-vs-vm", "charcoal", "FC", "78%", "84%", "83.6%", "16 K", "VM", "retort +4%", 12, 1, "lot", "BBQ", "74%", "hold 8 min extra", "biochar H/C vs ash", "ch_op", "rt_ch", "fc_ch", 18),
    A("biochar-h-c-vs-ash", "biochar", "H/C", "0.42", "0.30", "0.31", "18 K", "ash", "T +4%", 11, 1, "lot", "soil", "0.50", "hold 8 min extra", "lithium brine vs Mg", "bc_op", "t_bc", "hc_lab", 17),
    A("lithium-brine-vs-mg", "brine", "Mg/Li", "8.4", "4.0", "4.1", "6 K", "Mg", "lime +4%", 10, 1, "pond", "Li2CO3", "10", "lime 0.4 t extra", "potash K2O vs NaCl", "li_op", "lm_li", "mg_li", 16),
    A("potash-k2o-vs-nacl", "KCl", "NaCl", "1.8%", "0.8%", "0.82%", "8 K", "NaCl", "flotation +4%", 9, 1, "silo", "fert", "2.4%", "amine 8 kg extra", "phosphate P2O5 vs Cd", "k_op", "fl_k", "nacl_k", 15),
    A("phosphate-p2o5-vs-cd", "MAP", "Cd", "28 ppm", "12 ppm", "12.4 ppm", "10 K", "Cd", "acid +4%", 11, 1, "silo", "fert", "36 ppm", "acid 0.3 t extra", "sulfur purity vs ash", "phos_op", "ac_phos", "cd_lab", 14),
    A("sulfur-purity-vs-ash", "S", "purity", "99.42%", "99.80%", "99.78%", "7 K", "ash", "filter +4%", 8, 1, "pit", "acid", "99.20%", "filter 4% extra", "boron B2O3 vs Na", "su_op", "fil_su", "pur_su", 13),
    A("boron-b2o3-vs-na", "boric", "Na", "180 ppm", "50 ppm", "52 ppm", "9 K", "Na", "recryst +4%", 12, 1, "hopper", "glass", "240 ppm", "water 0.3 t extra", "fluorite CaF2 vs SiO2", "b_op", "rc_b", "na_b", 12),
    A("fluorite-caf2-vs-sio2", "fluorite", "SiO2", "4.8%", "2.0%", "2.1%", "11 K", "SiO2", "float +4%", 10, 1, "lot", "HF", "6.0%", "collector 4 kg extra", "barite SG vs Ba", "fl_op", "ft_fl", "si_fl", 11),
    A("barite-sg-vs-ba", "barite", "SG", "4.12", "4.20", "4.195", "8 K", "Si", "jig +4%", 9, 1, "silo", "mud", "4.05", "jig 4% extra", "bentonite yield vs MB", "ba_op", "jg_ba", "sg_ba", 10),
    A("bentonite-yield-vs-mb", "bentonite", "yield", "88 bbl", "100 bbl", "98 bbl", "6 K", "grit", "soda +4%", 8, 1, "silo", "mud", "78 bbl", "soda 8 kg extra", "kaolin ISO vs abr", "bn_op", "sd_bn", "yd_lab", 9),
    A("kaolin-iso-vs-abr", "kaolin", "ISO", "82", "88", "87.5", "10 K", "abr", "leach +4%", 11, 1, "silo", "paper", "78", "acid 0.2 t extra", "talc whiteness vs LOI", "ka_op", "lc_ka", "iso_ka", 8),
    A("talc-whiteness-vs-loi", "talc", "ISO", "88.4", "92.0", "91.7", "9 K", "LOI", "float +4%", 10, 1, "silo", "plastic", "86.0", "collector 4 kg extra", "mica K vs Fe", "tc_op", "ft_tc", "iso_tc", 7),
    A("mica-k-vs-fe", "mica", "Fe", "1.8%", "0.8%", "0.82%", "8 K", "Fe", "magnet +4%", 9, 1, "silo", "paint", "2.4%", "magnet 4% extra", "wollastonite aspect vs CaO", "mi_op", "mg_mi", "fe_mi", 6),
    A("wollastonite-aspect-vs-cao", "wollastonite", "aspect", "8.2", "12.0", "11.6", "7 K", "fines", "mill-cut 4%", 8, 1, "silo", "plastic", "6.5", "class 4% extra", "solder void vs reflow", "wo_op", "ml_wo", "as_wo", 5),
    A("solder-void-vs-reflow", "SMT", "void", "18%", "8%", "8.2%", "4 K", "tombstone", "profile -4 K", 6, 1, "lot", "QFN", "24%", "soak 8 s extra", "stencil paste vs volume", "smt_op", "pr_smt", "vd_lab", 4),
    A("stencil-paste-vs-volume", "stencil", "volume", "72%", "88%", "87%", "2 K", "bridge", "wipe +4%", 5, 1, "lot", "0201", "64%", "wipe 4% extra", "wave dross vs temp", "stn_op", "wp_stn", "vol_stn", 3),
    A("wave-dross-vs-temp", "wave", "dross", "8.4 kg/h", "4.0 kg/h", "4.1 kg/h", "5 K", "icicle", "N2 +4%", 7, 1, "line", "THT", "11 kg/h", "N2 4% extra", "conformal thickness vs visc", "wv_op", "n2_wv", "dr_lab", 2),
    A("conformal-thickness-vs-visc", "conformal", "DFT", "28 µm", "40 µm", "39 µm", "3 K", "orange", "visc +4%", 6, 1, "lot", "IPC", "22 µm", "thinner 4% extra", "PCB etch vs impedance", "cf_op", "vs_cf", "dft_cf", 73),
    A("pcb-etch-vs-impedance", "PCB", "Z", "52.8 Ω", "50.0 Ω", "50.2 Ω", "4 K", "undercut", "etch-cut 4%", 8, 1, "panel", "RF", "55 Ω", "speed 4% extra", "via fill vs void", "pcb_op", "et_pcb", "z_lab", 72),
    A("via-fill-vs-void", "via", "void", "12%", "3%", "3.2%", "5 K", "void", "plate +4%", 9, 1, "panel", "HDI", "18%", "current 4% extra", "ENEPIG thickness vs porosity", "via_op", "pl_via", "vd_via", 71),
    A("enepig-thickness-vs-porosity", "ENEPIG", "Au", "0.042 µm", "0.060 µm", "0.058 µm", "3 K", "porosity", "immersion +4%", 7, 1, "lot", "BGA", "0.030 µm", "time 8 s extra", "OSP thickness vs wet", "ene_op", "im_ene", "au_lab", 70),
    A("osp-thickness-vs-wet", "OSP", "wet", "8 s", "4 s", "4.2 s", "2 K", "skip", "coat +4%", 5, 1, "lot", "SMT", "12 s", "coat 4% extra", "cable cap vs impedance", "osp_op", "ct_osp", "wt_lab", 69),
    A("cable-cap-vs-impedance", "coax", "Z", "52.4 Ω", "50.0 Ω", "50.2 Ω", "4 K", "return", "foam +3%", 8, 1, "reel", "RF", "54 Ω", "N2 3% extra", "fiber splice vs loss", "cx_op", "fm_cx", "z_cx", 68),
    A("fiber-splice-vs-loss", "splice", "loss", "0.18 dB", "0.05 dB", "0.052 dB", "2 K", "offset", "arc +4%", 6, 1, "span", "long-haul", "0.28 dB", "arc 4% extra", "antenna VSWR vs match", "sp_op", "arc_sp", "ls_lab", 67),
    A("antenna-vswr-vs-match", "antenna", "VSWR", "1.82", "1.30", "1.32", "1 K", "match", "stub +4%", 5, 1, "tower", "LTE", "2.10", "stub 4% extra", "battery formation vs SEI", "ant_op", "st_ant", "vswr_lab", 66),
    A("battery-formation-vs-sei", "cell", "SEI", "18 mAh/g", "12 mAh/g", "12.2 mAh/g", "4 K", "gas", "C-rate -4%", 10, 1, "lot", "NMC", "24 mAh/g", "hold 20 min extra", "cell IR vs SOC", "bat_op", "cr_bat", "sei_lab", 65),
    A("cell-ir-vs-soc", "cell", "IR", "1.8 mΩ", "1.2 mΩ", "1.22 mΩ", "3 K", "heat", "rest +4%", 8, 1, "lot", "pack", "2.2 mΩ", "rest 8 min extra", "pack balance vs delta", "cl_op", "rs_cl", "ir_lab", 64),
    A("pack-balance-vs-delta", "pack", "dV", "42 mV", "15 mV", "16 mV", "2 K", "imbalance", "balance +4%", 12, 1, "pack", "EV", "55 mV", "balance 8 min extra", "inverter THD vs DC", "pk_op", "bl_pk", "dv_lab", 63),
    A("inverter-thd-vs-dc", "inverter", "THD", "4.8%", "3.0%", "3.05%", "3 K", "ripple", "DC +4%", 7, 1, "unit", "grid", "6.0%", "cap 4% extra", "EVSE pilot vs current", "inv_op", "dc_inv", "thd_lab", 62),
    A("evse-pilot-vs-current", "EVSE", "pilot", "18 A", "32 A", "31 A", "1 K", "fault", "pilot +4%", 5, 1, "stall", "L2", "12 A", "PWM 4% extra", "brake fluid vs wet", "ev_op", "pw_ev", "pl_lab", 61),
    A("brake-fluid-vs-wet", "DOT4", "wet", "148 C", "165 C", "164 C", "4 K", "water", "dry +4%", 8, 1, "drum", "service", "140 C", "N2 4% extra", "coolant freeze vs pH", "bf_op", "dry_bf", "wt_bf", 60),
    A("coolant-freeze-vs-ph", "coolant", "pH", "7.4", "8.2", "8.15", "3 K", "corrosion", "inhib +4%", 7, 1, "tank", "fleet", "7.0", "inhib 4 kg extra", "ATF shear vs visc", "clt_op", "in_clt", "ph_clt", 59),
    A("atf-shear-vs-visc", "ATF", "KV100", "5.8", "6.4", "6.35", "6 K", "shear", "VII +3%", 8, 1, "tank", "DEXRON", "5.4", "VII 8 kg extra", "DEF urea vs biuret", "atf_op", "vii_atf", "kv_atf", 58),
    A("def-urea-vs-biuret", "DEF", "biuret", "0.62%", "0.30%", "0.31%", "5 K", "deposit", "dilute +4%", 9, 1, "tank", "ISO22241", "0.80%", "water 40 L extra", "AdBlue alkali vs ISO", "def_op", "dl_def", "biu_def", 57),
    A("adblue-alkali-vs-iso", "AdBlue", "alkali", "0.42%", "0.20%", "0.21%", "4 K", "alkali", "IX +4%", 8, 1, "tank", "ISO", "0.55%", "resin 0.2 CV extra", "tire uniformity vs RFV", "ad_op", "ix_ad", "alk_ad", 56),
    A("tire-uniformity-vs-rfv", "tire", "RFV", "18 N", "8 N", "8.2 N", "5 K", "RFV", "cure +4%", 10, 1, "lot", "OE", "24 N", "mold 4% extra", "tread depth vs void", "tr_op", "cu_tr", "rfv_lab", 55),
    A("tread-depth-vs-void", "tread", "void", "28%", "32%", "31.6%", "4 K", "wear", "extrude +3%", 7, 1, "lot", "winter", "24%", "die 3% extra", "bead seat vs pressure", "td_op", "ex_td", "vd_td", 54),
    A("bead-seat-vs-pressure", "bead", "seat", "0.82 mm", "0.40 mm", "0.42 mm", "3 K", "leak", "press +4%", 6, 1, "lot", "mount", "1.10 mm", "press 4% extra", "paint DFT vs orange", "bd_op", "pr_bd", "st_bd", 53),
    A("paint-dft-vs-orange", "paint", "DFT", "42 µm", "55 µm", "54 µm", "4 K", "orange", "atom +4%", 7, 1, "line", "body", "35 µm", "flow 4% extra", "e-coat throw vs voltage", "pt_op", "at_pt", "dft_pt", 52),
    A("e-coat-throw-vs-voltage", "e-coat", "throw", "18 µm", "24 µm", "23.6 µm", "5 K", "crater", "V +4%", 8, 1, "tank", "cavity", "14 µm", "V 4% extra", "powder gel vs thickness", "ec_op", "v_ec", "th_ec", 51),
    A("powder-gel-vs-thickness", "powder", "gel", "82 s", "60 s", "61 s", "6 K", "orange", "T +4%", 7, 1, "line", "housing", "95 s", "zone 4 K extra", "anodize thickness vs sealing", "pwd_op", "t_pwd", "gel_pwd", 50),
    A("anodize-thickness-vs-sealing", "anodize", "seal", "18 min", "12 min", "12.2 min", "4 K", "dye", "seal +4%", 8, 1, "lot", "arch", "22 min", "Ni 4% extra", "solar next densify", "anod_op", "sl_anod", "sl_lab", 49),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(3543, s)
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
            print(f"MAC r{n} reserved/writing; wait (sbox reserved/writing={busy(SBOX)})", flush=True)
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
