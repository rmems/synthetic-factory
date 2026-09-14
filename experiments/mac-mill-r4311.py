#!/usr/bin/env python3
"""MAC mill r4311+. Unique biologics characterization plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205v", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("hplc-sec-vs-hmw", "SEC", "HMW", "1.8%", "0.5%", "0.52%", "2 K", "HMW", "load -4%", 6, 1, "column", "mAb", "2.4%", "load 4% extra", "CGE vs purity", "hs_op", "ld_hs", "hmw_lab", 30),
    A("cge-vs-purity", "CGE", "purity", "92.4%", "98.0%", "97.8%", "2 K", "purity", "inject +4%", 6, 1, "cap", "rCGE", "88%", "inject 4% extra", "IEF vs bands", "cg_op", "in_cg", "pu_cg", 29),
    A("ief-vs-bands", "IEF", "bands", "8", "4", "4.2", "2 K", "bands", "amph +4%", 6, 1, "gel", "cIEF", "12", "amph 4% extra", "SDS-PAGE vs load", "ie_op", "am_ie", "bd_lab", 28),
    A("sds-page-vs-load", "PAGE", "load", "18 µg", "8 µg", "8.2 µg", "2 K", "smear", "load -4%", 5, 1, "gel", "Coomassie", "24 µg", "load 4% extra", "western vs band", "sd_op", "ld_sd", "ld_sd_lab", 27),
    A("western-vs-band", "WB", "band", "fail", "pass", "pass", "2 K", "bg", "block +4%", 6, 1, "blot", "Ab", "fail", "block 4% extra", "ELISA vs CV", "wb_op", "bl_wb", "bd_wb", 26),
    A("elisa-vs-cv", "ELISA", "CV", "18%", "6%", "6.2%", "1 K", "CV", "wash +4%", 6, 1, "plate", "sandwich", "24%", "wash 4% extra", "Octet vs Kd", "el_op", "ws_el", "cv_el", 25),
    A("octet-vs-kd", "Octet", "Kd", "18%", "6%", "6.2%", "1 K", "Kd", "load +4%", 6, 1, "tip", "SA", "24%", "load 4% extra", "Biacore vs Kd", "oc_op", "ld_oc", "kd_oc", 24),
    A("biacore-vs-kd", "Biacore", "Kd", "18%", "6%", "6.2%", "1 K", "Kd", "Rmax +4%", 6, 1, "chip", "CM5", "24%", "Rmax 4% extra", "FACS vs CV", "bi_op", "rm_bi", "kd_bi", 23),
    A("facs-vs-cv", "FACS", "CV", "18%", "6%", "6.2%", "1 K", "CV", "volt +4%", 6, 1, "tube", "CD", "24%", "volt 4% extra", "ELISA ADA vs cut", "fa_op", "vl_fa", "cv_fa", 22),
    A("elisa-ada-vs-cut", "ADA", "cut", "fail", "pass", "pass", "2 K", "cut", "NC +4%", 6, 1, "plate", "bridging", "fail", "NC 4% extra", "NAb vs titer", "ad_op", "nc_ad", "ct_ad", 21),
    A("nab-vs-titer", "NAb", "titer", "18", "4", "4.2", "2 K", "titer", "dilute +4%", 6, 1, "plate", "cell", "24", "dilute 4% extra", "PK vs LLOQ", "nb_op", "dl_nb", "tt_lab", 20),
    A("pk-vs-lloq", "PK", "LLOQ", "18 ng/mL", "4 ng/mL", "4.2 ng/mL", "2 K", "LLOQ", "IS +4%", 6, 1, "LC-MS", "serum", "24 ng/mL", "IS 4% extra", "HPLC HCP vs ng", "pk_op", "is_pk", "ll_lab", 19),
    A("hplc-hcp-vs-ng", "HCP-HPLC", "ng/mg", "18", "4", "4.2", "2 K", "HCP", "grad +4%", 6, 1, "C4", "2D", "24", "grad 4% extra", "LC-MS HCP vs ppm", "hh_op", "gd_hh", "ng_hh", 18),
    A("lcms-hcp-vs-ppm", "HCP-MS", "ppm", "18", "4", "4.2", "2 K", "HCP", "DIA +4%", 6, 1, "orbitrap", "CHO", "24", "DIA 4% extra", "peptide MS vs ID", "lh_op", "dia_lh", "ppm_lab", 17),
    A("peptide-ms-vs-id", "MS/MS", "ID", "82%", "95%", "94.6%", "2 K", "ID", "NCE +4%", 6, 1, "orbitrap", "DDA", "74%", "NCE 4% extra", "intact decon vs species", "ps_op", "nce_ps", "id_lab", 16),
    A("intact-decon-vs-species", "decon", "species", "8", "3", "3.1", "2 K", "species", "res +4%", 6, 1, "QTOF", "intact", "12", "res 4% extra", "disulfide vs map", "id_op", "rs_id", "sp_lab", 15),
    A("disulfide-vs-map", "S-S", "map", "fail", "match", "match", "2 K", "map", "nonred +4%", 6, 1, "LC-MS", "mAb", "fail", "nonred 4% extra", "free thiol vs Ellman", "ss_op", "nr_ss", "mp_ss", 14),
    A("free-thiol-vs-ellman", "thiol", "µM", "18", "4", "4.2", "1 K", "thiol", "DTNB +4%", 5, 1, "cuvette", "Ellman", "24", "DTNB 4% extra", "sialic vs HPAEC", "ft_op", "dt_ft", "um_lab", 13),
    A("sialic-vs-hpaec", "HPAEC", "Neu5Ac", "18%", "8%", "8.2%", "2 K", "sialic", "PAD +4%", 6, 1, "column", "CarboPac", "24%", "PAD 4% extra", "mannose vs HILIC", "si_op", "pad_si", "neu_lab", 12),
    A("mannose-vs-hilic", "HILIC", "Man5", "18%", "6%", "6.2%", "2 K", "Man5", "2AB +4%", 6, 1, "column", "BEH", "24%", "2AB 4% extra", "SEC next densify", "mn_op", "ab_mn", "man_lab", 11),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4311, s)
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
