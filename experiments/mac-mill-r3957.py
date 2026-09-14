#!/usr/bin/env python3
"""MAC mill r3957+. Unique ink/adhesive/elastomer plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205k", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("ink-jet-vs-viscosity", "inkjet", "visc", "8.4 cP", "4.0 cP", "4.1 cP", "3 K", "satellite", "dilute +4%", 6, 1, "tank", "head", "11 cP", "dilute 4% extra", "offset tack vs mist", "ij_op", "dl_ij", "vs_ij", 54),
    A("offset-tack-vs-mist", "offset", "tack", "18", "12", "12.2", "4 K", "mist", "oil +4%", 7, 1, "fountain", "sheet", "22", "oil 4% extra", "flexo anilox vs volume", "of_op", "ol_of", "tk_lab", 53),
    A("flexo-anilox-vs-volume", "flexo", "BCM", "4.8", "6.5", "6.4", "3 K", "starved", "anilox +4%", 6, 1, "press", "label", "3.6", "anilox 4% extra", "gravure cell vs depth", "fx_op", "an_fx", "bcm_lab", 52),
    A("gravure-cell-vs-depth", "gravure", "depth", "28 µm", "40 µm", "39 µm", "4 K", "starved", "engrave +4%", 7, 1, "cyl", "pack", "22 µm", "engrave 4% extra", "screen mesh vs deposit", "gv_op", "en_gv", "dp_gv", 51),
    A("screen-mesh-vs-deposit", "screen", "deposit", "18 µm", "28 µm", "27.6 µm", "3 K", "thin", "mesh +4%", 6, 1, "frame", "PCB", "14 µm", "mesh 4% extra", "toner charge vs fuser", "sc_op", "ms_sc", "dp_sc", 50),
    A("toner-charge-vs-fuser", "toner", "q/m", "18 µC/g", "28 µC/g", "27.6 µC/g", "4 K", "background", "fuser +4%", 6, 1, "hopper", "laser", "14 µC/g", "fuser 4% extra", "UV ink vs dose", "tn_op", "fs_tn", "qm_lab", 49),
    A("uv-ink-vs-dose", "UV ink", "dose", "180 mJ", "280 mJ", "276 mJ", "3 K", "tack", "lamp +4%", 6, 1, "press", "label", "140 mJ", "lamp 4% extra", "EB ink vs dose", "uv_op", "lp_uv", "ds_uv", 48),
    A("eb-ink-vs-dose", "EB ink", "kGy", "18", "30", "29.6", "2 K", "uncure", "dose +4%", 6, 1, "line", "web", "14", "dose 4% extra", "adhesive peel vs open", "eb_op", "ds_eb", "kgy_lab", 47),
    A("adhesive-peel-vs-open", "adhesive", "peel", "8.4 N", "14 N", "13.8 N", "4 K", "open", "open +4%", 7, 1, "line", "laminate", "6 N", "open 4% extra", "hotmelt SAFT vs visc", "ad_op", "op_ad", "pl_ad", 46),
    A("hotmelt-saft-vs-visc", "HM", "SAFT", "62 C", "80 C", "79 C", "5 K", "creep", "resin +4%", 8, 1, "tank", "carton", "54 C", "resin 4% extra", "PSA loop vs tack", "hm_op", "rs_hm", "saft_lab", 45),
    A("psa-loop-vs-tack", "PSA", "loop", "8.4 N", "14 N", "13.8 N", "3 K", "dry", "tack +4%", 6, 1, "coat", "label", "6 N", "oil 4% extra", "epoxy lap vs mix", "psa_op", "tk_psa", "lp_psa", 44),
    A("epoxy-lap-vs-mix", "epoxy", "lap", "12 MPa", "18 MPa", "17.8 MPa", "4 K", "starve", "mix +4%", 7, 1, "bead", "metal", "9 MPa", "mix 4% extra", "cyano set vs moisture", "ep_op", "mx_ep", "lp_ep", 43),
    A("cyano-set-vs-moisture", "CA", "set", "18 s", "8 s", "8.2 s", "2 K", "slow", "RH +4%", 5, 1, "line", "fixture", "28 s", "RH 4% extra", "PU adhesive vs NCO", "ca_op", "rh_ca", "st_ca", 42),
    A("pu-adhesive-vs-nco", "PU", "NCO", "2.05%", "2.40%", "2.38%", "4 K", "cure", "NCO +4%", 7, 1, "drum", "panel", "1.80%", "iso 4% extra", "silicone adhesive vs peel", "pu_op", "nco_pu", "nco_lab", 41),
    A("silicone-adhesive-vs-peel", "Si PSA", "peel", "8.4 N", "14 N", "13.8 N", "4 K", "dry", "MQ +4%", 7, 1, "coat", "tape", "6 N", "MQ 4% extra", "acrylic PSA vs shear", "si_op", "mq_si", "pl_si", 40),
    A("acrylic-psa-vs-shear", "acrylic PSA", "shear", "18 h", "48 h", "46 h", "4 K", "creep", "crosslink +4%", 8, 1, "coat", "tape", "12 h", "XL 4% extra", "coating DFT vs orange2", "ac_op", "xl_ac", "sh_ac", 39),
    A("coating-dft-vs-orange2", "coat", "DFT", "42 µm", "60 µm", "59 µm", "4 K", "orange", "flow +4%", 7, 1, "line", "coil", "32 µm", "flow 4% extra", "varnish gloss vs DOI", "ct_op", "fl_ct", "dft_ct", 38),
    A("varnish-gloss-vs-doi", "varnish", "DOI", "62", "85", "84", "3 K", "orange", "flow +4%", 6, 1, "line", "auto", "50", "flow 4% extra", "laminate bond vs corona", "vr_op", "fl_vr", "doi_lab", 37),
    A("laminate-bond-vs-corona", "laminate", "bond", "1.8 N", "3.5 N", "3.45 N", "3 K", "peel", "corona +4%", 6, 1, "web", "pouch", "1.2 N", "dyne 4% extra", "foil peel vs adhesive", "lm_op", "cr_lm", "bd_lab", 36),
    A("foil-peel-vs-adhesive", "foil", "peel", "2.8 N", "5.0 N", "4.9 N", "4 K", "peel", "adhesive +4%", 7, 1, "web", "lid", "1.8 N", "coat 4% extra", "paper size vs Cobb", "fl_op", "ad_fl", "pl_fl", 35),
    A("paper-size-vs-cobb", "size", "Cobb", "42 g/m2", "22 g/m2", "22.4 g/m2", "4 K", "Cobb", "AKD +4%", 7, 1, "size-press", "offset", "55 g/m2", "AKD 4% extra", "board burst vs moisture", "sz_op", "akd_sz", "cb_lab", 34),
    A("board-burst-vs-moisture", "board", "burst", "180 kPa", "240 kPa", "236 kPa", "5 K", "soft", "dry +4%", 7, 1, "reel", "carton", "150 kPa", "dry 4% extra", "corrugate ECT vs glue", "bd_op", "dr_bd", "br_bd", 33),
    A("corrugate-ect-vs-glue", "corrugate", "ECT", "32 lb/in", "42 lb/in", "41.6 lb/in", "4 K", "crush", "glue +4%", 7, 1, "flute", "box", "26 lb/in", "glue 4% extra", "tissue wet vs temp", "cg_op", "gl_cg", "ect_lab", 32),
    A("tissue-wet-vs-temp", "tissue", "wet", "8.4 N", "14 N", "13.8 N", "4 K", "tear", "temp +4%", 6, 1, "reel", "towel", "6 N", "temp 4% extra", "rubber Mooney vs scorch", "ts_op", "tp_ts", "wt_ts", 31),
    A("rubber-mooney-vs-scorch", "compound", "t5", "8.4 min", "14 min", "13.8 min", "5 K", "scorch", "retarder +4%", 7, 1, "mill", "tire", "6 min", "retarder 4% extra", "NBR AN vs swell", "rb_op", "rt_rb", "t5_lab", 30),
    A("nbr-an-vs-swell", "NBR", "AN", "28%", "34%", "33.6%", "5 K", "swell", "AN +4%", 8, 1, "bale", "hose", "24%", "AN 4% extra", "SBR styrene vs Tg", "nbr_op", "an_nbr", "an_lab", 29),
    A("sbr-styrene-vs-tg", "SBR", "Tg", "-48 C", "-42 C", "-42.4 C", "5 K", "grip", "styrene +4%", 8, 1, "bale", "tread", "-54 C", "styrene 4% extra", "EPDM diene vs cure", "sbr_op", "st_sbr", "tg_sbr", 28),
    A("epdm-diene-vs-cure", "EPDM", "ENB", "4.2%", "6.0%", "5.9%", "5 K", "slow", "ENB +4%", 8, 1, "bale", "roof", "3.4%", "ENB 4% extra", "FKM fluorine vs swell", "ep_op", "enb_ep", "enb_lab", 27),
    A("fkm-fluorine-vs-swell", "FKM", "F", "64.8%", "66.5%", "66.4%", "6 K", "swell", "F +4%", 8, 1, "bale", "seal", "63.5%", "VDF 4% extra", "HNBR sat vs heat", "fkm_op", "f_fkm", "f_lab", 26),
    A("hnbr-sat-vs-heat", "HNBR", "sat", "91%", "96%", "95.6%", "6 K", "heat", "H2 +4%", 9, 1, "bale", "belt", "88%", "H2 4% extra", "CSM chlorine vs oil", "hn_op", "h2_hn", "sat_lab", 25),
    A("csm-chlorine-vs-oil", "CSM", "Cl", "28%", "35%", "34.6%", "5 K", "oil", "Cl +4%", 8, 1, "bale", "hose", "24%", "Cl 4% extra", "ACM acrylate vs heat", "csm_op", "cl_csm", "cl_csm_lab", 24),
    A("acm-acrylate-vs-heat", "ACM", "heat", "150 C", "175 C", "174 C", "6 K", "crack", "cure +4%", 8, 1, "bale", "gasket", "140 C", "cure 4% extra", "AEM ethylene vs heat", "acm_op", "cu_acm", "ht_acm", 23),
    A("aem-ethylene-vs-heat", "AEM", "heat", "150 C", "175 C", "174 C", "6 K", "crack", "cure +4%", 8, 1, "bale", "hose", "140 C", "cure 4% extra", "ECO epichlor vs fuel", "aem_op", "cu_aem", "ht_aem", 22),
    A("eco-epichlor-vs-fuel", "ECO", "fuel", "18%", "8%", "8.2%", "5 K", "swell", "ECH +4%", 8, 1, "bale", "fuel-hose", "24%", "ECH 4% extra", "IIR unsat vs barrier", "eco_op", "ech_eco", "fl_eco", 21),
    A("iir-unsat-vs-barrier", "IIR", "perm", "18", "8", "8.2", "5 K", "air", "unsat -4%", 8, 1, "bale", "inner", "24", "unsat 4% extra", "BIIR bromine vs cure", "iir_op", "un_iir", "pm_lab", 20),
    A("bii-bromine-vs-cure", "BIIR", "Br", "1.8%", "2.2%", "2.18%", "5 K", "slow", "Br +4%", 8, 1, "bale", "tire", "1.4%", "Br 4% extra", "CIIR chlorine vs cure", "bii_op", "br_bii", "br_lab", 19),
    A("cii-chlorine-vs-cure", "CIIR", "Cl", "1.05%", "1.25%", "1.24%", "5 K", "slow", "Cl +4%", 8, 1, "bale", "tire", "0.90%", "Cl 4% extra", "XNBR carboxyl vs tear", "cii_op", "cl_cii", "cl_cii_lab", 18),
    A("xnbr-carboxyl-vs-tear", "XNBR", "COOH", "4.2%", "6.0%", "5.9%", "5 K", "tear", "COOH +4%", 8, 1, "bale", "glove", "3.4%", "COOH 4% extra", "SBR oil vs ext", "xn_op", "co_xn", "co_lab", 17),
    A("sbr-oil-vs-ext", "oSBR", "oil", "28 phr", "37.5 phr", "37 phr", "4 K", "bloom", "oil +4%", 7, 1, "bale", "tread", "22 phr", "oil 4% extra", "BR cis vs rebound", "osbr_op", "ol_osbr", "ol_lab", 16),
    A("br-cis-vs-rebound", "BR", "rebound", "62%", "72%", "71.4%", "5 K", "hysteresis", "cis +4%", 8, 1, "bale", "tread", "55%", "cis 4% extra", "IR cis vs green", "br_op", "cis_br", "rb_br", 15),
    A("ir-cis-vs-green", "IR", "green", "18", "28", "27.6", "5 K", "weak", "cis +4%", 8, 1, "bale", "gasket", "14", "cis 4% extra", "NR PRI vs dirt", "ir_op", "cis_ir", "gr_ir", 14),
    A("nr-pri-vs-dirt", "NR", "PRI", "42", "60", "59", "4 K", "dirt", "clean +4%", 8, 1, "bale", "tire", "34", "clean 4% extra", "CR chloroprene vs crystal", "nr_op", "cl_nr", "pri_lab", 13),
    A("cr-chloroprene-vs-crystal", "CR", "crystal", "18 min", "8 min", "8.2 min", "4 K", "stiff", "sulfur +4%", 7, 1, "bale", "belt", "24 min", "sulfur 4% extra", "TPE hardness vs oil", "cr_op", "su_cr", "cr_lab", 12),
    A("tpe-hardness-vs-oil", "TPE", "Shore A", "52", "65", "64", "4 K", "soft", "oil-cut 4%", 7, 1, "lot", "grip", "46", "oil 4% extra", "ink next densify", "tpe_op", "ol_tpe", "sh_tpe", 11),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(3957, s)
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
