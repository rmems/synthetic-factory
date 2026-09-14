#!/usr/bin/env python3
"""Mill docker-build-cache-factory r778+. MPI/NFC leftover plants.

BAN r645 nerdctl, r646 containerd, r549 scsh/scsi-debug, GNU Prolog/landlock/
SWI pack/seccomp/AppArmor/GOTOOLCHAIN clones, harbor-pin, leftover×sysctl.
17-step success + 18-step leftover. meta.generator=grok-4.6. Q=2.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("dbc_mill_r754", HERE / "dbc-mill-r754.py")
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
BANNED_NEEDLES = _m.BANNED_NEEDLES
slug_taken = _m.slug_taken

PAIRS: list[tuple[dict, dict]] = [
    (
        lang("hwloc-cache", "HWLOC_XMLFILE", "hwloc-info", "2.10.0", "2.11.2",
             "share/hwloc/hwloc-ps.1", "test_hwloc.py", "src/topo.xml", "hwloc-2112",
             "rm -rf /usr/share/hwloc",
             "rm share does not drop 2.10 hwloc-ps.1 under unversioned HWLOC_XMLFILE",
             "2MB", "this mill ucx / this mill libfabric (hwloc xml, not UCX or libfabric)",
             "hwloc-info", "hwloc-info --version"),
        leftover("pn533-leftover", "PN533_CLEAR", "pn533 proto=cache",
                 "pn533 leftover still NFC-protos cache as proto=cache",
                 "modprobe -r pn533",
                 "modprobe -r is EBUSY; leftover proto=cache still NFC-protos cache",
                 "leftover pn533 NFC-protoing cache",
                 "r hidraw / r uinput / cache-admin 403",
                 "r hidraw leftover (pn533 leftover, not hidraw hidraw0)",
                 "test_pn533.py",
                 "ls /sys/module/pn533; nfc-list | head",
                 "pn533 leftover proto=cache leftover"),
    ),
    (
        lang("ucx-cache", "UCX_HOME", "ucx_info", "1.16.0", "1.18.0",
             "share/ucx/ucx.conf", "test_ucx.py", "src/ucx.conf", "ucx-1180",
             "rm -rf /usr/share/ucx",
             "rm share does not drop 1.16 ucx.conf under unversioned UCX_HOME",
             "8MB", "this mill hwloc / this mill libfabric (UCX conf, not hwloc or libfabric)",
             "ucx_info -v", "ucx_info -v"),
        leftover("nfcmrvl-leftover", "NFCMRVL_CLEAR", "nfcmrvl fw=cache",
                 "nfcmrvl leftover still NFC-fws cache as fw=cache",
                 "modprobe -r nfcmrvl",
                 "modprobe -r is EBUSY; leftover fw=cache still NFC-fws cache",
                 "leftover nfcmrvl NFC-fwing cache",
                 "this mill pn533 / r hidraw / cache-admin 403",
                 "this mill pn533 leftover (nfcmrvl leftover, not pn533 proto)",
                 "test_nfcmrvl.py",
                 "ls /sys/module/nfcmrvl; nfc-list | head",
                 "nfcmrvl leftover fw=cache leftover"),
    ),
    (
        lang("libfabric-cache", "FI_PROVIDER_PATH", "fi_info", "1.20.1", "1.22.0",
             "lib/libfabric/libefa-fi.so", "test_fi.py", "src/demo.c", "fi-1220",
             "rm -rf /usr/lib/libfabric",
             "rm libefa does not drop 1.20 libefa-fi.so under unversioned FI_PROVIDER_PATH",
             "6MB", "this mill ucx / this mill openmpi-mca (libfabric efa-fi.so, not UCX or OpenMPI)",
             "fi_info", "fi_info --version"),
        leftover("s3fwrn5-leftover", "S3FWRN5_CLEAR", "s3fwrn5 fw=cache",
                 "s3fwrn5 leftover still NFC-fws cache as fw=cache",
                 "modprobe -r s3fwrn5",
                 "modprobe -r is EBUSY; leftover fw=cache still NFC-fws cache",
                 "leftover s3fwrn5 NFC-fwing cache",
                 "this mill nfcmrvl / this mill pn533 / cache-admin 403",
                 "this mill nfcmrvl leftover (s3fwrn5 leftover, not nfcmrvl fw)",
                 "test_s3fwrn5.py",
                 "ls /sys/module/s3fwrn5; nfc-list | head",
                 "s3fwrn5 leftover fw=cache leftover"),
    ),
    (
        lang("openmpi-mca-cache", "OMPI_MCA_PREFIX", "ompi_info", "4.1.6", "5.0.5",
             "share/openmpi/amca-param-sets/ft-enable-cr", "test_ompi.py", "src/demo.c", "ompi-505",
             "rm -rf /usr/share/openmpi",
             "rm amca does not drop 4.1 ft-enable-cr under unversioned OMPI_MCA_PREFIX",
             "11MB", "this mill mpich / this mill libfabric (OpenMPI amca, not MPICH or libfabric)",
             "ompi_info | head", "ompi_info --version"),
        leftover("st95hf-leftover", "ST95HF_CLEAR", "st95hf proto=cache",
                 "st95hf leftover still NFC-protos cache as proto=cache",
                 "modprobe -r st95hf",
                 "modprobe -r is EBUSY; leftover proto=cache still NFC-protos cache",
                 "leftover st95hf NFC-protoing cache",
                 "this mill s3fwrn5 / this mill pn533 / cache-admin 403",
                 "this mill s3fwrn5 leftover (st95hf leftover, not s3fwrn5 fw)",
                 "test_st95hf.py",
                 "ls /sys/module/st95hf; nfc-list | head",
                 "st95hf leftover proto=cache leftover"),
    ),
    (
        lang("mpich-cache", "MPICH_HOME", "mpichversion", "4.1.2", "4.2.3",
             "share/mpich/examples/cpi.c", "test_mpich.py", "src/cpi.c", "mpich-423",
             "rm -rf /usr/share/mpich",
             "rm examples does not drop 4.1 cpi.c under unversioned MPICH_HOME",
             "5MB", "this mill openmpi-mca / this mill pmix (MPICH cpi.c, not OpenMPI or PMIx)",
             "mpichversion", "mpichversion"),
        leftover("port100-leftover", "PORT100_CLEAR", "port100 proto=cache",
                 "port100 leftover still NFC-protos cache as proto=cache",
                 "modprobe -r port100",
                 "modprobe -r is EBUSY; leftover proto=cache still NFC-protos cache",
                 "leftover port100 NFC-protoing cache",
                 "this mill st95hf / this mill pn533 / cache-admin 403",
                 "this mill st95hf leftover (port100 leftover, not st95hf proto)",
                 "test_port100.py",
                 "ls /sys/module/port100; nfc-list | head",
                 "port100 leftover proto=cache leftover"),
    ),
    (
        lang("pmix-cache", "PMIX_INSTALL_PREFIX", "pmix_info", "4.2.9", "5.0.6",
             "share/pmix/help-pmix-mca-var.txt", "test_pmix.py", "src/demo.c", "pmix-506",
             "rm -rf /usr/share/pmix",
             "rm help does not drop 4.2 help-pmix-mca-var.txt under unversioned PMIX_INSTALL_PREFIX",
             "4MB", "this mill openmpi-mca / this mill prrte (PMIx help txt, not OpenMPI or PRRTE)",
             "pmix_info | head", "pmix_info --version"),
        leftover("pn532-leftover", "PN532_CLEAR", "pn532 proto=cache",
                 "pn532 leftover still NFC-protos cache as proto=cache",
                 "modprobe -r pn532",
                 "modprobe -r is EBUSY; leftover proto=cache still NFC-protos cache",
                 "leftover pn532 NFC-protoing cache",
                 "this mill pn533 / this mill port100 / cache-admin 403",
                 "this mill pn533 leftover (pn532 leftover, not pn533 proto)",
                 "test_pn532.py",
                 "ls /sys/module/pn532; nfc-list | head",
                 "pn532 leftover proto=cache leftover"),
    ),
    (
        lang("prrte-cache", "PRTE_PREFIX", "prte", "3.0.2", "3.0.8",
             "share/prte/help-prte-runtime.txt", "test_prte.py", "src/demo.c", "prte-308",
             "rm -rf /usr/share/prte",
             "rm help does not drop 3.0 help-prte-runtime.txt under unversioned PRTE_PREFIX",
             "3MB", "this mill pmix / this mill openmpi-mca (PRRTE help, not PMIx or OpenMPI)",
             "prte --version", "prte --version"),
        leftover("wacom-leftover", "WACOM_CLEAR", "wacom stylus=cache",
                 "wacom leftover still styluses cache as stylus=cache",
                 "modprobe -r wacom",
                 "modprobe -r is EBUSY; leftover stylus=cache still styluses cache",
                 "leftover wacom styling cache",
                 "r hidraw / r uinput / cache-admin 403",
                 "r hidraw leftover (wacom leftover, not hidraw hidraw0)",
                 "test_wacom.py",
                 "ls /sys/module/wacom; cat /sys/class/input/event0/device/name",
                 "wacom leftover stylus=cache leftover"),
    ),
    (
        lang("ucc-cache", "UCC_HOME", "ucc_info", "1.2.0", "1.3.0",
             "lib/ucc/libucc_tl_ucp.so", "test_ucc.py", "src/demo.c", "ucc-130",
             "rm -rf /usr/lib/ucc",
             "rm tl_ucp does not drop 1.2 libucc_tl_ucp.so under unversioned UCC_HOME",
             "7MB", "this mill ucx / this mill libfabric (UCC tl_ucp.so, not UCX or libfabric)",
             "ucc_info", "ucc_info --version"),
        leftover("uclogic-leftover", "UCLOGIC_CLEAR", "hid_uclogic pad=cache",
                 "hid_uclogic leftover still pads cache tablet as pad=cache",
                 "modprobe -r hid-uclogic",
                 "modprobe -r is EBUSY; leftover pad=cache still pads cache tablet",
                 "leftover hid_uclogic padding cache tablet",
                 "this mill wacom / r hidraw / cache-admin 403",
                 "this mill wacom leftover (uclogic leftover, not wacom stylus)",
                 "test_uclogic.py",
                 "ls /sys/module/hid_uclogic; cat /sys/class/input/event0/device/name",
                 "uclogic leftover pad=cache leftover"),
    ),
    (
        lang("gloo-cache", "GLOO_HOME", "gloo", "0.5.0", "0.5.0-post",
             "include/gloo/transport/tcp.h", "test_gloo.py", "src/demo.cpp", "gloo-050",
             "rm -rf /usr/include/gloo",
             "rm include does not drop 0.5 tcp.h under unversioned GLOO_HOME",
             "2MB", "this mill ucc / this mill ucx (Gloo tcp.h, not UCC or UCX)",
             "pkg-config --modversion gloo", "pkg-config --modversion gloo"),
        leftover("hid-steam-leftover", "HID_STEAM_CLEAR", "hid_steam lizard=0",
                 "hid_steam leftover still lizards cache Steam Controller as lizard=0",
                 "modprobe -r hid-steam",
                 "modprobe -r is EBUSY; leftover lizard=0 still lizards cache Steam Controller",
                 "leftover hid_steam lizarding cache Steam Controller",
                 "this mill wacom / r hidraw / cache-admin 403",
                 "this mill wacom leftover (hid-steam leftover, not wacom stylus)",
                 "test_hidsteam.py",
                 "ls /sys/module/hid_steam; cat /sys/class/input/js0/device/name",
                 "hid leftover steam lizard=0 leftover"),
    ),
    (
        lang("libevent-cache", "EVENT_NOKQUEUE", "event_rpcgen.py", "2.1.12", "2.1.12-stable",
             "include/event2/event.h", "test_event.py", "src/demo.c", "ev-2112",
             "rm -rf /usr/include/event2",
             "rm event.h does not drop 2.1 event.h under unversioned EVENT_NOKQUEUE",
             "1MB", "this mill pmix / this mill prrte (libevent event.h, not PMIx or PRRTE)",
             "pkg-config --modversion libevent", "pkg-config --modversion libevent"),
        leftover("nfc-nci-leftover", "NFC_NCI_CLEAR", "nfc_nci proto=cache",
                 "nfc_nci leftover still NCI-protos cache as proto=cache",
                 "modprobe -r nfc_nci",
                 "modprobe -r is EBUSY; leftover proto=cache still NCI-protos cache",
                 "leftover nfc_nci NCI-protoing cache",
                 "this mill pn533 / this mill pn532 / cache-admin 403",
                 "this mill pn533 leftover (nfc-nci leftover, not pn533 proto)",
                 "test_nfcnci.py",
                 "ls /sys/module/nfc_nci; nfc-list | head",
                 "nfc leftover nci proto=cache leftover"),
    ),
    (
        lang("slurm-plugstack-cache", "SLURM_CONF", "scontrol", "23.11.6", "24.05.3",
             "lib/slurm/cli_filter_lua.so", "test_slurm.py", "src/slurm.conf", "slurm-2405",
             "rm -rf /usr/lib/slurm",
             "rm cli_filter does not drop 23.11 cli_filter_lua.so under unversioned SLURM_CONF",
             "15MB", "this mill openmpi-mca / this mill pmix (Slurm cli_filter_lua, not OpenMPI or PMIx)",
             "scontrol --version", "scontrol --version"),
        leftover("nfc-hci-leftover", "NFC_HCI_CLEAR", "nfc_hci gate=cache",
                 "nfc_hci leftover still HCI-gates cache as gate=cache",
                 "modprobe -r nfc_hci",
                 "modprobe -r is EBUSY; leftover gate=cache still HCI-gates cache",
                 "leftover nfc_hci HCI-gating cache",
                 "this mill nfc-nci / this mill pn533 / cache-admin 403",
                 "this mill nfc-nci leftover (nfc-hci leftover, not nfc_nci proto)",
                 "test_nfchci.py",
                 "ls /sys/module/nfc_hci; nfc-list | head",
                 "nfc leftover hci gate=cache leftover"),
    ),
    (
        lang("cxi-cache", "CXI_HOME", "cxi_stat", "1.0.0", "1.1.0",
             "lib/libcxi.so.1", "test_cxi.py", "src/demo.c", "cxi-110",
             "rm -rf /usr/lib/libcxi.so.1",
             "rm libcxi does not drop 1.0 libcxi.so.1 under unversioned CXI_HOME",
             "4MB", "this mill libfabric / this mill ucx (CXI libcxi.so, not libfabric efa or UCX)",
             "cxi_stat", "cxi_stat --version"),
        leftover("nfc-digital-leftover", "NFC_DIGITAL_CLEAR", "nfc_digital framing=cache",
                 "nfc_digital leftover still framings cache as framing=cache",
                 "modprobe -r nfc_digital",
                 "modprobe -r is EBUSY; leftover framing=cache still framings cache",
                 "leftover nfc_digital framing cache",
                 "this mill nfc-hci / this mill nfc-nci / cache-admin 403",
                 "this mill nfc-hci leftover (nfc-digital leftover, not nfc_hci gate)",
                 "test_nfcdig.py",
                 "ls /sys/module/nfc_digital; nfc-list | head",
                 "nfc leftover digital framing=cache leftover"),
    ),
]


def catalog_selfcheck() -> None:
    seen: set[str] = set()
    for suc, leftp in PAIRS:
        for spec in (suc, leftp):
            slug = spec["slug"]
            if slug in seen:
                raise SystemExit(f"duplicate catalog slug {slug}")
            seen.add(slug)
            ident = " ".join(str(spec.get(k, "")) for k in ("slug", "harbor", "env", "tool", "leftover", "token", "cache_id")).lower()
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
    suc, leftp = PAIRS[idx]
    for spec in (suc, leftp):
        if slug_taken(spec["slug"]):
            raise SystemExit(f"slug {spec['slug']} already published")
    srec = success_episode(round_n, suc)
    lrec = leftover_episode(round_n, leftp)
    blob = json.dumps(srec) + json.dumps(lrec)
    for key in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
        if key in srec or key in lrec or f'"{key}"' in blob:
            raise SystemExit(f"forbidden key {key}")
    nsteps_s, nsteps_l = srec["reward"]["cost_steps"], lrec["reward"]["cost_steps"]
    if not (16 <= nsteps_s <= 24 and 16 <= nsteps_l <= 24):
        raise SystemExit("step count")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(json.dumps(srec, separators=(",", ":")) + "\n" + json.dumps(lrec, separators=(",", ":")) + "\n")
    notes.write_text(notes_for(round_n, suc, leftp, srec, lrec))
    print(json.dumps({"round": round_n, "idx": idx, "ids": [srec["id"], lrec["id"]], "steps": [nsteps_s, nsteps_l]}))


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
