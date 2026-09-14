#!/usr/bin/env python3
"""MAC mill r4155+. Unique nuclear/fusion/accelerator plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205p", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("pwr-boron-vs-axial", "PWR", "AO", "0.18", "0.05", "0.052", "4 K", "AO", "boron +4%", 8, 1, "core", "EOL", "0.24", "boron 4% extra", "BWR void vs MCP", "pwr_op", "b_pwr", "ao_lab", 42),
    A("bwr-void-vs-mcp", "BWR", "MCPR", "1.18", "1.35", "1.34", "3 K", "MCPR", "flow +4%", 8, 1, "core", "OLMCPR", "1.10", "flow 4% extra", "CANDU D2O vs tritium", "bwr_op", "fl_bwr", "mcpr_lab", 41),
    A("candu-d2o-vs-tritium", "CANDU", "T", "18 Ci/kg", "6 Ci/kg", "6.2 Ci/kg", "3 K", "T", "cleanup +4%", 9, 1, "mod", "PHWR", "24 Ci/kg", "cleanup 4% extra", "SMR SBO vs decay", "cd_op", "cl_cd", "t_cd", 40),
    A("smr-sbo-vs-decay", "SMR", "clad", "18 C", "8 C", "8.2 C", "2 K", "heat", "PRHR +4%", 8, 1, "NSSS", "iPWR", "24 C", "PRHR 4% extra", "HTGR He vs activity", "sm_op", "pr_sm", "cl_sm", 39),
    A("htgr-he-vs-activity", "HTGR", "He", "18 Bq/m3", "4 Bq/m3", "4.2 Bq/m3", "4 K", "act", "filter +4%", 8, 1, "loop", "pebble", "24 Bq/m3", "filter 4% extra", "SFR Na vs cover", "ht_op", "fl_ht", "he_lab", 38),
    A("sfr-na-vs-cover", "SFR", "O2", "8 ppm", "2 ppm", "2.1 ppm", "3 K", "O2", "cover +4%", 7, 1, "pool", "Na", "12 ppm", "cover 4% extra", "MSR fluoride vs redox", "sf_op", "cv_sf", "o2_sf", 37),
    A("msr-fluoride-vs-redox", "MSR", "U4/U3", "42", "80", "78", "5 K", "redox", "Be +4%", 8, 1, "salt", "FLiBe", "32", "Be 4% extra", "LFR Pb vs oxygen", "ms_op", "be_ms", "rd_lab", 36),
    A("lfr-pb-vs-oxygen", "LFR", "O", "1.8e-6", "5e-7", "5.2e-7", "4 K", "O", "control +4%", 8, 1, "pool", "Pb", "3e-6", "control 4% extra", "fusion NBI vs shine", "lf_op", "ct_lf", "o_lf", 35),
    A("fusion-nbi-vs-shine", "NBI", "shine", "18%", "6%", "6.2%", "3 K", "shine", "aim +4%", 7, 1, "beam", "D", "24%", "aim 4% extra", "tokamak disr vs halo", "nb_op", "am_nb", "sh_nb", 34),
    A("tokamak-disr-vs-halo", "tokamak", "halo", "1.8 MA", "0.4 MA", "0.42 MA", "2 K", "halo", "killer +4%", 6, 1, "plasma", "divertor", "2.4 MA", "killer 4% extra", "stellarator divert vs heat", "tk_op", "kl_tk", "hl_lab", 33),
    A("stellarator-divert-vs-heat", "W7-X", "qdiv", "18 MW/m2", "8 MW/m2", "8.2 MW/m2", "3 K", "heat", "strike +4%", 7, 1, "divertor", "island", "24 MW/m2", "strike 4% extra", "ICRF vs coupling", "st_op", "sk_st", "qd_lab", 32),
    A("icrf-vs-coupling", "ICRF", "R", "8.4 Ω", "3.0 Ω", "3.1 Ω", "2 K", "reflect", "match +4%", 6, 1, "antenna", "H", "11 Ω", "match 4% extra", "ECAL vs cluster", "ic_op", "mt_ic", "r_ic", 31),
    A("ecal-vs-cluster", "ECAL", "res", "8.4%", "3.0%", "3.1%", "1 K", "res", "cal +4%", 6, 1, "module", "PbWO4", "11%", "cal 4% extra", "HCAL vs MIP", "ec_op", "cl_ec", "res_ec", 30),
    A("hcal-vs-mip", "HCAL", "MIP", "1.8 pe", "4.0 pe", "3.95 pe", "1 K", "MIP", "HV +4%", 6, 1, "tile", "scint", "1.2 pe", "HV 4% extra", "muon vs ID", "hc_op", "hv_hc", "mip_lab", 29),
    A("muon-vs-id", "muon", "eff", "82%", "96%", "95.6%", "1 K", "punch", "RPC +4%", 6, 1, "station", "barrel", "74%", "RPC 4% extra", "tracker vs align", "mu_op", "rp_mu", "ef_lab", 28),
    A("tracker-vs-align", "tracker", "res", "18 µm", "6 µm", "6.2 µm", "1 K", "align", "track +4%", 6, 1, "layer", "pixel", "24 µm", "track 4% extra", "synch RF vs fill", "tr_op", "tk_tr", "res_tr", 27),
    A("synch-rf-vs-fill", "RF", "fill", "82%", "96%", "95.6%", "2 K", "trip", "LLRF +4%", 6, 1, "cavity", "ring", "74%", "LLRF 4% extra", "undulator vs gap", "sy_op", "ll_sy", "fl_sy", 26),
    A("undulator-vs-gap", "undulator", "K", "1.18", "1.80", "1.78", "2 K", "K", "gap -4%", 6, 1, "ID", "soft-X", "0.90", "gap 4% extra", "beamline vs flux", "un_op", "gp_un", "k_lab", 25),
    A("beamline-vs-flux", "BL", "flux", "1.8e12", "8e12", "7.8e12", "2 K", "flux", "slit +4%", 6, 1, "BL", "PX", "1e12", "slit 4% extra", "cryoring vs quench", "bl_op", "sl_bl", "fx_lab", 24),
    A("cryoring-vs-quench", "sc magnet", "quench", "fail", "hold", "hold", "3 K", "quench", "ramp -4%", 7, 1, "dipole", "arc", "fail", "ramp 4% extra", "linac klystron vs RF", "cy_op", "rp_cy", "qh_lab", 23),
    A("linac-klystron-vs-rf", "klystron", "P", "18 MW", "32 MW", "31.6 MW", "3 K", "P", "drive +4%", 7, 1, "gallery", "S-band", "14 MW", "drive 4% extra", "cyclotron dee vs energy", "kl_op", "dr_kl", "p_kl", 22),
    A("cyclotron-dee-vs-energy", "cyclotron", "E", "18 MeV", "30 MeV", "29.6 MeV", "3 K", "E", "B +4%", 7, 1, "dee", "PET", "14 MeV", "B 4% extra", "synchrocyclo vs FM", "cy_op", "b_cy", "e_cy", 21),
    A("synchrocyclo-vs-fm", "FM cyclo", "capture", "42%", "70%", "69%", "3 K", "capture", "FM +4%", 7, 1, "dee", "proton", "32%", "FM 4% extra", "FFAG vs tune", "fm_op", "fm_fm", "cp_lab", 20),
    A("ffag-vs-tune", "FFAG", "tune", "fail", "lock", "lock", "2 K", "res", "kicker +4%", 6, 1, "ring", "proton", "fail", "kicker 4% extra", "storage ring vs lifetime", "ff_op", "kk_ff", "tn_ff", 19),
    A("storage-ring-vs-lifetime", "SR", "τ", "8.4 h", "20 h", "19.6 h", "2 K", "life", "vacuum +4%", 7, 1, "ring", "e-", "6 h", "vacuum 4% extra", "booster vs ramp", "sr_op", "vc_sr", "tau_lab", 18),
    A("booster-vs-ramp", "booster", "loss", "18%", "4%", "4.2%", "2 K", "loss", "ramp +4%", 6, 1, "ring", "inject", "24%", "ramp 4% extra", "injector vs emittance", "bs_op", "rp_bs", "ls_bs", 17),
    A("injector-vs-emittance", "gun", "ε", "8.4 mm mrad", "2.0 mm mrad", "2.1 mm mrad", "2 K", "ε", "solenoid +4%", 6, 1, "gun", "photocathode", "11 mm mrad", "solenoid 4% extra", "RFQ vs transmission", "in_op", "sl_in", "em_lab", 16),
    A("rfq-vs-transmission", "RFQ", "T", "82%", "94%", "93.6%", "2 K", "T", "vane +4%", 6, 1, "tank", "H+", "74%", "vane 4% extra", "DTL vs phase", "rfq_op", "vn_rfq", "t_rfq", 15),
    A("dtl-vs-phase", "DTL", "φ", "fail", "lock", "lock", "2 K", "phase", "LLRF +4%", 6, 1, "tank", "proton", "fail", "LLRF 4% extra", "SCL vs cavity", "dt_op", "ll_dt", "ph_dt", 14),
    A("scl-vs-cavity", "SCL", "Eacc", "8.4 MV/m", "14 MV/m", "13.8 MV/m", "3 K", "Eacc", "Q +4%", 7, 1, "cryomodule", "β=0.61", "6 MV/m", "Q 4% extra", "SCRF vs Qo", "sc_op", "q_sc", "ea_lab", 13),
    A("scrf-vs-qo", "SCRF", "Q0", "8e9", "2e10", "1.96e10", "3 K", "Q0", "EP +4%", 8, 1, "cavity", "1.3 GHz", "4e9", "EP 4% extra", "PIM vs dark", "sr_op", "ep_sr", "q0_lab", 12),
    A("pim-vs-dark", "PIM", "dark", "18 Hz", "4 Hz", "4.2 Hz", "1 K", "dark", "cool +4%", 6, 1, "SiPM", "PET", "24 Hz", "cool 4% extra", "PWR next densify", "pm_op", "cl_pm", "dk_lab", 11),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4155, s)
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
