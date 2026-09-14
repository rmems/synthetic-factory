#!/usr/bin/env python3
"""MAC mill r4119+. Unique cryo/vacuum/analytical plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205o", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("cryo-4k-vs-load", "4K", "T", "4.8 K", "4.2 K", "4.22 K", "2 K", "load", "shield +4%", 8, 1, "cryostat", "sample", "5.5 K", "shield 4% extra", "dilution mK vs base", "cr_op", "sh_cr", "t_cr", 44),
    A("dilution-mk-vs-base", "DR", "T", "18 mK", "8 mK", "8.2 mK", "1 K", "base", "still +4%", 8, 1, "MC", "qubit", "24 mK", "still 4% extra", "pulse tube vs tilt", "dr_op", "st_dr", "t_dr", 43),
    A("pulse-tube-vs-tilt", "PT", "T2", "4.8 K", "3.5 K", "3.55 K", "2 K", "tilt", "orient +4%", 7, 1, "coldhead", "GM", "5.5 K", "orient 4% extra", "GM cooler vs MAP", "pt_op", "or_pt", "t2_lab", 42),
    A("gm-cooler-vs-map", "GM", "MAP", "1.8 W", "1.0 W", "1.02 W", "3 K", "MAP", "He +4%", 8, 1, "coldhead", "2-stage", "2.4 W", "He 4% extra", "sorption cooler vs cycle", "gm_op", "he_gm", "map_lab", 41),
    A("sorption-cooler-vs-cycle", "sorption", "T", "18 K", "10 K", "10.2 K", "3 K", "cycle", "charcoal +4%", 8, 1, "stage", "IR", "24 K", "charcoal 4% extra", "Stirling cryo vs lift", "sp_op", "ch_sp", "t_sp", 40),
    A("stirling-cryo-vs-lift", "Stirling", "lift", "1.8 W", "3.0 W", "2.95 W", "3 K", "lift", "stroke +4%", 7, 1, "head", "IR", "1.2 W", "stroke 4% extra", "JT valve vs temp", "st_op", "sk_st", "lf_lab", 39),
    A("jt-valve-vs-temp", "JT", "T", "82 K", "70 K", "70.4 K", "2 K", "T", "orifice +4%", 6, 1, "probe", "LN2", "90 K", "orifice 4% extra", "LN2 dewar vs hold", "jt_op", "or_jt", "t_jt", 38),
    A("ln2-dewar-vs-hold", "LN2", "hold", "18 d", "40 d", "39 d", "1 K", "boiloff", "vent +4%", 6, 1, "dewar", "storage", "12 d", "vent 4% extra", "LHe dewar vs boiloff", "ln_op", "vt_ln", "hd_ln", 37),
    A("lhe-dewar-vs-boiloff", "LHe", "boil", "1.8 %/d", "0.5 %/d", "0.52 %/d", "1 K", "boil", "shield +4%", 7, 1, "dewar", "NMR", "2.4 %/d", "shield 4% extra", "cryopump vs regen", "he_op", "sh_he", "bl_he", 36),
    A("cryopump-vs-regen", "cryopump", "P", "1.8e-6", "5e-8", "5.2e-8", "3 K", "sat", "regen +4%", 8, 1, "chamber", "PVD", "3e-6", "regen 4% extra", "turbo pump vs fore", "cp_op", "rg_cp", "p_cp", 35),
    A("turbo-pump-vs-fore", "TMP", "P", "1.8e-6", "5e-8", "5.2e-8", "2 K", "fore", "scroll +4%", 7, 1, "chamber", "SEM", "3e-6", "scroll 4% extra", "ion pump vs leak", "tm_op", "sc_tm", "p_tm", 34),
    A("ion-pump-vs-leak", "SIP", "I", "18 µA", "4 µA", "4.2 µA", "2 K", "leak", "bake +4%", 8, 1, "chamber", "UHV", "24 µA", "bake 4% extra", "RGA partial vs bake", "ip_op", "bk_ip", "i_ip", 33),
    A("rga-partial-vs-bake", "RGA", "18 amu", "1.8e-8", "2e-10", "2.1e-10", "3 K", "H2O", "bake +4%", 9, 1, "chamber", "UHV", "3e-8", "bake 4% extra", "QMS amu vs res", "rg_op", "bk_rg", "h2o_lab", 32),
    A("qms-amu-vs-res", "QMS", "Δm", "0.8 amu", "0.3 amu", "0.31 amu", "2 K", "res", "RF +4%", 6, 1, "head", "process", "1.1 amu", "RF 4% extra", "UHV bake vs outgas", "qm_op", "rf_qm", "dm_lab", 31),
    A("uhv-bake-vs-outgas", "UHV", "P", "1.8e-9", "5e-11", "5.2e-11", "4 K", "outgas", "bake +4%", 10, 1, "chamber", "surface", "3e-9", "bake 4% extra", "XHV vs ESD", "uh_op", "bk_uh", "p_uh", 30),
    A("xhv-vs-esd", "XHV", "P", "1.8e-11", "5e-13", "5.2e-13", "3 K", "ESD", "NEG +4%", 8, 1, "chamber", "atom", "3e-11", "NEG 4% extra", "CMM probe vs uncert", "xh_op", "ng_xh", "p_xh", 29),
    A("cmm-probe-vs-uncert", "CMM", "U", "8.4 µm", "2.0 µm", "2.1 µm", "1 K", "U", "cal +4%", 6, 1, "CMM", "ISO", "11 µm", "cal 4% extra", "laser tracker vs SMR", "cm_op", "cl_cm", "u_lab", 28),
    A("laser-tracker-vs-smr", "tracker", "U", "42 µm", "15 µm", "15.4 µm", "1 K", "U", "SMR +4%", 6, 1, "tracker", "jig", "55 µm", "SMR 4% extra", "photogram CMM vs scale", "lt_op", "smr_lt", "u_lt", 27),
    A("photogram-cmm-vs-scale", "V-STARS", "U", "82 µm", "25 µm", "26 µm", "1 K", "U", "scale +4%", 6, 1, "set", "tool", "110 µm", "scale 4% extra", "artic arm vs joint", "pg_op", "sc_pg", "u_pg", 26),
    A("artic-arm-vs-joint", "arm", "U", "42 µm", "18 µm", "18.4 µm", "1 K", "U", "cal +4%", 6, 1, "arm", "shop", "55 µm", "cal 4% extra", "vision gage vs pixel", "aa_op", "cl_aa", "u_aa", 25),
    A("vision-gage-vs-pixel", "vision", "U", "8.4 µm", "2.0 µm", "2.1 µm", "1 K", "U", "mag +4%", 5, 1, "stage", "2D", "11 µm", "mag 4% extra", "white light vs NA", "vg_op", "mg_vg", "u_vg", 24),
    A("white-light-vs-na", "WLI", "U", "18 nm", "4 nm", "4.2 nm", "1 K", "U", "NA +4%", 6, 1, "obj", "rough", "24 nm", "NA 4% extra", "confocal z vs NA", "wl_op", "na_wl", "u_wl", 23),
    A("confocal-z-vs-na", "confocal", "dz", "0.42 µm", "0.12 µm", "0.12 µm", "1 K", "dz", "NA +4%", 6, 1, "obj", "step", "0.55 µm", "NA 4% extra", "AFM vs scan", "cf_op", "na_cf", "dz_lab", 22),
    A("afm-vs-scan", "AFM", "noise", "0.18 nm", "0.04 nm", "0.042 nm", "1 K", "noise", "iso +4%", 6, 1, "head", "Si", "0.28 nm", "iso 4% extra", "XRF LOD vs time", "af_op", "is_af", "ns_lab", 21),
    A("xrf-lod-vs-time", "XRF", "LOD", "18 ppm", "4 ppm", "4.2 ppm", "2 K", "LOD", "time +4%", 7, 1, "cup", "alloy", "24 ppm", "time 4% extra", "XRD FWHM vs align", "xr_op", "tm_xr", "lod_lab", 20),
    A("xrd-fwhm-vs-align", "XRD", "FWHM", "0.18 °", "0.06 °", "0.062 °", "2 K", "FWHM", "align +4%", 6, 1, "goni", "powder", "0.24 °", "align 4% extra", "XPS charge vs flood", "xd_op", "al_xd", "fw_lab", 19),
    A("xps-charge-vs-flood", "XPS", "shift", "1.8 eV", "0.3 eV", "0.32 eV", "2 K", "charge", "flood +4%", 6, 1, "chamber", "polymer", "2.4 eV", "flood 4% extra", "AES sputter vs depth", "xp_op", "fl_xp", "sh_xp", 18),
    A("aes-sputter-vs-depth", "AES", "res", "18 nm", "5 nm", "5.2 nm", "2 K", "mix", "Ar +4%", 6, 1, "chamber", "film", "24 nm", "Ar 4% extra", "SIMS matrix vs RSF", "ae_op", "ar_ae", "res_ae", 17),
    A("sims-matrix-vs-rsf", "SIMS", "RSF", "18%", "5%", "5.2%", "2 K", "matrix", "std +4%", 7, 1, "chamber", "dopant", "24%", "std 4% extra", "ToF-S mass vs res", "si_op", "st_si", "rsf_lab", 16),
    A("tofs-mass-vs-res", "ToF-SIMS", "m/Δm", "4200", "8000", "7900", "2 K", "res", "reflect +4%", 7, 1, "chamber", "organic", "3200", "reflect 4% extra", "ICP-MS oxide vs tune", "tf_op", "rf_tf", "res_tf", 15),
    A("icpms-oxide-vs-tune", "ICP-MS", "CeO", "4.8%", "1.5%", "1.55%", "2 K", "oxide", "tune +4%", 6, 1, "torch", "trace", "6.0%", "tune 4% extra", "ICP-OES RSD vs power", "ic_op", "tn_ic", "ceo_lab", 14),
    A("icpoes-rfsd-vs-power", "ICP-OES", "RSD", "1.8%", "0.4%", "0.42%", "2 K", "RSD", "power +4%", 6, 1, "torch", "major", "2.4%", "power 4% extra", "AA BG vs D2", "oe_op", "pw_oe", "rsd_lab", 13),
    A("aa-bg-vs-d2", "AAS", "BG", "0.18 A", "0.04 A", "0.042 A", "2 K", "BG", "D2 +4%", 6, 1, "flame", "Pb", "0.28 A", "D2 4% extra", "GC-MS tune vs DFTPP", "aa_op", "d2_aa", "bg_lab", 12),
    A("gcms-tune-vs-dftpp", "GC-MS", "DFTPP", "fail", "pass", "pass", "2 K", "tune", "lens +4%", 6, 1, "quad", "SVOC", "fail", "lens 4% extra", "LC-MS spray vs cap", "gc_op", "ln_gc", "df_lab", 11),
    A("lcms-spray-vs-cap", "LC-MS", "spray", "fail", "stable", "stable", "2 K", "spray", "cap +4%", 6, 1, "ESI", "peptide", "fail", "cap 4% extra", "IR ATR vs contact", "lc_op", "cp_lc", "sp_lc", 10),
    A("ir-atr-vs-contact", "ATR", "contact", "fail", "pass", "pass", "1 K", "air", "press +4%", 5, 1, "crystal", "polymer", "fail", "press 4% extra", "cryo next densify", "ir_op", "pr_ir", "ct_ir", 9),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4119, s)
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
