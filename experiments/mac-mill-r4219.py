#!/usr/bin/env python3
"""MAC mill r4219+. Unique ocean/paleo plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205r", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("argo-sal-vs-drift", "Argo", "S", "0.018", "0.004", "0.0042", "1 K", "drift", "offset +4%", 6, 1, "float", "T/S", "0.024", "offset 4% extra", "glider vs yo", "ar_op", "of_ar", "s_lab", 38),
    A("glider-vs-yo", "glider", "yo", "18 min", "8 min", "8.2 min", "1 K", "yo", "buoy +4%", 6, 1, "glider", "Slocum", "24 min", "buoy 4% extra", "ADCP vs bias", "gl_op", "by_gl", "yo_lab", 37),
    A("adcp-vs-bias", "ADCP", "bias", "1.8 cm/s", "0.4 cm/s", "0.42 cm/s", "1 K", "bias", "comp +4%", 6, 1, "mooring", "75 kHz", "2.4 cm/s", "comp 4% extra", "CTD vs hysteresis", "ad_op", "cp_ad", "bs_ad", 36),
    A("ctd-vs-hysteresis", "CTD", "hyst", "0.018 PSU", "0.004 PSU", "0.0042 PSU", "1 K", "hyst", "pump +4%", 6, 1, "rosette", "SBE", "0.024 PSU", "pump 4% extra", "mooring vs biofoul", "ct_op", "pm_ct", "hy_lab", 35),
    A("mooring-vs-biofoul", "mooring", "foul", "18 d", "60 d", "58 d", "1 K", "foul", "copper +4%", 7, 1, "line", "coast", "12 d", "copper 4% extra", "HF radar vs current", "mo_op", "cu_mo", "fl_mo", 34),
    A("hf-radar-vs-current", "HF", "u", "8.4 cm/s", "3.0 cm/s", "3.1 cm/s", "1 K", "bias", "GDOP +4%", 6, 1, "site", "CODAR", "11 cm/s", "GDOP 4% extra", "altimeter vs SSH", "hf_op", "gd_hf", "u_hf", 33),
    A("altimeter-vs-ssh", "alt", "SSH", "4.2 cm", "1.5 cm", "1.55 cm", "1 K", "SSH", "retrack +4%", 6, 1, "pass", "Ku", "5.5 cm", "retrack 4% extra", "SST vs skin", "al_op", "rt_al", "ssh_lab", 32),
    A("sst-vs-skin", "SST", "skin", "0.42 K", "0.12 K", "0.12 K", "1 K", "skin", "IR +4%", 6, 1, "buoy", "skin", "0.55 K", "IR 4% extra", "Chl vs fluor", "ss_op", "ir_ss", "sk_lab", 31),
    A("chl-vs-fluor", "chl", "F", "18%", "6%", "6.2%", "1 K", "NPQ", "NPQ +4%", 6, 1, "flow", "fluor", "24%", "NPQ 4% extra", "CDOM vs abs", "ch_op", "npq_ch", "f_lab", 30),
    A("cdom-vs-abs", "CDOM", "a350", "0.42 /m", "0.15 /m", "0.16 /m", "1 K", "abs", "blank +4%", 6, 1, "cuvette", "CDOM", "0.55 /m", "blank 4% extra", "pH optode vs drift", "cd_op", "bl_cd", "a_lab", 29),
    A("ph-optode-vs-drift", "pH", "drift", "0.018 /mo", "0.004 /mo", "0.0042 /mo", "1 K", "drift", "cal +4%", 6, 1, "optode", "SeaFET", "0.024 /mo", "cal 4% extra", "O2 optode vs gain", "ph_op", "cl_ph", "dr_ph", 28),
    A("o2-optode-vs-gain", "O2", "gain", "1.8%", "0.4%", "0.42%", "1 K", "gain", "Winkler +4%", 6, 1, "optode", "Aanderaa", "2.4%", "Winkler 4% extra", "nutrient vs blank", "o2_op", "wk_o2", "gn_o2", 27),
    A("nutrient-vs-blank", "NO3", "blank", "0.18 µM", "0.04 µM", "0.042 µM", "1 K", "blank", "MQ +4%", 6, 1, "AA", "WOCE", "0.24 µM", "MQ 4% extra", "pCO2 vs equil", "nu_op", "mq_nu", "bl_nu", 26),
    A("pco2-vs-equil", "pCO2", "equil", "8.4 µatm", "2.0 µatm", "2.1 µatm", "1 K", "equil", "flow +4%", 6, 1, "equil", "underway", "11 µatm", "flow 4% extra", "alkalinity vs CRM", "pc_op", "fl_pc", "eq_lab", 25),
    A("alkalinity-vs-crm", "TA", "CRM", "8.4 µmol/kg", "2.0 µmol/kg", "2.1 µmol/kg", "1 K", "CRM", "titrate +4%", 6, 1, "cell", "Dickson", "11 µmol/kg", "titrate 4% extra", "DIC vs CRM", "ta_op", "tt_ta", "crm_lab", 24),
    A("dic-vs-crm", "DIC", "CRM", "8.4 µmol/kg", "2.0 µmol/kg", "2.1 µmol/kg", "1 K", "CRM", "coul +4%", 6, 1, "cell", "SOMMA", "11 µmol/kg", "coul 4% extra", "ice core vs d18O", "di_op", "cl_di", "crm_di", 23),
    A("ice-core-vs-d18o", "ice", "d18O", "0.18 ‰", "0.04 ‰", "0.042 ‰", "1 K", "d18O", "melt +4%", 6, 1, "core", "GISP", "0.24 ‰", "melt 4% extra", "speleothem vs d13C", "ic_op", "ml_ic", "d18_lab", 22),
    A("speleothem-vs-d13c", "speleo", "d13C", "0.18 ‰", "0.04 ‰", "0.042 ‰", "1 K", "d13C", "drill +4%", 6, 1, "stal", "drip", "0.24 ‰", "drill 4% extra", "tree ring vs width", "sp_op", "dr_sp", "d13_lab", 21),
    A("tree-ring-vs-width", "ring", "width", "0.18 mm", "0.04 mm", "0.042 mm", "1 K", "width", "cross +4%", 6, 1, "core", "oak", "0.24 mm", "cross 4% extra", "coral vs Sr/Ca", "tr_op", "cr_tr", "wd_tr", 20),
    A("coral-vs-sr-ca", "coral", "Sr/Ca", "0.018 mmol/mol", "0.004 mmol/mol", "0.0042 mmol/mol", "1 K", "Sr/Ca", "LA +4%", 6, 1, "core", "Porites", "0.024 mmol/mol", "LA 4% extra", "sediment vs TOC", "co_op", "la_co", "sr_lab", 19),
    A("sediment-vs-toc", "sed", "TOC", "0.18%", "0.04%", "0.042%", "1 K", "TOC", "acid +4%", 6, 1, "core", "marine", "0.24%", "acid 4% extra", "pollen vs count", "sd_op", "ac_sd", "toc_sd", 18),
    A("pollen-vs-count", "pollen", "count", "180", "400", "392", "1 K", "count", "slide +4%", 6, 1, "core", "lake", "140", "slide 4% extra", "foramin vs d18O", "po_op", "sl_po", "ct_po", 17),
    A("foramin-vs-d18o", "foram", "d18O", "0.18 ‰", "0.04 ‰", "0.042 ‰", "1 K", "d18O", "clean +4%", 6, 1, "core", "G.ruber", "0.24 ‰", "clean 4% extra", "diatom vs Si", "fo_op", "cl_fo", "d18_fo", 16),
    A("diatom-vs-si", "diatom", "Si", "18%", "6%", "6.2%", "1 K", "diss", "clean +4%", 6, 1, "core", "lake", "24%", "clean 4% extra", "varve vs count", "di_op", "cl_di", "si_di", 15),
    A("varve-vs-count", "varve", "count", "fail", "pass", "pass", "1 K", "count", "scan +4%", 6, 1, "core", "lake", "fail", "scan 4% extra", "tephra vs glass", "va_op", "sc_va", "ct_va", 14),
    A("tephra-vs-glass", "tephra", "glass", "fail", "match", "match", "1 K", "chem", "EPMA +4%", 6, 1, "shard", "isochron", "fail", "EPMA 4% extra", "OSL vs dose", "te_op", "ep_te", "gl_te", 13),
    A("osl-vs-dose", "OSL", "De", "18%", "6%", "6.2%", "1 K", "De", "SAR +4%", 6, 1, "quartz", "dose", "24%", "SAR 4% extra", "C14 vs reservoir", "os_op", "sar_os", "de_lab", 12),
    A("c14-vs-reservoir", "C14", "R", "180 y", "40 y", "42 y", "1 K", "R", "local +4%", 6, 1, "shell", "AMS", "240 y", "local 4% extra", "Argo next densify", "c14_op", "lc_c14", "r_c14", 11),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4219, s)
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
