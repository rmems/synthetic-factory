#!/usr/bin/env python3
"""MAC mill r4247+. Unique chromatography/spectroscopy plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205s", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("hplc-rsd-vs-pump", "HPLC", "RSD", "1.8%", "0.4%", "0.42%", "2 K", "RSD", "seal +4%", 6, 1, "pump", "assay", "2.4%", "seal 4% extra", "GC split vs lin", "hp_op", "sl_hp", "rsd_hp", 36),
    A("gc-split-vs-lin", "GC", "lin", "8.4%", "2.0%", "2.1%", "2 K", "lin", "split +4%", 6, 1, "inlet", "VOC", "11%", "split 4% extra", "IC suppress vs BG", "gc_op", "sp_gc", "ln_gc", 35),
    A("ic-suppress-vs-bg", "IC", "BG", "1.8 µS", "0.4 µS", "0.42 µS", "2 K", "BG", "regen +4%", 6, 1, "suppressor", "anion", "2.4 µS", "regen 4% extra", "CE EOF vs buffer", "ic_op", "rg_ic", "bg_ic", 34),
    A("ce-eof-vs-buffer", "CE", "EOF", "fail", "stable", "stable", "2 K", "EOF", "pH +4%", 6, 1, "capillary", "CZE", "fail", "pH 4% extra", "TLC Rf vs sat", "ce_op", "ph_ce", "eof_lab", 33),
    A("tlc-rf-vs-sat", "TLC", "Rf", "0.42", "0.55", "0.54", "1 K", "Rf", "sat +4%", 5, 1, "tank", "silica", "0.30", "sat 4% extra", "flash vs elute", "tl_op", "st_tl", "rf_lab", 32),
    A("flash-vs-elute", "flash", "elute", "fail", "pass", "pass", "2 K", "tail", "grad +4%", 6, 1, "column", "SiO2", "fail", "grad 4% extra", "prep HPLC vs load", "fl_op", "gd_fl", "el_lab", 31),
    A("prep-hplc-vs-load", "prep", "load", "18 mg", "40 mg", "39 mg", "2 K", "overload", "load -4%", 6, 1, "column", "C18", "12 mg", "load 4% extra", "SFE vs CO2", "pr_op", "ld_pr", "ld_lab", 30),
    A("sfe-vs-co2", "SFE", "yield", "62%", "85%", "84%", "3 K", "yield", "P +4%", 7, 1, "vessel", "CO2", "50%", "P 4% extra", "SPE vs recover", "sf_op", "p_sf", "yd_sf", 29),
    A("spe-vs-recover", "SPE", "rec", "62%", "90%", "89%", "2 K", "rec", "elute +4%", 6, 1, "cartridge", "C18", "50%", "elute 4% extra", "LPE vs partition", "sp_op", "el_sp", "rc_sp", 28),
    A("lpe-vs-partition", "LLE", "K", "8.4", "18", "17.6", "2 K", "K", "pH +4%", 6, 1, "sep", "DCM", "6", "pH 4% extra", "QuEChERS vs matrix", "lp_op", "ph_lp", "k_lab", 27),
    A("queche-vs-matrix", "QuEChERS", "ME", "42%", "10%", "10.4%", "2 K", "ME", "dSPE +4%", 6, 1, "tube", "pesticide", "55%", "dSPE 4% extra", "d-SPE vs fat", "qe_op", "ds_qe", "me_lab", 26),
    A("d-spe-vs-fat", "dSPE", "fat", "18%", "4%", "4.2%", "2 K", "fat", "C18 +4%", 6, 1, "tube", "lipid", "24%", "C18 4% extra", "NMR shim vs LW", "ds_op", "c18_ds", "ft_lab", 25),
    A("nmr-shim-vs-lw", "NMR", "LW", "1.8 Hz", "0.4 Hz", "0.42 Hz", "1 K", "LW", "shim +4%", 6, 1, "probe", "500", "2.4 Hz", "shim 4% extra", "MS tune vs res", "nm_op", "sh_nm", "lw_lab", 24),
    A("ms-tune-vs-res", "MS", "R", "8200", "15000", "14800", "2 K", "R", "tune +4%", 6, 1, "orbitrap", "HRMS", "6000", "tune 4% extra", "IR gain vs SNR", "ms_op", "tn_ms", "r_ms", 23),
    A("ir-gain-vs-snr", "FTIR", "SNR", "820", "2000", "1960", "1 K", "SNR", "scan +4%", 6, 1, "bench", "ATR", "600", "scan 4% extra", "Raman vs fluores", "ir_op", "sc_ir", "snr_ir", 22),
    A("raman-vs-fluores", "Raman", "bg", "fail", "pass", "pass", "2 K", "fluores", "785 +4%", 6, 1, "probe", "solid", "fail", "785 4% extra", "UV blank vs abs", "rm_op", "wl_rm", "bg_rm", 21),
    A("uv-blank-vs-abs", "UV", "blank", "0.018 A", "0.002 A", "0.0021 A", "1 K", "blank", "cuvette +4%", 5, 1, "cell", "A260", "0.024 A", "cuvette 4% extra", "fluor vs quench", "uv_op", "cv_uv", "bl_uv", 20),
    A("fluor-vs-quench", "fluor", "Q", "42%", "10%", "10.4%", "1 K", "Q", "dilute +4%", 6, 1, "cuvette", "Trp", "55%", "dilute 4% extra", "CD vs HT", "fl_op", "dl_fl", "q_lab", 19),
    A("cd-vs-ht", "CD", "HT", "820 V", "400 V", "410 V", "1 K", "HT", "path -4%", 6, 1, "cell", "peptide", "1000 V", "path 4% extra", "DSC vs onset", "cd_op", "pt_cd", "ht_lab", 18),
    A("dsc-vs-onset", "DSC", "onset", "1.8 K", "0.4 K", "0.42 K", "2 K", "onset", "rate -4%", 6, 1, "pan", "Tg", "2.4 K", "rate 4% extra", "TGA vs onset", "ds_op", "rt_ds", "on_lab", 17),
    A("tga-vs-onset", "TGA", "onset", "8.4 K", "2.0 K", "2.1 K", "2 K", "onset", "rate -4%", 6, 1, "pan", "decomp", "11 K", "rate 4% extra", "DMA vs Tg", "tg_op", "rt_tg", "on_tg", 16),
    A("dma-vs-tg", "DMA", "Tg", "4.2 K", "1.0 K", "1.05 K", "2 K", "Tg", "freq -4%", 6, 1, "bar", "E'", "5.5 K", "freq 4% extra", "TMA vs CTE", "dm_op", "fr_dm", "tg_dm", 15),
    A("tma-vs-cte", "TMA", "CTE", "18 ppm", "6 ppm", "6.2 ppm", "2 K", "CTE", "force -4%", 6, 1, "probe", "exp", "24 ppm", "force 4% extra", "rheo vs Gprime", "tm_op", "fc_tm", "cte_lab", 14),
    A("rheo-vs-gprime", "rheo", "G'", "18%", "6%", "6.2%", "2 K", "G'", "gap +4%", 6, 1, "plate", "gel", "24%", "gap 4% extra", "HPLC next densify", "rh_op", "gp_rh", "g_lab", 13),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4247, s)
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
