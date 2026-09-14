#!/usr/bin/env python3
"""MAC mill r3715+. Unique aviation/port/forestry/DC/venue plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205g", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("runway-friction-vs-rubber", "runway", "mu", "0.38", "0.50", "0.49", "2 K", "rubber", "sweep +4%", 8, 1, "RWY", "arrivals", "0.30", "sweep 4% extra", "taxiway hold vs incursion", "rw_op", "sw_rw", "mu_lab", 62),
    A("taxiway-hold-vs-incursion", "taxi", "hold", "fail", "pass", "pass", "1 K", "incursion", "stopbar +4%", 5, 1, "A3", "ground", "fail", "bar 4% extra", "ILS CAT vs RVR", "tx_op", "sb_tx", "hd_tx", 61),
    A("ils-cat-vs-rvr", "ILS", "RVR", "280 m", "550 m", "540 m", "1 K", "CAT", "light +4%", 6, 1, "RWY", "CAT-II", "200 m", "ALS 4% extra", "radar clutter vs gain", "ils_op", "lt_ils", "rvr_lab", 60),
    A("radar-clutter-vs-gain", "ASR", "clutter", "18%", "6%", "6.2%", "1 K", "false", "gain -4%", 5, 1, "scope", "approach", "24%", "MTI 4% extra", "ATC sector vs count", "rd_op", "gn_rd", "cl_lab", 59),
    A("atc-sector-vs-count", "sector", "count", "28", "18", "18.4", "1 K", "overload", "split +4%", 6, 1, "sector", "enroute", "36", "split 4% extra", "gate turn vs tow", "atc_op", "sp_atc", "ct_lab", 58),
    A("gate-turn-vs-tow", "gate", "turn", "52 min", "38 min", "38.5 min", "1 K", "delay", "tow +4%", 7, 1, "B12", "narrowbody", "62 min", "tow 4 min extra", "fuel hydrant vs FSII", "gt_op", "tw_gt", "tn_lab", 57),
    A("fuel-hydrant-vs-fsii", "Jet-A", "FSII", "0.08%", "0.12%", "0.118%", "2 K", "freeze", "FSII +4%", 8, 1, "hydrant", "wing", "0.05%", "inject 4% extra", "deice type vs holdover", "fu_op", "fs_fu", "fsii_lab", 56),
    A("deice-type-vs-holdover", "deice", "HOT", "8 min", "20 min", "19 min", "1 K", "holdover", "Type-IV +4%", 6, 1, "pad", "depart", "5 min", "Type-IV 4% extra", "jetbridge level vs door", "di_op", "t4_di", "hot_lab", 55),
    A("jetbridge-level-vs-door", "bridge", "level", "80 mm", "20 mm", "22 mm", "1 K", "door", "cab +4%", 5, 1, "B12", "jet", "120 mm", "cab 4% extra", "baggage belt vs jam", "jb_op", "cb_jb", "lv_jb", 54),
    A("baggage-belt-vs-jam", "belt", "jam", "18 /h", "4 /h", "4.2 /h", "1 K", "jam", "speed -4%", 6, 1, "carousel", "claim", "24 /h", "gap 4% extra", "cargo ULD vs CG", "bg_op", "sp_bg", "jm_lab", 53),
    A("cargo-uld-vs-cg", "ULD", "CG", "8.4%", "3.0%", "3.1%", "1 K", "CG", "restow +4%", 7, 1, "hold", "belly", "11%", "restow 4% extra", "catering temp vs hold", "cg_op", "rs_cg", "cg_lab", 52),
    A("catering-temp-vs-hold", "galley", "T", "8.4 C", "4.0 C", "4.2 C", "1 K", "warm", "ice +4%", 5, 1, "cart", "service", "10 C", "ice 4% extra", "APU EGT vs bleed", "ct_op", "ic_ct", "t_ct", 51),
    A("apu-egt-vs-bleed", "APU", "EGT", "680 C", "620 C", "622 C", "3 K", "hot", "bleed -4%", 6, 1, "tail", "gate", "720 C", "load 4% extra", "engine EGT vs N1", "apu_op", "bl_apu", "egt_apu", 50),
    A("engine-egt-vs-n1", "CFM", "EGT", "920 C", "860 C", "862 C", "4 K", "hot", "N1 -4%", 6, 1, "eng", "TO", "960 C", "flex 4% extra", "hyd qty vs leak", "en_op", "n1_en", "egt_en", 49),
    A("hyd-qty-vs-leak", "HYD", "qty", "0.62", "0.85", "0.84", "1 K", "leak", "isolate +4%", 5, 1, "sys-A", "green", "0.50", "isolate 4% extra", "cabin press vs outflow", "hy_op", "is_hy", "qt_lab", 48),
    A("cabin-press-vs-outflow", "cabin", "dP", "8.8 psi", "8.0 psi", "8.05 psi", "1 K", "overpress", "outflow +4%", 5, 1, "cabin", "climb", "9.2 psi", "valve 4% extra", "pitot heat vs IAS", "cb_op", "of_cb", "dp_cb", 47),
    A("pitot-heat-vs-ias", "pitot", "IAS", "fail", "live", "live", "1 K", "ice", "heat +4%", 4, 1, "probe", "climb", "fail", "heat 4% extra", "TCAS RA vs alt", "pt_op", "ht_pt", "ias_lab", 46),
    A("tcas-ra-vs-alt", "TCAS", "RA", "climb", "monitor", "monitor", "1 K", "RA", "alt +4%", 4, 1, "cockpit", "enroute", "descend", "vs 4% extra", "GPWS sink vs flap", "tc_op", "al_tc", "ra_lab", 45),
    A("gpws-sink-vs-flap", "GPWS", "sink", "alert", "clear", "clear", "1 K", "sinkrate", "flap +4%", 4, 1, "cockpit", "approach", "alert", "vs 4% extra", "wx radar vs gain", "gp_op", "fl_gp", "sk_lab", 44),
    A("wx-radar-vs-gain", "wx", "gain", "18 dB", "8 dB", "8.2 dB", "1 K", "atten", "tilt +4%", 5, 1, "wx", "cell", "24 dB", "tilt 4% extra", "dock fender vs berth", "wx_op", "tl_wx", "gn_wx", 43),
    A("dock-fender-vs-berth", "berth", "energy", "280 kNm", "180 kNm", "182 kNm", "1 K", "impact", "approach -4%", 6, 1, "quay", "panamax", "360 kNm", "tug 4% extra", "crane spreader vs twist", "dk_op", "ap_dk", "en_dk", 42),
    A("crane-spreader-vs-twist", "STS", "twist", "fail", "lock", "lock", "1 K", "unlock", "align +4%", 5, 1, "spreader", "40ft", "fail", "land 4% extra", "reefer plug vs set", "cr_op", "al_cr", "tw_cr", 41),
    A("reefer-plug-vs-set", "reefer", "T", "8.4 C", "4.0 C", "4.1 C", "1 K", "warm", "plug +4%", 6, 1, "stack", "reefer", "10 C", "alarm 4 min extra", "pilot ladder vs freeboard", "rf_op", "pl_rf", "t_rf", 40),
    A("pilot-ladder-vs-freeboard", "ladder", "spread", "fail", "pass", "pass", "1 K", "IMO", "spread +4%", 5, 1, "pilot", "board", "fail", "manrope 4% extra", "tug bollard vs current", "pl_op", "sp_pl", "sp_lab", 39),
    A("tug-bollard-vs-current", "tug", "bp", "42 t", "55 t", "54 t", "1 K", "current", "assist +4%", 6, 1, "tug", "berth", "36 t", "second tug 4% extra", "lock level vs gate", "tg_op", "as_tg", "bp_lab", 38),
    A("lock-level-vs-gate", "lock", "level", "180 mm", "40 mm", "42 mm", "1 K", "gate", "fill +4%", 7, 1, "chamber", "barge", "280 mm", "fill 4% extra", "weir crest vs Q", "lk_op", "fl_lk", "lv_lk", 37),
    A("weir-crest-vs-q", "weir", "Q", "18 m3/s", "12 m3/s", "12.2 m3/s", "1 K", "overtop", "gate +4%", 6, 1, "crest", "flood", "24 m3/s", "gate 4% extra", "levee seepage vs head", "wr_op", "gt_wr", "q_wr", 36),
    A("levee-seepage-vs-head", "levee", "seep", "18 L/min", "6 L/min", "6.2 L/min", "1 K", "boil", "blanket +4%", 8, 1, "toe", "flood", "28 L/min", "sandbag 4% extra", "dam uplift vs drain", "lv_op", "bl_lv", "sp_lv", 35),
    A("dam-uplift-vs-drain", "dam", "uplift", "0.42", "0.25", "0.26", "1 K", "drain", "relief +4%", 7, 1, "gallery", "gravity", "0.55", "flush 4% extra", "spillway gate vs Q", "dm_op", "rl_dm", "up_lab", 34),
    A("spillway-gate-vs-q", "spillway", "Q", "280 m3/s", "180 m3/s", "182 m3/s", "1 K", "overtop", "gate +4%", 6, 1, "bay", "flood", "360 m3/s", "gate 4% extra", "fish ladder vs attract", "sp_op", "gt_sp", "q_sp", 33),
    A("fish-ladder-vs-attract", "ladder", "attract", "0.42", "0.70", "0.68", "1 K", "delay", "flow +4%", 7, 1, "ladder", "salmon", "0.30", "orifice 4% extra", "sediment sluice vs turbid", "fs_op", "fl_fs", "at_lab", 32),
    A("sediment-sluice-vs-turbid", "sluice", "NTU", "280", "80", "82", "1 K", "plume", "pulse +4%", 6, 1, "sluice", "reservoir", "360", "pulse 4% extra", "forest slash vs fuel", "sd_op", "pl_sd", "ntu_sd", 31),
    A("forest-slash-vs-fuel", "slash", "load", "28 t/ha", "12 t/ha", "12.4 t/ha", "2 K", "fire", "chip +4%", 8, 1, "unit", "thin", "36 t/ha", "chip 4% extra", "skidder rut vs soil", "fr_op", "ch_fr", "ld_fr", 30),
    A("skidder-rut-vs-soil", "skid", "rut", "180 mm", "80 mm", "82 mm", "1 K", "rut", "slash +4%", 6, 1, "trail", "harvest", "240 mm", "slash 4% extra", "mill chip vs bark", "sk_op", "sl_sk", "rt_lab", 29),
    A("mill-chip-vs-bark", "chip", "bark", "4.8%", "1.5%", "1.55%", "3 K", "bark", "screen +4%", 7, 1, "pile", "pulp", "6.0%", "screen 4% extra", "saw kerf vs yield", "ch_op", "sc_ch", "bk_ch", 28),
    A("saw-kerf-vs-yield", "saw", "kerf", "4.8 mm", "3.2 mm", "3.25 mm", "2 K", "yield", "thin +4%", 6, 1, "line", "lumber", "5.5 mm", "plate 4% extra", "veneer moisture vs check", "sw_op", "tn_sw", "kf_lab", 27),
    A("veneer-moisture-vs-check", "veneer", "MC", "12.4%", "8.0%", "8.1%", "5 K", "check", "dry +4%", 8, 1, "sheet", "ply", "14%", "zone 4% extra", "plywood void vs glue", "vn_op", "dr_vn", "mc_vn", 26),
    A("plywood-void-vs-glue", "ply", "void", "8%", "2%", "2.1%", "4 K", "void", "spread +4%", 7, 1, "press", "CDX", "12%", "glue 4% extra", "OSB IB vs resin", "ply_op", "sp_ply", "vd_ply", 25),
    A("osb-ib-vs-resin", "OSB", "IB", "0.32 MPa", "0.45 MPa", "0.44 MPa", "6 K", "swell", "resin +4%", 8, 1, "press", "sheath", "0.26 MPa", "resin 4% extra", "MDF swell vs resin", "osb_op", "rs_osb", "ib_lab", 24),
    A("mdf-swell-vs-resin", "MDF", "TS", "12.4%", "8.0%", "8.1%", "5 K", "swell", "resin +4%", 8, 1, "press", "furniture", "14%", "resin 4% extra", "lumber grade vs wane", "mdf_op", "rs_mdf", "ts_lab", 23),
    A("lumber-grade-vs-wane", "lumber", "wane", "18%", "8%", "8.2%", "2 K", "wane", "trim +4%", 6, 1, "bay", "#2", "24%", "trim 4% extra", "kiln MC vs check", "lm_op", "tr_lm", "wn_lab", 22),
    A("kiln-mc-vs-check", "kiln", "MC", "14.2%", "12.0%", "12.1%", "6 K", "check", "schedule +4%", 10, 1, "charge", "KD", "16%", "hold 4 h extra", "treat retention vs penetration", "kl_op", "sc_kl", "mc_kl", 21),
    A("treat-retention-vs-penetration", "CCA", "pcf", "0.28", "0.40", "0.39", "4 K", "pen", "vac +4%", 8, 1, "charge", "ground", "0.22", "vac 4% extra", "pole MCA vs check", "tr_op", "vc_tr", "pcf_lab", 20),
    A("pole-mca-vs-check", "pole", "check", "18 mm", "8 mm", "8.2 mm", "5 K", "check", "season +4%", 9, 1, "yard", "class-2", "24 mm", "season 4% extra", "DC PUE vs inlet", "po_op", "sn_po", "ck_po", 19),
    A("dc-pue-vs-inlet", "DC", "PUE", "1.62", "1.35", "1.36", "3 K", "hot", "set +4%", 7, 1, "hall", "IT", "1.80", "aisle 4% extra", "PDU load vs phase", "dc_op", "st_dc", "pue_lab", 18),
    A("pdu-load-vs-phase", "PDU", "imbal", "18%", "6%", "6.2%", "1 K", "phase", "move +4%", 6, 1, "row", "A", "24%", "move 4% extra", "UPS runtime vs load", "pdu_op", "mv_pdu", "im_lab", 17),
    A("ups-runtime-vs-load", "UPS", "min", "8 min", "15 min", "14.6 min", "2 K", "runtime", "shed +4%", 6, 1, "UPS", "N+1", "5 min", "shed 4% extra", "CRAC delta vs set", "ups_op", "sh_ups", "rt_lab", 16),
    A("crac-delta-vs-set", "CRAC", "dT", "8.4 K", "12 K", "11.8 K", "2 K", "short", "set +4%", 6, 1, "CRAC", "hot-aisle", "6 K", "plenum 4% extra", "aisle contain vs bypass", "cr_op", "st_cr", "dt_cr", 15),
    A("aisle-contain-vs-bypass", "aisle", "bypass", "18%", "6%", "6.2%", "1 K", "bypass", "blank +4%", 5, 1, "row", "contain", "24%", "blank 4% extra", "fiber OTDR vs loss", "ai_op", "bl_ai", "bp_lab", 14),
    A("fiber-otdr-vs-loss", "span", "dB", "0.42", "0.20", "0.21", "1 K", "splice", "resplice +4%", 6, 1, "span", "metro", "0.55", "splice 4% extra", "DWDM OSNR vs span", "fb_op", "rs_fb", "db_lab", 13),
    A("dwdm-osnr-vs-span", "DWDM", "OSNR", "14.2 dB", "18.0 dB", "17.8 dB", "2 K", "OSNR", "EDFA +4%", 7, 1, "span", "long-haul", "12 dB", "pump 4% extra", "OLT PON vs ONU", "dw_op", "ed_dw", "osnr_lab", 12),
    A("olt-pon-vs-onu", "PON", "ONU", "fail", "reg", "reg", "1 K", "LOS", "power +4%", 5, 1, "OLT", "GPON", "fail", "atten 4% extra", "mobile RSRP vs handover", "olt_op", "pw_olt", "onu_lab", 11),
    A("mobile-rsrp-vs-handover", "LTE", "RSRP", "-118 dBm", "-102 dBm", "-103 dBm", "1 K", "drop", "tilt +4%", 6, 1, "sector", "urban", "-124 dBm", "tilt 4% extra", "BTS VSWR vs return", "mb_op", "tl_mb", "rsrp_lab", 10),
    A("bts-vswr-vs-return", "BTS", "VSWR", "1.82", "1.30", "1.32", "1 K", "return", "jumper +4%", 5, 1, "sector", "macro", "2.10", "jumper 4% extra", "microwave fade vs ATPC", "bts_op", "jp_bts", "vswr_bts", 9),
    A("microwave-fade-vs-atpc", "MW", "fade", "18 dB", "8 dB", "8.2 dB", "1 K", "fade", "ATPC +4%", 6, 1, "hop", "18GHz", "24 dB", "ATPC 4% extra", "satcom C/N0 vs rain", "mw_op", "at_mw", "fd_lab", 8),
    A("satcom-cno-vs-rain", "sat", "C/N0", "42 dBHz", "52 dBHz", "51.6 dBHz", "2 K", "rain", "power +4%", 6, 1, "dish", "Ku", "38 dBHz", "uplink 4% extra", "broadcast MER vs constellation", "sat_op", "pw_sat", "cn_lab", 7),
    A("broadcast-mer-vs-constellation", "TX", "MER", "22 dB", "28 dB", "27.6 dB", "2 K", "MER", "drive +4%", 6, 1, "TX", "ATSC", "18 dB", "drive 4% extra", "studio loudness vs LUFS", "bc_op", "dr_bc", "mer_lab", 6),
    A("studio-loudness-vs-lufs", "mix", "LUFS", "-12", "-16", "-15.8", "1 K", "loud", "limit +4%", 5, 1, "studio", "deliver", "-10", "limit 4% extra", "cinema DCI vs nit", "st_op", "lm_st", "lufs_lab", 5),
    A("cinema-dci-vs-nit", "proj", "nit", "38", "48", "47.6", "2 K", "lamp", "lamp +4%", 6, 1, "screen", "DCI", "32", "lamp 4% extra", "LED wall vs nits", "cn_op", "lp_cn", "nt_lab", 4),
    A("led-wall-vs-nits", "wall", "nit", "420", "600", "590", "2 K", "dim", "drive +4%", 6, 1, "wall", "IMAG", "320", "drive 4% extra", "stage SPL vs limit", "led_op", "dr_led", "nt_led", 3),
    A("stage-spl-vs-limit", "PA", "SPL", "112 dB", "102 dB", "102.4 dB", "1 K", "limit", "gain -4%", 5, 1, "FOH", "festival", "118 dB", "limit 4% extra", "rig load vs SWL", "st_op", "gn_st", "spl_lab", 2),
    A("rig-load-vs-swl", "truss", "SWL", "0.92", "0.70", "0.71", "1 K", "overload", "point +4%", 6, 1, "grid", "roof", "1.05", "point 4% extra", "pyro cue vs arm", "rg_op", "pt_rg", "swl_lab", 73),
    A("pyro-cue-vs-arm", "pyro", "arm", "fail", "safe", "safe", "1 K", "arm", "key +4%", 4, 1, "cue", "finale", "fail", "key 4% extra", "fog density vs detect", "py_op", "ky_py", "arm_lab", 72),
    A("fog-density-vs-detect", "fog", "OD", "0.42", "0.20", "0.21", "1 K", "detect", "haze -4%", 5, 1, "stage", "beam", "0.55", "haze 4% extra", "pool FAC vs pH", "fg_op", "hz_fg", "od_lab", 71),
    A("pool-fac-vs-ph", "pool", "FAC", "0.42 ppm", "1.5 ppm", "1.48 ppm", "2 K", "FAC", "feed +4%", 6, 1, "basin", "lap", "0.20 ppm", "feed 4% extra", "spa bromine vs ORP", "pl_op", "fd_pl", "fac_lab", 70),
    A("spa-bromine-vs-orp", "spa", "ORP", "420 mV", "650 mV", "640 mV", "2 K", "ORP", "Br +4%", 6, 1, "spa", "hot", "360 mV", "Br 4% extra", "ice rink vs brine", "sp_op", "br_sp", "orp_sp", 69),
    A("ice-rink-vs-brine", "ice", "T", "-4.8 C", "-7.0 C", "-6.9 C", "3 K", "soft", "brine +4%", 7, 1, "pad", "hockey", "-3.0 C", "brine 4% extra", "turf hardness vs Gmax", "ic_op", "br_ic", "t_ic", 68),
    A("turf-hardness-vs-gmax", "turf", "Gmax", "142", "110", "112", "2 K", "Gmax", "infill +4%", 6, 1, "field", "soccer", "160", "infill 4% extra", "track stiffness vs Gmax", "tf_op", "in_tf", "gmax_tf", 67),
    A("track-stiffness-vs-gmax", "track", "Gmax", "180", "140", "142", "2 K", "Gmax", "mat +4%", 6, 1, "oval", "sprint", "200", "mat 4% extra", "scoreboard pixel vs mod", "tk_op", "mt_tk", "gmax_tk", 66),
    A("scoreboard-pixel-vs-mod", "board", "mod", "fail", "pass", "pass", "1 K", "dead", "card +4%", 5, 1, "board", "endzone", "fail", "card 4% extra", "lighting lux vs glare", "sc_op", "cd_sc", "md_lab", 65),
    A("lighting-lux-vs-glare", "field", "lux", "280", "500", "490", "2 K", "glare", "aim +4%", 6, 1, "pole", "night", "220", "aim 4% extra", "PA STI vs delay", "lt_op", "am_lt", "lx_lab", 64),
    A("pa-sti-vs-delay", "PA", "STI", "0.42", "0.60", "0.59", "1 K", "echo", "delay +4%", 5, 1, "bowl", "announce", "0.32", "delay 4% extra", "runway next densify", "pa_op", "dl_pa", "sti_lab", 63),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(3715, s)
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
