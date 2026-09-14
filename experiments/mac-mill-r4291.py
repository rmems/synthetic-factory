#!/usr/bin/env python3
"""MAC mill r4291+. Unique biologics QC plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205u", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("sec-malls-vs-mw", "SEC-MALS", "Mw", "18%", "6%", "6.2%", "2 K", "Mw", "dn/dc +4%", 6, 1, "column", "mAb", "24%", "dn/dc 4% extra", "AUC vs s", "sec_op", "dn_sec", "mw_lab", 32),
    A("auc-vs-s", "AUC", "s", "1.8 S", "0.4 S", "0.42 S", "2 K", "s", "align +4%", 6, 1, "cell", "SV", "2.4 S", "align 4% extra", "FFF vs d", "au_op", "al_au", "s_lab", 31),
    A("fff-vs-d", "AF4", "d", "18%", "6%", "6.2%", "2 K", "d", "cross +4%", 6, 1, "channel", "mAb", "24%", "cross 4% extra", "CE-SDS vs purity", "ff_op", "cr_ff", "d_lab", 30),
    A("ce-sds-vs-purity", "CE-SDS", "purity", "92.4%", "98.0%", "97.8%", "2 K", "purity", "load +4%", 6, 1, "cap", "rCE", "88%", "load 4% extra", "icIEF vs pI", "ce_op", "ld_ce", "pu_lab", 29),
    A("icief-vs-pi", "icIEF", "pI", "0.18", "0.04", "0.042", "2 K", "pI", "amph +4%", 6, 1, "cap", "cIEF", "0.24", "amph 4% extra", "HPLC peptide vs Rs", "ic_op", "am_ic", "pi_lab", 28),
    A("hplc-peptide-vs-rs", "RP-HPLC", "Rs", "1.18", "1.80", "1.78", "2 K", "Rs", "grad +4%", 6, 1, "C18", "tryptic", "0.90", "grad 4% extra", "glycan vs G0", "hp_op", "gd_hp", "rs_lab", 27),
    A("glycan-vs-g0", "HILIC", "G0", "18%", "8%", "8.2%", "2 K", "G0", "PNGase +4%", 6, 1, "column", "N-glycan", "24%", "PNGase 4% extra", "intact MS vs mass", "gl_op", "pn_gl", "g0_lab", 26),
    A("intact-ms-vs-mass", "intact", "Δm", "18 Da", "4 Da", "4.2 Da", "2 K", "Δm", "decon +4%", 6, 1, "QTOF", "mAb", "24 Da", "decon 4% extra", "peptide map vs cover", "in_op", "dc_in", "dm_lab", 25),
    A("peptide-map-vs-cover", "map", "cover", "82%", "95%", "94.6%", "2 K", "cover", "digest +4%", 6, 1, "LC-MS", "tryptic", "74%", "digest 4% extra", "HCP ELISA vs ng", "pm_op", "dg_pm", "cv_lab", 24),
    A("hcp-elisa-vs-ng", "HCP", "ng/mg", "18", "4", "4.2", "2 K", "HCP", "kit +4%", 6, 1, "plate", "CHO", "24", "kit 4% extra", "DNA qPCR vs pg", "hc_op", "kt_hc", "ng_lab", 23),
    A("dna-qpcr-vs-pg", "qPCR", "pg/mg", "18", "4", "4.2", "2 K", "DNA", "extract +4%", 6, 1, "plate", "resDNA", "24", "extract 4% extra", "endotoxin LAL vs EU", "dn_op", "ex_dn", "pg_lab", 22),
    A("endotoxin-lal-vs-eu", "LAL", "EU/mg", "0.18", "0.04", "0.042", "1 K", "EU", "spike +4%", 5, 1, "plate", "kinetic", "0.24", "spike 4% extra", "bioburden vs CFU", "en_op", "sp_en", "eu_lab", 21),
    A("bioburden-vs-cfu", "bioburden", "CFU", "18", "4", "4.2", "2 K", "CFU", "method +4%", 6, 1, "plate", "TAMC", "24", "method 4% extra", "sterility vs growth", "bb_op", "md_bb", "cfu_bb", 20),
    A("sterility-vs-growth", "sterility", "growth", "fail", "pass", "pass", "2 K", "growth", "media +4%", 7, 1, "vial", "14d", "fail", "media 4% extra", "mycoplasma vs PCR", "st_op", "md_st", "gr_st", 19),
    A("mycoplasma-vs-pcr", "myco", "Ct", "38.4", "28.0", "28.2", "2 K", "Ct", "extract +4%", 6, 1, "plate", "qPCR", "40.0", "extract 4% extra", "adventitious vs ind", "my_op", "ex_my", "ct_my", 18),
    A("adventitious-vs-ind", "ADV", "ind", "fail", "pass", "pass", "3 K", "CPE", "indicator +4%", 8, 1, "flask", "in vitro", "fail", "indicator 4% extra", "potency vs rel", "ad_op", "id_ad", "ind_lab", 17),
    A("potency-vs-rel", "potency", "rel", "82%", "100%", "98%", "2 K", "rel", "curve +4%", 6, 1, "plate", "bioassay", "74%", "curve 4% extra", "binding ELISA vs EC50", "po_op", "cv_po", "rel_lab", 16),
    A("binding-elisa-vs-ec50", "ELISA", "EC50", "18%", "6%", "6.2%", "2 K", "EC50", "coat +4%", 6, 1, "plate", "bind", "24%", "coat 4% extra", "cell based vs rel", "el_op", "ct_el", "ec_lab", 15),
    A("cell-based-vs-rel", "cell", "rel", "82%", "100%", "98%", "2 K", "rel", "seed +4%", 6, 1, "plate", "NFκB", "74%", "seed 4% extra", "ADCC vs EC50", "cb_op", "sd_cb", "rel_cb", 14),
    A("adcc-vs-ec50", "ADCC", "EC50", "18%", "6%", "6.2%", "2 K", "EC50", "E:T +4%", 6, 1, "plate", "PBMC", "24%", "E:T 4% extra", "SEC next densify", "ad_op", "et_ad", "ec_ad", 13),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4291, s)
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
