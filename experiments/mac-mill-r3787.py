#!/usr/bin/env python3
"""MAC mill r3787+. Unique recycling/logistics/hospital-ops plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205h", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("mrf-fiber-vs-contamination", "MRF", "contam", "8.4%", "3.0%", "3.1%", "2 K", "reject", "sort +4%", 8, 1, "bunker", "OCC", "11%", "sort 4% extra", "EDF aluminum vs Fe", "mrf_op", "sr_mrf", "ct_lab", 60),
    A("edf-aluminum-vs-fe", "eddy", "Fe", "1.8%", "0.4%", "0.42%", "1 K", "Fe", "amp +4%", 6, 1, "belt", "UBC", "2.4%", "amp 4% extra", "glass cullet vs ceramic", "ed_op", "am_ed", "fe_ed", 59),
    A("glass-cullet-vs-ceramic", "cullet", "ceramic", "180 ppm", "40 ppm", "42 ppm", "2 K", "stone", "optic +4%", 7, 1, "bunker", "furnace", "240 ppm", "optic 4% extra", "plastic NIR vs black", "gl_op", "op_gl", "cr_lab", 58),
    A("plastic-nir-vs-black", "NIR", "miss", "18%", "6%", "6.2%", "1 K", "black", "air +4%", 6, 1, "belt", "PE", "24%", "air 4% extra", "PET flake vs PVC", "nir_op", "air_nir", "ms_lab", 57),
    A("pet-flake-vs-pvc", "PET", "PVC", "180 ppm", "50 ppm", "52 ppm", "3 K", "PVC", "sink +4%", 8, 1, "silo", "bottle", "240 ppm", "float 4% extra", "HDPE melt vs PP", "pet_op", "sk_pet", "pvc_lab", 56),
    A("hdpe-melt-vs-pp", "HDPE", "PP", "4.8%", "1.0%", "1.05%", "4 K", "PP", "NIR +4%", 7, 1, "silo", "bottle", "6.0%", "NIR 4% extra", "paper pulper vs stickies", "hd_op", "nr_hd", "pp_hd", 55),
    A("paper-pulper-vs-stickies", "OCC", "stickies", "18 mm2/kg", "6 mm2/kg", "6.2", "5 K", "stickies", "screen +4%", 8, 1, "chest", "liner", "24", "slot 4% extra", "organics contamination vs plastics", "pp_op", "sc_pp", "st_pp", 54),
    A("organics-contamination-vs-plastics", "SSO", "plastic", "8.4%", "2.0%", "2.1%", "2 K", "plastic", "sort +4%", 7, 1, "bunker", "AD", "11%", "sort 4% extra", "compost inerts vs screen", "or_op", "sr_or", "pl_or", 53),
    A("compost-inerts-vs-screen", "compost", "inerts", "4.8%", "1.5%", "1.55%", "3 K", "glass", "screen +4%", 8, 1, "pile", "soil", "6.0%", "screen 4% extra", "AD digestate vs pathogen", "cp_op", "sc_cp", "in_lab", 52),
    A("ad-digestate-vs-pathogen", "digestate", "E.coli", "1800", "100", "110", "4 K", "pathogen", "hold +4%", 10, 1, "tank", "land", "2400", "hold 4 h extra", "landfill leachate vs ammonia", "ad_op", "hd_ad", "ec_lab", 51),
    A("landfill-leachate-vs-ammonia", "leachate", "NH3-N", "420 mg/L", "180 mg/L", "185 mg/L", "5 K", "NH3", "strip +4%", 9, 1, "pond", "WWTP", "550 mg/L", "air 4% extra", "LF gas well vs liquid", "lc_op", "st_lc", "nh3_lc", 50),
    A("lf-gas-well-vs-liquid", "LFG well", "liquid", "1.8 m", "0.4 m", "0.42 m", "2 K", "flood", "pump +4%", 7, 1, "well", "flare", "2.4 m", "pump 4% extra", "incin bottom ash vs LOI", "lf_op", "pm_lf", "lq_lab", 49),
    A("incin-bottom-ash-vs-loi", "BA", "LOI", "4.8%", "2.0%", "2.05%", "12 K", "C", "burn +4%", 8, 1, "pit", "agg", "6.0%", "O2 4% extra", "APC residue vs leach", "ba_op", "bn_ba", "loi_ba", 48),
    A("apc-residue-vs-leach", "APC", "Pb", "18 mg/kg", "6 mg/kg", "6.2 mg/kg", "6 K", "leach", "lime +4%", 8, 1, "silo", "haz", "24 mg/kg", "lime 4% extra", "WWTP MLSS vs SVI", "apc_op", "lm_apc", "pb_lab", 47),
    A("wwtp-mlss-vs-svi", "AS", "SVI", "180 mL/g", "120 mL/g", "122 mL/g", "3 K", "bulking", "DO +4%", 8, 1, "basin", "sec", "220 mL/g", "DO 4% extra", "Bardenpho N vs DO", "ww_op", "do_ww", "svi_lab", 46),
    A("bardenpho-n-vs-do", "BNR", "TN", "12 mg/L", "6 mg/L", "6.2 mg/L", "4 K", "N", "anox +4%", 9, 1, "train", "NPDES", "16 mg/L", "recycle 4% extra", "UV disinfect vs UVT", "bn_op", "ax_bn", "tn_bn", 45),
    A("uv-disinfect-vs-uvt", "UV", "UVT", "62%", "75%", "74.5%", "2 K", "coliform", "clean +4%", 6, 1, "channel", "reuse", "55%", "wipe 4% extra", "chlorine CT vs NH2Cl", "uv_op", "cl_uv", "uvt_lab", 44),
    A("chlorine-ct-vs-nh2cl", "CT", "NH2Cl", "1.8 mg/L", "2.5 mg/L", "2.48 mg/L", "3 K", "CT", "Cl2 +4%", 7, 1, "clearwell", "dist", "1.2 mg/L", "Cl2 4% extra", "fluoride dose vs ion", "ct_op", "cl_ct", "nh2_lab", 43),
    A("fluoride-dose-vs-ion", "F", "mg/L", "0.42", "0.70", "0.69", "2 K", "low", "dose +4%", 6, 1, "clearwell", "dist", "0.30", "dose 4% extra", "lime softening vs pH", "fl_op", "ds_fl", "f_lab", 42),
    A("lime-softening-vs-ph", "softening", "pH", "9.8", "10.4", "10.35", "4 K", "carry", "lime +4%", 8, 1, "basin", "dist", "9.4", "lime 4% extra", "ionex nitrate vs leak", "lm_op", "li_lm", "ph_lm", 41),
    A("ionex-nitrate-vs-leak", "IX", "NO3", "18 mg/L", "6 mg/L", "6.2 mg/L", "3 K", "leak", "regen +4%", 8, 1, "bed", "well", "24 mg/L", "brine 4% extra", "GAC TOC vs EBCT", "ix_op", "rg_ix", "no3_lab", 40),
    A("gac-toc-vs-ebct", "GAC", "TOC", "1.8 mg/L", "0.8 mg/L", "0.82 mg/L", "4 K", "TOC", "EBCT +4%", 9, 1, "contactor", "taste", "2.4 mg/L", "empty 4% extra", "PAC taste vs dose", "gac_op", "eb_gac", "toc_lab", 39),
    A("pac-taste-vs-dose", "PAC", "T&O", "8 TON", "3 TON", "3.1 TON", "3 K", "MIB", "PAC +4%", 7, 1, "basin", "dist", "11 TON", "PAC 4% extra", "membrane integrity vs LDP", "pac_op", "ds_pac", "ton_lab", 38),
    A("membrane-integrity-vs-ldp", "MF", "LRV", "2.8", "4.0", "3.95", "2 K", "fiber", "PDT +4%", 6, 1, "skid", "reuse", "2.2", "PDT 4% extra", "postal sort vs OCR", "mf_op", "pdt_mf", "lrv_lab", 37),
    A("postal-sort-vs-ocr", "OCR", "read", "82%", "94%", "93.6%", "1 K", "reject", "lamp +4%", 6, 1, "DBCS", "letter", "74%", "lamp 4% extra", "parcel dim vs oversize", "po_op", "lp_po", "ocr_lab", 36),
    A("parcel-dim-vs-oversize", "DWS", "over", "8.4%", "3.0%", "3.1%", "1 K", "oversize", "cal +4%", 6, 1, "induct", "parcel", "11%", "cal 4% extra", "hub dwell vs missort", "pr_op", "cl_pr", "ov_lab", 35),
    A("hub-dwell-vs-missort", "hub", "missort", "1.8%", "0.4%", "0.42%", "1 K", "missort", "scan +4%", 7, 1, "sort", "next-day", "2.4%", "scan 4% extra", "lastmile scan vs OTP", "hb_op", "sc_hb", "ms_hb", 34),
    A("lastmile-scan-vs-otp", "DSP", "OTP", "88%", "96%", "95.6%", "1 K", "OTP", "geo +4%", 6, 1, "route", "residential", "82%", "geo 4% extra", "warehouse pick vs accuracy", "lm_op", "geo_lm", "otp_lab", 33),
    A("warehouse-pick-vs-accuracy", "pick", "acc", "97.2%", "99.5%", "99.4%", "1 K", "short", "scan +4%", 6, 1, "aisle", "B2C", "95.0%", "scan 4% extra", "ASRS cycle vs queue", "wh_op", "sc_wh", "ac_lab", 32),
    A("asrs-cycle-vs-queue", "ASRS", "cycle", "42 s", "28 s", "28.4 s", "1 K", "queue", "aisle +4%", 6, 1, "crane", "pallet", "55 s", "aisle 4% extra", "conveyor jam vs photoeye", "as_op", "ai_as", "cy_lab", 31),
    A("conveyor-jam-vs-photoeye", "belt", "jam", "18 /h", "4 /h", "4.2 /h", "1 K", "jam", "eye +4%", 5, 1, "line", "sort", "24 /h", "gap 4% extra", "packer weight vs giveaway", "cv_op", "ey_cv", "jm_cv", 30),
    A("packer-weight-vs-giveaway", "packer", "give", "4.8 g", "1.5 g", "1.55 g", "2 K", "giveaway", "tare +4%", 6, 1, "line", "bag", "6.0 g", "tare 4% extra", "label print vs scan", "pk_op", "tr_pk", "gv_lab", 29),
    A("label-print-vs-scan", "label", "grade", "C", "A", "A", "1 K", "unreadable", "head +4%", 5, 1, "line", "GS1", "F", "ribbon 4% extra", "shrink tunnel vs seal", "lb_op", "hd_lb", "gr_lab", 28),
    A("shrink-tunnel-vs-seal", "shrink", "seal", "fail", "pass", "pass", "3 K", "burn", "T -4%", 6, 1, "tunnel", "bundle", "fail", "belt 4% extra", "case erect vs glue", "sh_op", "t_sh", "sl_sh", 27),
    A("case-erect-vs-glue", "case", "glue", "fail", "pass", "pass", "2 K", "open", "glue +4%", 5, 1, "erector", "RSC", "fail", "glue 4% extra", "pallet wrap vs contain", "cs_op", "gl_cs", "gl_lab", 26),
    A("pallet-wrap-vs-contain", "wrap", "contain", "fail", "pass", "pass", "1 K", "shift", "wrap +4%", 6, 1, "pallet", "stretch", "fail", "rev 4% extra", "cold chain logger vs excursion", "pl_op", "wp_pl", "ct_lab", 25),
    A("cold-chain-logger-vs-excursion", "logger", "excurs", "18", "2", "2.2", "1 K", "warm", "set +4%", 6, 1, "lane", "2-8C", "28", "pack 4% extra", "crossdock dwell vs late", "cc_op", "st_cc", "ex_lab", 24),
    A("crossdock-dwell-vs-late", "Xdock", "dwell", "42 min", "22 min", "22.4 min", "1 K", "late", "door +4%", 6, 1, "dock", "LTL", "55 min", "door 4% extra", "yard checkin vs dwell", "xd_op", "dr_xd", "dw_lab", 23),
    A("yard-checkin-vs-dwell", "yard", "dwell", "180 min", "60 min", "62 min", "1 K", "dwell", "spot +4%", 7, 1, "yard", "inbound", "240 min", "jockey 4% extra", "trailer seal vs manifest", "yd_op", "sp_yd", "dw_yd", 22),
    A("trailer-seal-vs-manifest", "seal", "mismatch", "fail", "pass", "pass", "1 K", "seal", "photo +4%", 5, 1, "gate", "OTR", "fail", "photo 4% extra", "retail shrink vs scan", "tr_op", "ph_tr", "sl_tr", 21),
    A("retail-shrink-vs-scan", "POS", "shrink", "1.8%", "0.6%", "0.62%", "1 K", "shrink", "scan +4%", 6, 1, "lane", "grocery", "2.4%", "scan 4% extra", "POS void vs override", "rt_op", "sc_rt", "sh_rt", 20),
    A("pos-void-vs-override", "POS", "void", "4.8%", "1.5%", "1.55%", "1 K", "void", "PIN +4%", 5, 1, "lane", "front", "6.0%", "PIN 4% extra", "scale tare vs PLU", "pos_op", "pn_pos", "vd_lab", 19),
    A("scale-tare-vs-plu", "scale", "PLU", "fail", "pass", "pass", "1 K", "tare", "zero +4%", 5, 1, "produce", "self", "fail", "zero 4% extra", "fuel pump vs blend", "sc_op", "zr_sc", "plu_lab", 18),
    A("fuel-pump-vs-blend", "dispenser", "blend", "fail", "pass", "pass", "2 K", "octane", "valve +4%", 6, 1, "pump", "E10", "fail", "valve 4% extra", "cstore age vs ID", "fp_op", "vl_fp", "bl_fp", 17),
    A("cstore-age-vs-id", "ID", "fail", "fail", "pass", "pass", "1 K", "underage", "scan +4%", 5, 1, "counter", "tobacco", "fail", "scan 4% extra", "pharmacy fill vs NDC", "cs_op", "sc_cs", "id_lab", 16),
    A("pharmacy-fill-vs-ndc", "fill", "NDC", "fail", "match", "match", "1 K", "wrong", "scan +4%", 5, 1, "bench", "Rx", "fail", "scan 4% extra", "lab draw vs hemolysis", "ph_op", "sc_ph", "ndc_lab", 15),
    A("lab-draw-vs-hemolysis", "draw", "H", "8.4%", "2.0%", "2.1%", "1 K", "hemol", "gauge +4%", 5, 1, "OP", "BMP", "11%", "gauge 4% extra", "ER triage vs ESI", "lb_op", "gg_lb", "h_lab", 14),
    A("er-triage-vs-esi", "ESI", "LWBS", "8.4%", "3.0%", "3.1%", "1 K", "LWBS", "ESI +4%", 6, 1, "triage", "ED", "11%", "bed 4% extra", "OR turnover vs TR", "er_op", "esi_er", "lw_lab", 13),
    A("or-turnover-vs-tr", "OR", "turn", "42 min", "22 min", "22.4 min", "1 K", "delay", "EVS +4%", 6, 1, "OR", "block", "55 min", "EVS 4% extra", "ICU nurse vs ratio", "or_op", "ev_or", "tn_or", 12),
    A("icu-nurse-vs-ratio", "ICU", "ratio", "3:1", "2:1", "2:1", "1 K", "unsafe", "staff +4%", 5, 1, "pod", "MICU", "4:1", "float 4% extra", "ED LWBS vs wait", "icu_op", "st_icu", "rt_lab", 11),
    A("ed-lwbs-vs-wait", "ED", "wait", "180 min", "60 min", "62 min", "1 K", "LWBS", "fast-track +4%", 6, 1, "lobby", "ESI-4", "240 min", "fast-track 4% extra", "lab TAT vs STAT", "ed_op", "ft_ed", "wt_lab", 10),
    A("lab-tat-vs-stat", "STAT", "TAT", "82 min", "45 min", "46 min", "1 K", "TAT", "tube +4%", 6, 1, "core", "ED", "110 min", "tube 4% extra", "blood issue vs XM", "lab_op", "tb_lab", "tat_lab", 9),
    A("blood-issue-vs-xm", "XM", "delay", "42 min", "18 min", "18.4 min", "1 K", "delay", "type +4%", 5, 1, "BB", "OR", "55 min", "type 4% extra", "sterile case vs count", "bb_op", "tp_bb", "xm_lab", 8),
    A("sterile-case-vs-count", "count", "mismatch", "fail", "pass", "pass", "1 K", "count", "recount +4%", 5, 1, "OR", "close", "fail", "xray 4% extra", "CSSD loaner vs set", "st_op", "rc_st", "ct_st", 7),
    A("cssd-loaner-vs-set", "loaner", "late", "fail", "pass", "pass", "1 K", "late", "track +4%", 6, 1, "CSSD", "spine", "fail", "track 4% extra", "diet tray vs ID", "cs_op", "tr_cs", "ln_lab", 6),
    A("diet-tray-vs-id", "tray", "mismatch", "fail", "pass", "pass", "1 K", "allergy", "scan +4%", 5, 1, "kitchen", "NPO", "fail", "scan 4% extra", "linen par vs OR", "dt_op", "sc_dt", "id_dt", 5),
    A("linen-par-vs-or", "linen", "par", "0.62", "1.00", "0.98", "1 K", "short", "par +4%", 6, 1, "OR", "pack", "0.50", "par 4% extra", "EVS ATP vs room", "ln_op", "pr_ln", "par_lab", 4),
    A("evs-atp-vs-room", "EVS", "ATP", "180 RLU", "50 RLU", "52 RLU", "1 K", "ATP", "clean +4%", 6, 1, "room", "ISO", "240 RLU", "clean 4% extra", "morgue ID vs tag", "evs_op", "cl_evs", "atp_evs", 3),
    A("morgue-id-vs-tag", "morgue", "ID", "fail", "pass", "pass", "1 K", "mismatch", "tag +4%", 5, 1, "drawer", "release", "fail", "photo 4% extra", "biobank freeze vs ID", "mg_op", "tg_mg", "id_mg", 2),
    A("biobank-freeze-vs-id", "biobank", "ID", "fail", "pass", "pass", "2 K", "mix", "scan +4%", 6, 1, "LN2", "aliquot", "fail", "scan 4% extra", "MRF next densify", "bbk_op", "sc_bbk", "id_bbk", 61),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(3787, s)
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
