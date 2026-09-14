#!/usr/bin/env python3
"""Mill docker-build-cache-factory r1125+. Video codecs × Bluetooth leftovers.

NEW unique-pair catalog after r1077 solvers/IR.
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
_spec = importlib.util.spec_from_file_location("dbc_mill_r1077", HERE / "dbc-mill-r1077.py")
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
    "umfpack-cache",
    "ir-spi-tx-leftover",
    "pinocchio-cache",
    "rc-core-leftover",
)

# slug, env, tool, old, new, artifact, mb
_CRYPTO = [
    ("x264-cli-cache", "X264_HOME", "x264", "0.164.3108", "0.164.3191", "include/x264.h", "3MB"),
    ("x265-cli-cache", "X265_HOME", "x265", "3.5", "4.1", "include/x265.h", "4MB"),
    ("dav1d-dec-cache", "DAV1D_HOME", "dav1d", "1.4.3", "1.5.1", "include/dav1d/dav1d.h", "2MB"),
    ("svt-av1-enc-cache", "SVT_AV1_HOME", "SvtAv1EncApp", "2.1.2", "2.3.0", "include/svt-av1/EbSvtAv1Enc.h", "5MB"),
    ("aomenc-cli-cache", "LIBAOM_HOME", "aomenc", "3.9.1", "3.12.1", "include/aom/aom_encoder.h", "6MB"),
    ("rav1e-cli-cache", "RAV1E_HOME", "rav1e", "0.7.1", "0.8.1", "include/rav1e/rav1e.h", "4MB"),
    ("libvpx-enc-cache", "LIBVPX_HOME", "vpxenc", "1.14.1", "1.15.2", "include/vpx/vp8cx.h", "3MB"),
    ("libvmaf-model-cache", "VMAF_MODEL_PATH", "vmaf", "3.0.0", "3.0.0-post", "share/vmaf/model/vmaf_v0.6.1.json", "8MB"),
    ("kvazaar-enc-cache", "KVAZAAR_HOME", "kvazaar", "2.3.1", "2.3.1-post", "include/kvazaar.h", "2MB"),
    ("vvenc-cli-cache", "VVENC_HOME", "vvencapp", "1.12.0", "1.13.1", "include/vvenc/vvenc.h", "5MB"),
    ("vvdec-cli-cache", "VVDEC_HOME", "vvdecapp", "2.3.0", "3.0.0", "include/vvdec/vvdec.h", "3MB"),
    ("openh264-enc-cache", "OPENH264_HOME", "h264enc", "2.4.1", "2.6.0", "include/wels/codec_api.h", "3MB"),
    ("libde265-dec-cache", "LIBDE265_HOME", "dec265", "1.0.15", "1.0.16", "include/libde265/de265.h", "2MB"),
    ("libheif-tool-cache", "LIBHEIF_PLUGIN_PATH", "heif-convert", "1.17.6", "1.19.7", "lib/libheif/plugins", "4MB"),
    ("jpegxl-tool-cache", "LIBJXL_HOME", "cjxl", "0.10.3", "0.11.1", "include/jxl/encode.h", "6MB"),
    ("libavif-tool-cache", "LIBAVIF_HOME", "avifenc", "1.1.1", "1.2.1", "include/avif/avif.h", "3MB"),
    ("libwebp-tool-cache", "LIBWEBP_HOME", "cwebp", "1.4.0", "1.5.0", "include/webp/encode.h", "2MB"),
    ("mozjpeg-tool-cache", "MOZJPEG_HOME", "cjpeg", "4.1.5", "4.1.5-post", "include/jpeglib.h", "2MB"),
    ("davs2-dec-cache", "DAVS2_HOME", "davs2", "1.7", "1.7-post", "include/davs2.h", "2MB"),
    ("xavs2-enc-cache", "XAVS2_HOME", "xavs2", "1.4", "1.4-post", "include/xavs2.h", "3MB"),
    ("uavs3e-enc-cache", "UAVS3E_HOME", "uavs3enc", "1.1.0", "1.2.0", "include/uavs3e/uavs3e.h", "3MB"),
    ("uavs3d-dec-cache", "UAVS3D_HOME", "uavs3dec", "1.1.0", "1.2.0", "include/uavs3d.h", "2MB"),
    ("svt-hevc-enc-cache", "SVT_HEVC_HOME", "SvtHevcEncApp", "1.5.1", "1.5.1-post", "include/svt-hevc/EbApi.h", "4MB"),
    ("svt-vp9-enc-cache", "SVT_VP9_HOME", "SvtVp9EncApp", "0.3.0", "0.3.0-post", "include/svt-vp9/EbSvtVp9Enc.h", "3MB"),
    ("libtheora-enc-cache", "THEORA_HOME", "encoder_example", "1.1.1", "1.2.0", "include/theora/theoraenc.h", "2MB"),
    ("fdk-aac-enc-cache", "FDK_AAC_HOME", "aac-enc", "2.0.3", "2.0.3-post", "include/fdk-aac/aacenc_lib.h", "2MB"),
    ("shine-mp3-enc-cache", "SHINE_HOME", "shineenc", "3.1.1", "3.1.1-post", "include/shine/layer3.h", "1MB"),
    ("wavpack-cli-cache", "WAVPACK_HOME", "wavpack", "5.7.0", "5.8.1", "include/wavpack/wavpack.h", "2MB"),
    ("soxr-lib-cache", "SOXR_HOME", "soxr", "0.1.3", "0.1.3-post", "include/soxr.h", "1MB"),
    ("lame-mp3-enc-cache", "LAME_HOME", "lame", "3.100", "3.100-post", "include/lame/lame.h", "2MB"),
    ("vo-amrwbenc-cache", "VO_AMRWBENC_HOME", "amrwb-enc", "0.1.3", "0.1.3-post", "include/vo-amrwbenc/enc_if.h", "1MB"),
    ("opencore-amr-cache", "OPENCORE_AMR_HOME", "amrnb-enc", "0.1.6", "0.1.6-post", "include/opencore-amrnb/interf_enc.h", "1MB"),
    ("twolame-enc-cache", "TWOLAME_HOME", "twolame", "0.4.0", "0.4.0-post", "include/twolame.h", "1MB"),
    ("faac-enc-cache", "FAAC_HOME", "faac", "1.30", "1.30-post", "include/faac.h", "1MB"),
    ("vo-aacenc-cache", "VO_AACENC_HOME", "vo-aacenc", "0.1.3", "0.1.3-post", "include/vo-aacenc/voAAC.h", "1MB"),
    ("libgsm-codec-cache", "GSM_HOME", "toast", "1.0.22", "1.0.22-post", "include/gsm/gsm.h", "1MB"),
    ("libopus-enc-cache", "OPUS_HOME", "opusenc", "1.5.2", "1.5.2-post", "include/opus/opus.h", "2MB"),
    ("flac-enc-cache", "FLAC_HOME", "flac", "1.4.3", "1.5.0", "include/FLAC/stream_encoder.h", "2MB"),
    ("libvorbis-enc-cache", "VORBIS_HOME", "oggenc", "1.3.7", "1.3.7-post", "include/vorbis/vorbisenc.h", "2MB"),
    ("libogg-mux-cache", "OGG_HOME", "ogginfo", "1.3.5", "1.3.6", "include/ogg/ogg.h", "1MB"),
    ("speex-enc-cache", "SPEEX_HOME", "speexenc", "1.2.1", "1.2.1-post", "include/speex/speex.h", "1MB"),
    ("codec2-enc-cache", "CODEC2_HOME", "c2enc", "1.2.0", "1.2.0-post", "include/codec2/codec2.h", "2MB"),
    ("lilv-lv2-cache", "LV2_PATH", "lv2ls", "0.24.24", "0.24.26", "lib/lv2", "2MB"),
    ("rubberband-cli-cache", "RUBBERBAND_HOME", "rubberband", "3.3.0", "4.0.0", "include/rubberband/RubberBandStretcher.h", "2MB"),
    ("zimg-lib-cache", "ZIMG_HOME", "zimg", "3.0.5", "3.0.5-post", "include/zimg++.hpp", "2MB"),
    ("libplacebo-cache", "LIBPLACEBO_HOME", "plplay", "7.349.0", "7.351.0", "include/libplacebo/renderer.h", "4MB"),
    ("vapoursynth-cache", "VAPOURSYNTH_HOME", "vspipe", "68", "70", "include/vapoursynth/VapourSynth4.h", "3MB"),
    ("avisynthplus-cache", "AVISYNTH_HOME", "avs2pipemod", "3.7.3", "3.7.5", "include/avisynth/avisynth.h", "4MB"),
]

_GPIO = [
    ("btusb-leftover", "BTUSB_CLEAR", "btusb reset=1", "btusb", "hciconfig -a"),
    ("btintel-leftover", "BTINTEL_CLEAR", "btintel debug=1", "btintel", "ls /sys/module/btintel"),
    ("btrtl-leftover", "BTRTL_CLEAR", "btrtl fw=cache", "btrtl", "ls /lib/firmware/rtl_bt"),
    ("btbcm-leftover", "BTBCM_CLEAR", "btbcm fw=cache", "btbcm", "ls /lib/firmware/brcm"),
    ("btmtk-leftover", "BTMTK_CLEAR", "btmtk fw=cache", "btmtk", "ls /lib/firmware/mediatek"),
    ("hci-uart-leftover", "HCI_UART_CLEAR", "hci_uart proto=cache", "hci_uart", "ls /sys/module/hci_uart"),
    ("hci-vhci-leftover", "HCI_VHCI_CLEAR", "hci_vhci amp=1", "hci_vhci", "ls /dev/vhci"),
    ("rfcomm-leftover", "RFCOMM_CLEAR", "rfcomm debug=1", "rfcomm", "ls /dev/rfcomm*"),
    ("bnep-leftover", "BNEP_CLEAR", "bnep compress=1", "bnep", "ls /sys/module/bnep"),
    ("hidp-leftover", "HIDP_CLEAR", "hidp idle=cache", "hidp", "ls /sys/module/hidp"),
    ("btsdio-leftover", "BTSDIO_CLEAR", "btsdio debug=1", "btsdio", "ls /sys/module/btsdio"),
    ("btqca-leftover", "BTQCA_CLEAR", "btqca fw=cache", "btqca", "ls /lib/firmware/qca"),
    ("btmrvl-leftover", "BTMRVL_CLEAR", "btmrvl debug=1", "btmrvl", "ls /sys/module/btmrvl"),
    ("bt3c-cs-leftover", "BT3C_CS_CLEAR", "bt3c_cs irq=cache", "bt3c_cs", "ls /sys/module/bt3c_cs"),
    ("btbcm-uart-leftover", "BTBCM_UART_CLEAR", "hci_bcm baud=cache", "hci_bcm", "ls /sys/module/hci_bcm"),
    ("btintel-pcie-leftover", "BTINTEL_PCIE_CLEAR", "btintel pcie=1", "btintel", "lspci -nn | rg -i bluetooth"),
    ("ath3k-fw-leftover", "ATH3K_CLEAR", "ath3k fw=cache", "ath3k", "ls /lib/firmware/ath3k-1.fw"),
    ("btmtksdio-leftover", "BTMTKSDIO_CLEAR", "btmtksdio fw=cache", "btmtksdio", "ls /sys/module/btmtksdio"),
    ("btmtkuart-leftover", "BTMTKUART_CLEAR", "btmtkuart baud=cache", "btmtkuart", "ls /sys/module/btmtkuart"),
    ("hci-intel-leftover", "HCI_INTEL_CLEAR", "hci_intel fw=cache", "hci_intel", "ls /sys/module/hci_intel"),
    ("hci-qca-leftover", "HCI_QCA_CLEAR", "hci_qca fw=cache", "hci_qca", "ls /sys/module/hci_qca"),
    ("hci-ll-leftover", "HCI_LL_CLEAR", "hci_ll proto=cache", "hci_ll", "ls /sys/module/hci_ll"),
    ("hci-h4-leftover", "HCI_H4_CLEAR", "hci_h4 proto=cache", "hci_h4", "ls /sys/module/hci_h4"),
    ("hci-h5-leftover", "HCI_H5_CLEAR", "hci_h5 proto=cache", "hci_h5", "ls /sys/module/hci_h5"),
    ("hci-bcsp-leftover", "HCI_BCSP_CLEAR", "hci_bcsp proto=cache", "hci_bcsp", "ls /sys/module/hci_bcsp"),
    ("btmrvl-sdio-leftover", "BTMRVL_SDIO_CLEAR", "btmrvl_sdio fw=cache", "btmrvl_sdio", "ls /sys/module/btmrvl_sdio"),
    ("btwilink-leftover", "BTWILINK_CLEAR", "btwilink debug=1", "btwilink", "ls /sys/module/btwilink"),
    ("hci-nokia-leftover", "HCI_NOKIA_CLEAR", "hci_nokia proto=cache", "hci_nokia", "ls /sys/module/hci_nokia"),
    ("hci-ag6xx-leftover", "HCI_AG6XX_CLEAR", "hci_ag6xx fw=cache", "hci_ag6xx", "ls /sys/module/hci_ag6xx"),
    ("hci-mrvl-leftover", "HCI_MRVL_CLEAR", "hci_mrvl proto=cache", "hci_mrvl", "ls /sys/module/hci_mrvl"),
    ("btnxpuart-leftover", "BTNXPUART_CLEAR", "btnxpuart baud=cache", "btnxpuart", "ls /sys/module/btnxpuart"),
    ("btqcomsmd-leftover", "BTQCOMSMD_CLEAR", "btqcomsmd debug=1", "btqcomsmd", "ls /sys/module/btqcomsmd"),
    ("dtl1-cs-leftover", "DTL1_CS_CLEAR", "dtl1_cs irq=cache", "dtl1_cs", "ls /sys/module/dtl1_cs"),
    ("bluecard-cs-leftover", "BLUECARD_CS_CLEAR", "bluecard_cs irq=cache", "bluecard_cs", "ls /sys/module/bluecard_cs"),
    ("btuart-cs-leftover", "BTUART_CS_CLEAR", "btuart_cs irq=cache", "btuart_cs", "ls /sys/module/btuart_cs"),
    ("bcm203x-fw-leftover", "BCM203X_CLEAR", "bcm203x fw=cache", "bcm203x", "ls /lib/firmware/BCM2033-FW.bin"),
    ("bfusb-fw-leftover", "BFUSB_CLEAR", "bfusb fw=cache", "bfusb", "ls /sys/module/bfusb"),
    ("bpa10x-leftover", "BPA10X_CLEAR", "bpa10x debug=1", "bpa10x", "ls /sys/module/bpa10x"),
    ("sco-bt-leftover", "SCO_BT_CLEAR", "sco mtu=cache", "sco", "ls /sys/module/sco"),
    ("l2cap-bt-leftover", "L2CAP_BT_CLEAR", "l2cap ertm=1", "bluetooth", "ls /sys/module/bluetooth"),
    ("bt-core-leftover", "BT_CORE_CLEAR", "bluetooth disable_esco=1", "bluetooth", "hciconfig -a"),
    ("hci-amp-leftover", "HCI_AMP_CLEAR", "hci_vhci amp=1", "hci_vhci", "ls /dev/vhci"),
    ("hci-serdev-leftover", "HCI_SERDEV_CLEAR", "hci_serdev proto=cache", "hci_uart", "ls /sys/module/hci_uart"),
    ("hci-bcm4377-leftover", "HCI_BCM4377_CLEAR", "hci_bcm4377 fw=cache", "hci_bcm4377", "ls /sys/module/hci_bcm4377"),
    ("btintel-nvs-leftover", "BTINTEL_NVS_CLEAR", "btintel nvs=cache", "btintel", "ls /lib/firmware/intel"),
    ("btrtl-uart-leftover", "BTRTL_UART_CLEAR", "hci_rtl baud=cache", "hci_btrtl", "ls /sys/module/hci_btrtl"),
    ("ath3k-dfu-leftover", "ATH3K_DFU_CLEAR", "ath3k dfu=cache", "ath3k", "ls /lib/firmware/ath3k-1.fw"),
    ("hci-ath3k-leftover", "HCI_ATH3K_CLEAR", "hci_ath3k proto=cache", "hci_ath3k", "ls /sys/module/hci_ath3k"),
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
        mb, f"{sib} (unique {slug.split('-')[0]} cache, not prior NGS/astro/speech/solver catalogs)",
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
