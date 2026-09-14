#!/usr/bin/env python3
"""MAC mill r4039+. Unique compound-semiconductor/passive plants."""
from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

_b = SourceFileLoader("mac3205m", str(REPO / "experiments/mac-mill-r3205.py")).load_module()
A = _b.A
build_record = _b.build_record
notes_text = _b.notes_text
busy = _b.busy

FACTORY = REPO / "outputs/raw/2026-08-19-agentic/multi-agent-coordination-factory"
SBOX = REPO / "outputs/raw/2026-08-19-agentic/sandbox-refusal-factory"
DEADLINE_S = 6 * 60 * 60
BANNED_SUB = ("capro-oxime-vs-beckmann", "whiskey-barrel", "hearts-vs-tails", "whiskey")

SCENARIOS = [
    A("sic-wafer-vs-micropipe", "SiC", "MPD", "1.8 /cm2", "0.4 /cm2", "0.42 /cm2", "8 K", "pipe", "growth +4%", 12, 1, "boule", "4H", "2.4 /cm2", "growth 4% extra", "GaN-on-Si vs bow", "sic_op", "gr_sic", "mpd_lab", 48),
    A("gan-on-si-vs-bow", "GaN/Si", "bow", "82 µm", "40 µm", "41 µm", "6 K", "crack", "buffer +4%", 10, 1, "wafer", "HEMT", "110 µm", "buffer 4% extra", "sapphire C vs disloc", "gan_op", "bf_gan", "bw_gan", 47),
    A("sapphire-c-vs-disloc", "sapphire", "EPD", "1.8e5", "5e4", "5.2e4", "8 K", "EPD", "pull +4%", 12, 1, "boule", "c-plane", "3e5", "pull 4% extra", "SiC epitaxy vs doping", "sa_op", "pl_sa", "epd_lab", 46),
    A("sic-epitaxy-vs-doping", "SiC epi", "Nd", "1.8e16", "1.0e16", "1.02e16", "6 K", "dope", "C/Si +4%", 10, 1, "wafer", "MOSFET", "2.4e16", "C/Si 4% extra", "GaN epitaxy vs pit2", "epi_op", "cs_epi", "nd_lab", 45),
    A("gan-epitaxy-vs-pit2", "GaN epi", "pit", "8e6", "2e6", "2.1e6", "6 K", "pit", "NH3 +4%", 9, 1, "wafer", "LED", "1.2e7", "NH3 4% extra", "InGaN MQW vs PL", "ge_op", "nh_ge", "pit_ge", 44),
    A("ingan-mqw-vs-pl", "MQW", "PL", "18 nm", "8 nm", "8.2 nm", "5 K", "FWHM", "T -4%", 8, 1, "wafer", "blue", "24 nm", "T 4% extra", "AlN buffer vs crack", "mq_op", "t_mq", "pl_lab", 43),
    A("aln-buffer-vs-crack", "AlN", "crack", "18 /cm", "4 /cm", "4.2 /cm", "8 K", "crack", "T +4%", 10, 1, "wafer", "UV", "24 /cm", "T 4% extra", "SiC implant vs act", "aln_op", "t_aln", "cr_aln", 42),
    A("sic-implant-vs-act", "implant", "Rs", "180 Ω", "80 Ω", "82 Ω", "6 K", "act", "anneal +4%", 9, 1, "wafer", "SBD", "240 Ω", "anneal 4% extra", "GaN ohm vs contact", "im_op", "an_im", "rs_lab", 41),
    A("gan-ohm-vs-contact", "ohmic", "Rc", "1.8 Ωmm", "0.4 Ωmm", "0.42 Ωmm", "5 K", "Rc", "alloy +4%", 8, 1, "wafer", "HEMT", "2.4 Ωmm", "alloy 4% extra", "SiC Schottky vs barrier", "oh_op", "al_oh", "rc_lab", 40),
    A("sic-schottky-vs-barrier", "SBD", "phiB", "1.18 eV", "1.40 eV", "1.38 eV", "5 K", "leak", "metal +4%", 8, 1, "wafer", "600V", "1.05 eV", "metal 4% extra", "GaN HEMT vs current", "sbd_op", "mt_sbd", "ph_lab", 39),
    A("gan-hemts-vs-current", "HEMT", "Idss", "0.42 A/mm", "0.80 A/mm", "0.78 A/mm", "5 K", "collapse", "pass +4%", 8, 1, "wafer", "RF", "0.30 A/mm", "pass 4% extra", "SiC MOSFET vs Vth", "he_op", "ps_he", "id_lab", 38),
    A("sic-mosfet-vs-vth", "MOSFET", "Vth", "1.8 V", "2.8 V", "2.76 V", "6 K", "Vth", "ox +4%", 9, 1, "wafer", "1200V", "1.2 V", "ox 4% extra", "InGaN LED vs EQE", "mf_op", "ox_mf", "vth_lab", 37),
    A("ingan-led-vs-eqe", "LED", "EQE", "28%", "42%", "41.6%", "5 K", "droop", "barrier +4%", 8, 1, "wafer", "white", "22%", "barrier 4% extra", "AlN UV vs EQE", "led_op", "br_led", "eqe_lab", 36),
    A("aln-uv-vs-eqe", "UV LED", "EQE", "4.2%", "8.0%", "7.9%", "6 K", "EQE", "TDD -4%", 9, 1, "wafer", "UVC", "2.8%", "TDD 4% extra", "GaN laser vs threshold", "uv_op", "td_uv", "eqe_uv", 35),
    A("gan-laser-vs-threshold", "LD", "Ith", "42 mA", "22 mA", "22.4 mA", "5 K", "Ith", "facet +4%", 8, 1, "bar", "blue", "55 mA", "facet 4% extra", "SiC PiN vs leak", "ld_op", "fc_ld", "ith_lab", 34),
    A("sic-pin-vs-leak", "PiN", "leak", "18 µA", "4 µA", "4.2 µA", "6 K", "leak", "term +4%", 8, 1, "wafer", "3kV", "24 µA", "term 4% extra", "GaN RF vs fT", "pin_op", "tm_pin", "lk_pin", 33),
    A("gan-rf-vs-ft", "RF", "fT", "42 GHz", "80 GHz", "78 GHz", "5 K", "fT", "Lg -4%", 8, 1, "wafer", "mmW", "32 GHz", "Lg 4% extra", "SiC JFET vs Rdson", "rf_op", "lg_rf", "ft_lab", 32),
    A("sic-jfet-vs-rdson", "JFET", "Rdson", "18 mΩ", "8 mΩ", "8.2 mΩ", "6 K", "Rdson", "epi +4%", 9, 1, "wafer", "1kV", "24 mΩ", "epi 4% extra", "InGaN microLED vs EQE", "jf_op", "ep_jf", "rd_lab", 31),
    A("ingan-microled-vs-eqe", "µLED", "EQE", "8.4%", "18%", "17.6%", "5 K", "sidewall", "pass +4%", 8, 1, "wafer", "display", "6%", "pass 4% extra", "AlN SAW vs kt2", "ul_op", "ps_ul", "eqe_ul", 30),
    A("aln-saw-vs-kt2", "SAW", "kt2", "4.2%", "6.5%", "6.4%", "4 K", "kt2", "AlN +4%", 8, 1, "wafer", "RF", "3.2%", "AlN 4% extra", "LTCC shrink vs camber", "sw_op", "aln_sw", "kt_lab", 29),
    A("ltcc-shrink-vs-camber", "LTCC", "camber", "82 µm", "30 µm", "31 µm", "6 K", "camber", "profile +4%", 10, 1, "tape", "module", "110 µm", "profile 4% extra", "HTCC shrink vs density", "lt_op", "pr_lt", "cm_lab", 28),
    A("htcc-shrink-vs-density", "HTCC", "density", "92%", "97%", "96.8%", "8 K", "void", "sinter +4%", 12, 1, "tape", "package", "88%", "sinter 4% extra", "DPC copper vs peel", "ht_op", "sn_ht", "dn_ht", 27),
    A("dpc-copper-vs-peel", "DPC", "peel", "8.4 N/cm", "14 N/cm", "13.8 N/cm", "5 K", "peel", "seed +4%", 8, 1, "sub", "power", "6 N/cm", "seed 4% extra", "DBC void vs solder", "dpc_op", "sd_dpc", "pl_dpc", 26),
    A("dbc-void-vs-solder", "DBC", "void", "8.4%", "2.0%", "2.1%", "6 K", "void", "profile +4%", 9, 1, "sub", "IGBT", "11%", "profile 4% extra", "AMB bond vs void", "dbc_op", "pr_dbc", "vd_dbc", 25),
    A("amb-bond-vs-void", "AMB", "void", "4.8%", "1.0%", "1.05%", "6 K", "void", "Ag +4%", 9, 1, "sub", "SiC", "6.0%", "Ag 4% extra", "IMS thermal vs copper", "amb_op", "ag_amb", "vd_amb", 24),
    A("ims-thermal-vs-copper", "IMS", "Rth", "1.8 K/W", "0.8 K/W", "0.82 K/W", "5 K", "Rth", "Cu +4%", 8, 1, "board", "LED", "2.4 K/W", "Cu 4% extra", "ceramic via vs fill", "ims_op", "cu_ims", "rth_lab", 23),
    A("ceramic-via-vs-fill", "via", "void", "8.4%", "2.0%", "2.1%", "5 K", "void", "fill +4%", 8, 1, "tape", "LTCC", "11%", "fill 4% extra", "LTCC via vs resist", "cv_op", "fl_cv", "vd_cv", 22),
    A("ltcc-via-vs-resist", "via", "R", "18 mΩ", "6 mΩ", "6.2 mΩ", "5 K", "R", "fill +4%", 8, 1, "tape", "RF", "24 mΩ", "fill 4% extra", "MLCC ESL vs ESR", "lv_op", "fl_lv", "r_lv", 21),
    A("mlcc-esl-vs-esr", "MLCC", "ESR", "18 mΩ", "6 mΩ", "6.2 mΩ", "4 K", "ESR", "Ni +4%", 7, 1, "lot", "X7R", "24 mΩ", "Ni 4% extra", "tantalum CV vs leak", "ml_op", "ni_ml", "esr_lab", 20),
    A("tantalum-cv-vs-leak", "Ta", "leak", "1.8 µA", "0.4 µA", "0.42 µA", "5 K", "leak", "form +4%", 8, 1, "lot", "MnO2", "2.4 µA", "form 4% extra", "Al cap vs ESR", "ta_op", "fm_ta", "lk_ta", 19),
    A("al-cap-vs-esr", "Al-e", "ESR", "82 mΩ", "28 mΩ", "28.4 mΩ", "4 K", "ESR", "foil +4%", 7, 1, "lot", "low-ESR", "110 mΩ", "foil 4% extra", "supercap ESR vs life", "al_op", "fl_al", "esr_al", 18),
    A("supercap-esr-vs-life", "EDLC", "ESR", "18 mΩ", "8 mΩ", "8.2 mΩ", "4 K", "ESR", "carbon +4%", 8, 1, "lot", "module", "24 mΩ", "carbon 4% extra", "film cap vs DF", "sc_op", "c_sc", "esr_sc", 17),
    A("film-cap-vs-df", "film", "DF", "0.42%", "0.10%", "0.11%", "4 K", "DF", "dry +4%", 8, 1, "lot", "PP", "0.55%", "dry 4% extra", "mica cap vs Q", "fm_op", "dr_fm", "df_lab", 16),
    A("mica-cap-vs-q", "mica", "Q", "820", "1400", "1380", "4 K", "Q", "silver +4%", 8, 1, "lot", "RF", "600", "silver 4% extra", "ceramic trim vs TC", "mc_op", "ag_mc", "q_lab", 15),
    A("ceramic-trim-vs-tc", "trimmer", "TC", "180 ppm", "50 ppm", "52 ppm", "3 K", "TC", "ceramic +4%", 7, 1, "lot", "VHF", "240 ppm", "ceramic 4% extra", "varactor C vs V", "tr_op", "cr_tr", "tc_lab", 14),
    A("varactor-c-vs-v", "varactor", "Cmax/Cmin", "4.2", "8.0", "7.9", "4 K", "tune", "epi +4%", 8, 1, "wafer", "VCO", "3.2", "epi 4% extra", "ferrite mu vs loss", "vr_op", "ep_vr", "cv_lab", 13),
    A("ferrite-mu-vs-loss", "ferrite", "tanδ", "8.4e-3", "2e-3", "2.1e-3", "6 K", "loss", "sinter +4%", 9, 1, "core", "MnZn", "1.1e-2", "sinter 4% extra", "powder core vs Bmax", "fe_op", "sn_fe", "td_lab", 12),
    A("powder-core-vs-bmax", "powder", "Bsat", "0.82 T", "1.20 T", "1.18 T", "5 K", "sat", "Fe +4%", 8, 1, "core", "PFC", "0.70 T", "Fe 4% extra", "nanocry vs loss", "pw_op", "fe_pw", "bs_lab", 11),
    A("nanocry-vs-loss", "nanocrystal", "Pcv", "180 kW/m3", "80 kW/m3", "82 kW/m3", "6 K", "loss", "anneal +4%", 9, 1, "core", "CMC", "240 kW/m3", "anneal 4% extra", "amorphous vs Bsat", "nc_op", "an_nc", "pcv_lab", 10),
    A("amorphous-vs-bsat", "amorphous", "Bsat", "1.18 T", "1.56 T", "1.54 T", "6 K", "Bsat", "anneal +4%", 9, 1, "core", "cut", "1.05 T", "anneal 4% extra", "NdFeB Br vs Hcj", "am_op", "an_am", "bs_am", 9),
    A("ndfeb-br-vs-hcj", "NdFeB", "Hcj", "18 kOe", "25 kOe", "24.6 kOe", "6 K", "Hcj", "Dy +4%", 9, 1, "block", "N48SH", "14 kOe", "Dy 4% extra", "SmCo Br vs temp", "nd_op", "dy_nd", "hcj_lab", 8),
    A("smco-br-vs-temp", "SmCo", "Br", "10.4 kG", "11.2 kG", "11.15 kG", "6 K", "Br", "sinter +4%", 9, 1, "block", "2:17", "9.8 kG", "sinter 4% extra", "ferrite magnet vs Br", "sm_op", "sn_sm", "br_sm", 7),
    A("ferrite-magnet-vs-br", "ferrite mag", "Br", "3.8 kG", "4.4 kG", "4.38 kG", "8 K", "Br", "sinter +4%", 10, 1, "block", "Y30", "3.4 kG", "sinter 4% extra", "Alnico Br vs Hc", "fm_op", "sn_fm", "br_fm", 6),
    A("alnico-br-vs-hc", "Alnico", "Hc", "620 Oe", "780 Oe", "775 Oe", "7 K", "Hc", "field +4%", 9, 1, "cast", "Alnico-5", "540 Oe", "field 4% extra", "SiC next densify", "al_op", "fd_al", "hc_al", 5),
]


def self_check() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    for s in SCENARIOS:
        if any(b in s["slug"] for b in BANNED_SUB):
            raise SystemExit(s["slug"])
        rec = build_record(4039, s)
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
        except round_txn.TransactionError as ext:
            print(f"PUBLISH FAIL r{n}: {ext}", flush=True)
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
