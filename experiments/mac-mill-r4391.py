#!/usr/bin/env python3
"""MAC mill r4391+. Unique CEMS/process-gas/stack analyzer plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205z", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("tdlas-h2o-vs-span", "TDLAS", "H2O", "18 ppm", "4 ppm", "4.2 ppm", "2 K", "H2O", "span +4%", 6, 1, "cell", "stack", "24 ppm", "span 4% extra", "NDIR vs span", "td_op", "sp_td", "h2o_td", 31),
    A("ndir-co2-vs-span", "NDIR", "CO2", "1.8%", "0.4%", "0.42%", "2 K", "CO2", "span +4%", 6, 1, "cell", "flue", "2.4%", "span 4% extra", "paramag vs span", "nd_op", "sp_nd", "co2_nd", 30),
    A("paramag-o2-vs-span", "paramag", "O2", "1.8%", "0.4%", "0.42%", "2 K", "O2", "span +4%", 6, 1, "cell", "flue", "2.4%", "span 4% extra", "zirconia vs lambda", "pm_op", "sp_pm", "o2_pm", 29),
    A("zirconia-o2-vs-lambda", "zirconia", "λ", "1.18", "1.00", "1.01", "2 K", "λ", "air +4%", 6, 1, "probe", "kiln", "1.28", "air 4% extra", "TCD vs span", "zr_op", "lm_zr", "lam_zr", 28),
    A("tcd-h2-vs-span", "TCD", "H2", "1.8%", "0.4%", "0.42%", "2 K", "H2", "span +4%", 6, 1, "cell", "syngas", "2.4%", "span 4% extra", "CLD vs ozone", "tc_op", "sp_tc", "h2_tc", 27),
    A("cld-nox-vs-ozone", "CLD", "NOx", "180 ppm", "40 ppm", "42 ppm", "2 K", "NOx", "O3 +4%", 6, 1, "cell", "stack", "240 ppm", "O3 4% extra", "FID vs span", "cl_op", "oz_cl", "nox_cl", 26),
    A("fid-thc-vs-span", "FID", "THC", "18 ppm", "4 ppm", "4.2 ppm", "2 K", "THC", "H2 +4%", 6, 1, "jet", "VOC", "24 ppm", "H2 4% extra", "DOAS vs path", "fd_op", "h2_fd", "thc_fd", 25),
    A("doas-so2-vs-path", "DOAS", "SO2", "18 ppm", "4 ppm", "4.2 ppm", "2 K", "SO2", "path +4%", 6, 1, "path", "stack", "24 ppm", "path 4% extra", "opacity vs span", "da_op", "pt_da", "so2_da", 24),
    A("opacity-vs-span", "opacity", "opac", "18%", "6%", "6.2%", "2 K", "opac", "span +4%", 6, 1, "trans", "stack", "24%", "span 4% extra", "FTIR vs H2O", "op_op", "sp_op", "opac_op", 23),
    A("ftir-cems-vs-h2o", "FTIR", "H2O", "18%", "6%", "6.2%", "2 K", "H2O", "purge +4%", 6, 1, "cell", "CEMS", "24%", "purge 4% extra", "QCL vs NH3", "ft_op", "pg_ft", "h2o_ft", 22),
    A("qcl-nh3-vs-ppm", "QCL", "NH3", "18 ppm", "4 ppm", "4.2 ppm", "2 K", "NH3", "span +4%", 6, 1, "cell", "SCR", "24 ppm", "span 4% extra", "PAS vs span", "qc_op", "sp_qc", "nh3_qc", 21),
    A("pas-co-vs-span", "PAS", "CO", "18 ppm", "4 ppm", "4.2 ppm", "2 K", "CO", "span +4%", 6, 1, "cell", "flue", "24 ppm", "span 4% extra", "CRDS vs span", "pa_op", "sp_pa", "co_pa", 20),
    A("crds-ch4-vs-span", "CRDS", "CH4", "1.8 ppm", "0.4 ppm", "0.42 ppm", "2 K", "CH4", "span +4%", 6, 1, "cavity", "leak", "2.4 ppm", "span 4% extra", "GC vs C1", "cr_op", "sp_cr", "ch4_cr", 19),
    A("gc-cems-vs-c1", "PGC", "C1", "1.8%", "0.4%", "0.42%", "2 K", "C1", "carrier +4%", 6, 1, "column", "flare", "2.4%", "carrier 4% extra", "Wobbe vs N2", "gc_op", "c1_gc", "c1_lab", 18),
    A("cems-wobbe-vs-n2", "Wobbe", "WI", "48.2", "52.0", "51.8", "2 K", "WI", "N2 -4%", 6, 1, "cell", "fuel", "46.0", "N2 4% extra", "Coriolis vs zero", "wb_op", "n2_wb", "wi_wb", 17),
    A("coriolis-mass-vs-zero", "Coriolis", "zero", "fail", "pass", "pass", "2 K", "zero", "zero +4%", 6, 1, "tube", "mass", "fail", "zero 4% extra", "magmeter vs empty", "co_op", "zr_co", "z_co", 16),
    A("magmeter-vs-empty", "magmeter", "empty", "fail", "pass", "pass", "2 K", "empty", "fill +4%", 6, 1, "liner", "slurry", "fail", "fill 4% extra", "vortex vs K", "mg_op", "fl_mg", "em_mg", 15),
    A("vortex-k-vs-pipe", "vortex", "K", "1.8%", "0.4%", "0.42%", "2 K", "K", "Re +4%", 6, 1, "bluff", "steam", "2.4%", "Re 4% extra", "USM vs SoS", "vx_op", "re_vx", "k_vx", 14),
    A("usm-sos-vs-span", "USM", "SoS", "1.8%", "0.4%", "0.42%", "2 K", "SoS", "span +4%", 6, 1, "path", "gas", "2.4%", "span 4% extra", "orifice vs beta", "us_op", "sp_us", "sos_us", 13),
    A("orifice-beta-vs-dp", "orifice", "dP", "1.8%", "0.4%", "0.42%", "2 K", "dP", "tap +4%", 6, 1, "plate", "gas", "2.4%", "tap 4% extra", "S-type vs K", "or_op", "tp_or", "dp_or", 12),
    A("stype-pitot-vs-k", "S-type", "K", "1.8%", "0.4%", "0.42%", "2 K", "K", "yaw +4%", 6, 1, "probe", "stack", "2.4%", "yaw 4% extra", "gamma vs span", "st_op", "yw_st", "k_st", 11),
    A("gamma-dens-vs-span", "gamma", "ρ", "1.8%", "0.4%", "0.42%", "2 K", "ρ", "span +4%", 6, 1, "source", "slurry", "2.4%", "span 4% extra", "dilution vs ratio", "gm_op", "sp_gm", "rho_gm", 10),
    A("dilprobe-o2-vs-ratio", "dilprobe", "O2", "1.8%", "0.4%", "0.42%", "2 K", "O2", "ratio +4%", 6, 1, "probe", "hot", "2.4%", "ratio 4% extra", "Hg vs gold", "dl_op", "rt_dl", "o2_dl", 9),
    A("hg-cems-vs-gold", "Hg-CEMS", "Hg", "18 µg/m3", "4 µg/m3", "4.2 µg/m3", "2 K", "Hg", "gold +4%", 6, 1, "trap", "coal", "24 µg/m3", "gold 4% extra", "isokin vs ratio", "hg_op", "au_hg", "hg_lab", 8),
    A("isokin-vs-ratio", "isokin", "ratio", "1.18", "1.00", "1.01", "2 K", "ratio", "nozzle +4%", 6, 1, "nozzle", "PM", "1.28", "nozzle 4% extra", "3D vs yaw", "ik_op", "nz_ik", "iso_ik", 7),
    A("anem3d-vs-yaw", "3D-anem", "yaw", "18 °", "4 °", "4.2 °", "2 K", "yaw", "align +4%", 6, 1, "probe", "stack", "24 °", "align 4% extra", "TDLAS next densify", "an_op", "al_an", "yaw_an", 6),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    if len(SCENARIOS) != 26:
        raise SystemExit(f"need 26 plants, got {len(SCENARIOS)}")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4391, s)
        if len(rec["transcript"]) < 8 or len(s["agents"]) != 3:
            raise SystemExit(s["slug"])
        if s["novel"] < 6:
            raise SystemExit(f"novel {s['novel']} below 6% {s['slug']}")
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
        if spec["novel"] < 5:
            print(f"STOP novel {spec['novel']}%", flush=True)
            break
    print(json.dumps({"published": published, "count": len(published),
                      "frontier": round_txn.frontier_status(FACTORY)["next_round"]}), flush=True)
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
