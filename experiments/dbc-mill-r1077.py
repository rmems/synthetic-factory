#!/usr/bin/env python3
"""Mill docker-build-cache-factory r1077+. DB engines × I2C/SPI/WDT leftovers.

NEW unique-pair catalog after r1029 compilers/ALSA.
BAN prior DBC catalogs, r645 nerdctl, r549 scsh/scsi, GNU Prolog/landlock/
SWI pack/seccomp/AppArmor/GOTOOLCHAIN, harbor-pin, leftover×sysctl.
17+18 steps. meta.generator=grok-4.6.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("dbc_mill_r1029", HERE / "dbc-mill-r1029.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
lang = _m.lang
leftover = _m.leftover
success_episode = _m.success_episode
leftover_episode = _m.leftover_episode
notes_for = _m.notes_for
slug_taken = _m.slug_taken
BANNED_NEEDLES = _m.BANNED_NEEDLES + (
    "odin-lang-cache",
    "snd-hda-intel-leftover",
    "duckdb-httpfs-cache",
    "i2c-i801-leftover",
)

# slug, env, tool, old, new, artifact, mb
_CRYPTO = [
    ("pinocchio-cache", "PINOCCHIO_HOME", "pinocchio", "2.7.0", "3.4.0", "include/pinocchio/fwd.hpp", "11MB"),
    ("dart-sim-cache", "DART_HOME", "dart", "6.13.2", "6.15.0", "include/dart/dart.hpp", "14MB"),
    ("crocoddyl-cache", "CROCODDYL_HOME", "crocoddyl", "2.0.2", "2.1.0", "include/crocoddyl/core/fwd.hpp", "8MB"),
    ("tsid-cache", "TSID_HOME", "tsid", "1.7.1", "1.8.0", "include/tsid/robots/robot-wrapper.hpp", "5MB"),
    ("hpp-fcl-cache", "HPP_FCL_HOME", "hpp-fcl", "2.4.4", "2.4.5", "include/hpp/fcl/fwd.hh", "6MB"),
    ("coal-cache", "COAL_HOME", "coal", "3.0.0", "3.0.1", "include/coal/fwd.hh", "6MB"),
    ("eiquadprog-cache", "EIQUADPROG_HOME", "eiquadprog", "1.2.8", "1.2.9", "include/eiquadprog/eiquadprog.hpp", "1MB"),
    ("proxsuite-cache", "PROXSUITE_HOME", "proxsuite", "0.6.6", "0.7.2", "include/proxsuite/proxqp/dense/wrapper.hpp", "4MB"),
    ("osqp-eigen-cache", "OSQP_EIGEN_HOME", "OsqpEigen", "0.8.1", "0.10.0", "include/OsqpEigen/OsqpEigen.h", "2MB"),
    ("rbdl-cache", "RBDL_HOME", "rbdl", "3.3.1", "3.3.1-post", "include/rbdl/rbdl.h", "3MB"),
    ("hpp-core-cache", "HPP_CORE_HOME", "hpp-core", "5.1.0", "6.0.0", "include/hpp/core/fwd.hh", "7MB"),
    ("casadi-cache", "CASADI_HOME", "casadi", "3.6.5", "3.6.7", "include/casadi/casadi.hpp", "12MB"),
    ("acados-cache", "ACADOS_SOURCE_DIR", "acados", "0.3.5", "0.4.1", "include/acados/ocp_nlp.h", "9MB"),
    ("hpipm-cache", "HPIPM_HOME", "hpipm", "0.1.3", "0.1.3-post", "include/hpipm_d_ocp_qp.h", "3MB"),
    ("blasfeo-cache", "BLASFEO_PATH", "blasfeo", "0.1.3", "0.1.3-post", "include/blasfeo_target.h", "2MB"),
    ("fatrop-cache", "FATROP_HOME", "fatrop", "0.0.3", "0.0.4", "include/fatrop/ocp/OcpSolver.hpp", "4MB"),
    ("ipopt-cache", "IPOPT_HOME", "ipopt", "3.14.16", "3.14.17", "include/coin-or/IpIpoptApplication.hpp", "7MB"),
    ("knitro-cache", "KNITRODIR", "knitro", "14.0.0", "14.2.0", "include/knitro.h", "15MB"),
    ("mosek-cache", "MOSEKLM_LICENSE_FILE", "mosek", "10.1.28", "11.0.20", "include/mosek.h", "18MB"),
    ("gurobi-cache", "GUROBI_HOME", "gurobi_cl", "11.0.2", "12.0.1", "include/gurobi_c.h", "16MB"),
    ("cplex-cache", "CPLEX_STUDIO_DIR", "cplex", "22.1.1", "22.1.2", "include/ilcplex/cplex.h", "22MB"),
    ("highs-cache", "HIGHS_HOME", "highs", "1.7.1", "1.8.1", "include/Highs.h", "5MB"),
    ("scip-cache", "SCIP_HOME", "scip", "9.1.0", "9.2.0", "include/scip/scip.h", "10MB"),
    ("soplex-cache", "SOPLEX_HOME", "soplex", "7.1.0", "7.1.1", "include/soplex.h", "4MB"),
    ("clp-cache", "CLP_HOME", "clp", "1.17.9", "1.17.10", "include/coin/ClpSimplex.hpp", "3MB"),
    ("cbc-cache", "CBC_HOME", "cbc", "2.10.11", "2.10.12", "include/coin/CbcModel.hpp", "4MB"),
    ("symphony-cache", "SYMPHONY_HOME", "symphony", "5.6.19", "5.6.20", "include/symphony.h", "3MB"),
    ("cgl-cache", "CGL_HOME", "cgl", "0.60.8", "0.60.9", "include/coin/CglCutGenerator.hpp", "2MB"),
    ("osi-cache", "OSI_HOME", "osi", "0.108.10", "0.108.11", "include/coin/OsiSolverInterface.hpp", "2MB"),
    ("coinutils-cache", "COINUTILS_HOME", "CoinUtils", "2.11.10", "2.11.11", "include/coin/CoinPackedMatrix.hpp", "2MB"),
    ("alps-cache", "ALPS_HOME", "alps", "1.5.11", "1.5.12", "include/Alps.h", "2MB"),
    ("bcp-cache", "BCP_HOME", "bcp", "1.4.4", "1.4.5", "include/BCP_lp.hpp", "3MB"),
    ("cgcg-cache", "CGCG_HOME", "cgcg", "3.0.0", "3.0.1", "include/cgcg/gcg.h", "4MB"),
    ("papilo-cache", "PAPILO_HOME", "papilo", "2.3.0", "2.4.0", "include/papilo/core/Problem.hpp", "3MB"),
    ("zimpl-cache", "ZIMPL_HOME", "zimpl", "3.6.1", "3.6.2", "include/zimpl/zimpl.h", "1MB"),
    ("gams-cache", "GAMS_HOME", "gams", "46.4.0", "47.1.0", "share/gams/gamsconfig.yaml", "28MB"),
    ("ampl-cache", "AMPL_HOME", "ampl", "20240315", "20250110", "share/ampl/ampl.lic", "9MB"),
    ("pulp-cache", "PULP_CBC_PATH", "pulptest", "2.8.0", "2.9.0", "lib/python3/dist-packages/pulp/solverdir", "3MB"),
    ("pyomo-cache", "PYOMO_HOME", "pyomo", "6.7.3", "6.8.2", "lib/python3/dist-packages/pyomo/solvers", "8MB"),
    ("cvxpy-cache", "CVXPY_HOME", "python3", "1.5.2", "1.6.0", "lib/python3/dist-packages/cvxpy/reductions", "5MB"),
    ("cvxopt-cache", "CVXOPT_HOME", "python3", "1.3.2", "1.3.2-post", "lib/python3/dist-packages/cvxopt/base.so", "3MB"),
    ("scs-cache", "SCS_HOME", "python3", "3.2.6", "3.2.7", "lib/python3/dist-packages/scs/_scs.so", "2MB"),
    ("ecos-cache", "ECOS_HOME", "python3", "2.0.14", "2.0.14-post", "lib/python3/dist-packages/ecos/_ecos.so", "1MB"),
    ("osqp-cache", "OSQP_HOME", "osqp", "0.6.3", "1.0.0", "include/osqp/osqp.h", "2MB"),
    ("qdldl-cache", "QDLDL_HOME", "qdldl", "0.1.7", "0.1.8", "include/qdldl.h", "1MB"),
    ("amd-sparse-cache", "AMD_HOME", "amd", "3.3.2", "3.3.3", "include/amd.h", "1MB"),
    ("cholmod-cache", "CHOLMOD_HOME", "cholmod", "5.2.1", "5.3.0", "include/cholmod.h", "4MB"),
    ("umfpack-cache", "UMFPACK_HOME", "umfpack", "6.3.3", "6.3.5", "include/umfpack.h", "3MB"),
]

_GPIO = [
    ("rc-core-leftover", "RC_CORE_CLEAR", "rc_core protocols=cache", "rc_core", "ls /sys/class/rc"),
    ("lirc-dev-leftover", "LIRC_DEV_CLEAR", "lirc_dev debug=1", "lirc_dev", "ls /dev/lirc*"),
    ("ir-kbd-i2c-leftover", "IR_KBD_I2C_CLEAR", "ir_kbd_i2c debug=1", "ir_kbd_i2c", "ls /sys/class/rc"),
    ("nuvoton-cir-leftover", "NUVOTON_CIR_CLEAR", "nuvoton_cir debug=1", "nuvoton_cir", "ls /sys/class/rc"),
    ("ite-cir-leftover", "ITE_CIR_CLEAR", "ite_cir rx_high_carrier=cache", "ite_cir", "ls /sys/class/rc"),
    ("fintek-cir-leftover", "FINTEK_CIR_CLEAR", "fintek_cir debug=1", "fintek_cir", "ls /sys/class/rc"),
    ("ene-ir-leftover", "ENE_IR_CLEAR", "ene_ir learning=1", "ene_ir", "ls /sys/class/rc"),
    ("gpio-ir-recv-leftover", "GPIO_IR_RECV_CLEAR", "gpio_ir_recv map=cache", "gpio_ir_recv", "ls /sys/class/rc"),
    ("gpio-ir-tx-leftover", "GPIO_IR_TX_CLEAR", "gpio_ir_tx carrier=cache", "gpio_ir_tx", "ls /sys/class/rc"),
    ("pwm-ir-tx-leftover", "PWM_IR_TX_CLEAR", "pwm_ir_tx carrier=cache", "pwm_ir_tx", "ls /sys/class/rc"),
    ("ir-spi-leftover", "IR_SPI_CLEAR", "ir_spi carrier=cache", "ir_spi", "ls /sys/class/rc"),
    ("ir-hix5hd2-leftover", "IR_HIX5HD2_CLEAR", "ir_hix5hd2 protocol=cache", "ir_hix5hd2", "ls /sys/class/rc"),
    ("meson-ir-leftover", "MESON_IR_CLEAR", "meson_ir protocol=cache", "meson_ir", "ls /sys/class/rc"),
    ("sunxi-cir-leftover", "SUNXI_CIR_CLEAR", "sunxi_cir protocol=cache", "sunxi_cir", "ls /sys/class/rc"),
    ("img-ir-leftover", "IMG_IR_CLEAR", "img_ir protocol=cache", "img_ir", "ls /sys/class/rc"),
    ("mtk-cir-leftover", "MTK_CIR_CLEAR", "mtk_cir protocol=cache", "mtk_cir", "ls /sys/class/rc"),
    ("imon-leftover", "IMON_CLEAR", "imon display=cache", "imon", "ls /sys/class/rc"),
    ("mceusb-leftover", "MCEUSB_CLEAR", "mceusb debug=1", "mceusb", "ls /sys/class/rc"),
    ("ati-remote-leftover", "ATI_REMOTE_CLEAR", "ati_remote channel=cache", "ati_remote", "ls /sys/class/rc"),
    ("ati-remote2-leftover", "ATI_REMOTE2_CLEAR", "ati_remote2 mode=cache", "ati_remote2", "ls /sys/class/rc"),
    ("winbond-cir-leftover", "WINBOND_CIR_CLEAR", "winbond_cir rx_carrier=cache", "winbond_cir", "ls /sys/class/rc"),
    ("streamzap-leftover", "STREAMZAP_CLEAR", "streamzap debug=1", "streamzap", "ls /sys/class/rc"),
    ("redrat3-leftover", "REDRAT3_CLEAR", "redrat3 debug=1", "redrat3", "ls /sys/class/rc"),
    ("iguanair-leftover", "IGUANAIR_CLEAR", "iguanair timeout=cache", "iguanair", "ls /sys/class/rc"),
    ("ttusbir-leftover", "TTUSBIR_CLEAR", "ttusbir debug=1", "ttusbir", "ls /sys/class/rc"),
    ("ir-usb-leftover", "IR_USB_CLEAR", "ir_usb debug=1", "ir_usb", "ls /sys/class/rc"),
    ("xbox-remote-leftover", "XBOX_REMOTE_CLEAR", "xbox_remote debug=1", "xbox_remote", "ls /sys/class/rc"),
    ("keyspan-remote-leftover", "KEYSPAN_REMOTE_CLEAR", "keyspan_remote debug=1", "keyspan_remote", "ls /sys/class/rc"),
    ("ati-remote-usb-leftover", "ATI_REMOTE_USB_CLEAR", "ati_remote_usb debug=1", "ati_remote", "ls /sys/class/rc"),
    ("lirc-bt829-leftover", "LIRC_BT829_CLEAR", "lirc_bt829 debug=1", "lirc_bt829", "ls /dev/lirc*"),
    ("lirc-imon-leftover", "LIRC_IMON_CLEAR", "lirc_imon debug=1", "lirc_imon", "ls /dev/lirc*"),
    ("lirc-sasem-leftover", "LIRC_SASEM_CLEAR", "lirc_sasem debug=1", "lirc_sasem", "ls /dev/lirc*"),
    ("lirc-serial-leftover", "LIRC_SERIAL_CLEAR", "lirc_serial debug=1", "lirc_serial", "ls /dev/lirc*"),
    ("lirc-sir-leftover", "LIRC_SIR_CLEAR", "lirc_sir debug=1", "lirc_sir", "ls /dev/lirc*"),
    ("rc-loopback-leftover", "RC_LOOPBACK_CLEAR", "rc_loopback debug=1", "rc_loopback", "ls /sys/class/rc"),
    ("ir-kbd-i2c-haup-leftover", "IR_KBD_HAUP_CLEAR", "ir_kbd_i2c haup=cache", "ir_kbd_i2c", "ls /sys/class/rc"),
    ("ir-rx51-leftover", "IR_RX51_CLEAR", "ir_rx51 carrier=cache", "ir_rx51", "ls /sys/class/rc"),
    ("ir-sanyo-decoder-leftover", "IR_SANYO_CLEAR", "ir_sanyo_decoder proto=cache", "ir_sanyo_decoder", "ls /sys/class/rc"),
    ("ir-sony-decoder-leftover", "IR_SONY_CLEAR", "ir_sony_decoder proto=cache", "ir_sony_decoder", "ls /sys/class/rc"),
    ("ir-nec-decoder-leftover", "IR_NEC_CLEAR", "ir_nec_decoder proto=cache", "ir_nec_decoder", "ls /sys/class/rc"),
    ("ir-rc5-decoder-leftover", "IR_RC5_CLEAR", "ir_rc5_decoder proto=cache", "ir_rc5_decoder", "ls /sys/class/rc"),
    ("ir-rc6-decoder-leftover", "IR_RC6_CLEAR", "ir_rc6_decoder proto=cache", "ir_rc6_decoder", "ls /sys/class/rc"),
    ("ir-jvc-decoder-leftover", "IR_JVC_CLEAR", "ir_jvc_decoder proto=cache", "ir_jvc_decoder", "ls /sys/class/rc"),
    ("ir-sharp-decoder-leftover", "IR_SHARP_CLEAR", "ir_sharp_decoder proto=cache", "ir_sharp_decoder", "ls /sys/class/rc"),
    ("ir-mce-kbd-decoder-leftover", "IR_MCE_KBD_CLEAR", "ir_mce_kbd_decoder proto=cache", "ir_mce_kbd_decoder", "ls /sys/class/rc"),
    ("ir-xmp-decoder-leftover", "IR_XMP_CLEAR", "ir_xmp_decoder proto=cache", "ir_xmp_decoder", "ls /sys/class/rc"),
    ("ir-imon-decoder-leftover", "IR_IMON_DEC_CLEAR", "ir_imon_decoder proto=cache", "ir_imon_decoder", "ls /sys/class/rc"),
    ("ir-spi-tx-leftover", "IR_SPI_TX_CLEAR", "ir_spi_tx carrier=cache", "ir_spi", "ls /sys/class/rc"),
]

def _mk_lang(row: tuple, sib: str) -> dict:
    slug, env, tool, old, new, artifact, mb = row
    leaf = artifact.rsplit("/", 1)[-1]
    parent = artifact.rsplit("/", 1)[0] if "/" in artifact else artifact
    return lang(
        slug, env, tool, old, new, artifact, f"test_{slug.split('-')[0]}.py", "src/demo.c",
        slug.split("-")[0][:8] + "-x",
        f"rm -rf /usr/{parent}" if not parent.startswith("/") else f"rm -rf {parent}",
        f"rm {leaf} does not drop {old} {leaf} under unversioned {env}",
        mb, f"{sib} (unique {slug.split('-')[0]} cache, not prior NGS/astro/speech catalogs)",
        f"{tool} --version", f"{tool} --version",
    )


def _mk_left(row: tuple, sib: str) -> dict:
    slug, token, lefts, module, probe = row
    flag = lefts.split(None, 1)[1] if " " in lefts else lefts
    return leftover(
        slug, token, lefts,
        f"{module} leftover still caches as {flag}",
        f"modprobe -r {module}",
        f"modprobe -r is EBUSY; leftover {flag} still caches",
        f"leftover {module} caching",
        "r coretemp / r nct6775 / cache-admin 403",
        f"r coretemp leftover ({slug} leftover, not coretemp tjmax) / {sib}",
        f"test_{slug.split('-')[0]}.py",
        f"ls /sys/module/{module}; {probe}",
        f"{slug.split('-')[0]} leftover {flag} leftover",
    )


assert len(_CRYPTO) == len(_GPIO) == 48
PAIRS = []
for i, (c, g) in enumerate(zip(_CRYPTO, _GPIO)):
    sib_c = _CRYPTO[(i + 1) % 48][0]
    sib_g = _GPIO[(i + 1) % 48][0]
    PAIRS.append((_mk_lang(c, sib_c), _mk_left(g, sib_g)))


def catalog_selfcheck() -> None:
    seen: set[str] = set()
    for suc, leftp in PAIRS:
        for spec in (suc, leftp):
            slug = spec["slug"]
            if slug in seen:
                raise SystemExit(f"duplicate catalog slug {slug}")
            seen.add(slug)
            ident = " ".join(
                str(spec.get(k, ""))
                for k in ("slug", "harbor", "env", "tool", "leftover", "token", "cache_id")
            ).lower()
            for needle in BANNED_NEEDLES:
                if needle in ident:
                    raise SystemExit(f"banned needle {needle!r} in {slug}")
            if "harbor-" in slug or "sysctl" in ident:
                raise SystemExit(f"ban {slug}")
    if len(PAIRS) < 12:
        raise SystemExit(f"catalog too small: {len(PAIRS)}")


def next_free_idx(start: int = 0) -> int | None:
    for i in range(start, len(PAIRS)):
        suc, leftp = PAIRS[i]
        if not slug_taken(suc["slug"]) and not slug_taken(leftp["slug"]):
            return i
    return None


def write_round(round_n: int, staging: Path, idx: int | None = None) -> None:
    if idx is None:
        raise SystemExit("catalog idx required")
    suc, leftp = PAIRS[idx]
    for spec in (suc, leftp):
        if slug_taken(spec["slug"]):
            raise SystemExit(f"slug {spec['slug']} already published; refuse clone")
    srec = success_episode(round_n, suc)
    lrec = leftover_episode(round_n, leftp)
    blob = json.dumps(srec) + json.dumps(lrec)
    for key in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
        if key in srec or key in lrec or f'"{key}"' in blob:
            raise SystemExit(f"forbidden key {key}")
    if '"sim_or_real": "real"' in blob:
        raise SystemExit("sim_or_real real forbidden")
    nsteps_s = srec["reward"]["cost_steps"]
    nsteps_l = lrec["reward"]["cost_steps"]
    if not (16 <= nsteps_s <= 24 and 16 <= nsteps_l <= 24):
        raise SystemExit(f"step count out of range {nsteps_s}/{nsteps_l}")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        json.dumps(srec, separators=(",", ":")) + "\n" + json.dumps(lrec, separators=(",", ":")) + "\n"
    )
    notes.write_text(notes_for(round_n, suc, leftp, srec, lrec))
    if "Novel coverage:" not in notes.read_text():
        raise SystemExit("NOTES missing Novel coverage")
    print(json.dumps({"round": round_n, "idx": idx, "ids": [srec["id"], lrec["id"]], "steps": [nsteps_s, nsteps_l], "bytes": batch.stat().st_size}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--idx", type=int, required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging), args.idx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
