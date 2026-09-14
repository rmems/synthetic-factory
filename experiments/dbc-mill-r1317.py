#!/usr/bin/env python3
"""Mill docker-build-cache-factory r1317+. CAD/CAE × FireWire/IPMI leftovers.

NEW unique-pair catalog after r1269 fonts/PPP.
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
_spec = importlib.util.spec_from_file_location("dbc_mill_r1269", HERE / "dbc-mill-r1269.py")
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
    "graphite2-shaper-cache",
    "ppp-generic-leftover",
    "ots-idempotent-cache",
    "ppp-syncppp-leftover",
)

_CRYPTO = [
    ("opencascade-occt-cache", "CASROOT", "DRAWEXE", "7.8.1", "7.9.1", "include/opencascade/Standard.hxx", "42MB"),
    ("occt-draw-cache", "CSF_OCCTResourcePath", "DRAWEXE", "7.8.1", "7.9.1", "share/opencascade/resources/DrawResources", "8MB"),
    ("elmerfem-bin-cache", "ELMER_HOME", "ElmerSolver", "9.0", "9.0-post", "share/elmersolver/lib", "18MB"),
    ("dolfinx-jit-cache", "DOLFINX_DIR", "python3", "0.8.0", "0.9.0", "lib/python3/dist-packages/dolfinx/__init__.py", "12MB"),
    ("moose-app-cache", "MOOSE_DIR", "moose-opt", "2024.08", "2025.04", "share/moose/framework", "36MB"),
    ("ngsolve-py-cache", "NETGENDIR", "python3", "6.2.2404", "6.2.2501", "lib/python3/dist-packages/ngsolve/__init__.py", "14MB"),
    ("librecad-bin-cache", "LIBRECAD_HOME", "librecad", "2.2.0", "2.2.1", "share/librecad/library", "10MB"),
    ("brlcad-rt-cache", "BRLCAD_ROOT", "rt", "7.38.2", "7.40.2", "share/brlcad/7.38.2/db", "22MB"),
    ("pythonocc-core-cache", "PYTHONOCC_HOME", "python3", "7.8.1", "7.9.0", "lib/python3/dist-packages/OCC/Core/__init__.py", "28MB"),
    ("cadquery-cache", "CADQUERY_HOME", "python3", "2.4.0", "2.5.2", "lib/python3/dist-packages/cadquery/__init__.py", "8MB"),
    ("build123d-cache", "BUILD123D_HOME", "python3", "0.7.0", "0.9.1", "lib/python3/dist-packages/build123d/__init__.py", "5MB"),
    ("ifcopenshell-cache", "IFCOPENSHELL_HOME", "IfcConvert", "0.8.0", "0.8.2", "include/ifcparse/IfcParse.h", "16MB"),
    ("opencamlib-cache", "OPENCAML_HOME", "python3", "2023.01", "2024.01", "lib/python3/dist-packages/ocl/__init__.py", "3MB"),
    ("libfive-cache", "LIBFIVE_HOME", "studio", "0.0.0", "0.0.0-post", "include/libfive.h", "4MB"),
    ("siconos-cache", "SICONOS_HOME", "python3", "4.4.0", "4.5.0", "lib/python3/dist-packages/siconos/__init__.py", "11MB"),
    ("chrono-engine-cache", "CHRONO_HOME", "python3", "9.0.0", "9.0.1", "include/chrono/ChConfig.h", "18MB"),
    ("ode-physics-cache", "ODE_HOME", "ode-test", "0.16.5", "0.16.6", "include/ode/ode.h", "3MB"),
    ("raisim-cache", "RAISIM_HOME", "python3", "1.1.7", "1.1.8", "include/raisim/World.hpp", "9MB"),
    ("bullet3-cache", "BULLET_HOME", "App_ExampleBrowser", "3.25", "3.25-post", "include/bullet/btBulletDynamicsCommon.h", "12MB"),
    ("su2-cfd-cache", "SU2_RUN", "SU2_CFD", "8.0.1", "8.1.0", "bin/SU2_CFD", "24MB"),
    ("nalu-wind-cache", "NALU_WIND_HOME", "naluX", "2.1.0", "2.2.0", "share/nalu-wind/xml", "15MB"),
    ("nektarpp-cache", "NEKTAR_HOME", "NekMesh", "5.6.0", "5.7.0", "include/LibUtilities/BasicConst/NektarUnivConsts.hpp", "20MB"),
    ("palabos-cfd-cache", "PALABOS_ROOT", "python3", "2.3.0", "2.3.1", "include/palabos3D.h", "8MB"),
    ("openlb-cache", "OPENLB_HOME", "python3", "1.6", "1.7", "include/olb3D.h", "7MB"),
    ("basilisk-cfd-cache", "BASILISK", "qcc", "2024.08", "2025.02", "include/basilisk.h", "6MB"),
    ("firedrake-core-cache", "FIREDRAKE_HOME", "python3", "2024.10", "2025.4", "lib/python3/dist-packages/firedrake/__init__.py", "16MB"),
    ("basix-cache", "BASIX_HOME", "python3", "0.8.0", "0.9.0", "include/basix/finite-element.h", "3MB"),
    ("ffcx-cache", "FFCX_HOME", "python3", "0.8.0", "0.9.0", "lib/python3/dist-packages/ffcx/__init__.py", "2MB"),
    ("ufl-lang-cache", "UFL_HOME", "python3", "2024.2.0", "2025.1.0", "lib/python3/dist-packages/ufl/__init__.py", "2MB"),
    ("slepc-cache", "SLEPC_DIR", "python3", "3.21.1", "3.22.2", "include/slepc.h", "6MB"),
    ("hypre-lib-cache", "HYPRE_DIR", "python3", "2.31.0", "2.32.0", "include/HYPRE.h", "8MB"),
    ("superlu-dist-cache", "SUPERLU_DIST_DIR", "python3", "9.0.0", "9.1.0", "include/superlu_dist_config.h", "4MB"),
    ("mumps-cache", "MUMPS_DIR", "python3", "5.7.2", "5.7.3", "include/dmumps_c.h", "7MB"),
    ("parmetis-cache", "PARMETIS_DIR", "python3", "4.0.3", "4.0.3-post", "include/parmetis.h", "2MB"),
    ("scotch-cache", "SCOTCH_DIR", "gmap", "7.0.4", "7.0.6", "include/scotch.h", "3MB"),
    ("ptscotch-cache", "PTSCOTCH_DIR", "dgmap", "7.0.4", "7.0.6", "include/ptscotch.h", "3MB"),
    ("trilinos-lib-cache", "TRILINOS_DIR", "python3", "16.0.0", "16.1.0", "include/Teuchos_Version.hpp", "48MB"),
    ("kokkos-cache", "KOKKOS_DIR", "python3", "4.3.1", "4.5.1", "include/Kokkos_Core.hpp", "6MB"),
    ("raja-cache", "RAJA_DIR", "python3", "2024.02.1", "2025.03.0", "include/RAJA/RAJA.hpp", "4MB"),
    ("umpire-cache", "UMPIRE_DIR", "python3", "2024.02.1", "2025.03.0", "include/umpire/Allocator.hpp", "3MB"),
    ("sundials-lib-cache", "SUNDIALS_DIR", "python3", "7.1.1", "7.2.1", "include/sundials/sundials_config.h", "8MB"),
    ("cvode-cache", "CVODE_DIR", "python3", "7.1.1", "7.2.1", "include/cvode/cvode.h", "2MB"),
    ("arkode-cache", "ARKODE_DIR", "python3", "7.1.1", "7.2.1", "include/arkode/arkode.h", "2MB"),
    ("ida-sundials-cache", "IDA_DIR", "python3", "7.1.1", "7.2.1", "include/ida/ida.h", "2MB"),
    ("kinsol-cache", "KINSOL_DIR", "python3", "7.1.1", "7.2.1", "include/kinsol/kinsol.h", "2MB"),
    ("salome-gui-cache", "SALOME_ROOT_DIR", "salome", "9.12.0", "9.14.0", "share/salome/gui", "30MB"),
    ("salome-smesh-cache", "SMESH_ROOT_DIR", "salome", "9.12.0", "9.14.0", "share/salome/smesh", "14MB"),
    ("ocp-cad-cache", "OCP_HOME", "python3", "7.8.1", "7.8.1.1", "lib/python3/dist-packages/OCP/__init__.py", "40MB"),
]

_GPIO = [
    ("firewire-ohci-leftover", "FIREWIRE_OHCI_CLEAR", "firewire_ohci debug=1", "firewire_ohci", "ls /sys/module/firewire_ohci"),
    ("firewire-core-leftover", "FIREWIRE_CORE_CLEAR", "firewire_core debug=1", "firewire_core", "ls /sys/bus/firewire"),
    ("firewire-sbp2-leftover", "FIREWIRE_SBP2_CLEAR", "firewire_sbp2 workarounds=cache", "firewire_sbp2", "ls /sys/module/firewire_sbp2"),
    ("firewire-net-leftover", "FIREWIRE_NET_CLEAR", "firewire_net debug=1", "firewire_net", "ls /sys/module/firewire_net"),
    ("sbp2-leftover", "SBP2_CLEAR", "firewire_sbp2 exclusive_login=1", "firewire_sbp2", "ls /sys/module/firewire_sbp2"),
    ("firewire-nosy-leftover", "NOSY_CLEAR", "nosy debug=1", "nosy", "ls /sys/module/nosy"),
    ("firedtv-leftover", "FIREDTV_CLEAR", "firedtv debug=1", "firedtv", "ls /sys/module/firedtv"),
    ("edac-core-leftover", "EDAC_CORE_CLEAR", "edac_core edac_mc_log_ue=1", "edac_core", "ls /sys/devices/system/edac"),
    ("i7core-edac-leftover", "I7CORE_EDAC_CLEAR", "i7core_edac debug=1", "i7core_edac", "ls /sys/module/i7core_edac"),
    ("skx-edac-leftover", "SKX_EDAC_CLEAR", "skx_edac debug=1", "skx_edac", "ls /sys/module/skx_edac"),
    ("sb-edac-leftover", "SB_EDAC_CLEAR", "sb_edac debug=1", "sb_edac", "ls /sys/module/sb_edac"),
    ("ie31200-edac-leftover", "IE31200_EDAC_CLEAR", "ie31200_edac debug=1", "ie31200_edac", "ls /sys/module/ie31200_edac"),
    ("ipmi-si-leftover", "IPMI_SI_CLEAR", "ipmi_si type=kcs", "ipmi_si", "ls /sys/module/ipmi_si"),
    ("ipmi-devintf-leftover", "IPMI_DEVINTF_CLEAR", "ipmi_devintf debug=1", "ipmi_devintf", "ls /dev/ipmi0"),
    ("ipmi-msghandler-leftover", "IPMI_MSGHANDLER_CLEAR", "ipmi_msghandler panic_op=cache", "ipmi_msghandler", "ls /sys/module/ipmi_msghandler"),
    ("ipmi-ssif-leftover", "IPMI_SSIF_CLEAR", "ipmi_ssif dbg=1", "ipmi_ssif", "ls /sys/module/ipmi_ssif"),
    ("ipmi-watchdog-leftover", "IPMI_WATCHDOG_CLEAR", "ipmi_watchdog action=reset", "ipmi_watchdog", "ls /sys/module/ipmi_watchdog"),
    ("ipmi-poweroff-leftover", "IPMI_POWEROFF_CLEAR", "ipmi_poweroff poweroff_powercycle=1", "ipmi_poweroff", "ls /sys/module/ipmi_poweroff"),
    ("ipmb-dev-int-leftover", "IPMB_DEV_INT_CLEAR", "ipmb_dev_int debug=1", "ipmb_dev_int", "ls /sys/module/ipmb_dev_int"),
    ("ssif-bmc-leftover", "SSIF_BMC_CLEAR", "ssif_bmc debug=1", "ssif_bmc", "ls /sys/module/ssif_bmc"),
    ("kcs-bmc-leftover", "KCS_BMC_CLEAR", "kcs_bmc debug=1", "kcs_bmc", "ls /sys/module/kcs_bmc"),
    ("bt-bmc-leftover", "BT_BMC_CLEAR", "bt_bmc debug=1", "bt_bmc", "ls /sys/module/bt_bmc"),
    ("ipmi-si-kcs-leftover", "IPMI_SI_KCS_CLEAR", "ipmi_si type=kcs", "ipmi_si", "ls /sys/module/ipmi_si"),
    ("ipmi-si-smic-leftover", "IPMI_SI_SMIC_CLEAR", "ipmi_si type=smic", "ipmi_si", "ls /sys/module/ipmi_si"),
    ("ipmi-si-bt-leftover", "IPMI_SI_BT_CLEAR", "ipmi_si type=bt", "ipmi_si", "ls /sys/module/ipmi_si"),
    ("firewire-sbp2-excl-leftover", "FIREWIRE_SBP2_EXCL_CLEAR", "firewire_sbp2 exclusive_login=1", "firewire_sbp2", "ls /sys/module/firewire_sbp2"),
    ("firewire-ohci-phys-leftover", "FIREWIRE_OHCI_PHYS_CLEAR", "firewire_ohci remote_dma=1", "firewire_ohci", "ls /sys/module/firewire_ohci"),
    ("firewire-core-guid-leftover", "FIREWIRE_CORE_GUID_CLEAR", "firewire_core debug=guid", "firewire_core", "ls /sys/bus/firewire"),
    ("ipmi-si-tryacpi-leftover", "IPMI_SI_ACPI_CLEAR", "ipmi_si tryacpi=1", "ipmi_si", "ls /sys/module/ipmi_si"),
    ("ipmi-si-trydmi-leftover", "IPMI_SI_DMI_CLEAR", "ipmi_si trydmi=1", "ipmi_si", "ls /sys/module/ipmi_si"),
    ("ipmi-si-tryplatform-leftover", "IPMI_SI_PLAT_CLEAR", "ipmi_si tryplatform=1", "ipmi_si", "ls /sys/module/ipmi_si"),
    ("ipmi-si-trydefaults-leftover", "IPMI_SI_DEF_CLEAR", "ipmi_si trydefaults=1", "ipmi_si", "ls /sys/module/ipmi_si"),
    ("ipmi-watchdog-preop-leftover", "IPMI_WD_PREOP_CLEAR", "ipmi_watchdog preop=preop_panic", "ipmi_watchdog", "ls /sys/module/ipmi_watchdog"),
    ("ipmi-watchdog-pretimeout-leftover", "IPMI_WD_PRETO_CLEAR", "ipmi_watchdog pretimeout=cache", "ipmi_watchdog", "ls /sys/module/ipmi_watchdog"),
    ("ipmi-ssif-dbg-leftover", "IPMI_SSIF_DBG_CLEAR", "ipmi_ssif dbg_probe=1", "ipmi_ssif", "ls /sys/module/ipmi_ssif"),
    ("firewire-net-fifo-leftover", "FIREWIRE_NET_FIFO_CLEAR", "firewire_net fifo=cache", "firewire_net", "ls /sys/module/firewire_net"),
    ("psmouse-leftover", "PSMOUSE_CLEAR", "psmouse proto=exps", "psmouse", "ls /sys/module/psmouse"),
    ("atkbd-leftover", "ATKBD_CLEAR", "atkbd softraw=1", "atkbd", "ls /sys/module/atkbd"),
    ("serio-raw-leftover", "SERIO_RAW_CLEAR", "serio_raw debug=1", "serio_raw", "ls /sys/module/serio_raw"),
    ("evdev-leftover", "EVDEV_CLEAR", "evdev debug=1", "evdev", "ls /sys/class/input"),
    ("joydev-leftover", "JOYDEV_CLEAR", "joydev debug=1", "joydev", "ls /sys/module/joydev"),
    ("mtd-blkdevs-leftover", "MTD_BLKDEVS_CLEAR", "mtd_blkdevs debug=1", "mtd_blkdevs", "ls /sys/module/mtd_blkdevs"),
    ("ipmi-dmi-decode-leftover", "IPMI_DMI_CLEAR", "ipmi_si dmi=1", "ipmi_si", "ls /sys/module/ipmi_si"),
    ("ipmi-hotmod-leftover", "IPMI_HOTMOD_CLEAR", "ipmi_si hotmod=add", "ipmi_si", "ls /sys/module/ipmi_si"),
    ("ipmi-si-force-kipmid-leftover", "IPMI_KIPMID_CLEAR", "ipmi_si force_kipmid=1", "ipmi_si", "ls /sys/module/ipmi_si"),
    ("ipmi-si-kipmid-max-leftover", "IPMI_KIPMID_MAX_CLEAR", "ipmi_si kipmid_max_busy_us=cache", "ipmi_si", "ls /sys/module/ipmi_si"),
    ("firewire-ohci-quirks-leftover", "FIREWIRE_OHCI_QUIRKS_CLEAR", "firewire_ohci quirks=cache", "firewire_ohci", "ls /sys/module/firewire_ohci"),
    ("firewire-core-user-tlabel-leftover", "FIREWIRE_TLABEL_CLEAR", "firewire_core user_tlabel=1", "firewire_core", "ls /sys/module/firewire_core"),
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
        mb, f"{sib} (unique {slug.split('-')[0]} cache, not prior NGS/astro/speech/solver/video/mq/quantum/font catalogs)",
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


_cursor = 0


def next_free_idx(start: int = 0) -> int | None:
    global _cursor
    for i in range(max(start, _cursor), len(PAIRS)):
        suc, leftp = PAIRS[i]
        if not slug_taken(suc["slug"]) and not slug_taken(leftp["slug"]):
            _cursor = i
            return i
        _cursor = i + 1
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
