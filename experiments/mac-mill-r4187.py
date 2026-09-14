#!/usr/bin/env python3
"""MAC mill r4187+. Unique space/weather/geodesy plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205q", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("leo-drag-vs-alt", "LEO", "h", "380 km", "410 km", "408 km", "1 K", "drag", "boost +4%", 6, 1, "bus", "SSO", "360 km", "boost 4% extra", "GEO station vs incl", "leo_op", "bst_leo", "h_lab", 40),
    A("geo-station-vs-incl", "GEO", "i", "0.42 °", "0.10 °", "0.11 °", "1 K", "incl", "NS +4%", 6, 1, "bus", "comsat", "0.55 °", "NS 4% extra", "HEO perigee vs drag", "geo_op", "ns_geo", "i_lab", 39),
    A("heo-perigee-vs-drag", "HEO", "hp", "180 km", "400 km", "392 km", "1 K", "drag", "raise +4%", 6, 1, "bus", "Molniya", "140 km", "raise 4% extra", "SSO LTAN vs RAAN", "heo_op", "rs_heo", "hp_lab", 38),
    A("sso-ltan-vs-raan", "SSO", "LTAN", "18 min", "4 min", "4.2 min", "1 K", "LTAN", "RAAN +4%", 6, 1, "bus", "EO", "24 min", "RAAN 4% extra", "reaction wheel vs saturate", "sso_op", "ra_sso", "lt_lab", 37),
    A("reaction-wheel-vs-saturate", "RW", "h", "0.92", "0.60", "0.61", "1 K", "sat", "desat +4%", 6, 1, "bus", "3-axis", "1.05", "desat 4% extra", "CMG gimbal vs sing", "rw_op", "ds_rw", "h_rw", 36),
    A("cmg-gimbal-vs-sing", "CMG", "sing", "fail", "pass", "pass", "1 K", "sing", "steer +4%", 6, 1, "bus", "agile", "fail", "steer 4% extra", "thruster Isp vs mix", "cm_op", "st_cm", "sg_cm", 35),
    A("thruster-isp-vs-mix", "biprop", "Isp", "280 s", "320 s", "318 s", "2 K", "Isp", "mix +4%", 7, 1, "tank", "MMH", "260 s", "mix 4% extra", "ion thruster vs erode", "th_op", "mx_th", "isp_lab", 34),
    A("ion-thruster-vs-erode", "ion", "life", "8200 h", "12000 h", "11800 h", "2 K", "grid", "accel -4%", 7, 1, "XIPS", "Xe", "7000 h", "accel 4% extra", "solar array vs degrad", "ion_op", "ac_ion", "lf_ion", 33),
    A("solar-array-vs-degrad", "array", "P", "82%", "94%", "93.6%", "2 K", "degrad", "anneal +4%", 7, 1, "wing", "GaAs", "74%", "anneal 4% extra", "battery DOD vs life", "sa_op", "an_sa", "p_sa", 32),
    A("battery-dod-vs-life", "Li-ion", "DOD", "42%", "25%", "25.4%", "2 K", "life", "DOD -4%", 7, 1, "pack", "GEO", "50%", "DOD 4% extra", "star tracker vs stray", "bt_op", "dd_bt", "dod_lab", 31),
    A("star-tracker-vs-stray", "ST", "lost", "18 /d", "2 /d", "2.2 /d", "1 K", "stray", "baffle +4%", 6, 1, "head", "att", "24 /d", "baffle 4% extra", "IMU gyro vs ARW", "st_op", "bf_st", "ls_st", 30),
    A("imu-gyro-vs-arw", "gyro", "ARW", "0.18 °/√h", "0.04 °/√h", "0.042 °/√h", "1 K", "ARW", "cal +4%", 6, 1, "IMU", "nav", "0.28 °/√h", "cal 4% extra", "antenna point vs EPD", "im_op", "cl_im", "arw_lab", 29),
    A("antenna-point-vs-epd", "HGA", "EPD", "0.42 °", "0.10 °", "0.11 °", "1 K", "EPD", "track +4%", 6, 1, "boom", "Ka", "0.55 °", "track 4% extra", "TTC link vs Eb/N0", "an_op", "tk_an", "epd_lab", 28),
    A("ttc-link-vs-ebno", "TTC", "Eb/N0", "4.2 dB", "8.0 dB", "7.9 dB", "1 K", "link", "power +4%", 6, 1, "S-band", "LEOP", "3.0 dB", "power 4% extra", "payload temp vs heater", "tt_op", "pw_tt", "eb_lab", 27),
    A("payload-temp-vs-heater", "payload", "T", "18 C", "8 C", "8.2 C", "2 K", "hot", "heater -4%", 6, 1, "bay", "IR", "24 C", "heater 4% extra", "prop tank vs PMD", "pl_op", "ht_pl", "t_pl", 26),
    A("prop-tank-vs-pmd", "tank", "ullage", "18%", "6%", "6.2%", "1 K", "gas", "PMD +4%", 6, 1, "tank", "blowdown", "24%", "PMD 4% extra", "weather radar vs clutter2", "pr_op", "pmd_pr", "ul_lab", 25),
    A("weather-radar-vs-clutter2", "WSR", "clutter", "18 dBZ", "6 dBZ", "6.2 dBZ", "1 K", "clutter", "filter +4%", 6, 1, "volume", "S-band", "24 dBZ", "filter 4% extra", "lidar ceilom vs cloud", "wx_op", "fl_wx", "cl_wx", 24),
    A("lidar-ceilom-vs-cloud", "ceilom", "base", "180 m", "80 m", "82 m", "1 K", "miss", "SNR +4%", 6, 1, "site", "ASOS", "240 m", "SNR 4% extra", "sodar vs inversion", "cl_op", "sn_cl", "bs_lab", 23),
    A("sodar-vs-inversion", "SODAR", "zi", "180 m", "400 m", "392 m", "1 K", "zi", "pulse +4%", 6, 1, "site", "PBL", "140 m", "pulse 4% extra", "radiosonde vs burst", "sd_op", "pl_sd", "zi_lab", 22),
    A("radiosonde-vs-burst", "sonde", "burst", "18 km", "28 km", "27.6 km", "1 K", "burst", "fill +4%", 6, 1, "balloon", "00Z", "14 km", "fill 4% extra", "ASCAT vs wind", "rs_op", "fl_rs", "br_rs", 21),
    A("ascat-vs-wind", "ASCAT", "spd", "1.8 m/s", "0.6 m/s", "0.62 m/s", "1 K", "bias", "GMF +4%", 6, 1, "swath", "C-band", "2.4 m/s", "GMF 4% extra", "AMSR vs SST", "as_op", "gmf_as", "sp_as", 20),
    A("amsr-vs-sst", "AMSR", "SST", "0.42 K", "0.15 K", "0.16 K", "1 K", "SST", "cal +4%", 6, 1, "scan", "C-band", "0.55 K", "cal 4% extra", "GOES vs IR", "am_op", "cl_am", "sst_lab", 19),
    A("goes-vs-ir", "GOES", "IR", "1.8 K", "0.5 K", "0.52 K", "1 K", "IR", "bb +4%", 6, 1, "ABI", "IR", "2.4 K", "bb 4% extra", "MODIS vs AOD", "go_op", "bb_go", "ir_go", 18),
    A("modis-vs-aod", "MODIS", "AOD", "0.18", "0.05", "0.052", "1 K", "AOD", "DT +4%", 6, 1, "granule", "ocean", "0.24", "DT 4% extra", "seismo vs SNR", "md_op", "dt_md", "aod_lab", 17),
    A("seismo-vs-snr", "seismo", "SNR", "8.4", "18", "17.6", "1 K", "noise", "vault +4%", 6, 1, "vault", "BB", "6", "vault 4% extra", "gravimeter vs drift", "sz_op", "vt_sz", "snr_sz", 16),
    A("gravimeter-vs-drift", "grav", "drift", "18 µGal/d", "4 µGal/d", "4.2 µGal/d", "1 K", "drift", "cal +4%", 6, 1, "pier", "AG", "24 µGal/d", "cal 4% extra", "magnetom vs diurnal", "gv_op", "cl_gv", "dr_gv", 15),
    A("magnetom-vs-diurnal", "mag", "diurnal", "18 nT", "4 nT", "4.2 nT", "1 K", "diurnal", "base +4%", 6, 1, "station", "F", "24 nT", "base 4% extra", "tide gauge vs datum", "mg_op", "bs_mg", "dn_lab", 14),
    A("tide-gauge-vs-datum", "tide", "datum", "18 mm", "4 mm", "4.2 mm", "1 K", "datum", "GNSS +4%", 6, 1, "still", "MSL", "24 mm", "GNSS 4% extra", "GNSS PWV vs ZTD", "tg_op", "gn_tg", "dt_lab", 13),
    A("gnss-pwv-vs-ztd", "GNSS", "PWV", "1.8 mm", "0.5 mm", "0.52 mm", "1 K", "PWV", "ZTD +4%", 6, 1, "CORS", "met", "2.4 mm", "ZTD 4% extra", "InSAR vs atm", "gn_op", "ztd_gn", "pwv_lab", 12),
    A("insar-vs-atm", "InSAR", "atm", "18 mm", "4 mm", "4.2 mm", "1 K", "atm", "GACOS +4%", 6, 1, "pair", "C-band", "24 mm", "GACOS 4% extra", "CORS vs multipath", "is_op", "gc_is", "atm_lab", 11),
    A("cors-vs-multipath", "CORS", "MP", "18 mm", "4 mm", "4.2 mm", "1 K", "MP", "choke +4%", 6, 1, "site", "IGS", "24 mm", "choke 4% extra", "VLBI vs clock", "cr_op", "ck_cr", "mp_cr", 10),
    A("vlbi-vs-clock", "VLBI", "clock", "18 ps", "4 ps", "4.2 ps", "1 K", "clock", "H-maser +4%", 6, 1, "station", "IVS", "24 ps", "maser 4% extra", "LEO next densify", "vl_op", "hm_vl", "cl_vl", 9),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4187, s)
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
