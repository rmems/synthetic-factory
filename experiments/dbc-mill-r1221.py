#!/usr/bin/env python3
"""Mill docker-build-cache-factory r1221+. Quantum SDKs × USB-gadget leftovers.

NEW unique-pair catalog after r1173 MQ/NIC.
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
_spec = importlib.util.spec_from_file_location("dbc_mill_r1173", HERE / "dbc-mill-r1173.py")
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
    "nats-server-cache",
    "igb-leftover",
    "kafka-rest-cache",
    "i40e-vf-leftover",
)

# slug, env, tool, old, new, artifact, mb
_CRYPTO = [
    ("qiskit-terra-cache", "QISKIT_HOME", "python3", "1.2.4", "1.4.2", "lib/python3/dist-packages/qiskit/__init__.py", "18MB"),
    ("qiskit-aer-cache", "QISKIT_AER_HOME", "python3", "0.15.1", "0.16.1", "lib/python3/dist-packages/qiskit_aer/__init__.py", "22MB"),
    ("qulacs-core-cache", "QULACS_HOME", "python3", "0.6.6", "0.6.11", "lib/python3/dist-packages/qulacs/__init__.py", "8MB"),
    ("stim-cli-cache", "STIM_HOME", "stim", "1.13.0", "1.14.0", "include/stim.h", "4MB"),
    ("pyzx-cache", "PYZX_HOME", "python3", "0.8.0", "0.9.0", "lib/python3/dist-packages/pyzx/__init__.py", "3MB"),
    ("cirq-core-cache", "CIRQ_HOME", "python3", "1.4.1", "1.5.0", "lib/python3/dist-packages/cirq/__init__.py", "12MB"),
    ("pennylane-core-cache", "PENNYLANE_HOME", "python3", "0.38.0", "0.41.1", "lib/python3/dist-packages/pennylane/__init__.py", "16MB"),
    ("braket-sdk-cache", "BRAKET_HOME", "python3", "1.88.0", "1.90.1", "lib/python3/dist-packages/braket/__init__.py", "7MB"),
    ("pytket-cache", "PYTKET_HOME", "python3", "1.31.1", "1.37.0", "lib/python3/dist-packages/pytket/__init__.py", "14MB"),
    ("tket-bin-cache", "TKET_HOME", "tket", "1.31.1", "1.37.0", "include/tket/Circuit/Circuit.hpp", "9MB"),
    ("projectq-cache", "PROJECTQ_HOME", "python3", "0.8.0", "0.8.0-post", "lib/python3/dist-packages/projectq/__init__.py", "5MB"),
    ("pyquil-cache", "PYQUIL_HOME", "python3", "4.14.2", "4.16.1", "lib/python3/dist-packages/pyquil/__init__.py", "6MB"),
    ("quilc-cache", "QUILC_HOME", "quilc", "1.26.0", "1.27.0", "share/quilc/quilc.md", "18MB"),
    ("qvm-cache", "QVM_HOME", "qvm", "1.17.1", "1.17.2", "share/qvm/qvm.md", "12MB"),
    ("qsharp-lang-cache", "QSHARP_HOME", "qsc", "1.10.0", "1.16.0", "share/qsharp/qsc.md", "20MB"),
    ("strawberry-fields-cache", "STRAWBERRYFIELDS_HOME", "python3", "0.23.0", "0.23.0-post", "lib/python3/dist-packages/strawberryfields/__init__.py", "8MB"),
    ("pennylane-lightning-cache", "LIGHTNING_HOME", "python3", "0.38.0", "0.41.0", "lib/python3/dist-packages/pennylane_lightning/__init__.py", "10MB"),
    ("openqasm3-cache", "OPENQASM_HOME", "oqpy", "1.0.0", "1.0.1", "include/openqasm/parser.h", "3MB"),
    ("qiskit-ibm-runtime-cache", "QISKIT_IBM_TOKEN", "python3", "0.29.1", "0.36.1", "lib/python3/dist-packages/qiskit_ibm_runtime/__init__.py", "5MB"),
    ("qiskit-nature-cache", "QISKIT_NATURE_HOME", "python3", "0.7.2", "0.7.2-post", "lib/python3/dist-packages/qiskit_nature/__init__.py", "7MB"),
    ("qiskit-algorithms-cache", "QISKIT_ALGORITHMS_HOME", "python3", "0.3.0", "0.3.1", "lib/python3/dist-packages/qiskit_algorithms/__init__.py", "4MB"),
    ("qiskit-dynamics-cache", "QISKIT_DYNAMICS_HOME", "python3", "0.5.1", "0.5.1-post", "lib/python3/dist-packages/qiskit_dynamics/__init__.py", "5MB"),
    ("qiskit-experiments-cache", "QISKIT_EXPERIMENTS_HOME", "python3", "0.7.0", "0.8.1", "lib/python3/dist-packages/qiskit_experiments/__init__.py", "6MB"),
    ("mthree-mit-cache", "MTHREE_HOME", "python3", "2.6.3", "2.7.0", "lib/python3/dist-packages/mthree/__init__.py", "3MB"),
    ("mitiq-cache", "MITIQ_HOME", "python3", "0.38.0", "0.43.0", "lib/python3/dist-packages/mitiq/__init__.py", "5MB"),
    ("qutip-core-cache", "QUTIP_HOME", "python3", "5.0.4", "5.1.1", "lib/python3/dist-packages/qutip/__init__.py", "11MB"),
    ("qutip-qip-cache", "QUTIP_QIP_HOME", "python3", "0.3.3", "0.4.0", "lib/python3/dist-packages/qutip_qip/__init__.py", "3MB"),
    ("scqubits-cache", "SCQUBITS_HOME", "python3", "4.2.0", "4.3.0", "lib/python3/dist-packages/scqubits/__init__.py", "6MB"),
    ("pulser-cache", "PULSER_HOME", "python3", "1.1.1", "1.4.0", "lib/python3/dist-packages/pulser/__init__.py", "4MB"),
    ("bloqade-cache", "BLOQADE_HOME", "python3", "0.16.0", "0.16.3", "lib/python3/dist-packages/bloqade/__init__.py", "5MB"),
    ("cuda-quantum-cache", "CUDAQ_HOME", "nvq++", "0.8.0", "0.9.1", "include/cudaq/spin_op.h", "28MB"),
    ("qibo-cache", "QIBO_HOME", "python3", "0.2.12", "0.2.16", "lib/python3/dist-packages/qibo/__init__.py", "7MB"),
    ("tensorcircuit-cache", "TENSORCIRCUIT_HOME", "python3", "0.12.0", "1.2.0", "lib/python3/dist-packages/tensorcircuit/__init__.py", "8MB"),
    ("openfermion-cache", "OPENFERMION_HOME", "python3", "1.6.1", "1.6.1-post", "lib/python3/dist-packages/openfermion/__init__.py", "9MB"),
    ("quest-sim-cache", "QUEST_HOME", "quest", "3.7.0", "4.0.0", "include/QuEST.h", "4MB"),
    ("sinter-cache", "SINTER_HOME", "sinter", "1.13.0", "1.14.0", "share/sinter/sinter.md", "3MB"),
    ("pymatching-cache", "PYMATCHING_HOME", "python3", "2.2.1", "2.2.2", "lib/python3/dist-packages/pymatching/__init__.py", "2MB"),
    ("fusion-blossom-cache", "FUSION_BLOSSOM_HOME", "fusion_blossom", "0.2.11", "0.2.12", "include/fusion_blossom.h", "3MB"),
    ("ldpc-dec-cache", "LDPC_HOME", "python3", "0.1.51", "2.1.8", "lib/python3/dist-packages/ldpc/__init__.py", "3MB"),
    ("beliefmatching-cache", "BELIEFMATCHING_HOME", "python3", "0.1.0", "0.1.1", "lib/python3/dist-packages/beliefmatching/__init__.py", "1MB"),
    ("qiskit-metal-cache", "QISKIT_METAL_HOME", "python3", "0.1.5", "0.1.5-post", "lib/python3/dist-packages/qiskit_metal/__init__.py", "10MB"),
    ("krotov-opt-cache", "KROTOV_HOME", "python3", "1.2.2", "1.3.0", "lib/python3/dist-packages/krotov/__init__.py", "2MB"),
    ("qibojit-cache", "QIBOJIT_HOME", "python3", "0.1.5", "0.1.7", "lib/python3/dist-packages/qibojit/__init__.py", "3MB"),
    ("paddle-quantum-cache", "PADDLE_QUANTUM_HOME", "python3", "2.4.0", "2.4.0-post", "lib/python3/dist-packages/paddle_quantum/__init__.py", "8MB"),
    ("mindquantum-cache", "MINDQUANTUM_HOME", "python3", "0.9.11", "0.10.0", "lib/python3/dist-packages/mindquantum/__init__.py", "12MB"),
    ("qiskit-addon-aqc-cache", "QISKIT_AQC_HOME", "python3", "0.2.0", "0.3.0", "lib/python3/dist-packages/qiskit_addon_aqc_tensor/__init__.py", "2MB"),
    ("stimcirq-cache", "STIMCIRQ_HOME", "python3", "1.13.0", "1.14.0", "lib/python3/dist-packages/stimcirq/__init__.py", "1MB"),
    ("amazon-braket-default-sim-cache", "BRAKET_SIM_HOME", "python3", "1.24.0", "1.26.1", "lib/python3/dist-packages/braket/default_simulator/__init__.py", "4MB"),
]

_GPIO = [
    ("usb-f-acm-leftover", "USB_F_ACM_CLEAR", "usb_f_acm use_acm=1", "usb_f_acm", "ls /sys/module/usb_f_acm"),
    ("usb-f-ecm-leftover", "USB_F_ECM_CLEAR", "usb_f_ecm qmult=cache", "usb_f_ecm", "ls /sys/module/usb_f_ecm"),
    ("g-ether-leftover", "G_ETHER_CLEAR", "g_ether host_addr=cache", "g_ether", "ls /sys/module/g_ether"),
    ("g-serial-leftover", "G_SERIAL_CLEAR", "g_serial use_acm=1", "g_serial", "ls /sys/module/g_serial"),
    ("libcomposite-leftover", "LIBCOMPOSITE_CLEAR", "libcomposite debug=1", "libcomposite", "ls /sys/module/libcomposite"),
    ("usb-f-rndis-leftover", "USB_F_RNDIS_CLEAR", "usb_f_rndis wceis=1", "usb_f_rndis", "ls /sys/module/usb_f_rndis"),
    ("usb-f-ncm-leftover", "USB_F_NCM_CLEAR", "usb_f_ncm qmult=cache", "usb_f_ncm", "ls /sys/module/usb_f_ncm"),
    ("usb-f-eem-leftover", "USB_F_EEM_CLEAR", "usb_f_eem qmult=cache", "usb_f_eem", "ls /sys/module/usb_f_eem"),
    ("usb-f-obex-leftover", "USB_F_OBEX_CLEAR", "usb_f_obex debug=1", "usb_f_obex", "ls /sys/module/usb_f_obex"),
    ("usb-f-phonet-leftover", "USB_F_PHONET_CLEAR", "usb_f_phonet debug=1", "usb_f_phonet", "ls /sys/module/usb_f_phonet"),
    ("usb-f-ss-lb-leftover", "USB_F_SS_LB_CLEAR", "usb_f_ss_lb buflen=cache", "usb_f_ss_lb", "ls /sys/module/usb_f_ss_lb"),
    ("usb-f-mass-storage-leftover", "USB_F_MS_CLEAR", "usb_f_mass_storage stall=1", "usb_f_mass_storage", "ls /sys/module/usb_f_mass_storage"),
    ("usb-f-uac1-leftover", "USB_F_UAC1_CLEAR", "usb_f_uac1 p_chmask=cache", "usb_f_uac1", "ls /sys/module/usb_f_uac1"),
    ("usb-f-uac2-leftover", "USB_F_UAC2_CLEAR", "usb_f_uac2 p_chmask=cache", "usb_f_uac2", "ls /sys/module/usb_f_uac2"),
    ("usb-f-uvc-leftover", "USB_F_UVC_CLEAR", "usb_f_uvc streaming_interval=cache", "usb_f_uvc", "ls /sys/module/usb_f_uvc"),
    ("usb-f-midi-leftover", "USB_F_MIDI_CLEAR", "usb_f_midi in_ports=cache", "usb_f_midi", "ls /sys/module/usb_f_midi"),
    ("usb-f-hid-leftover", "USB_F_HID_CLEAR", "usb_f_hid no_out_endpoint=1", "usb_f_hid", "ls /sys/module/usb_f_hid"),
    ("usb-f-printer-leftover", "USB_F_PRINTER_CLEAR", "usb_f_printer qlen=cache", "usb_f_printer", "ls /sys/module/usb_f_printer"),
    ("g-mass-storage-leftover", "G_MASS_STORAGE_CLEAR", "g_mass_storage stall=1", "g_mass_storage", "ls /sys/module/g_mass_storage"),
    ("g-hid-leftover", "G_HID_CLEAR", "g_hid no_out_endpoint=1", "g_hid", "ls /sys/module/g_hid"),
    ("g-midi-leftover", "G_MIDI_CLEAR", "g_midi in_ports=cache", "g_midi", "ls /sys/module/g_midi"),
    ("g-audio-leftover", "G_AUDIO_CLEAR", "g_audio p_chmask=cache", "g_audio", "ls /sys/module/g_audio"),
    ("g-webcam-leftover", "G_WEBCAM_CLEAR", "g_webcam streaming_interval=cache", "g_webcam", "ls /sys/module/g_webcam"),
    ("g-printer-leftover", "G_PRINTER_CLEAR", "g_printer qlen=cache", "g_printer", "ls /sys/module/g_printer"),
    ("g-ffs-leftover", "G_FFS_CLEAR", "g_ffs functions=cache", "g_ffs", "ls /sys/module/g_ffs"),
    ("g-multi-leftover", "G_MULTI_CLEAR", "g_multi use_eem=1", "g_multi", "ls /sys/module/g_multi"),
    ("g-cdc-leftover", "G_CDC_CLEAR", "g_cdc use_acm=1", "g_cdc", "ls /sys/module/g_cdc"),
    ("g-ncm-leftover", "G_NCM_CLEAR", "g_ncm qmult=cache", "g_ncm", "ls /sys/module/g_ncm"),
    ("g-acm-ms-leftover", "G_ACM_MS_CLEAR", "g_acm_ms stall=1", "g_acm_ms", "ls /sys/module/g_acm_ms"),
    ("dummy-hcd-leftover", "DUMMY_HCD_CLEAR", "dummy_hcd is_super_speed=1", "dummy_hcd", "ls /sys/module/dummy_hcd"),
    ("dwc3-gadget-leftover", "DWC3_CLEAR", "dwc3 usb2_lpm_disable=1", "dwc3", "ls /sys/module/dwc3"),
    ("dwc2-gadget-leftover", "DWC2_CLEAR", "dwc2 gadget_lpm=1", "dwc2", "ls /sys/module/dwc2"),
    ("musb-hdrc-leftover", "MUSB_HDRC_CLEAR", "musb_hdrc use_dma=1", "musb_hdrc", "ls /sys/module/musb_hdrc"),
    ("chipidea-udc-leftover", "CI_HDRC_CLEAR", "ci_hdrc lpm=1", "ci_hdrc", "ls /sys/module/ci_hdrc"),
    ("isp1760-udc-leftover", "ISP1760_CLEAR", "isp1760 def_role=gadget", "isp1760", "ls /sys/module/isp1760"),
    ("configfs-gadget-leftover", "CONFIGFS_GADGET_CLEAR", "libcomposite configfs=1", "libcomposite", "ls /sys/kernel/config/usb_gadget"),
    ("usb-f-fs-leftover", "USB_F_FS_CLEAR", "usb_f_fs debug=1", "usb_f_fs", "ls /sys/module/usb_f_fs"),
    ("usb-f-tcm-leftover", "USB_F_TCM_CLEAR", "usb_f_tcm debug=1", "usb_f_tcm", "ls /sys/module/usb_f_tcm"),
    ("usb-f-uac1-legacy-leftover", "USB_F_UAC1_LEGACY_CLEAR", "usb_f_uac1_legacy req_buf_size=cache", "usb_f_uac1_legacy", "ls /sys/module/usb_f_uac1_legacy"),
    ("g-zero-leftover", "G_ZERO_CLEAR", "g_zero buflen=cache", "g_zero", "ls /sys/module/g_zero"),
    ("g-dbgp-leftover", "G_DBGP_CLEAR", "g_dbgp vendor=cache", "g_dbgp", "ls /sys/module/g_dbgp"),
    ("raw-gadget-leftover", "RAW_GADGET_CLEAR", "raw_gadget debug=1", "raw_gadget", "ls /sys/module/raw_gadget"),
    ("gr-udc-leftover", "GR_UDC_CLEAR", "gr_udc debug=1", "gr_udc", "ls /sys/module/gr_udc"),
    ("mv-udc-leftover", "MV_UDC_CLEAR", "mv_udc debug=1", "mv_udc", "ls /sys/module/mv_udc"),
    ("fsl-udc-leftover", "FSL_USB2_UDC_CLEAR", "fsl_usb2_udc debug=1", "fsl_usb2_udc", "ls /sys/module/fsl_usb2_udc"),
    ("omap-udc-leftover", "OMAP_UDC_CLEAR", "omap_udc fifo_mode=cache", "omap_udc", "ls /sys/module/omap_udc"),
    ("pxa27x-udc-leftover", "PXA27X_UDC_CLEAR", "pxa27x_udc debug=1", "pxa27x_udc", "ls /sys/module/pxa27x_udc"),
    ("s3c-hsudc-leftover", "S3C_HSUDC_CLEAR", "s3c_hsudc debug=1", "s3c_hsudc", "ls /sys/module/s3c_hsudc"),
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
        mb, f"{sib} (unique {slug.split('-')[0]} cache, not prior NGS/astro/speech/solver/video/mq catalogs)",
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
