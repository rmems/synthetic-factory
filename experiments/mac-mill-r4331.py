#!/usr/bin/env python3
"""MAC mill r4331+. Unique protein characterization plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205w", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("hplc-charge-vs-cax", "CEX", "main", "62%", "80%", "79.4%", "2 K", "main", "pH +4%", 6, 1, "column", "mAb", "50%", "pH 4% extra", "HIC vs HICS", "cx_op", "ph_cx", "mn_lab", 28),
    A("hplc-hics-vs-hics", "HIC", "HMW", "1.8%", "0.5%", "0.52%", "2 K", "HMW", "salt +4%", 6, 1, "column", "mAb", "2.4%", "salt 4% extra", "RP vs ox", "hi_op", "st_hi", "hmw_hi", 27),
    A("hplc-rp-vs-ox", "RP", "ox", "4.2%", "1.0%", "1.05%", "2 K", "ox", "T -4%", 6, 1, "C4", "Met", "5.5%", "T 4% extra", "CE cIEF vs pI2", "rp_op", "t_rp", "ox_lab", 26),
    A("ce-cief-vs-pi2", "cIEF", "pI", "0.18", "0.04", "0.042", "2 K", "pI", "urea +4%", 6, 1, "cap", "icIEF", "0.24", "urea 4% extra", "MS subunit vs mass", "ci_op", "ur_ci", "pi_ci", 25),
    A("ms-subunit-vs-mass", "subunit", "Δm", "18 Da", "4 Da", "4.2 Da", "2 K", "Δm", "IdeS +4%", 6, 1, "QTOF", "Hc/Lc", "24 Da", "IdeS 4% extra", "MS middle vs Fc", "su_op", "id_su", "dm_su", 24),
    A("ms-middle-vs-fc", "middle-down", "Fc", "fail", "match", "match", "2 K", "Fc", "IdeS +4%", 6, 1, "QTOF", "Fc/2", "fail", "IdeS 4% extra", "HDX vs uptake", "md_op", "id_md", "fc_lab", 23),
    A("hd-x-vs-uptake", "HDX", "uptake", "18%", "6%", "6.2%", "2 K", "uptake", "pH +4%", 6, 1, "pep", "HDX", "24%", "pH 4% extra", "IM-MS vs CCS", "hd_op", "ph_hd", "up_lab", 22),
    A("im-ms-vs-ccs", "IM-MS", "CCS", "18 Å2", "4 Å2", "4.2 Å2", "2 K", "CCS", "cal +4%", 6, 1, "TWIMS", "mAb", "24 Å2", "cal 4% extra", "HDX vs pep", "im_op", "cl_im", "ccs_lab", 21),
    A("hdx-vs-pep", "HDX", "pep", "82%", "95%", "94.6%", "2 K", "pep", "digest +4%", 6, 1, "pepsin", "HDX", "74%", "digest 4% extra", "native MS vs charge", "hx_op", "dg_hx", "pp_lab", 20),
    A("native-ms-vs-charge", "native", "z", "18+", "24+", "23.6+", "2 K", "z", "ammo +4%", 6, 1, "QTOF", "mAb", "14+", "ammo 4% extra", "topdown vs frag", "nv_op", "am_nv", "z_lab", 19),
    A("topdown-vs-frag", "top-down", "cover", "42%", "70%", "69%", "2 K", "cover", "EThcD +4%", 6, 1, "orbitrap", "mAb", "32%", "EThcD 4% extra", "bottomup vs cover2", "td_op", "et_td", "cv_td", 18),
    A("bottomup-vs-cover2", "bottom-up", "cover", "82%", "95%", "94.6%", "2 K", "cover", "missed -4%", 6, 1, "orbitrap", "tryptic", "74%", "missed 4% extra", "SEC-MALS vs Rg", "bu_op", "ms_bu", "cv_bu", 17),
    A("hplc-sec-malls-vs-rg", "SEC-MALS", "Rg", "1.8 nm", "0.4 nm", "0.42 nm", "2 K", "Rg", "dn/dc +4%", 6, 1, "column", "mAb", "2.4 nm", "dn/dc 4% extra", "visc vs IV", "sm_op", "dn_sm", "rg_lab", 16),
    A("visc-vs-iv", "visc", "IV", "18%", "6%", "6.2%", "2 K", "IV", "T +4%", 6, 1, "Ubbelohde", "mAb", "24%", "T 4% extra", "DSC vs Tm2", "vs_op", "t_vs", "iv_lab", 15),
    A("dsc-vs-tm2", "DSC", "Tm", "1.8 K", "0.4 K", "0.42 K", "2 K", "Tm", "scan -4%", 6, 1, "pan", "mAb", "2.4 K", "scan 4% extra", "CD vs helix", "dc_op", "sc_dc", "tm_dc", 14),
    A("cd-vs-helix", "CD", "helix", "8.4%", "2.0%", "2.1%", "1 K", "helix", "path +4%", 6, 1, "cell", "far-UV", "11%", "path 4% extra", "FTIR vs amide", "cd_op", "pt_cd", "hx_lab", 13),
    A("ftir-vs-amide", "FTIR", "amide I", "18 cm-1", "4 cm-1", "4.2 cm-1", "1 K", "amide", "ATR +4%", 6, 1, "crystal", "mAb", "24 cm-1", "ATR 4% extra", "Raman vs amide", "ft_op", "at_ft", "am_lab", 12),
    A("raman-vs-amide", "Raman", "amide", "18 cm-1", "4 cm-1", "4.2 cm-1", "1 K", "amide", "785 +4%", 6, 1, "probe", "mAb", "24 cm-1", "785 4% extra", "DLS vs Rh", "rm_op", "wl_rm", "am_rm", 11),
    A("dls-vs-rh", "DLS", "Rh", "1.8 nm", "0.4 nm", "0.42 nm", "1 K", "Rh", "T +4%", 6, 1, "cuvette", "mAb", "2.4 nm", "T 4% extra", "AUC SV vs s2", "dl_op", "t_dl", "rh_lab", 10),
    A("auc-sv-vs-s2", "SV-AUC", "s", "0.18 S", "0.04 S", "0.042 S", "2 K", "s", "align +4%", 6, 1, "cell", "mAb", "0.24 S", "align 4% extra", "CEX next densify", "sv_op", "al_sv", "s_sv", 9),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4331, s)
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
