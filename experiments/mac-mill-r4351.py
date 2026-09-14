#!/usr/bin/env python3
"""MAC mill r4351+. Unique particle/fill-finish plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205x", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("hplc-upa-vs-hmw", "UPLC-SEC", "HMW", "1.8%", "0.5%", "0.52%", "2 K", "HMW", "load -4%", 6, 1, "BEH", "mAb", "2.4%", "load 4% extra", "MFI vs count", "up_op", "ld_up", "hmw_up", 26),
    A("mfi-vs-count", "MFI", "≥10µm", "180 /mL", "40 /mL", "42 /mL", "1 K", "count", "dilute +4%", 6, 1, "cuvette", "USP788", "240 /mL", "dilute 4% extra", "LO vs count", "mf_op", "dl_mf", "ct_mf", 25),
    A("lo-vs-count", "LO", "≥10µm", "180 /mL", "40 /mL", "42 /mL", "1 K", "count", "dilute +4%", 6, 1, "HIAC", "USP788", "240 /mL", "dilute 4% extra", "DLS vs PDI2", "lo_op", "dl_lo", "ct_lo", 24),
    A("dls-vs-pdi2", "DLS", "PDI", "0.42", "0.12", "0.12", "1 K", "PDI", "filter +4%", 6, 1, "cuvette", "mAb", "0.55", "filter 4% extra", "NTA vs count", "dl_op", "fl_dl", "pdi_dl", 23),
    A("ntau-vs-count", "NTA", "N", "1.8e8 /mL", "4e7 /mL", "4.2e7 /mL", "1 K", "N", "dilute +4%", 6, 1, "cell", "NS300", "2.4e8 /mL", "dilute 4% extra", "Archi vs count", "nt_op", "dl_nt", "n_lab", 22),
    A("archi-vs-count", "Archimedes", "N", "1.8e6 /mL", "4e5 /mL", "4.2e5 /mL", "1 K", "N", "dilute +4%", 6, 1, "sensor", "RMM", "2.4e6 /mL", "dilute 4% extra", "FlowCam vs count", "ar_op", "dl_ar", "n_ar", 21),
    A("flowcam-vs-count", "FlowCam", "N", "180 /mL", "40 /mL", "42 /mL", "1 K", "N", "dilute +4%", 6, 1, "flow", "image", "240 /mL", "dilute 4% extra", "HIAC vs count", "fc_op", "dl_fc", "n_fc", 20),
    A("hiac-vs-count", "HIAC", "≥25µm", "18 /mL", "2 /mL", "2.2 /mL", "1 K", "count", "dilute +4%", 6, 1, "HIAC", "USP788", "24 /mL", "dilute 4% extra", "K visc vs shear", "hi_op", "dl_hi", "ct_hi", 19),
    A("k-visc-vs-shear", "visc", "η", "18 cP", "8 cP", "8.2 cP", "2 K", "η", "shear +4%", 6, 1, "cone", "mAb", "24 cP", "shear 4% extra", "osc vs Gstar", "kv_op", "sh_kv", "eta_lab", 18),
    A("osc-vs-gstar", "osc", "G*", "18%", "6%", "6.2%", "2 K", "G*", "strain -4%", 6, 1, "plate", "gel", "24%", "strain 4% extra", "creep vs J", "os_op", "st_os", "g_lab", 17),
    A("creep-vs-j", "creep", "J", "18%", "6%", "6.2%", "2 K", "J", "stress -4%", 6, 1, "plate", "gel", "24%", "stress 4% extra", "thix vs rec", "cr_op", "st_cr", "j_lab", 16),
    A("thix-vs-rec", "thix", "rec", "42%", "80%", "79%", "2 K", "rec", "rest +4%", 6, 1, "plate", "gel", "32%", "rest 4% extra", "syringe vs glide", "th_op", "rs_th", "rc_lab", 15),
    A("syringe-vs-glide", "PFS", "glide", "18 N", "8 N", "8.2 N", "1 K", "glide", "silicon +4%", 6, 1, "1mL", "PFS", "24 N", "silicon 4% extra", "vial vs CCIT", "sy_op", "si_sy", "gl_lab", 14),
    A("vial-vs-ccit", "CCIT", "leak", "fail", "pass", "pass", "1 K", "leak", "HVLD +4%", 6, 1, "vial", "2R", "fail", "HVLD 4% extra", "stopper vs coring", "vi_op", "hv_vi", "lk_lab", 13),
    A("stopper-vs-coring", "stopper", "core", "18 /100", "2 /100", "2.2 /100", "1 K", "core", "bevel +4%", 6, 1, "20mm", "W4023", "24 /100", "bevel 4% extra", "needle vs force", "st_op", "bv_st", "cr_st", 12),
    A("needle-vs-force", "needle", "F", "18 N", "8 N", "8.2 N", "1 K", "F", "silicon +4%", 5, 1, "27G", "PFS", "24 N", "silicon 4% extra", "lyo vs cake2", "nd_op", "si_nd", "f_lab", 11),
    A("lyo-vs-cake2", "lyo", "cake", "fail", "elegant", "elegant", "3 K", "collapse", "shelf -4%", 8, 1, "vial", "2R", "fail", "shelf 4% extra", "fill vs volume", "ly_op", "sh_ly", "ck_lab", 10),
    A("fill-vs-volume", "fill", "vol", "1.8%", "0.5%", "0.52%", "1 K", "vol", "tare +4%", 6, 1, "line", "1mL", "2.4%", "tare 4% extra", "crimp vs seal", "fi_op", "tr_fi", "vl_lab", 9),
    A("crimp-vs-seal", "crimp", "seal", "fail", "pass", "pass", "1 K", "seal", "force +4%", 5, 1, "capping", "13mm", "fail", "force 4% extra", "label vs adh", "cr_op", "fc_cr", "sl_cr", 8),
    A("label-vs-adh", "label", "peel", "fail", "pass", "pass", "1 K", "peel", "dwell +4%", 5, 1, "vial", "PSA", "fail", "dwell 4% extra", "UPLC next densify", "lb_op", "dw_lb", "pl_lb", 7),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4351, s)
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
