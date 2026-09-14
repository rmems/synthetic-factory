#!/usr/bin/env python3
"""MAC mill r4001+. Unique film/nonwoven/geosynthetic plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205l", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("biax-film-vs-bow", "BOPP", "bow", "18 mm", "6 mm", "6.2 mm", "5 K", "bow", "TD +4%", 8, 1, "roll", "label", "24 mm", "TD 4% extra", "cast film vs gauge", "bx_op", "td_bx", "bw_lab", 50),
    A("cast-film-vs-gauge", "cast", "gauge", "8.4%", "3.0%", "3.1%", "4 K", "gauge", "die +4%", 7, 1, "roll", "CPP", "11%", "die 4% extra", "blown film vs frost", "cs_op", "die_cs", "gg_lab", 49),
    A("blown-film-vs-frost", "blown", "frost", "420 mm", "280 mm", "282 mm", "5 K", "gauge", "BUR +4%", 7, 1, "roll", "bag", "500 mm", "air 4% extra", "CPP film vs haze", "bl_op", "bur_bl", "fr_lab", 48),
    A("cpp-film-vs-haze", "CPP", "haze", "8.4%", "3.0%", "3.1%", "4 K", "haze", "chill +4%", 7, 1, "roll", "retort", "11%", "chill 4% extra", "BOPP film vs shrink", "cpp_op", "ch_cpp", "hz_lab", 47),
    A("bopp-film-vs-shrink", "BOPP", "shrink", "4.8%", "2.0%", "2.1%", "5 K", "shrink", "anneal +4%", 8, 1, "roll", "tape", "6.0%", "anneal 4% extra", "BOPET film vs dyne", "bp_op", "an_bp", "sh_bp", 46),
    A("bopet-film-vs-dyne", "BOPET", "dyne", "38", "46", "45.6", "4 K", "ink", "corona +4%", 6, 1, "roll", "print", "34", "corona 4% extra", "PA film vs OTR", "pet_op", "cr_pet", "dy_lab", 45),
    A("pa-film-vs-otr", "PA", "OTR", "42", "18", "18.4", "5 K", "OTR", "quench +4%", 8, 1, "roll", "barrier", "55", "quench 4% extra", "EVOH film vs OTR2", "pa_op", "qn_pa", "otr_pa", 44),
    A("evoh-film-vs-otr2", "EVOH", "OTR", "1.8", "0.6", "0.62", "5 K", "OTR", "RH-cut 4%", 8, 1, "roll", "MAP", "2.4", "RH 4% extra", "alufoil pin vs pinhole", "ev_op", "rh_ev", "otr_ev", 43),
    A("alufoil-pin-vs-pinhole", "foil", "pin", "18 /m2", "4 /m2", "4.2 /m2", "4 K", "pin", "anneal +4%", 7, 1, "roll", "pharma", "24 /m2", "anneal 4% extra", "metallize OD vs rate", "al_op", "an_al", "pn_lab", 42),
    A("metallize-od-vs-rate", "met", "OD", "1.8", "2.4", "2.38", "4 K", "OD", "Al +4%", 7, 1, "roll", "snack", "1.4", "Al 4% extra", "SiOx coat vs OTR", "mt_op", "al_mt", "od_lab", 41),
    A("siox-coat-vs-otr", "SiOx", "OTR", "8.4", "2.0", "2.1", "5 K", "OTR", "power +4%", 8, 1, "roll", "PET", "11", "power 4% extra", "AlOx coat vs MVTR", "sx_op", "pw_sx", "otr_sx", 40),
    A("alox-coat-vs-mvtr", "AlOx", "MVTR", "1.8", "0.5", "0.52", "5 K", "MVTR", "power +4%", 8, 1, "roll", "PET", "2.4", "power 4% extra", "stretch film vs cling", "ax_op", "pw_ax", "mv_lab", 39),
    A("stretch-film-vs-cling", "stretch", "cling", "8.4 N", "14 N", "13.8 N", "4 K", "slip", "PIB +4%", 7, 1, "roll", "pallet", "6 N", "PIB 4% extra", "shrink film vs ratio", "st_op", "pib_st", "cl_st", 38),
    A("shrink-film-vs-ratio", "shrink", "ratio", "42%", "55%", "54.6%", "5 K", "ratio", "orient +4%", 8, 1, "roll", "bundle", "34%", "orient 4% extra", "spunbond gsm vs MD", "sh_op", "or_sh", "rt_lab", 37),
    A("spunbond-gsm-vs-md", "spunbond", "MD", "18 N", "28 N", "27.6 N", "5 K", "weak", "draw +4%", 8, 1, "roll", "hygiene", "14 N", "draw 4% extra", "meltblown fiber vs dia", "sb_op", "dr_sb", "md_sb", 36),
    A("meltblown-fiber-vs-dia", "meltblown", "d50", "8.4 µm", "3.0 µm", "3.1 µm", "6 K", "coarse", "air +4%", 8, 1, "roll", "filter", "11 µm", "air 4% extra", "SMS barrier vs hydrohead", "mb_op", "air_mb", "d50_mb", 35),
    A("sms-barrier-vs-hydrohead", "SMS", "HH", "18 cm", "40 cm", "39 cm", "5 K", "leak", "MB +4%", 8, 1, "roll", "medical", "14 cm", "MB 4% extra", "spunlace entangle vs strength", "sms_op", "mb_sms", "hh_lab", 34),
    A("spunlace-entangle-vs-strength", "spunlace", "MD", "28 N", "42 N", "41.6 N", "4 K", "weak", "jet +4%", 7, 1, "roll", "wipe", "22 N", "jet 4% extra", "airlaid SAP vs acquire", "sl_op", "jt_sl", "md_sl", 33),
    A("airlaid-sap-vs-acquire", "airlaid", "acq", "18 s", "8 s", "8.2 s", "4 K", "slow", "SAP +4%", 7, 1, "roll", "core", "24 s", "SAP 4% extra", "wetlaid formation vs CV", "al_op", "sap_al", "acq_lab", 32),
    A("wetlaid-formation-vs-cv", "wetlaid", "CV", "18%", "8%", "8.2%", "4 K", "cloud", "dilute +4%", 7, 1, "wire", "glass", "24%", "dilute 4% extra", "needlefelt punch vs density", "wl_op", "dl_wl", "cv_wl", 31),
    A("needlefelt-punch-vs-density", "felt", "density", "0.12", "0.18", "0.178", "4 K", "loft", "punch +4%", 7, 1, "roll", "filter", "0.09", "punch 4% extra", "stitchbond loop vs peel", "nf_op", "pn_nf", "dn_lab", 30),
    A("stitchbond-loop-vs-peel", "stitchbond", "peel", "8.4 N", "14 N", "13.8 N", "4 K", "peel", "stitch +4%", 7, 1, "roll", "geo", "6 N", "stitch 4% extra", "carded web vs MDCD", "st_op", "st_st", "pl_st", 29),
    A("carded-web-vs-mdcd", "card", "MD/CD", "4.8", "2.5", "2.55", "3 K", "aniso", "doffer +4%", 6, 1, "web", "wipes", "6.0", "doffer 4% extra", "crosslap angle vs isotropy", "cd_op", "df_cd", "mdcd_lab", 28),
    A("crosslap-angle-vs-isotropy", "crosslap", "MD/CD", "2.8", "1.4", "1.42", "3 K", "aniso", "angle +4%", 6, 1, "web", "felt", "3.5", "angle 4% extra", "thermalbond point vs loft", "cl_op", "an_cl", "iso_lab", 27),
    A("thermalbond-point-vs-loft", "TB", "loft", "8.4 mm", "14 mm", "13.8 mm", "4 K", "crush", "T -4%", 6, 1, "roll", "hygiene", "6 mm", "T 4% extra", "chembond add-on vs hand", "tb_op", "t_tb", "lf_lab", 26),
    A("chembond-add-on-vs-hand", "chembond", "add-on", "18%", "12%", "12.2%", "4 K", "harsh", "add-on -4%", 7, 1, "roll", "wipe", "22%", "add-on 4% extra", "geotext CBR vs perm", "cb_op", "ao_cb", "hd_cb", 25),
    A("geotext-cbr-vs-perm", "GTX", "CBR", "1800 N", "2400 N", "2360 N", "4 K", "puncture", "gsm +4%", 8, 1, "roll", "road", "1500 N", "gsm 4% extra", "geomem HDPE vs weld", "gt_op", "gs_gt", "cbr_lab", 24),
    A("geomem-hdpe-vs-weld", "HDPE GM", "weld", "fail", "pass", "pass", "5 K", "peel", "T +4%", 7, 1, "panel", "landfill", "fail", "T 4% extra", "geogrid tensile vs creep", "gm_op", "t_gm", "wd_gm", 23),
    A("geogrid-tensile-vs-creep", "geogrid", "creep", "18%", "8%", "8.2%", "4 K", "creep", "orient +4%", 8, 1, "roll", "wall", "24%", "orient 4% extra", "geonet transmiss vs clog", "gg_op", "or_gg", "cr_gg", 22),
    A("geonet-transmiss-vs-clog", "geonet", "trans", "0.42", "0.80", "0.78", "3 K", "clog", "gap +4%", 7, 1, "roll", "leachate", "0.30", "gap 4% extra", "GCL swell vs perm", "gn_op", "gp_gn", "tr_lab", 21),
    A("gcl-swell-vs-perm", "GCL", "k", "1.8e-9", "5e-10", "5.2e-10", "4 K", "perm", "swell +4%", 8, 1, "roll", "pond", "3e-9", "hydrate 4% extra", "EPDM roof vs seam2", "gcl_op", "sw_gcl", "k_lab", 20),
    A("epdm-roof-vs-seam2", "EPDM roof", "seam", "fail", "pass", "pass", "4 K", "peel", "tape +4%", 7, 1, "sheet", "ballast", "fail", "tape 4% extra", "TPO roof vs weld", "er_op", "tp_er", "sm_er", 19),
    A("tpo-roof-vs-weld", "TPO roof", "weld", "fail", "pass", "pass", "5 K", "peel", "T +4%", 7, 1, "sheet", "mechan", "fail", "T 4% extra", "PVC roof vs plasticizer", "tpo_op", "t_tpo", "wd_tpo", 18),
    A("pvc-roof-vs-plasticizer", "PVC roof", "migr", "18%", "8%", "8.2%", "5 K", "brittle", "stab +4%", 8, 1, "sheet", "adhered", "24%", "stab 4% extra", "builtup asphalt vs void", "pvc_op", "st_pvc", "mg_lab", 17),
    A("builtup-asphalt-vs-void", "BUR", "void", "8.4%", "3.0%", "3.1%", "6 K", "blister", "mop +4%", 8, 1, "ply", "hot", "11%", "mop 4% extra", "modbit selvedge vs torch", "bur_op", "mp_bur", "vd_bur", 16),
    A("modbit-selvedge-vs-torch", "modbit", "selvedge", "fail", "flow", "flow", "5 K", "cold", "torch +4%", 7, 1, "roll", "APP", "fail", "torch 4% extra", "shingle granule vs loss", "mb_op", "tc_mb", "sv_lab", 15),
    A("shingle-granule-vs-loss", "shingle", "loss", "1.8 g", "0.5 g", "0.52 g", "4 K", "loss", "press +4%", 7, 1, "line", "arch", "2.4 g", "press 4% extra", "metal roof vs clip", "sg_op", "pr_sg", "ls_sg", 14),
    A("metal-roof-vs-clip", "standing-seam", "clip", "fail", "pass", "pass", "3 K", "oil-can", "clip +4%", 6, 1, "panel", "SS", "fail", "clip 4% extra", "biax next densify", "mr_op", "cl_mr", "cl_lab", 13),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4001, s)
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
