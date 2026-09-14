#!/usr/bin/env python3
"""Mill docker-build-cache-factory r647+ after r646.

Uses leftover unused r598 pairs plus NEW lang × leftover driver plants.
BAN r645 nerdctl-namespace-snapshot-l3 / nerdctl-cni-ipam-l3, r646
containerd-content-lease-l3 / containerd-gc-root-label-l3, r549 scsh/scsi-debug,
r337 cantera/binfmt, GNU Prolog/landlock/SWI pack/seccomp/AppArmor/GOTOOLCHAIN
clones, harbor-pin, leftover×sysctl cartesian.
17-step success + 18-step leftover. meta.generator=grok-4.6. Q=2.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("dbc_mill_r598", HERE / "dbc-mill-r598.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
FACTORY_DIR = _m.FACTORY_DIR
lang = _m.lang
leftover = _m.leftover
success_episode = _m.success_episode
leftover_episode = _m.leftover_episode
notes_for = _m.notes_for
hx = _m.hx

BANNED_NEEDLES = _m.BANNED_NEEDLES + (
    "nerdctl-namespace-snapshot",
    "nerdctl-cni-ipam",
    "containerd-content-lease",
    "containerd-gc-root-label",
)


def slug_taken(slug: str) -> bool:
    proc = subprocess.run(
        [
            "rg",
            "-l",
            "--glob",
            "batch-r*.jsonl",
            rf"dbc-r\d+-{re.escape(slug)}(?:-[0-9a-f]{{4}})?",
            str(FACTORY_DIR),
        ],
        cwd=FACTORY_DIR.parent.parent.parent.parent,
        capture_output=True,
        text=True,
    )
    return bool(proc.stdout.strip())


NEW_PAIRS: list[tuple[dict, dict]] = [
    (
        lang("squeak-image-cache", "SQUEAK_IMAGE", "squeak", "5.3", "6.0",
             "share/squeak/Squeak5.3.image", "test_squeak.py", "src/demo.st", "sq-60",
             "rm -rf /usr/share/squeak",
             "rm share does not drop 5.3 Squeak5.3.image under unversioned SQUEAK_IMAGE",
             "48MB", "r pharo-iceberg (Squeak image, not Pharo Iceberg)",
             "squeak src/demo.st", "squeak -version"),
        leftover("ufshcd-leftover", "UFSHCD_CLEAR", "ufshcd wb=cache",
                 "ufshcd leftover still write-boosts cache UFS as wb=cache",
                 "echo 0 > /sys/class/scsi_host/host0/device/device_desc",
                 "ufshcd desc write is EBUSY; leftover wb=cache still write-boosts cache UFS",
                 "leftover ufshcd write-boosting cache UFS",
                 "r549 scsi-debug / r558 scsi-mq / cache-admin 403",
                 "r549 scsi-debug leftover (ufshcd leftover, not scsi_debug fake LUN)",
                 "test_ufshcd.py",
                 "ls /sys/class/scsi_host; cat /sys/devices/platform/ufshcd/wb",
                 "ufshcd leftover wb=cache leftover"),
    ),
    (
        lang("arturo-lib-cache", "ARTURO_HOME", "arturo", "0.9.80", "0.9.83",
             "lib/arturo/prelude.art", "test_arturo.py", "src/app.art", "art-0983",
             "rm -rf /usr/lib/arturo",
             "rm lib does not drop 0.9.80 prelude.art under unversioned ARTURO_HOME",
             "6MB", "r uiua-pad / r gleam-packages (Arturo prelude.art, not Uiua pad or Gleam)",
             "arturo src/app.art", "arturo --version"),
        leftover("thunderbolt-xd-leftover", "TB_XDOMAIN_CLEAR", "thunderbolt xdomain=cache",
                 "thunderbolt leftover still xdomains cache as UUID cache",
                 "echo 1 > /sys/bus/thunderbolt/devices/0-1/authorized",
                 "tb authorized write is EBUSY; leftover xdomain=cache still xdomains cache",
                 "leftover thunderbolt xdomaining cache",
                 "r584 hyperv-vmbus / r156 vfio-iommu / cache-admin 403",
                 "r584 hv_vmbus leftover (thunderbolt xdomain leftover, not VMBus class_id)",
                 "test_tbxd.py",
                 "ls /sys/bus/thunderbolt/devices; cat /sys/bus/thunderbolt/devices/0-1/unique_id",
                 "tb leftover xdomain=cache leftover"),
    ),
    (
        lang("pyscf-gto-cache", "PYSCF_EXT_PATH", "pyscf", "2.4.0", "2.7.0",
             "pyscf/gto/basis/cc-pvdz.dat", "test_pyscf.py", "src/demo.py", "pyscf-270",
             "rm -rf /usr/lib/python3/dist-packages/pyscf",
             "rm pyscf does not drop 2.4 cc-pvdz.dat under unversioned PYSCF_EXT_PATH",
             "22MB", "r psi4-data / r rdkit-data (PySCF gto basis, not Psi4 or RDKit)",
             "python3 src/demo.py", "python3 -c 'import pyscf; print(pyscf.__version__)'"),
        leftover("apple-dart-leftover", "APPLE_DART_CLEAR", "apple-dart iommu=cache",
                 "apple-dart leftover still IOMMUs cache streams as iommu=cache",
                 "echo 1 > /sys/devices/platform/dart/unbind",
                 "dart unbind is EBUSY; leftover iommu=cache still IOMMUs cache",
                 "leftover apple-dart IOMMUing cache",
                 "r156 vfio-iommu / r590 virtio-iommu / cache-admin 403",
                 "r156 vfio leftover (apple-dart leftover, not VFIO IOMMU group)",
                 "test_dartiommu.py",
                 "ls /sys/devices/platform/dart; cat /sys/kernel/iommu_groups/*/type",
                 "apple leftover dart iommu=cache leftover"),
    ),
    (
        lang("plumed-kernel-cache", "PLUMED_KERNEL", "plumed", "2.8.3", "2.9.2",
             "lib/plumed/kernel.so", "test_plumed.py", "src/demo.dat", "plumed-292",
             "rm -rf /usr/lib/plumed",
             "rm lib does not drop 2.8 kernel.so under unversioned PLUMED_KERNEL",
             "14MB", "r gromacs-top / r lammps-potentials (PLUMED kernel.so, not GROMACS or LAMMPS)",
             "plumed src/demo.dat", "plumed --no-mpi info"),
        leftover("tegra-xusb-leftover", "TEGRA_XUSB_CLEAR", "tegra-xusb pad=cache",
                 "tegra-xusb leftover still pads cache USB as pad=cache",
                 "echo 1 > /sys/bus/tegra-xusb/drivers/tegra-xusb/unbind",
                 "tegra-xusb unbind is EBUSY; leftover pad=cache still pads cache USB",
                 "leftover tegra-xusb padding cache USB",
                 "r577 uhid-dev / r441 xhci / cache-admin 403",
                 "r577 uhid leftover (tegra-xusb leftover, not uhid cache-hid)",
                 "test_tegraxusb.py",
                 "ls /sys/bus/platform/drivers/tegra-xusb; lsusb | head",
                 "tegra leftover xusb pad=cache leftover"),
    ),
    (
        lang("nwchem-basis-cache", "NWCHEM_BASIS_LIBRARY", "nwchem", "7.0.2", "7.2.2",
             "libraries/cc-pvdz", "test_nwchem.py", "src/demo.nw", "nw-722",
             "rm -rf /usr/share/nwchem",
             "rm libraries does not drop 7.0 cc-pvdz under unversioned NWCHEM_BASIS_LIBRARY",
             "31MB", "r psi4-data / r cp2k-data (NWChem cc-pvdz, not Psi4 or CP2K)",
             "nwchem src/demo.nw", "nwchem -v"),
        leftover("hantro-vpu-leftover", "HANTRO_VPU_CLEAR", "hantro codec=cache",
                 "hantro leftover still codecs cache VPU as codec=cache",
                 "echo 1 > /sys/bus/platform/drivers/hantro-vpu/unbind",
                 "hantro unbind is EBUSY; leftover codec=cache still codecs cache VPU",
                 "leftover hantro coding cache VPU",
                 "r560 v4l2loopback / r645 nerdctl-cni / cache-admin 403",
                 "r560 v4l2loopback leftover (hantro leftover, not v4l2loopback video_nr)",
                 "test_hantro.py",
                 "ls /sys/bus/platform/drivers/hantro-vpu; ls /dev/video*",
                 "hantro leftover codec=cache leftover"),
    ),
    (
        lang("xtend-lib-cache", "XTEND_HOME", "xtend", "2.32.0", "2.36.0",
             "lib/org.eclipse.xtend.lib.jar", "test_xtend.py", "src/App.xtend", "xt-236",
             "rm -rf /opt/xtend",
             "rm lib does not drop 2.32 org.eclipse.xtend.lib.jar under unversioned XTEND_HOME",
             "9MB", "r ceylon-repo / r groovy (Xtend lib.jar, not Ceylon or Groovy)",
             "xtendc src/App.xtend", "xtendc -version"),
        leftover("wave5-vpu-leftover", "WAVE5_VPU_CLEAR", "wave5 inst=cache",
                 "wave5 leftover still instances cache VPU as inst=cache",
                 "echo 1 > /sys/bus/platform/drivers/wave5/unbind",
                 "wave5 unbind is EBUSY; leftover inst=cache still instances cache VPU",
                 "leftover wave5 instancing cache VPU",
                 "this mill hantro-vpu / r560 v4l2loopback / cache-admin 403",
                 "this mill hantro leftover (wave5 leftover, not Hantro codec)",
                 "test_wave5.py",
                 "ls /sys/bus/platform/drivers/wave5; ls /dev/video*",
                 "wave5 leftover inst=cache leftover"),
    ),
    (
        lang("genie-lang-cache", "GENIE_HOME", "genie", "0.46.0", "0.48.0",
             "share/genie/prelude.gs", "test_genie.py", "src/app.gs", "genie-048",
             "rm -rf /usr/share/genie",
             "rm share does not drop 0.46 prelude.gs under unversioned GENIE_HOME",
             "3MB", "r vala-vapi (Genie prelude.gs, not Vala vapi)",
             "genie src/app.gs", "genie --version"),
        leftover("vicodec-leftover", "VICODEC_CLEAR", "vicodec n_devs=1",
                 "vicodec leftover still virtual-codecs cache as n_devs=1",
                 "modprobe -r vicodec",
                 "modprobe -r is EBUSY; leftover n_devs=1 still virtual-codecs cache",
                 "leftover vicodec virtual-coding cache",
                 "r560 v4l2loopback / this mill hantro-vpu / cache-admin 403",
                 "r560 v4l2loopback leftover (vicodec leftover, not v4l2loopback video_nr)",
                 "test_vicodec.py",
                 "ls /sys/module/vicodec; v4l2-ctl --list-devices",
                 "vicodec leftover n_devs=1 leftover"),
    ),
    (
        lang("jakt-lib-cache", "JAKT_HOME", "jakt", "0.0.1", "0.0.2",
             "runtime/libjakt_runtime.a", "test_jakt.py", "src/app.jakt", "jakt-002",
             "rm -rf /usr/lib/jakt",
             "rm runtime does not drop 0.0.1 libjakt_runtime.a under unversioned JAKT_HOME",
             "8MB", "r carbon-toolchain / r zig (Jakt runtime.a, not Carbon or Zig)",
             "jakt src/app.jakt", "jakt --version"),
        leftover("vim2m-leftover", "VIM2M_CLEAR", "vim2m n_devs=1",
                 "vim2m leftover still mem2mems cache as n_devs=1",
                 "modprobe -r vim2m",
                 "modprobe -r is EBUSY; leftover n_devs=1 still mem2mems cache",
                 "leftover vim2m mem2mem-ing cache",
                 "this mill vicodec / r560 v4l2loopback / cache-admin 403",
                 "this mill vicodec leftover (vim2m leftover, not vicodec n_devs)",
                 "test_vim2m.py",
                 "ls /sys/module/vim2m; v4l2-ctl --list-devices",
                 "vim2m leftover n_devs=1 leftover"),
    ),
    (
        lang("algol68g-cache", "A68G_HOME", "a68g", "3.1.2", "3.5.5",
             "lib/algol68g/prelude.a68", "test_a68.py", "src/demo.a68", "a68-355",
             "rm -rf /usr/lib/algol68g",
             "rm lib does not drop 3.1 prelude.a68 under unversioned A68G_HOME",
             "5MB", "r simula-cim / r cobol-cobc (Algol68g prelude.a68, not Simula or COBOL)",
             "a68g src/demo.a68", "a68g --version"),
        leftover("imx-gpu-leftover", "IMX_GPU_CLEAR", "etnaviv gpu=cache",
                 "etnaviv leftover still GPUs cache as gpu=cache",
                 "echo 1 > /sys/bus/platform/drivers/etnaviv/unbind",
                 "etnaviv unbind is EBUSY; leftover gpu=cache still GPUs cache",
                 "leftover etnaviv GPUing cache",
                 "r156 vfio-mdev / r645 nerdctl-namespace / cache-admin 403",
                 "r156 vfio leftover (etnaviv leftover, not vfio-mdev uuid)",
                 "test_etnaviv.py",
                 "ls /sys/module/etnaviv; ls /dev/dri",
                 "etnaviv leftover gpu=cache leftover"),
    ),
    (
        lang("simula-cim-cache", "CIM_HOME", "cim", "5.1", "5.3",
             "lib/cim/simula.bin", "test_cim.py", "src/demo.sim", "cim-53",
             "rm -rf /usr/lib/cim",
             "rm lib does not drop 5.1 simula.bin under unversioned CIM_HOME",
             "7MB", "this mill algol68g / r cobol-cobc (Simula cim bin, not Algol68 or COBOL)",
             "cim src/demo.sim", "cim -version"),
        leftover("rockchip-vpu-leftover", "ROCKCHIP_VPU_CLEAR", "rkvdec iommu=cache",
                 "rkvdec leftover still IOMMUs cache VPU as iommu=cache",
                 "echo 1 > /sys/bus/platform/drivers/rkvdec/unbind",
                 "rkvdec unbind is EBUSY; leftover iommu=cache still IOMMUs cache VPU",
                 "leftover rkvdec IOMMUing cache VPU",
                 "this mill hantro-vpu / this mill wave5-vpu / cache-admin 403",
                 "this mill hantro leftover (rkvdec leftover, not Hantro codec)",
                 "test_rkvdec.py",
                 "ls /sys/bus/platform/drivers/rkvdec; ls /dev/video*",
                 "rkvdec leftover iommu=cache leftover"),
    ),
    (
        lang("spoofax-sdf-cache", "SPOOFAX_HOME", "spoofax", "2.5.16", "2.5.17",
             "org.metaborg.meta.lang.sdf/sdf.tbl", "test_spoofax.py", "src/demo.sdf3", "spx-2517",
             "rm -rf /opt/spoofax",
             "rm sdf does not drop 2.5.16 sdf.tbl under unversioned SPOOFAX_HOME",
             "18MB", "r rascal-lib / r antlr (Spoofax sdf.tbl, not Rascal or ANTLR)",
             "spoofax src/demo.sdf3", "spoofax --version"),
        leftover("dwc3-gadget-leftover", "DWC3_GADGET_CLEAR", "dwc3 gadget=cache",
                 "dwc3 leftover still gadgets cache USB as gadget=cache",
                 "echo 1 > /sys/bus/platform/drivers/dwc3/unbind",
                 "dwc3 unbind is EBUSY; leftover gadget=cache still gadgets cache USB",
                 "leftover dwc3 gadgeting cache USB",
                 "this mill tegra-xusb / r441 xhci / cache-admin 403",
                 "this mill tegra-xusb leftover (dwc3 leftover, not tegra pad)",
                 "test_dwc3.py",
                 "ls /sys/bus/platform/drivers/dwc3; ls /sys/class/udc",
                 "dwc3 leftover gadget=cache leftover"),
    ),
    (
        lang("pmd-rules-cache", "PMD_HOME", "pmd", "6.55.0", "7.7.0",
             "rulesets/java/quickstart.xml", "test_pmd.py", "src/App.java", "pmd-770",
             "rm -rf /opt/pmd",
             "rm rulesets does not drop 6.55 quickstart.xml under unversioned PMD_HOME",
             "12MB", "r semgrep-rules / r checkstyle (PMD quickstart.xml, not Semgrep or Checkstyle)",
             "pmd check -d src", "pmd --version"),
        leftover("xhci-plat-leftover", "XHCI_PLAT_CLEAR", "xhci-plat quirks=cache",
                 "xhci-plat leftover still quirks cache USB as quirks=cache",
                 "echo 1 > /sys/bus/platform/drivers/xhci-hcd/unbind",
                 "xhci-plat unbind is EBUSY; leftover quirks=cache still quirks cache USB",
                 "leftover xhci-plat quirking cache USB",
                 "this mill dwc3-gadget / this mill tegra-xusb / cache-admin 403",
                 "this mill dwc3 leftover (xhci-plat leftover, not dwc3 gadget)",
                 "test_xhciplat.py",
                 "ls /sys/bus/platform/drivers/xhci-hcd; lsusb | head",
                 "xhci leftover plat quirks=cache leftover"),
    ),
    (
        lang("spotbugs-aux-cache", "SPOTBUGS_HOME", "spotbugs", "4.8.3", "4.8.6",
             "plugin/findsecbugs-plugin.jar", "test_spotbugs.py", "src/App.java", "sb-486",
             "rm -rf /opt/spotbugs",
             "rm plugin does not drop 4.8.3 findsecbugs-plugin.jar under unversioned SPOTBUGS_HOME",
             "11MB", "this mill pmd-rules / r infer-static (SpotBugs findsecbugs, not PMD or Infer)",
             "spotbugs -textui src", "spotbugs -version"),
        leftover("ehci-hcd-leftover", "EHCI_HCD_CLEAR", "ehci-hcd park=0",
                 "ehci leftover still parks cache USB as park=0",
                 "modprobe -r ehci-hcd",
                 "modprobe -r is EBUSY; leftover park=0 still parks cache USB",
                 "leftover ehci parking cache USB",
                 "this mill xhci-plat / this mill dwc3-gadget / cache-admin 403",
                 "this mill xhci leftover (ehci leftover, not xhci-plat quirks)",
                 "test_ehci.py",
                 "ls /sys/module/ehci_hcd/parameters; lsusb | head",
                 "ehci leftover park=0 leftover"),
    ),
    (
        lang("errorprone-javac-cache", "ERRORPRONE_HOME", "errorprone", "2.23.0", "2.36.0",
             "lib/error_prone_core.jar", "test_ep.py", "src/App.java", "ep-236",
             "rm -rf /opt/errorprone",
             "rm lib does not drop 2.23 error_prone_core.jar under unversioned ERRORPRONE_HOME",
             "15MB", "this mill spotbugs-aux / r clang-tidy (Error Prone core.jar, not SpotBugs or clang-tidy)",
             "javac -J-Xbootclasspath/p:error_prone_core.jar src/App.java",
             "java -jar error_prone_core.jar -version"),
        leftover("ohci-hcd-leftover", "OHCI_HCD_CLEAR", "ohci-hcd no_handshake=1",
                 "ohci leftover still no-handshakes cache USB as no_handshake=1",
                 "modprobe -r ohci-hcd",
                 "modprobe -r is EBUSY; leftover no_handshake=1 still no-handshakes cache USB",
                 "leftover ohci no-handshaking cache USB",
                 "this mill ehci-hcd / this mill xhci-plat / cache-admin 403",
                 "this mill ehci leftover (ohci leftover, not ehci park)",
                 "test_ohci.py",
                 "ls /sys/module/ohci_hcd/parameters; lsusb | head",
                 "ohci leftover no_handshake=1 leftover"),
    ),
    (
        lang("checker-fw-cache", "CHECKERFRAMEWORK", "checkerframework", "3.42.0", "3.48.3",
             "checker/dist/checker.jar", "test_cf.py", "src/App.java", "cf-3483",
             "rm -rf /opt/checkerframework",
             "rm dist does not drop 3.42 checker.jar under unversioned CHECKERFRAMEWORK",
             "28MB", "this mill errorprone-javac / this mill spotbugs-aux (Checker Framework jar, not Error Prone or SpotBugs)",
             "javac -processor org.checkerframework.checker.nullness.NullnessChecker src/App.java",
             "java -jar checker.jar -version"),
        leftover("uhci-hcd-leftover", "UHCI_HCD_CLEAR", "uhci-hcd ignore_oc=1",
                 "uhci leftover still ignore-OCs cache USB as ignore_oc=1",
                 "modprobe -r uhci-hcd",
                 "modprobe -r is EBUSY; leftover ignore_oc=1 still ignore-OCs cache USB",
                 "leftover uhci ignore-OCing cache USB",
                 "this mill ohci-hcd / this mill ehci-hcd / cache-admin 403",
                 "this mill ohci leftover (uhci leftover, not ohci no_handshake)",
                 "test_uhci.py",
                 "ls /sys/module/uhci_hcd/parameters; lsusb | head",
                 "uhci leftover ignore_oc=1 leftover"),
    ),
    (
        lang("ktlint-rules-cache", "KTLINT_HOME", "ktlint", "1.1.1", "1.5.0",
             "lib/ktlint-ruleset-standard.jar", "test_ktlint.py", "src/App.kt", "ktl-150",
             "rm -rf /opt/ktlint",
             "rm lib does not drop 1.1 ktlint-ruleset-standard.jar under unversioned KTLINT_HOME",
             "4MB", "this mill detekt-cfg / r kotlin (ktlint ruleset-standard, not Detekt or kotlinc)",
             "ktlint src", "ktlint --version"),
        leftover("musb-gadget-leftover", "MUSB_GADGET_CLEAR", "musb gadget=cache",
                 "musb leftover still gadgets cache USB as gadget=cache",
                 "echo 1 > /sys/bus/platform/drivers/musb-hdrc/unbind",
                 "musb unbind is EBUSY; leftover gadget=cache still gadgets cache USB",
                 "leftover musb gadgeting cache USB",
                 "this mill dwc3-gadget / this mill tegra-xusb / cache-admin 403",
                 "this mill dwc3 leftover (musb leftover, not dwc3 gadget)",
                 "test_musb.py",
                 "ls /sys/bus/platform/drivers/musb-hdrc; ls /sys/class/udc",
                 "musb leftover gadget=cache leftover"),
    ),
    (
        lang("detekt-cfg-cache", "DETEKT_CONFIG", "detekt", "1.23.6", "1.23.7",
             "config/detekt.yml", "test_detekt.py", "src/App.kt", "det-1237",
             "rm -rf /opt/detekt",
             "rm config does not drop 1.23.6 detekt.yml under unversioned DETEKT_CONFIG",
             "3MB", "this mill ktlint-rules / r semgrep-rules (Detekt detekt.yml, not ktlint or Semgrep)",
             "detekt --input src", "detekt --version"),
        leftover("chipidea-leftover", "CHIPIDEA_CLEAR", "ci_hdrc gadget=cache",
                 "ci_hdrc leftover still gadgets cache USB as gadget=cache",
                 "echo 1 > /sys/bus/platform/drivers/ci_hdrc/unbind",
                 "ci_hdrc unbind is EBUSY; leftover gadget=cache still gadgets cache USB",
                 "leftover ci_hdrc gadgeting cache USB",
                 "this mill musb-gadget / this mill dwc3-gadget / cache-admin 403",
                 "this mill musb leftover (chipidea leftover, not musb gadget)",
                 "test_cihdrc.py",
                 "ls /sys/bus/platform/drivers/ci_hdrc; ls /sys/class/udc",
                 "ci leftover hdrc gadget=cache leftover"),
    ),
    (
        lang("scalafmt-conf-cache", "SCALAFMT_CONF", "scalafmt", "3.7.17", "3.8.3",
             "lib/scalafmt-core_2.13.jar", "test_sfmt.py", "src/App.scala", "sfmt-383",
             "rm -rf /opt/scalafmt",
             "rm lib does not drop 3.7 scalafmt-core_2.13.jar under unversioned SCALAFMT_CONF",
             "6MB", "this mill scalafix-rules / r mill-scala-zinc (scalafmt core jar, not Scalafix or Mill zinc)",
             "scalafmt src/App.scala", "scalafmt --version"),
        leftover("dwc2-gadget-leftover", "DWC2_GADGET_CLEAR", "dwc2 gadget=cache",
                 "dwc2 leftover still gadgets cache USB as gadget=cache",
                 "echo 1 > /sys/bus/platform/drivers/dwc2/unbind",
                 "dwc2 unbind is EBUSY; leftover gadget=cache still gadgets cache USB",
                 "leftover dwc2 gadgeting cache USB",
                 "this mill dwc3-gadget / this mill chipidea / cache-admin 403",
                 "this mill dwc3 leftover (dwc2 leftover, not dwc3 gadget)",
                 "test_dwc2.py",
                 "ls /sys/bus/platform/drivers/dwc2; ls /sys/class/udc",
                 "dwc2 leftover gadget=cache leftover"),
    ),
    (
        lang("scalafix-rules-cache", "SCALAFIX_HOME", "scalafix", "0.11.1", "0.14.2",
             "rules/ProcedureSyntax.semanticdb", "test_sfix.py", "src/App.scala", "sfix-0142",
             "rm -rf /opt/scalafix",
             "rm rules does not drop 0.11 ProcedureSyntax.semanticdb under unversioned SCALAFIX_HOME",
             "5MB", "this mill scalafmt-conf / this mill bloop-compile (Scalafix ProcedureSyntax, not scalafmt or Bloop)",
             "scalafix src/App.scala", "scalafix --version"),
        leftover("cdns3-leftover", "CDNS3_CLEAR", "cdns3 role=cache",
                 "cdns3 leftover still roles cache USB as role=cache",
                 "echo 1 > /sys/bus/platform/drivers/cdns3/unbind",
                 "cdns3 unbind is EBUSY; leftover role=cache still roles cache USB",
                 "leftover cdns3 roleing cache USB",
                 "this mill dwc3-gadget / this mill dwc2-gadget / cache-admin 403",
                 "this mill dwc3 leftover (cdns3 leftover, not dwc3 gadget)",
                 "test_cdns3.py",
                 "ls /sys/bus/platform/drivers/cdns3; ls /sys/class/udc",
                 "cdns3 leftover role=cache leftover"),
    ),
    (
        lang("bloop-compile-cache", "BLOOP_HOME", "bloop", "1.5.17", "2.0.8",
             "cache/classes/bloop-backend", "test_bloop.py", "src/App.scala", "bloop-208",
             "rm -rf /root/.bloop",
             "rm cache does not drop 1.5 bloop-backend under unversioned BLOOP_HOME",
             "19MB", "this mill metals-semanticdb / r mill-scala-zinc (Bloop backend classes, not Metals or Mill)",
             "bloop compile app", "bloop about"),
        leftover("typec-tcpci-leftover", "TCPCI_CLEAR", "tcpci port=cache",
                 "tcpci leftover still ports cache Type-C as port=cache",
                 "echo 1 > /sys/bus/i2c/drivers/tcpci/unbind",
                 "tcpci unbind is EBUSY; leftover port=cache still ports cache Type-C",
                 "leftover tcpci porting cache Type-C",
                 "this mill cdns3 / this mill dwc3-gadget / cache-admin 403",
                 "this mill cdns3 leftover (tcpci leftover, not cdns3 role)",
                 "test_tcpci.py",
                 "ls /sys/class/typec; cat /sys/class/typec/port0/data_role",
                 "tcpci leftover port=cache leftover"),
    ),
    (
        lang("metals-semanticdb-cache", "METALS_ENABLED", "metals", "1.3.0", "1.4.2",
             ".metals/semanticdb", "test_metals.py", "src/App.scala", "met-142",
             "rm -rf /root/.metals",
             "rm .metals does not drop 1.3 semanticdb under unversioned METALS_ENABLED",
             "16MB", "this mill bloop-compile / this mill scalafix-rules (Metals semanticdb, not Bloop or Scalafix)",
             "metals-doctor", "metals --version"),
        leftover("ucsi-acpi-leftover", "UCSI_ACPI_CLEAR", "ucsi_acpi ppm=cache",
                 "ucsi_acpi leftover still PPMs cache Type-C as ppm=cache",
                 "echo 1 > /sys/bus/acpi/drivers/ucsi_acpi/unbind",
                 "ucsi_acpi unbind is EBUSY; leftover ppm=cache still PPMs cache Type-C",
                 "leftover ucsi_acpi PPMing cache Type-C",
                 "this mill typec-tcpci / this mill cdns3 / cache-admin 403",
                 "this mill tcpci leftover (ucsi_acpi leftover, not tcpci port)",
                 "test_ucsi.py",
                 "ls /sys/bus/acpi/drivers/ucsi_acpi; cat /sys/class/typec/port0/power_role",
                 "ucsi leftover acpi ppm=cache leftover"),
    ),
    (
        lang("bitbake-sstate-cache", "SSTATE_DIR", "bitbake", "2.6.0", "2.8.0",
             "sstate-cache/universal/sstate", "test_bb.py", "src/recipe.bb", "bb-280",
             "rm -rf /opt/yocto/sstate-cache",
             "rm sstate does not drop 2.6 universal/sstate under unversioned SSTATE_DIR",
             "210MB", "this mill yocto-downloads / r spack-cache-gcc (BitBake sstate, not DL_DIR or Spack)",
             "bitbake core-image-minimal", "bitbake --version"),
        leftover("i915-gvt-leftover", "I915_GVT_CLEAR", "i915 enable_gvt=1",
                 "i915 leftover still GVTs cache as enable_gvt=1",
                 "modprobe -r i915",
                 "modprobe -r is EBUSY; leftover enable_gvt=1 still GVTs cache",
                 "leftover i915 GVTing cache",
                 "r156 vfio-mdev / r590 virtio-iommu / cache-admin 403",
                 "r156 vfio leftover (i915-gvt leftover, not vfio-mdev uuid)",
                 "test_i915gvt.py",
                 "ls /sys/module/i915/parameters; ls /sys/class/mdev_bus",
                 "i915 leftover enable_gvt=1 leftover"),
    ),
    (
        lang("yocto-downloads-cache", "DL_DIR", "poky", "4.3", "5.0",
             "downloads/git2", "test_yocto.py", "src/local.conf", "yocto-50",
             "rm -rf /opt/yocto/downloads",
             "rm downloads does not drop 4.3 git2 under unversioned DL_DIR",
             "480MB", "this mill bitbake-sstate / this mill buildroot-dl (Yocto DL_DIR git2, not sstate or Buildroot dl)",
             "bitbake -c fetch busybox", "bitbake --version"),
        leftover("nouveau-leftover", "NOUVEAU_CLEAR", "nouveau runpm=0",
                 "nouveau leftover still runpms cache GPU as runpm=0",
                 "modprobe -r nouveau",
                 "modprobe -r is EBUSY; leftover runpm=0 still runpms cache GPU",
                 "leftover nouveau runpm-ing cache GPU",
                 "this mill i915-gvt / r156 vfio-mdev / cache-admin 403",
                 "this mill i915 leftover (nouveau leftover, not i915 enable_gvt)",
                 "test_nouveau.py",
                 "ls /sys/module/nouveau/parameters; ls /dev/dri",
                 "nouveau leftover runpm=0 leftover"),
    ),
    (
        lang("buildroot-dl-cache", "BR2_DL_DIR", "buildroot", "2024.02", "2024.11",
             "dl/busybox", "test_br.py", "src/defconfig", "br-2411",
             "rm -rf /opt/buildroot/dl",
             "rm dl does not drop 2024.02 busybox under unversioned BR2_DL_DIR",
             "95MB", "this mill yocto-downloads / this mill bitbake-sstate (Buildroot dl/busybox, not Yocto DL_DIR or sstate)",
             "make busybox", "make print-version"),
        leftover("mgag200-leftover", "MGAG200_CLEAR", "mgag200 modeset=cache",
                 "mgag200 leftover still modesets cache BMC as modeset=cache",
                 "modprobe -r mgag200",
                 "modprobe -r is EBUSY; leftover modeset=cache still modesets cache BMC",
                 "leftover mgag200 modesetting cache BMC",
                 "this mill nouveau / this mill i915-gvt / cache-admin 403",
                 "this mill nouveau leftover (mgag200 leftover, not nouveau runpm)",
                 "test_mgag200.py",
                 "ls /sys/module/mgag200; ls /dev/dri",
                 "mgag200 leftover modeset=cache leftover"),
    ),
    (
        lang("bazelisk-bin-cache", "BAZELISK_HOME", "bazelisk", "1.19.0", "1.25.0",
             "bin/bazelisk-linux-amd64", "test_bazelisk.py", "src/WORKSPACE", "bisk-125",
             "rm -rf /root/.bazelisk",
             "rm bin does not drop 1.19 bazelisk-linux-amd64 under unversioned BAZELISK_HOME",
             "28MB", "r bazel-disk-cache-vs-module-name (Bazelisk wrapper bin, not Bazel disk cache)",
             "bazelisk build //...", "bazelisk version"),
        leftover("ast-drm-leftover", "AST_DRM_CLEAR", "ast modeset=cache",
                 "ast leftover still modesets cache ASPEED as modeset=cache",
                 "modprobe -r ast",
                 "modprobe -r is EBUSY; leftover modeset=cache still modesets cache ASPEED",
                 "leftover ast modesetting cache ASPEED",
                 "this mill mgag200 / this mill nouveau / cache-admin 403",
                 "this mill mgag200 leftover (ast leftover, not mgag200 modeset)",
                 "test_astdrm.py",
                 "ls /sys/module/ast; ls /dev/dri",
                 "ast leftover modeset=cache leftover"),
    ),
    (
        lang("nx-dcache-cache", "NX_CACHE_DIRECTORY", "nx", "18.3.4", "20.2.1",
             ".nx/cache", "test_nx.py", "src/project.json", "nx-2021",
             "rm -rf /src/.nx",
             "rm .nx does not drop 18 .nx/cache under unversioned NX_CACHE_DIRECTORY",
             "33MB", "r lerna-bootstrap / r turbo-team (Nx .nx/cache, not Lerna or Turbo token)",
             "nx build app", "nx --version"),
        leftover("qxl-drm-leftover", "QXL_DRM_CLEAR", "qxl surfaces=cache",
                 "qxl leftover still surfaces cache SPICE as surfaces=cache",
                 "modprobe -r qxl",
                 "modprobe -r is EBUSY; leftover surfaces=cache still surfaces cache SPICE",
                 "leftover qxl surfacing cache SPICE",
                 "this mill ast-drm / this mill mgag200 / cache-admin 403",
                 "this mill ast leftover (qxl leftover, not ast modeset)",
                 "test_qxl.py",
                 "ls /sys/module/qxl; ls /dev/dri",
                 "qxl leftover surfaces=cache leftover"),
    ),
    (
        lang("biome-lint-cache", "BIOME_CACHE", "biome", "1.7.3", "1.9.4",
             ".biome/cache", "test_biome.py", "src/app.ts", "biome-194",
             "rm -rf /src/.biome",
             "rm .biome does not drop 1.7 .biome/cache under unversioned BIOME_CACHE",
             "8MB", "r eslint / r prettier (Biome .biome/cache, not ESLint or Prettier)",
             "biome check src", "biome --version"),
        leftover("bochs-drm-leftover", "BOCHS_DRM_CLEAR", "bochs-drm fb=cache",
                 "bochs-drm leftover still fbs cache as fb=cache",
                 "modprobe -r bochs-drm",
                 "modprobe -r is EBUSY; leftover fb=cache still fbs cache",
                 "leftover bochs-drm fbing cache",
                 "this mill qxl-drm / this mill ast-drm / cache-admin 403",
                 "this mill qxl leftover (bochs-drm leftover, not qxl surfaces)",
                 "test_bochsdrm.py",
                 "ls /sys/module/bochs_drm; ls /dev/dri",
                 "bochs leftover drm fb=cache leftover"),
    ),
    (
        lang("oxc-parser-cache", "OXC_CACHE", "oxc", "0.24.0", "0.36.0",
             ".oxc/parser-cache", "test_oxc.py", "src/app.ts", "oxc-036",
             "rm -rf /src/.oxc",
             "rm .oxc does not drop 0.24 parser-cache under unversioned OXC_CACHE",
             "5MB", "this mill biome-lint / r swc (Oxc parser-cache, not Biome or SWC plugins)",
             "oxc src/app.ts", "oxc --version"),
        leftover("simpledrm-leftover", "SIMPLEDRM_CLEAR", "simpledrm fb=cache",
                 "simpledrm leftover still fbs cache as fb=cache",
                 "modprobe -r simpledrm",
                 "modprobe -r is EBUSY; leftover fb=cache still fbs cache",
                 "leftover simpledrm fbing cache",
                 "this mill bochs-drm / this mill qxl-drm / cache-admin 403",
                 "this mill bochs leftover (simpledrm leftover, not bochs-drm fb)",
                 "test_simpledrm.py",
                 "ls /sys/module/simpledrm; ls /dev/dri",
                 "simpledrm leftover fb=cache leftover"),
    ),
    (
        lang("swc-plugin-cache", "SWC_CACHE", "swc", "1.5.7", "1.10.1",
             ".swc/plugins", "test_swc.py", "src/app.ts", "swc-1101",
             "rm -rf /src/.swc",
             "rm .swc does not drop 1.5 plugins under unversioned SWC_CACHE",
             "7MB", "this mill oxc-parser / this mill biome-lint (SWC plugins, not Oxc parser or Biome)",
             "swc src/app.ts", "swc --version"),
        leftover("gm12u320-leftover", "GM12U320_CLEAR", "gm12u320 fb=cache",
                 "gm12u320 leftover still fbs cache USB projector as fb=cache",
                 "modprobe -r gm12u320",
                 "modprobe -r is EBUSY; leftover fb=cache still fbs cache projector",
                 "leftover gm12u320 fbing cache projector",
                 "this mill simpledrm / this mill bochs-drm / cache-admin 403",
                 "this mill simpledrm leftover (gm12u320 leftover, not simpledrm fb)",
                 "test_gm12.py",
                 "ls /sys/module/gm12u320; ls /dev/dri",
                 "gm12u320 leftover fb=cache leftover"),
    ),
    (
        lang("rspack-persist-cache", "RSPACK_CACHE", "rspack", "0.7.5", "1.2.2",
             ".rspack/persist", "test_rspack.py", "src/app.ts", "rsp-122",
             "rm -rf /src/.rspack",
             "rm .rspack does not drop 0.7 persist under unversioned RSPACK_CACHE",
             "21MB", "r next-standalone-vs-webpack-cache (Rspack persist, not Next webpack cache)",
             "rspack build", "rspack --version"),
        leftover("udl-drm-leftover", "UDL_DRM_CLEAR", "udl fb=cache",
                 "udl leftover still fbs cache DisplayLink as fb=cache",
                 "modprobe -r udl",
                 "modprobe -r is EBUSY; leftover fb=cache still fbs cache DisplayLink",
                 "leftover udl fbing cache DisplayLink",
                 "this mill gm12u320 / this mill simpledrm / cache-admin 403",
                 "this mill gm12u320 leftover (udl leftover, not gm12u320 projector fb)",
                 "test_udl.py",
                 "ls /sys/module/udl; ls /dev/dri",
                 "udl leftover fb=cache leftover"),
    ),
    (
        lang("farmfe-cache", "FARM_CACHE", "farm", "1.2.4", "1.3.0",
             ".farm/cache", "test_farm.py", "src/app.ts", "farm-130",
             "rm -rf /src/.farm",
             "rm .farm does not drop 1.2 .farm/cache under unversioned FARM_CACHE",
             "9MB", "this mill rspack-persist / this mill vite-opt (Farm .farm/cache, not Rspack or Vite)",
             "farm build", "farm --version"),
        leftover("v3d-drm-leftover", "V3D_DRM_CLEAR", "v3d reset=cache",
                 "v3d leftover still resets cache V3D as reset=cache",
                 "echo 1 > /sys/bus/platform/drivers/v3d/unbind",
                 "v3d unbind is EBUSY; leftover reset=cache still resets cache V3D",
                 "leftover v3d resetting cache V3D",
                 "this mill nouveau / this mill i915-gvt / cache-admin 403",
                 "this mill nouveau leftover (v3d leftover, not nouveau runpm)",
                 "test_v3d.py",
                 "ls /sys/module/v3d; ls /dev/dri",
                 "v3d leftover reset=cache leftover"),
    ),
    (
        lang("vite-opt-cache", "VITE_CACHE_DIR", "vite", "5.2.11", "6.0.7",
             "node_modules/.vite", "test_vite.py", "src/app.ts", "vite-607",
             "rm -rf /src/node_modules/.vite",
             "rm .vite does not drop 5.2 node_modules/.vite under unversioned VITE_CACHE_DIR",
             "14MB", "this mill farmfe / this mill rspack-persist (Vite .vite optimize, not Farm or Rspack)",
             "vite build", "vite --version"),
        leftover("vc4-hdmi-leftover", "VC4_HDMI_CLEAR", "vc4 hdmi=cache",
                 "vc4 leftover still HDMIs cache as hdmi=cache",
                 "echo 1 > /sys/bus/platform/drivers/vc4-hdmi/unbind",
                 "vc4-hdmi unbind is EBUSY; leftover hdmi=cache still HDMIs cache",
                 "leftover vc4 HDMIing cache",
                 "this mill v3d-drm / this mill cec / cache-admin 403",
                 "this mill v3d leftover (vc4 leftover, not v3d reset)",
                 "test_vc4hdmi.py",
                 "ls /sys/module/vc4; ls /sys/class/drm",
                 "vc4 leftover hdmi=cache leftover"),
    ),
    (
        lang("reason-bs-cache", "BSB_HOME", "bsc", "9.1.2", "11.2.0",
             "lib/ocaml/jscomp.cma", "test_reason.py", "src/App.re", "bsc-1120",
             "rm -rf /usr/lib/bs-platform",
             "rm lib does not drop 9.1 jscomp.cma under unversioned BSB_HOME",
             "17MB", "r rescript-compiler / r ocaml (bsc jscomp.cma, not ReScript compiler cache or OCaml opam)",
             "bsc src/App.re", "bsc -v"),
        leftover("iwlwifi-mvm-leftover", "IWLWIFI_MVM_CLEAR", "iwlwifi power_scheme=1",
                 "iwlwifi leftover still power-schemes cache Wi-Fi as power_scheme=1",
                 "modprobe -r iwlwifi",
                 "modprobe -r is EBUSY; leftover power_scheme=1 still power-schemes cache Wi-Fi",
                 "leftover iwlwifi power-scheming cache Wi-Fi",
                 "r591 rxe-soft / r442 nvme-rdma / cache-admin 403",
                 "r591 rxe leftover (iwlwifi leftover, not rxe-soft RoCE)",
                 "test_iwlwifi.py",
                 "ls /sys/module/iwlwifi/parameters; iw dev",
                 "iwlwifi leftover power_scheme=1 leftover"),
    ),
    (
        lang("parcel-fs-cache", "PARCEL_CACHE", "parcel", "2.12.0", "2.13.3",
             ".parcel-cache", "test_parcel.py", "src/app.ts", "parcel-2133",
             "rm -rf /src/.parcel-cache",
             "rm .parcel-cache does not drop 2.12 .parcel-cache under unversioned PARCEL_CACHE",
             "24MB", "this mill vite-opt / this mill farmfe (Parcel .parcel-cache, not Vite or Farm)",
             "parcel build src/app.ts", "parcel --version"),
        leftover("ath11k-leftover", "ATH11K_CLEAR", "ath11k frame_mode=1",
                 "ath11k leftover still frame-modes cache Wi-Fi as frame_mode=1",
                 "modprobe -r ath11k",
                 "modprobe -r is EBUSY; leftover frame_mode=1 still frame-modes cache Wi-Fi",
                 "leftover ath11k frame-moding cache Wi-Fi",
                 "this mill iwlwifi-mvm / r591 rxe-soft / cache-admin 403",
                 "this mill iwlwifi leftover (ath11k leftover, not iwlwifi power_scheme)",
                 "test_ath11k.py",
                 "ls /sys/module/ath11k/parameters; iw dev",
                 "ath11k leftover frame_mode=1 leftover"),
    ),
    (
        lang("lage-hash-cache", "LAGE_CACHE", "lage", "2.7.15", "2.12.1",
             ".lage/cache", "test_lage.py", "src/package.json", "lage-2121",
             "rm -rf /src/.lage",
             "rm .lage does not drop 2.7 .lage/cache under unversioned LAGE_CACHE",
             "11MB", "this mill nx-dcache / r turbo-team (Lage .lage/cache, not Nx or Turbo token)",
             "lage build", "lage --version"),
        leftover("ath12k-leftover", "ATH12K_CLEAR", "ath12k frame_mode=1",
                 "ath12k leftover still frame-modes cache Wi-Fi 7 as frame_mode=1",
                 "modprobe -r ath12k",
                 "modprobe -r is EBUSY; leftover frame_mode=1 still frame-modes cache Wi-Fi 7",
                 "leftover ath12k frame-moding cache Wi-Fi 7",
                 "this mill ath11k / this mill iwlwifi-mvm / cache-admin 403",
                 "this mill ath11k leftover (ath12k leftover, not ath11k frame_mode on Wi-Fi 6)",
                 "test_ath12k.py",
                 "ls /sys/module/ath12k/parameters; iw dev",
                 "ath12k leftover frame_mode=1 leftover"),
    ),
    (
        lang("carbon-toolchain-cache", "CARBON_TOOLCHAIN", "carbon", "0.1.0", "0.2.0",
             "lib/carbon/core.carbon", "test_carbon.py", "src/app.carbon", "carb-020",
             "rm -rf /usr/lib/carbon",
             "rm lib does not drop 0.1 core.carbon under unversioned CARBON_TOOLCHAIN",
             "13MB", "this mill jakt-lib / r zig (Carbon core.carbon, not Jakt runtime or Zig)",
             "carbon compile src/app.carbon", "carbon --version"),
        leftover("mt7921-leftover", "MT7921_CLEAR", "mt7921 disable_aspm=1",
                 "mt7921 leftover still disable-ASPMs cache Wi-Fi as disable_aspm=1",
                 "modprobe -r mt7921",
                 "modprobe -r is EBUSY; leftover disable_aspm=1 still disable-ASPMs cache Wi-Fi",
                 "leftover mt7921 disable-ASPMing cache Wi-Fi",
                 "this mill ath11k / this mill iwlwifi-mvm / cache-admin 403",
                 "this mill ath11k leftover (mt7921 leftover, not ath11k frame_mode)",
                 "test_mt7921.py",
                 "ls /sys/module/mt7921/parameters; iw dev",
                 "mt7921 leftover disable_aspm=1 leftover"),
    ),
]


def build_pairs() -> list[tuple[dict, dict]]:
    """Stable catalog. Do not drop taken slugs — idx must match the loop module."""
    # r598 PAIRS[36:] were the unused leftover pairs at r647 mill authoring.
    pairs: list[tuple[dict, dict]] = list(_m.PAIRS[36:]) + list(NEW_PAIRS)
    seen: set[str] = set()
    for suc, leftp in pairs:
        for spec in (suc, leftp):
            slug = spec["slug"]
            if slug in seen:
                raise SystemExit(f"duplicate catalog slug {slug}")
            seen.add(slug)
    return pairs


PAIRS = build_pairs()


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
            if slug.startswith("harbor-") or "harbor-" in slug:
                raise SystemExit(f"harbor slug forbidden: {slug}")
            if "sysctl" in slug or "sysctl" in ident:
                raise SystemExit(f"sysctl cartesian forbidden: {slug}")
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
        raise SystemExit("catalog idx required (do not bind to a stolen round)")
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"no catalog pair for idx={idx} (len={len(PAIRS)})")
    suc, leftp = PAIRS[idx]
    for spec in (suc, leftp):
        if slug_taken(spec["slug"]):
            raise SystemExit(f"slug {spec['slug']} already published; refuse clone")
    srec = success_episode(round_n, suc)
    lrec = leftover_episode(round_n, leftp)
    if "harbor-" in srec["id"] or "harbor-" in lrec["id"]:
        raise SystemExit("harbor id leaked")
    if "harbor-" in srec["goal"] and "pins" in srec["goal"] and "still compiles" in srec["goal"]:
        raise SystemExit("harbor-pin goal leaked")
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
        json.dumps(srec, separators=(",", ":"))
        + "\n"
        + json.dumps(lrec, separators=(",", ":"))
        + "\n"
    )
    notes.write_text(notes_for(round_n, suc, leftp, srec, lrec))
    if "Novel coverage:" not in notes.read_text():
        raise SystemExit("NOTES missing Novel coverage")
    print(
        json.dumps(
            {
                "round": round_n,
                "idx": idx,
                "ids": [srec["id"], lrec["id"]],
                "steps": [nsteps_s, nsteps_l],
                "bytes": batch.stat().st_size,
            }
        )
    )


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
