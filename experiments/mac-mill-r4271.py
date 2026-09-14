#!/usr/bin/env python3
"""MAC mill r4271+. Unique particle/surface/binding plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205t", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("bet-vs-area", "BET", "SA", "180 m2/g", "240 m2/g", "236 m2/g", "3 K", "SA", "degass +4%", 8, 1, "tube", "N2", "150 m2/g", "degass 4% extra", "BJH vs pore", "bt_op", "dg_bt", "sa_lab", 34),
    A("bjh-vs-pore", "BJH", "dp", "18 nm", "8 nm", "8.2 nm", "3 K", "pore", "N2 +4%", 7, 1, "tube", "meso", "24 nm", "N2 4% extra", "mercury vs intrusion", "bj_op", "n2_bj", "dp_lab", 33),
    A("mercury-vs-intrusion", "MIP", "intr", "fail", "pass", "pass", "4 K", "intr", "evac +4%", 7, 1, "penet", "macro", "fail", "evac 4% extra", "He pyc vs density", "hg_op", "ev_hg", "in_lab", 32),
    A("he-pyc-vs-density", "He pyc", "ρ", "0.018 g/cm3", "0.004 g/cm3", "0.0042 g/cm3", "2 K", "ρ", "purge +4%", 6, 1, "cell", "true", "0.024 g/cm3", "purge 4% extra", "PSD vs d50", "he_op", "pg_he", "rho_lab", 31),
    A("psd-vs-d50", "PSD", "d50", "18%", "6%", "6.2%", "2 K", "d50", "RI +4%", 6, 1, "cell", "laser", "24%", "RI 4% extra", "zeta vs pH", "ps_op", "ri_ps", "d50_ps", 30),
    A("zeta-vs-ph", "zeta", "ζ", "8.4 mV", "28 mV", "27.6 mV", "2 K", "ζ", "pH +4%", 6, 1, "cell", "ELS", "4 mV", "pH 4% extra", "DLS vs PDI", "zt_op", "ph_zt", "z_lab", 29),
    A("dls-vs-pdi", "DLS", "PDI", "0.42", "0.12", "0.12", "2 K", "PDI", "filter +4%", 6, 1, "cuvette", "nano", "0.55", "filter 4% extra", "SAXS vs dstar", "dl_op", "fl_dl", "pdi_lab", 28),
    A("saxs-vs-dstar", "SAXS", "d*", "18 nm", "8 nm", "8.2 nm", "2 K", "d*", "q +4%", 6, 1, "cap", "lamellar", "24 nm", "q 4% extra", "WAXS vs peak", "sx_op", "q_sx", "d_lab", 27),
    A("waxs-vs-peak", "WAXS", "FWHM", "0.42 °", "0.12 °", "0.12 °", "2 K", "FWHM", "align +4%", 6, 1, "cap", "crystal", "0.55 °", "align 4% extra", "GISAXS vs q", "wx_op", "al_wx", "fw_wx", 26),
    A("gisaxs-vs-q", "GISAXS", "q", "fail", "peak", "peak", "2 K", "q", "αi +4%", 6, 1, "film", "GISAXS", "fail", "αi 4% extra", "ellips vs n", "gs_op", "ai_gs", "q_gs", 25),
    A("ellips-vs-n", "ellips", "n", "0.018", "0.004", "0.0042", "1 K", "n", "model +4%", 6, 1, "film", "SiO2", "0.024", "model 4% extra", "profil vs Ra", "el_op", "md_el", "n_lab", 24),
    A("profil-vs-ra", "profil", "Ra", "18 nm", "4 nm", "4.2 nm", "1 K", "Ra", "scan +4%", 5, 1, "stage", "2D", "24 nm", "scan 4% extra", "nanoindent vs H", "pf_op", "sc_pf", "ra_lab", 23),
    A("nanoindent-vs-h", "indent", "H", "18%", "6%", "6.2%", "2 K", "H", "area +4%", 6, 1, "tip", "Berkovich", "24%", "area 4% extra", "AFM force vs adh", "ni_op", "ar_ni", "h_lab", 22),
    A("afm-force-vs-adh", "AFM", "Fadh", "18 nN", "6 nN", "6.2 nN", "1 K", "adh", "k +4%", 6, 1, "tip", "SiN", "24 nN", "k 4% extra", "QCM vs mass", "af_op", "k_af", "f_lab", 21),
    A("qcm-vs-mass", "QCM", "Δm", "18 ng", "4 ng", "4.2 ng", "1 K", "Δm", "Sauerbrey +4%", 6, 1, "crystal", "Au", "24 ng", "Sauerbrey 4% extra", "SPR vs RU", "qc_op", "sb_qc", "dm_lab", 20),
    A("spr-vs-ru", "SPR", "RU", "18 RU", "4 RU", "4.2 RU", "1 K", "RU", "ref +4%", 6, 1, "chip", "CM5", "24 RU", "ref 4% extra", "ITC vs Kd", "sp_op", "rf_sp", "ru_lab", 19),
    A("itc-vs-kd", "ITC", "Kd", "18%", "6%", "6.2%", "2 K", "Kd", "c +4%", 6, 1, "cell", "VP", "24%", "c 4% extra", "DSC bind vs Tm", "it_op", "c_it", "kd_lab", 18),
    A("dsc-bind-vs-tm", "nanoDSC", "Tm", "1.8 K", "0.4 K", "0.42 K", "2 K", "Tm", "scan -4%", 6, 1, "cell", "protein", "2.4 K", "scan 4% extra", "BLI vs Kd", "nb_op", "sc_nb", "tm_nb", 17),
    A("blitz-vs-kd", "BLI", "Kd", "18%", "6%", "6.2%", "1 K", "Kd", "load +4%", 6, 1, "tip", "SA", "24%", "load 4% extra", "MST vs Kd", "bl_op", "ld_bl", "kd_bl", 16),
    A("mst-vs-kd", "MST", "Kd", "18%", "6%", "6.2%", "1 K", "Kd", "LED +4%", 6, 1, "cap", "NT", "24%", "LED 4% extra", "BET next densify", "mt_op", "ld_mt", "kd_mt", 15),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4271, s)
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
