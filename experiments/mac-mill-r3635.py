#!/usr/bin/env python3
"""MAC mill r3635+. Unique medical/lab/civil plants. Never sbox if reserved/writing."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205f", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("dialysis-ktv-vs-uf", "HD", "Kt/V", "1.18", "1.40", "1.38", "2 K", "cramp", "time +12 min", 12, 1, "station", "outpatient", "1.05", "Qb 4% extra", "ventilator PEEP vs plateau", "hd_op", "tm_hd", "ktv_lab", 64),
    A("ventilator-peep-vs-plateau", "vent", "Pplat", "32 cm", "28 cm", "28.2 cm", "1 K", "baro", "PEEP -2", 5, 1, "ICU", "ARDS", "36 cm", "TV 4% extra", "anesthesia MAC vs EtCO2", "vt_op", "pp_vt", "pplat_lab", 63),
    A("anesthesia-mac-vs-etco2", "GA", "EtCO2", "52 mmHg", "38 mmHg", "38.5 mmHg", "1 K", "hypercap", "MV +8%", 4, 1, "OR", "case", "58 mmHg", "RR 4% extra", "sterilizer Bowie vs BD", "an_op", "mv_an", "et_lab", 62),
    A("sterilizer-bowie-vs-bd", "steam", "BD", "fail", "pass", "pass", "4 K", "air", "hold +4 min", 4, 1, "load", "CSSD", "fail", "hold 4 min extra", "endoscope ATP vs channel", "st_op", "hd_st", "bd_lab", 61),
    A("endoscope-atp-vs-channel", "scope", "ATP", "140 RLU", "40 RLU", "42 RLU", "2 K", "soil", "brush +4%", 6, 1, "scope", "GI", "180 RLU", "flush 4% extra", "blood bank Hct vs temp", "en_op", "br_en", "atp_en", 60),
    A("blood-bank-htc-vs-temp", "RBC", "T", "8.4 C", "4.0 C", "4.2 C", "2 K", "hemol", "cool +4%", 8, 1, "fridge", "issue", "10 C", "alarm 4 min extra", "lab QC Levey vs Westgard", "bb_op", "cl_bb", "t_bb", 59),
    A("lab-qc-levey-vs-westgard", "chem QC", "1-3s", "fail", "pass", "pass", "1 K", "shift", "recal +4%", 6, 1, "analyzer", "run", "2-2s", "cal 4% extra", "PCR Ct vs IPC", "qc_op", "rc_qc", "wg_lab", 58),
    A("pcr-ct-vs-ipc", "PCR", "IPC Ct", "38.4", "32.0", "32.2", "2 K", "inhibit", "dilute +4%", 7, 1, "run", "COVID", "40.0", "BSA 4% extra", "NGS Q30 vs cluster", "pcr_op", "dl_pcr", "ct_lab", 57),
    A("ngs-q30-vs-cluster", "NGS", "Q30", "78%", "85%", "84.6%", "3 K", "cluster", "load -4%", 8, 1, "flowcell", "WGS", "72%", "phiX 4% extra", "cytometry CV vs voltage", "ngs_op", "ld_ngs", "q30_lab", 56),
    A("cytometry-cv-vs-voltage", "FACS", "CV", "4.8%", "2.5%", "2.55%", "2 K", "CV", "volt -4%", 6, 1, "tube", "CD4", "6.0%", "gain 4% extra", "histology thickness vs artifact", "fc_op", "v_fc", "cv_lab", 55),
    A("histology-thickness-vs-artifact", "section", "µm", "6.2", "4.0", "4.1", "1 K", "chatters", "knife +4%", 5, 1, "block", "H&E", "8.0", "angle 4% extra", "path IHC vs Dako", "hs_op", "kn_hs", "um_lab", 54),
    A("path-ihc-vs-dako", "IHC", "H-score", "82", "140", "136", "2 K", "bg", "AR +4%", 8, 1, "slide", "ER", "60", "pH 4% extra", "xray dose vs noise", "ihc_op", "ar_ihc", "hs_ihc", 53),
    A("xray-dose-vs-noise", "DR", "EI", "280", "200", "205", "1 K", "noise", "kV +4%", 5, 1, "room", "chest", "340", "grid 4% extra", "CT CTDI vs noise", "xr_op", "kv_xr", "ei_lab", 52),
    A("ct-ctdi-vs-noise", "CT", "CTDIvol", "18 mGy", "12 mGy", "12.2 mGy", "2 K", "noise", "mA -4%", 6, 1, "scanner", "abd", "24 mGy", "IR 4% extra", "MRI SAR vs SNR", "ct_op", "ma_ct", "ctdi_lab", 51),
    A("mri-sar-vs-snr", "MRI", "SAR", "2.8 W/kg", "2.0 W/kg", "2.05 W/kg", "2 K", "heat", "TR +4%", 7, 1, "magnet", "body", "3.2 W/kg", "flip 4% extra", "ultrasound MI vs depth", "mr_op", "tr_mr", "sar_lab", 50),
    A("ultrasound-mi-vs-depth", "US", "MI", "1.4", "0.9", "0.92", "1 K", "cav", "MI -4%", 5, 1, "probe", "OB", "1.7", "freq 4% extra", "linac output vs energy", "us_op", "mi_us", "mi_lab", 49),
    A("linac-output-vs-energy", "linac", "cGy", "198", "200", "199.6", "3 K", "output", "cal +4%", 8, 1, "gantry", "6MV", "194", "MU 4% extra", "brachy dwell vs dose", "ln_op", "cl_ln", "cg_lab", 48),
    A("brachy-dwell-vs-dose", "HDR", "D90", "82%", "90%", "89.5%", "2 K", "hotspot", "dwell +4%", 6, 1, "afterloader", "Gyn", "76%", "channel 4% extra", "isotope half vs activity", "br_op", "dw_br", "d90_lab", 47),
    A("isotope-half-vs-activity", "Tc99m", "act", "18 mCi", "25 mCi", "24.6 mCi", "1 K", "decay", "elute +4%", 5, 1, "gen", "bone", "14 mCi", "elute 4 min extra", "PET SUV vs TOF", "iso_op", "el_iso", "act_lab", 46),
    A("pet-suv-vs-tof", "PET", "SUV", "2.4", "1.8", "1.82", "2 K", "noise", "TOF +4%", 7, 1, "scanner", "FDG", "3.0", "time 4% extra", "gamma uniformity vs CFO", "pet_op", "tof_pet", "suv_lab", 45),
    A("gamma-uniformity-vs-cfo", "gamma", "IU", "4.8%", "3.0%", "3.05%", "2 K", "PMT", "tune +4%", 8, 1, "camera", "planar", "6.0%", "HV 4% extra", "SPECT center vs FWHM", "gm_op", "tn_gm", "iu_gm", 44),
    A("spect-center-vs-fwhm", "SPECT", "COR", "2.8 mm", "1.0 mm", "1.05 mm", "2 K", "blur", "COR +4%", 6, 1, "camera", "MPI", "3.5 mm", "cal 4% extra", "mammography AGD vs CNR", "sp_op", "cor_sp", "fwhm_lab", 43),
    A("mammography-agds-vs-cnr", "mammo", "AGD", "2.4 mGy", "1.6 mGy", "1.62 mGy", "1 K", "dose", "kV +4%", 5, 1, "unit", "screen", "2.9 mGy", "filter 4% extra", "fluoro DAP vs fps", "mm_op", "kv_mm", "agd_lab", 42),
    A("fluoro-dap-vs-fps", "fluoro", "DAP", "18 Gycm2", "12 Gycm2", "12.2", "1 K", "dose", "fps -4%", 5, 1, "room", "angio", "24", "pulse 4% extra", "OR laminar vs CFU", "fl_op", "fps_fl", "dap_lab", 41),
    A("or-laminar-vs-cfu", "OR", "CFU", "18 /m3", "5 /m3", "5.2 /m3", "2 K", "count", "ACH +8%", 6, 1, "OR", "implant", "28 /m3", "fan 8% extra", "CSSD ATP vs washer", "or_op", "ach_or", "cfu_lab", 40),
    A("cssd-atp-vs-washer", "washer", "ATP", "120 RLU", "40 RLU", "42 RLU", "3 K", "soil", "alk +4%", 7, 1, "load", "tray", "160 RLU", "cycle 4 min extra", "pharmacy ISO5 vs particle", "cs_op", "alk_cs", "atp_cs", 39),
    A("pharmacy-iso5-vs-particle", "ISO5", "0.5µm", "2800", "800", "820", "2 K", "count", "ACH +8%", 6, 1, "hood", "CSP", "3500", "fan 8% extra", "compound beyond vs BUD", "ph_op", "ach_ph", "pt_ph", 38),
    A("compound-beyond-vs-bud", "CSP", "BUD", "48 h", "14 d", "13 d", "1 K", "sterile", "sterile +4%", 8, 1, "batch", "IV", "24 h", "test 4% extra", "IV admix vs sterility", "cpd_op", "st_cpd", "bud_lab", 37),
    A("iv-admix-vs-sterility", "admix", "CFU", "fail", "pass", "pass", "1 K", "contam", "aseptic +4%", 6, 1, "batch", "TPN", "fail", "garb 4% extra", "TPN calcium vs precip", "iv_op", "as_iv", "st_iv", 36),
    A("tpn-calcium-vs-precip", "TPN", "Ca", "18 mEq", "12 mEq", "12.2 mEq", "1 K", "precip", "Ca -4%", 5, 1, "bag", "neonate", "22 mEq", "phos 4% extra", "chemo closed vs surf", "tpn_op", "ca_tpn", "ca_lab", 35),
    A("chemo-closed-vs-surf", "HD", "wipe", "18 ng", "1 ng", "1.2 ng", "1 K", "surf", "CSTD +4%", 6, 1, "hood", "infusion", "28 ng", "wipe 4% extra", "radio pharmacy vs eluate", "chm_op", "cstd_chm", "wp_lab", 34),
    A("radio-pharmacy-vs-eluate", "eluate", "Mo", "0.18 µCi", "0.05 µCi", "0.052", "1 K", "Mo", "elute +4%", 5, 1, "gen", "kit", "0.28", "column 4% extra", "blood gas vs IQC", "rp_op", "el_rp", "mo_lab", 33),
    A("blood-gas-vs-iqc", "ABG", "pO2", "8 mmHg", "2 mmHg", "2.1 mmHg", "1 K", "bias", "cal +4%", 5, 1, "analyzer", "ICU", "12 mmHg", "cal 4% extra", "coag INR vs ISI", "bg_op", "cl_bg", "po2_lab", 32),
    A("coag-inr-vs-isi", "INR", "ISI", "1.28", "1.10", "1.11", "1 K", "bias", "cal +4%", 6, 1, "analyzer", "warfarin", "1.40", "cal 4% extra", "heme WBC vs flag", "cg_op", "cl_cg", "isi_lab", 31),
    A("heme-wbc-vs-flag", "CBC", "flag", "18%", "4%", "4.2%", "1 K", "clump", "rerun +4%", 5, 1, "analyzer", "ED", "24%", "warm 4 min extra", "chem Na vs ISE", "hm_op", "rr_hm", "fg_lab", 30),
    A("chem-na-vs-ise", "Na", "bias", "4.8 mmol", "1.0 mmol", "1.1 mmol", "1 K", "protein", "ISE +4%", 6, 1, "analyzer", "BMP", "6.0 mmol", "dilute 4% extra", "immuno hook vs dilution", "ch_op", "ise_ch", "na_lab", 29),
    A("immuno-hook-vs-dilution", "assay", "hook", "fail", "pass", "pass", "1 K", "hook", "dilute +4%", 6, 1, "analyzer", "hCG", "fail", "dilute 4% extra", "micro MALDI vs score", "im_op", "dl_im", "hk_lab", 28),
    A("micro-maldi-vs-score", "MALDI", "score", "1.62", "2.20", "2.18", "2 K", "mix", "spot +4%", 5, 1, "plate", "ID", "1.40", "laser 4% extra", "blood culture vs TTP", "md_op", "sp_md", "sc_lab", 27),
    A("blood-culture-vs-ttp", "BCx", "TTP", "28 h", "18 h", "18.4 h", "1 K", "volume", "vol +4%", 6, 1, "bottle", "sepsis", "36 h", "fill 4% extra", "AST MIC vs breakpoint", "bc_op", "vl_bc", "ttp_lab", 26),
    A("ast-mic-vs-breakpoint", "AST", "MIC", "off", "on", "on", "1 K", "skip", "panel +4%", 5, 1, "card", "ICU", "off", "dilute 4% extra", "env settle vs CFU", "ast_op", "pn_ast", "mic_lab", 25),
    A("env-settle-vs-cfu", "settle", "CFU", "18", "4", "4.2", "1 K", "count", "clean +4%", 6, 1, "room", "ISO7", "28", "wipe 4% extra", "water loop vs TVC", "ev_op", "cl_ev", "cfu_ev", 24),
    A("water-loop-vs-tvc", "WFI loop", "TVC", "18 CFU", "4 CFU", "4.2 CFU", "4 K", "biofilm", "heat +4%", 8, 1, "loop", "comp", "28 CFU", "sanitize 4% extra", "HEPA scan vs leak", "wf_op", "ht_wf", "tvc_lab", 23),
    A("hepa-scan-vs-leak", "HEPA", "leak", "0.028%", "0.008%", "0.009%", "1 K", "pinhole", "reseal +4%", 6, 1, "filter", "ISO5", "0.04%", "gel 4% extra", "BSA cabinet vs inflow", "hp_op", "rs_hp", "lk_lab", 22),
    A("bsa-cabinet-vs-inflow", "BSC", "inflow", "82 fpm", "100 fpm", "98 fpm", "1 K", "escape", "sash -2 in", 5, 1, "hood", "BSC-II", "70 fpm", "sash 2 in extra", "autoclave Bowie vs air", "bsc_op", "sh_bsc", "in_lab", 21),
    A("autoclave-bowie-vs-air", "prevac", "air", "fail", "pass", "pass", "3 K", "air", "pulse +4%", 6, 1, "load", "CSSD", "fail", "pulse 4% extra", "EtO EO vs aeration", "ac_op", "pl_ac", "air_ac", 20),
    A("eto-eo-vs-aeration", "EtO", "EO", "18 ppm", "1 ppm", "1.2 ppm", "4 K", "resid", "aerate +4%", 10, 1, "load", "device", "28 ppm", "air 4% extra", "H2O2 plasma vs lumen", "eto_op", "ae_eto", "eo_lab", 19),
    A("h2o2-plasma-vs-lumen", "VH2O2", "lumen", "fail", "pass", "pass", "3 K", "lumen", "boost +4%", 7, 1, "load", "scope", "fail", "boost 4% extra", "peracetic scope vs ATP", "h2_op", "bst_h2", "lm_lab", 18),
    A("peracetic-scope-vs-atp", "AER", "ATP", "80 RLU", "20 RLU", "21 RLU", "2 K", "channel", "cycle +4%", 6, 1, "scope", "GI", "120 RLU", "flush 4% extra", "laundry CFU vs temp", "pa_op", "cy_pa", "atp_pa", 17),
    A("laundry-cfu-vs-temp", "laundry", "CFU", "18", "2", "2.2", "6 K", "soil", "T +4%", 8, 1, "load", "OR", "28", "time 4 min extra", "CSSD peel vs seal", "ld_op", "t_ld", "cfu_ld", 16),
    A("cssd-peel-vs-seal", "pouch", "seal", "fail", "pass", "pass", "2 K", "channel", "temp +4%", 5, 1, "pouch", "implant", "fail", "dwell 4% extra", "implant bioburden vs SAL", "ps_op", "tp_ps", "sl_lab", 15),
    A("implant-bioburden-vs-sal", "implant", "SAL", "10^-4", "10^-6", "10^-6", "3 K", "bioburden", "dose +4%", 8, 1, "lot", "hip", "10^-3", "dose 4% extra", "suture tensile vs knot", "im_op", "ds_im", "sal_lab", 14),
    A("suture-tensile-vs-knot", "suture", "N", "18 N", "24 N", "23.6 N", "2 K", "break", "draw +4%", 6, 1, "lot", "OR", "14 N", "draw 4% extra", "concrete slump vs air", "su_op", "dr_su", "n_su", 13),
    A("concrete-slump-vs-air", "mix", "air", "2.8%", "6.0%", "5.9%", "3 K", "freeze", "AEA +4%", 7, 1, "truck", "pavement", "2.0%", "AEA 4% extra", "asphalt density vs void", "cn_op", "aea_cn", "air_cn", 12),
    A("asphalt-density-vs-void", "mat", "void", "8.4%", "4.0%", "4.1%", "8 K", "void", "roll +4%", 8, 1, "lane", "surface", "10%", "pass 4% extra", "rebar cover vs scan", "as_op", "rl_as", "vd_as", 11),
    A("rebar-cover-vs-scan", "cover", "mm", "28 mm", "40 mm", "39 mm", "1 K", "cover", "spacer +4%", 6, 1, "pour", "deck", "22 mm", "chair 4% extra", "weld UT vs porosity", "rb_op", "sp_rb", "cv_lab", 10),
    A("weld-ut-vs-porosity", "weld", "porosity", "8%", "2%", "2.1%", "4 K", "pore", "gas +4%", 7, 1, "joint", "pipe", "12%", "purge 4% extra", "bolt torque vs preload", "wd_op", "gs_wd", "por_wd", 9),
    A("bolt-torque-vs-preload", "bolt", "kN", "180 kN", "240 kN", "236 kN", "2 K", "embed", "torque +4%", 5, 1, "flange", "steel", "150 kN", "lube 4% extra", "crane load vs radius", "bt_op", "tq_bt", "kn_lab", 8),
    A("crane-load-vs-radius", "crane", "radius", "28 m", "22 m", "22.2 m", "1 K", "chart", "radius -4%", 5, 1, "pick", "steel", "32 m", "boom 4% extra", "scaffold plumb vs tie", "cr_op", "rd_cr", "rd_lab", 7),
    A("scaffold-plumb-vs-tie", "scaffold", "plumb", "28 mm", "12 mm", "12.4 mm", "1 K", "lean", "tie +4%", 6, 1, "bay", "facade", "36 mm", "tie 4% extra", "trench slope vs soil", "sc_op", "tie_sc", "pl_lab", 6),
    A("trench-slope-vs-soil", "trench", "slope", "0.8:1", "1.5:1", "1.48:1", "1 K", "cave", "bench +4%", 6, 1, "cut", "utility", "0.5:1", "bench 4% extra", "pile set vs capacity", "tr_op", "bn_tr", "sl_lab", 5),
    A("pile-set-vs-capacity", "pile", "set", "18 mm", "8 mm", "8.2 mm", "2 K", "refusal", "blow +4%", 7, 1, "bent", "bridge", "24 mm", "blow 4% extra", "shotcrete rebound vs thick", "pl_op", "bw_pl", "st_pl", 4),
    A("shotcrete-rebound-vs-thick", "shotcrete", "rebound", "18%", "8%", "8.2%", "3 K", "void", "accel +4%", 6, 1, "wall", "tunnel", "24%", "nozzle 4% extra", "grout flow vs bleed", "sh_op", "ac_sh", "rb_lab", 3),
    A("grout-flow-vs-bleed", "grout", "bleed", "4.8%", "1.0%", "1.1%", "2 K", "bleed", "w/c -4%", 5, 1, "duct", "PT", "6.0%", "hold 4 min extra", "epoxy floor vs DFT", "gr_op", "wc_gr", "bl_gr", 2),
    A("epoxy-floor-vs-dft", "epoxy", "DFT", "18 mil", "24 mil", "23.6 mil", "3 K", "orange", "spread +4%", 6, 1, "slab", "warehouse", "14 mil", "mix 4% extra", "roof membrane vs seam", "ep_op", "sp_ep", "dft_ep", 73),
    A("roof-membrane-vs-seam", "TPO", "seam", "fail", "pass", "pass", "4 K", "peel", "weld +4%", 7, 1, "roof", "EPDM", "fail", "temp 4% extra", "window air vs U-value", "rf_op", "wd_rf", "sm_lab", 72),
    A("window-air-vs-uvalue", "window", "U", "0.42", "0.30", "0.31", "2 K", "leak", "gas +4%", 6, 1, "unit", "curtain", "0.50", "spacer 4% extra", "HVAC duct vs leakage", "wn_op", "gs_wn", "u_lab", 71),
    A("hvac-duct-vs-leakage", "duct", "CL", "8.4", "4.0", "4.1", "1 K", "leak", "seal +4%", 6, 1, "riser", "VAV", "11", "mastic 4% extra", "plumb pressure vs hold", "du_op", "sl_du", "cl_du", 70),
    A("plumb-pressure-vs-hold", "DWV", "hold", "fail", "pass", "pass", "1 K", "drop", "cap +4%", 5, 1, "stack", "rough", "fail", "hold 4 min extra", "fire sprinkler vs K-factor", "pl_op", "cp_pl", "hd_pl", 69),
    A("fire-sprinkler-vs-kfactor", "sprinkler", "K", "5.6", "8.0", "7.9", "2 K", "density", "head +4%", 6, 1, "grid", "OH2", "5.6", "orifice 4% extra", "alarm NL vs candela", "sp_op", "hd_sp", "k_sp", 68),
    A("alarm-nl-vs-candela", "horn", "dBA", "68", "75", "74.5", "1 K", "audibility", "tap +4%", 5, 1, "zone", "corridor", "62", "candela 4% extra", "elevator level vs door", "al_op", "tp_al", "dba_lab", 67),
    A("elevator-level-vs-door", "car", "level", "18 mm", "6 mm", "6.2 mm", "1 K", "trip", "encoder +4%", 6, 1, "shaft", "passenger", "24 mm", "learn 4% extra", "escalator brake vs step", "el_op", "en_el", "lv_lab", 66),
    A("escalator-brake-vs-step", "escalator", "stop", "1.8 m", "1.0 m", "1.05 m", "1 K", "overrun", "brake +4%", 5, 1, "bank", "concourse", "2.4 m", "gap 4% extra", "parking CO vs fan", "es_op", "br_es", "st_es", 65),
    A("parking-co-vs-fan", "garage", "CO", "42 ppm", "20 ppm", "21 ppm", "1 K", "CO", "fan +8%", 6, 1, "level", "P2", "55 ppm", "fan 8% extra", "tunnel jet vs CO", "pk_op", "fn_pk", "co_pk", 64),
    A("tunnel-jet-vs-co", "tunnel", "CO", "38 ppm", "15 ppm", "15.4 ppm", "2 K", "CO", "jet +8%", 6, 1, "bore", "road", "50 ppm", "jet 8% extra", "bridge deflect vs load", "tn_op", "jt_tn", "co_tn", 63),
    A("bridge-deflect-vs-load", "span", "defl", "28 mm", "18 mm", "18.4 mm", "1 K", "deflect", "load-cut 4%", 7, 1, "span", "live", "36 mm", "limit 4% extra", "rail gauge vs wear", "br_op", "ld_br", "df_lab", 62),
    A("rail-gauge-vs-wear", "gauge", "wide", "18 mm", "6 mm", "6.2 mm", "1 K", "wear", "tamp +4%", 6, 1, "curve", "main", "24 mm", "tamp 4% extra", "track geometry vs twist", "rl_op", "tp_rl", "gg_lab", 61),
    A("track-geometry-vs-twist", "twist", "mm", "8.4 mm", "3.0 mm", "3.1 mm", "1 K", "twist", "tamp +4%", 6, 1, "curve", "class-4", "11 mm", "tamp 4% extra", "catenary sag vs temp", "tk_op", "tp_tk", "tw_lab", 60),
    A("catenary-sag-vs-temp", "OHLE", "sag", "180 mm", "120 mm", "122 mm", "2 K", "arc", "tension +4%", 7, 1, "span", "25kV", "220 mm", "tension 4% extra", "signal aspect vs relay", "ct_op", "tn_ct", "sg_lab", 59),
    A("signal-aspect-vs-relay", "signal", "aspect", "dark", "green", "green", "1 K", "dark", "relay +4%", 5, 1, "mast", "interlock", "red", "lamp 4% extra", "switch throw vs obstruct", "sg_op", "rl_sg", "as_lab", 58),
    A("switch-throw-vs-obstruct", "switch", "throw", "fail", "pass", "pass", "1 K", "obstruct", "clear +4%", 5, 1, "point", "main", "fail", "detect 4% extra", "dialysis next densify", "sw_op", "cl_sw", "th_lab", 57),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(3635, s)
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
