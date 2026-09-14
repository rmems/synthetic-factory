#!/usr/bin/env python3
"""MAC mill r4371+. Unique chromatography detector plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205y", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("hplc-cad-vs-nse", "CAD", "N", "1.8%", "0.5%", "0.52%", "2 K", "N", "N2 +4%", 6, 1, "CAD", "lipid", "2.4%", "N2 4% extra", "ELSD vs gain", "cd_op", "n2_cd", "n_lab", 24),
    A("hplc-elsd-vs-gain", "ELSD", "gain", "18%", "6%", "6.2%", "2 K", "gain", "T +4%", 6, 1, "ELSD", "sugar", "24%", "T 4% extra", "RI vs drift", "el_op", "t_el", "gn_el", 23),
    A("hplc-ri-vs-drift", "RI", "drift", "18 nRIU", "4 nRIU", "4.2 nRIU", "2 K", "drift", "T +4%", 6, 1, "RI", "SEC", "24 nRIU", "T 4% extra", "FL vs gain", "ri_op", "t_ri", "dr_ri", 22),
    A("hplc-fl-vs-gain", "FL", "S/N", "82", "200", "196", "1 K", "S/N", "gain +4%", 6, 1, "FL", "PAH", "60", "gain 4% extra", "GC-FID vs split", "fl_op", "gn_fl", "sn_lab", 21),
    A("gc-fid-vs-split", "FID", "lin", "8.4%", "2.0%", "2.1%", "2 K", "lin", "H2 +4%", 6, 1, "FID", "VOC", "11%", "H2 4% extra", "GC-ECD vs make", "fd_op", "h2_fd", "ln_fd", 20),
    A("gc-ecd-vs-make", "ECD", "bg", "18 Hz", "4 Hz", "4.2 Hz", "2 K", "bg", "N2 +4%", 6, 1, "ECD", "PCB", "24 Hz", "N2 4% extra", "GC-NPD vs bead", "ec_op", "n2_ec", "bg_ec", 19),
    A("gc-npd-vs-bead", "NPD", "bead", "fail", "pass", "pass", "2 K", "bead", "H2 +4%", 6, 1, "NPD", "N", "fail", "H2 4% extra", "GC-TCD vs current", "np_op", "h2_np", "bd_lab", 18),
    A("gc-tcd-vs-current", "TCD", "current", "fail", "pass", "pass", "2 K", "current", "He +4%", 6, 1, "TCD", "perm", "fail", "He 4% extra", "IC-CD vs suppress", "tc_op", "he_tc", "cu_lab", 17),
    A("ic-cd-vs-suppress", "IC-CD", "BG", "1.8 µS", "0.4 µS", "0.42 µS", "2 K", "BG", "regen +4%", 6, 1, "CD", "anion", "2.4 µS", "regen 4% extra", "IC-UV vs blank", "ic_op", "rg_ic", "bg_ic", 16),
    A("ic-uv-vs-blank", "IC-UV", "blank", "0.018 A", "0.002 A", "0.0021 A", "1 K", "blank", "cuvette +4%", 5, 1, "UV", "NO3", "0.024 A", "cuvette 4% extra", "CE-UV vs EOF", "iu_op", "cv_iu", "bl_iu", 15),
    A("ce-uv-vs-eof", "CE-UV", "EOF", "fail", "stable", "stable", "2 K", "EOF", "pH +4%", 6, 1, "cap", "CZE", "fail", "pH 4% extra", "CE-LIF vs gain", "cu_op", "ph_cu", "eof_cu", 14),
    A("ce-lif-vs-gain", "CE-LIF", "S/N", "82", "200", "196", "1 K", "S/N", "gain +4%", 6, 1, "LIF", "AA", "60", "gain 4% extra", "LC-MS ESI vs spray", "lf_op", "gn_lf", "sn_lf", 13),
    A("lcms-esi-vs-spray", "ESI", "spray", "fail", "stable", "stable", "2 K", "spray", "cap +4%", 6, 1, "ESI", "peptide", "fail", "cap 4% extra", "LC-MS APCI vs corona", "es_op", "cp_es", "sp_es", 12),
    A("lcms-apci-vs-corona", "APCI", "corona", "fail", "stable", "stable", "2 K", "corona", "µA +4%", 6, 1, "APCI", "steroid", "fail", "µA 4% extra", "GC-MS EI vs tune", "ap_op", "ua_ap", "cr_lab", 11),
    A("gcms-ei-vs-tune", "EI", "tune", "fail", "pass", "pass", "2 K", "tune", "lens +4%", 6, 1, "quad", "SVOC", "fail", "lens 4% extra", "GC-MS CI vs methane", "ei_op", "ln_ei", "tn_ei", 10),
    A("gcms-ci-vs-methane", "CI", "CH4", "fail", "pass", "pass", "2 K", "CI", "CH4 +4%", 6, 1, "ion", "PCI", "fail", "CH4 4% extra", "MALDI vs matrix", "ci_op", "ch_ci", "ci_lab", 9),
    A("maldi-vs-matrix", "MALDI", "spot", "fail", "pass", "pass", "2 K", "spot", "CHCA +4%", 6, 1, "plate", "peptide", "fail", "CHCA 4% extra", "ESI-FTICR vs res", "ma_op", "ch_ma", "sp_ma", 8),
    A("esi-fticr-vs-res", "FTICR", "R", "180k", "400k", "392k", "2 K", "R", "T +4%", 6, 1, "cell", "7T", "140k", "T 4% extra", "Orbitrap vs AGC", "ft_op", "t_ft", "r_ft", 7),
    A("orbitrap-vs-agc", "Orbitrap", "AGC", "fail", "pass", "pass", "2 K", "AGC", "target +4%", 6, 1, "QEx", "HRMS", "fail", "target 4% extra", "QTOF vs lock", "or_op", "tg_or", "agc_lab", 6),
    A("qtof-vs-lock", "QTOF", "lock", "fail", "pass", "pass", "2 K", "lock", "leu +4%", 6, 1, "QTOF", "HRMS", "fail", "leu 4% extra", "CAD next densify", "qt_op", "le_qt", "lk_lab", 5),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4371, s)
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
