#!/usr/bin/env python3
"""MAC mill r4083+. Unique photonics/sensing plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205n", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("edfa-nf-vs-gain", "EDFA", "NF", "6.2 dB", "4.5 dB", "4.55 dB", "3 K", "NF", "pump +4%", 7, 1, "amp", "C-band", "7.0 dB", "pump 4% extra", "Raman onoff vs gain", "ed_op", "pm_ed", "nf_lab", 46),
    A("raman-onoff-vs-gain", "Raman", "onoff", "8.4 dB", "14 dB", "13.8 dB", "3 K", "gain", "pump +4%", 7, 1, "span", "L-band", "6 dB", "pump 4% extra", "DCF CD vs PMD", "rm_op", "pm_rm", "oo_lab", 45),
    A("dcf-cd-vs-pmd", "DCF", "PMD", "0.42 ps", "0.15 ps", "0.16 ps", "2 K", "PMD", "spool +4%", 6, 1, "module", "10G", "0.55 ps", "spool 4% extra", "WDM crosstalk vs isolation", "dc_op", "sp_dc", "pmd_lab", 44),
    A("wdm-crosstalk-vs-isolation", "WDM", "XT", "18 dB", "28 dB", "27.6 dB", "2 K", "XT", "filter +4%", 6, 1, "mux", "40ch", "14 dB", "filter 4% extra", "ROADM IL vs WSS", "wd_op", "fl_wd", "xt_lab", 43),
    A("roadm-il-vs-wss", "ROADM", "IL", "8.4 dB", "5.0 dB", "5.1 dB", "2 K", "IL", "WSS +4%", 6, 1, "node", "CDC", "11 dB", "WSS 4% extra", "OCM OSNR vs res", "rd_op", "ws_rd", "il_rd", 42),
    A("ocm-osnr-vs-res", "OCM", "res", "18 GHz", "6.25 GHz", "6.4 GHz", "1 K", "OSNR", "RBW +4%", 5, 1, "port", "flexgrid", "25 GHz", "RBW 4% extra", "OTDR event vs dead", "oc_op", "rb_oc", "res_lab", 41),
    A("otdr-event-vs-dead", "OTDR", "dead", "8.4 m", "3.0 m", "3.1 m", "1 K", "dead", "pulse -4%", 5, 1, "span", "access", "12 m", "pulse 4% extra", "OPLM power vs cal", "ot_op", "pl_ot", "dd_lab", 40),
    A("oplm-power-vs-cal", "OPM", "err", "0.42 dB", "0.10 dB", "0.11 dB", "1 K", "cal", "ref +4%", 5, 1, "port", "line", "0.55 dB", "ref 4% extra", "transceiver BER vs Rx", "op_op", "rf_op", "er_lab", 39),
    A("transceiver-ber-vs-rx", "QSFP", "BER", "1.8e-6", "1e-12", "1.2e-12", "2 K", "BER", "Rx +4%", 6, 1, "port", "100G", "1e-5", "Rx 4% extra", "DWDM tunable vs lock", "qs_op", "rx_qs", "ber_lab", 38),
    A("dwdm-tunable-vs-lock", "tunable", "lock", "fail", "lock", "lock", "2 K", "unlock", "TEC +4%", 6, 1, "ITLA", "C-band", "fail", "TEC 4% extra", "CWDM mux vs IL", "tu_op", "tec_tu", "lk_tu", 37),
    A("cwdm-mux-vs-il", "CWDM", "IL", "2.8 dB", "1.2 dB", "1.22 dB", "2 K", "IL", "align +4%", 6, 1, "mux", "8ch", "3.5 dB", "align 4% extra", "PON splitter vs IL", "cw_op", "al_cw", "il_cw", 36),
    A("pon-splitter-vs-il", "1x32", "IL", "18.4 dB", "16.5 dB", "16.6 dB", "1 K", "IL", "fuse +4%", 5, 1, "PLC", "GPON", "19.5 dB", "fuse 4% extra", "circulator isolation vs IL", "pn_op", "fs_pn", "il_pn", 35),
    A("circulator-isolation-vs-il", "circ", "iso", "32 dB", "45 dB", "44.6 dB", "2 K", "iso", "align +4%", 6, 1, "3-port", "EDFA", "28 dB", "align 4% extra", "isolator isolation vs PMD", "ci_op", "al_ci", "iso_ci", 34),
    A("isolator-isolation-vs-pmd", "ISO", "PMD", "0.18 ps", "0.05 ps", "0.052 ps", "2 K", "PMD", "crystal +4%", 6, 1, "inline", "pump", "0.28 ps", "crystal 4% extra", "coupler split vs PDL", "iso_op", "cr_iso", "pmd_iso", 33),
    A("coupler-split-vs-pdl", "FBT", "PDL", "0.42 dB", "0.10 dB", "0.11 dB", "2 K", "PDL", "pull +4%", 6, 1, "2x2", "monitor", "0.55 dB", "pull 4% extra", "attenuator vs PDL", "cp_op", "pl_cp", "pdl_cp", 32),
    A("attenuator-vs-pdl", "VOA", "PDL", "0.28 dB", "0.08 dB", "0.082 dB", "2 K", "PDL", "align +4%", 5, 1, "MEMS", "line", "0.36 dB", "align 4% extra", "fiber laser vs M2", "vo_op", "al_vo", "pdl_vo", 31),
    A("fiber-laser-vs-m2", "fiber LD", "M2", "1.42", "1.10", "1.11", "4 K", "M2", "mode +4%", 7, 1, "kW", "cut", "1.60", "mode 4% extra", "DPSS green vs temp", "fl_op", "md_fl", "m2_lab", 30),
    A("dpss-green-vs-temp", "DPSS", "P", "8.4 W", "12 W", "11.8 W", "4 K", "drop", "TEC +4%", 7, 1, "head", "532", "6 W", "TEC 4% extra", "CO2 laser vs mode", "dp_op", "tec_dp", "p_dp", 29),
    A("co2-laser-vs-mode", "CO2", "M2", "1.8", "1.2", "1.22", "5 K", "mode", "align +4%", 8, 1, "tube", "cut", "2.2", "align 4% extra", "excimer vs energy", "co2_op", "al_co2", "m2_co2", 28),
    A("excimer-vs-energy", "excimer", "mJ", "180 mJ", "250 mJ", "246 mJ", "4 K", "energy", "gas +4%", 8, 1, "cavity", "KrF", "140 mJ", "gas 4% extra", "fiber amp vs ASE", "ex_op", "gs_ex", "mj_lab", 27),
    A("fiber-amp-vs-ase", "YDFA", "ASE", "18 dB", "8 dB", "8.2 dB", "3 K", "ASE", "filter +4%", 7, 1, "amp", "1um", "24 dB", "filter 4% extra", "OPA vs bandwidth", "yd_op", "fl_yd", "ase_lab", 26),
    A("opa-vs-bandwidth", "OPA", "BW", "42 nm", "80 nm", "78 nm", "4 K", "BW", "phase +4%", 8, 1, "xtal", "NIR", "32 nm", "phase 4% extra", "OPO vs idler", "opa_op", "ph_opa", "bw_lab", 25),
    A("opo-vs-idler", "OPO", "idler", "fail", "lock", "lock", "4 K", "unlock", "temp +4%", 7, 1, "cavity", "MIR", "fail", "temp 4% extra", "QCL vs linewidth", "opo_op", "tp_opo", "id_lab", 24),
    A("qcl-vs-linewidth", "QCL", "Δν", "18 MHz", "4 MHz", "4.2 MHz", "3 K", "broad", "current -4%", 6, 1, "chip", "MIR", "24 MHz", "current 4% extra", "lidar range vs SNR", "qc_op", "cu_qc", "lw_lab", 23),
    A("lidar-range-vs-snr", "lidar", "range", "82 m", "140 m", "138 m", "2 K", "SNR", "power +4%", 6, 1, "head", "auto", "60 m", "power 4% extra", "ToF camera vs fill", "ld_op", "pw_ld", "rg_lab", 22),
    A("tof-camera-vs-fill", "ToF", "fill", "62%", "88%", "87%", "2 K", "hole", "exp +4%", 6, 1, "mod", "depth", "50%", "exp 4% extra", "structured light vs pattern", "tf_op", "ex_tf", "fl_tf", 21),
    A("structured-light-vs-pattern", "SL", "rmse", "1.8 mm", "0.4 mm", "0.42 mm", "2 K", "rmse", "pattern +4%", 6, 1, "rig", "scan", "2.4 mm", "pattern 4% extra", "photogram vs RMSE", "sl_op", "pt_sl", "rmse_sl", 20),
    A("photogram-vs-rmse", "PGs", "RMSE", "8.4 mm", "2.0 mm", "2.1 mm", "1 K", "RMSE", "GCP +4%", 7, 1, "set", "UAV", "11 mm", "GCP 4% extra", "InSAR coherence vs baseline", "pg_op", "gcp_pg", "rmse_pg", 19),
    A("insar-coherence-vs-baseline", "InSAR", "γ", "0.42", "0.70", "0.68", "1 K", "decorr", "Bperp -4%", 7, 1, "pair", "C-band", "0.30", "Bperp 4% extra", "SAR NESZ vs look", "is_op", "bp_is", "g_lab", 18),
    A("sar-nesz-vs-look", "SAR", "NESZ", "-18 dB", "-24 dB", "-23.6 dB", "1 K", "NESZ", "look +4%", 6, 1, "scene", "X-band", "-14 dB", "look 4% extra", "GNSS DOP vs mask", "sr_op", "lk_sr", "nesz_lab", 17),
    A("gnss-dop-vs-mask", "GNSS", "HDOP", "2.8", "1.2", "1.22", "1 K", "DOP", "mask -4%", 5, 1, "rover", "RTK", "3.5", "mask 4% extra", "IMU bias vs temp", "gn_op", "mk_gn", "hdop_lab", 16),
    A("imu-bias-vs-temp", "IMU", "bias", "18 °/h", "4 °/h", "4.2 °/h", "2 K", "bias", "cal +4%", 6, 1, "IMU", "nav", "24 °/h", "cal 4% extra", "encoder jitter vs count", "im_op", "cl_im", "bs_im", 15),
    A("encoder-jitter-vs-count", "enc", "jitter", "0.42 cnt", "0.10 cnt", "0.11 cnt", "1 K", "jitter", "gain +4%", 5, 1, "shaft", "servo", "0.55 cnt", "gain 4% extra", "resolver null vs exc", "en_op", "gn_en", "jt_lab", 14),
    A("resolver-null-vs-exc", "resolver", "null", "18 mV", "4 mV", "4.2 mV", "1 K", "null", "exc +4%", 5, 1, "shaft", "aero", "24 mV", "exc 4% extra", "LVDT linearity vs core", "rs_op", "ex_rs", "nl_lab", 13),
    A("lvdt-linearity-vs-core", "LVDT", "NL", "0.42%", "0.10%", "0.11%", "1 K", "NL", "core +4%", 6, 1, "probe", "gage", "0.55%", "core 4% extra", "strain gage vs temp", "lv_op", "cr_lv", "nl_lv", 12),
    A("strain-gage-vs-temp", "gage", "TC", "18 ppm", "4 ppm", "4.2 ppm", "2 K", "TC", "comp +4%", 6, 1, "foil", "load", "24 ppm", "comp 4% extra", "EDFA next densify", "sg_op", "cp_sg", "tc_sg", 11),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4083, s)
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
