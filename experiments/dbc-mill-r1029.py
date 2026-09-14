#!/usr/bin/env python3
"""Mill docker-build-cache-factory r1029+. DB engines × I2C/SPI/WDT leftovers.

NEW unique-pair catalog after r981 DB/I2C.
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
_spec = importlib.util.spec_from_file_location("dbc_mill_r981", HERE / "dbc-mill-r981.py")
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
    "duckdb-httpfs-cache",
    "i2c-i801-leftover",
    "botan-cache",
    "pca953x-leftover",
)

# slug, env, tool, old, new, artifact, mb
_CRYPTO = [
    ("odin-lang-cache", "ODIN_ROOT", "odin", "dev-2024-05", "dev-2025-01", "share/odin/base/runtime.odin", "9MB"),
    ("vlang-cache", "VMODULES", "v", "0.4.6", "0.4.9", "share/v/vlib/builtin/builtin.v", "6MB"),
    ("nimble-pkgs-cache", "NIMBLE_DIR", "nimble", "0.14.2", "0.16.3", "share/nimble/pkgs2", "4MB"),
    ("crystal-shards-cache", "SHARDS_CACHE_PATH", "shards", "0.17.4", "0.19.0", "share/shards/cache", "3MB"),
    ("ponyc-pkg-cache", "PONYPATH", "ponyc", "0.58.3", "0.58.7", "share/pony/packages", "8MB"),
    ("red-lang-cache", "RED_HOME", "red", "0.6.5", "0.6.6", "share/red/runtime.red", "5MB"),
    ("factor-image-cache", "FACTOR_ROOTS", "factor", "0.99", "0.100", "share/factor/factor.image", "18MB"),
    ("io-lang-cache", "IO_HOME", "io", "2017.09.06", "2019.05.22", "lib/io/addons", "4MB"),
    ("self-world-cache", "SELF_HOME", "Self", "2017.1", "2024.1", "share/self/worlds/Clean.snap", "22MB"),
    ("squeak-vm-cache", "SQUEAK_HOME", "squeakvm", "4.19.2", "4.20.0", "lib/squeak/4.19.2-3315/squeakvm", "3MB"),
    ("pharo-vm-cache", "PHARO_VM", "pharo", "10.2.1", "12.0.0", "lib/pharo/pharo", "7MB"),
    ("newspeak-cache", "NEWSPEAK_HOME", "newspeak", "0.1", "0.2", "share/newspeak/Newspeak.image", "11MB"),
    ("smalltalk-x-cache", "STX_LIBDIR", "stx", "8.0.0", "8.3.0", "lib/smalltalkx/packages", "15MB"),
    ("gnu-smalltalk-cache", "GST_HOME", "gst", "3.2.5", "3.2.91", "share/gnu-smalltalk/kernel", "5MB"),
    ("visualworks-cache", "VISUALWORKS", "vw", "9.2.1", "9.3.1", "share/visualworks/image9.2.1", "28MB"),
    ("dolphin-cache", "DOLPHIN_HOME", "dolphin", "7.1", "7.2", "share/dolphin/Resources", "9MB"),
    ("cuis-image-cache", "CUIS_HOME", "cuis", "6.0", "7.0", "share/cuis/Cuis6.0.image", "8MB"),
    ("squeakjs-cache", "SQUEAKJS_HOME", "squeakjs", "1.2.0", "1.3.0", "share/squeakjs/vm.js", "2MB"),
    ("graalpy-cache", "GRAALPY_HOME", "graalpy", "24.0.1", "24.1.1", "lib/graalpy24.0/lib-python", "31MB"),
    ("graaljs-cache", "GRAALJS_HOME", "js", "24.0.1", "24.1.1", "lib/graaljs/js", "19MB"),
    ("truffleruby-cache", "TRUFFLERUBY_HOME", "truffleruby", "24.0.1", "24.1.1", "lib/truffleruby/lib/ruby", "24MB"),
    ("espresso-java-cache", "ESPRESSO_HOME", "java", "24.0.1", "24.1.1", "lib/espresso/lib/jvm.cfg", "16MB"),
    ("sulong-cache", "SULONG_HOME", "lli", "24.0.1", "24.1.1", "lib/sulong/native/lib", "12MB"),
    ("fastR-cache", "FASTR_HOME", "R", "24.0.1", "24.1.1", "lib/fastr/library", "21MB"),
    ("wasmtime-cache", "WASMTIME_HOME", "wasmtime", "22.0.0", "28.0.0", "share/wasmtime/cranelift", "7MB"),
    ("wasmer-cache", "WASMER_DIR", "wasmer", "4.3.1", "5.0.3", "share/wasmer/libwasmer.so", "6MB"),
    ("wasm3-cache", "WASM3_HOME", "wasm3", "0.5.0", "0.5.0-post", "share/wasm3/wasm3.1", "1MB"),
    ("wamr-cache", "WAMR_HOME", "iwasm", "2.1.1", "2.2.0", "lib/libiwasm.so", "3MB"),
    ("wasm-micro-cache", "WAMR_BH_HOME", "wamrc", "2.1.1", "2.2.0", "share/wamr/wamrc.1", "2MB"),
    ("lucet-cache", "LUCET_HOME", "lucetc", "0.7.0", "0.7.0-post", "share/lucet/lucetc.1", "4MB"),
    ("wasm2c-cache", "WABT_HOME", "wasm2c", "1.0.34", "1.0.36", "share/wabt/wasm2c.1", "2MB"),
    ("binaryen-cache", "BINARYEN_ROOT", "wasm-opt", "117", "120", "share/binaryen/wasm-opt.1", "5MB"),
    ("emscripten-cache-dir", "EM_CACHE", "emcc", "3.1.61", "4.0.1", "share/emscripten/cache/sysroot", "42MB"),
    ("cheerp-cache", "CHEERP_HOME", "clang++", "3.0", "3.0-post", "lib/cheerp/libcxx.bc", "11MB"),
    ("asterius-cache", "ASTERIUS_LIB_DIR", "ahc", "0.0.1", "0.0.2", "share/asterius/rts", "8MB"),
    ("haskell-wasm-cache", "GHC_WASM_HOME", "wasm32-wasi-ghc", "9.8.2", "9.10.1", "lib/wasm32-wasi-ghc-9.8.2", "33MB"),
    ("tinygo-cache", "TINYGOROOT", "tinygo", "0.31.2", "0.35.0", "lib/tinygo/src", "14MB"),
    ("tcc-cache", "TCC_HOME", "tcc", "0.9.27", "0.9.28rc", "lib/tcc/libtcc1.a", "2MB"),
    ("pcc-cache", "PCC_HOME", "pcc", "1.2.0.DEVEL", "1.2.0.DEVEL-post", "lib/pcc/x86_64-linux/libpcc.a", "3MB"),
    ("lcc-cache", "LCCDIR", "lcc", "4.2", "4.2-post", "lib/lcc/rcc", "2MB"),
    ("scc-cache", "SCC_HOME", "scc", "0.1", "0.2", "lib/scc/libscc.a", "2MB"),
    ("cproc-cache", "CPROC_HOME", "cproc", "0.1", "0.2", "share/cproc/cproc.1", "1MB"),
    ("qbe-cache", "QBE_HOME", "qbe", "1.2", "1.2-post", "share/qbe/qbe.1", "1MB"),
    ("chibicc-cache", "CHIBICC_HOME", "chibicc", "0.1", "0.1-post", "share/chibicc/include", "1MB"),
    ("8cc-cache", "EIGHTCC_HOME", "8cc", "1.0", "1.0-post", "share/8cc/include", "1MB"),
    ("cparser-cache", "CPARSER_HOME", "cparser", "1.22.0", "1.22.1", "share/cparser/cparser.1", "2MB"),
    ("sparse-cache", "SPARSE_HOME", "sparse", "0.6.4", "0.6.4-post", "share/sparse/sparse.1", "2MB"),
    ("coccinelle-cache", "COCCI_HOME", "spatch", "1.1.1", "1.3.0", "share/coccinelle/standard.iso", "6MB"),
]

_GPIO = [
    ("snd-hda-intel-leftover", "SND_HDA_INTEL_CLEAR", "snd_hda_intel power_save=1", "snd_hda_intel", "ls /proc/asound"),
    ("snd-usb-audio-leftover", "SND_USB_AUDIO_CLEAR", "snd_usb_audio nrpacks=cache", "snd_usb_audio", "ls /proc/asound"),
    ("snd-soc-core-leftover", "SND_SOC_CORE_CLEAR", "snd_soc_core prealloc=cache", "snd_soc_core", "ls /proc/asound"),
    ("snd-intel8x0-leftover", "SND_INTEL8X0_CLEAR", "snd_intel8x0 ac97_clock=cache", "snd_intel8x0", "ls /proc/asound"),
    ("snd-via82xx-leftover", "SND_VIA82XX_CLEAR", "snd_via82xx ac97_clock=cache", "snd_via82xx", "ls /proc/asound"),
    ("snd-emu10k1-leftover", "SND_EMU10K1_CLEAR", "snd_emu10k1 extin=cache", "snd_emu10k1", "ls /proc/asound"),
    ("snd-ice1712-leftover", "SND_ICE1712_CLEAR", "snd_ice1712 cs8427_timeout=cache", "snd_ice1712", "ls /proc/asound"),
    ("snd-ca0106-leftover", "SND_CA0106_CLEAR", "snd_ca0106 subsystem=cache", "snd_ca0106", "ls /proc/asound"),
    ("snd-hda-codec-realtek-leftover", "SND_HDA_REALTEK_CLEAR", "snd_hda_codec_realtek model=cache", "snd_hda_codec_realtek", "ls /proc/asound"),
    ("snd-hda-codec-hdmi-leftover", "SND_HDA_HDMI_CLEAR", "snd_hda_codec_hdmi static_hdmi_pcm=1", "snd_hda_codec_hdmi", "ls /proc/asound"),
    ("snd-hda-codec-analog-leftover", "SND_HDA_ANALOG_CLEAR", "snd_hda_codec_analog model=cache", "snd_hda_codec_analog", "ls /proc/asound"),
    ("snd-hda-codec-via-leftover", "SND_HDA_VIA_CLEAR", "snd_hda_codec_via model=cache", "snd_hda_codec_via", "ls /proc/asound"),
    ("snd-hda-codec-conexant-leftover", "SND_HDA_CONEXANT_CLEAR", "snd_hda_codec_conexant model=cache", "snd_hda_codec_conexant", "ls /proc/asound"),
    ("snd-hda-codec-cirrus-leftover", "SND_HDA_CIRRUS_CLEAR", "snd_hda_codec_cirrus model=cache", "snd_hda_codec_cirrus", "ls /proc/asound"),
    ("snd-hda-codec-ca0132-leftover", "SND_HDA_CA0132_CLEAR", "snd_hda_codec_ca0132 quirk=cache", "snd_hda_codec_ca0132", "ls /proc/asound"),
    ("snd-ctxfi-leftover", "SND_CTXFI_CLEAR", "snd_ctxfi reference_rate=cache", "snd_ctxfi", "ls /proc/asound"),
    ("snd-oxygen-leftover", "SND_OXYGEN_CLEAR", "snd_oxygen model=cache", "snd_oxygen", "ls /proc/asound"),
    ("snd-virtuoso-leftover", "SND_VIRTUOSO_CLEAR", "snd_virtuoso index=cache", "snd_virtuoso", "ls /proc/asound"),
    ("snd-hdsp-leftover", "SND_HDSP_CLEAR", "snd_hdsp precise_ptr=1", "snd_hdsp", "ls /proc/asound"),
    ("snd-hdspm-leftover", "SND_HDSPM_CLEAR", "snd_hdspm precise_ptr=1", "snd_hdspm", "ls /proc/asound"),
    ("snd-rme9652-leftover", "SND_RME9652_CLEAR", "snd_rme9652 precise_ptr=1", "snd_rme9652", "ls /proc/asound"),
    ("snd-fireface-leftover", "SND_FIREFACE_CLEAR", "snd_fireface midi=cache", "snd_firewire_digi00x", "ls /proc/asound"),
    ("snd-dice-leftover", "SND_DICE_CLEAR", "snd_dice midi=cache", "snd_dice", "ls /proc/asound"),
    ("snd-bebob-leftover", "SND_BEBOB_CLEAR", "snd_bebob midi=cache", "snd_bebob", "ls /proc/asound"),
    ("snd-oxfw-leftover", "SND_OXFW_CLEAR", "snd_oxfw midi=cache", "snd_oxfw", "ls /proc/asound"),
    ("snd-firewire-lib-leftover", "SND_FIREWIRE_LIB_CLEAR", "snd_firewire_lib midi=cache", "snd_firewire_lib", "ls /proc/asound"),
    ("snd-usb-6fire-leftover", "SND_USB_6FIRE_CLEAR", "snd_usb_6fire index=cache", "snd_usb_6fire", "ls /proc/asound"),
    ("snd-usb-us122l-leftover", "SND_USB_US122L_CLEAR", "snd_usb_us122l index=cache", "snd_usb_us122l", "ls /proc/asound"),
    ("snd-usb-usx2y-leftover", "SND_USB_USX2Y_CLEAR", "snd_usb_usx2y index=cache", "snd_usb_usx2y", "ls /proc/asound"),
    ("snd-usb-caiaq-leftover", "SND_USB_CAIAQ_CLEAR", "snd_usb_caiaq index=cache", "snd_usb_caiaq", "ls /proc/asound"),
    ("snd-usb-hiface-leftover", "SND_USB_HIFACE_CLEAR", "snd_usb_hiface index=cache", "snd_usb_hiface", "ls /proc/asound"),
    ("snd-bcd2000-leftover", "SND_BCD2000_CLEAR", "snd_bcd2000 index=cache", "snd_bcd2000", "ls /proc/asound"),
    ("snd-line6-leftover", "SND_LINE6_CLEAR", "snd_usb_line6 index=cache", "snd_usb_line6", "ls /proc/asound"),
    ("snd-podhd-leftover", "SND_PODHD_CLEAR", "snd_podhd index=cache", "snd_podhd", "ls /proc/asound"),
    ("snd-toneport-leftover", "SND_TONEPORT_CLEAR", "snd_toneport index=cache", "snd_toneport", "ls /proc/asound"),
    ("snd-variax-leftover", "SND_VARIAX_CLEAR", "snd_variax index=cache", "snd_variax", "ls /proc/asound"),
    ("snd-aloop-pcm-leftover", "SND_ALOOP_PCM_CLEAR", "snd_aloop pcm_substreams=8", "snd_aloop", "ls /proc/asound"),
    ("snd-dummy-leftover", "SND_DUMMY_CLEAR", "snd_dummy pcm_devs=1", "snd_dummy", "ls /proc/asound"),
    ("snd-virmidi-leftover", "SND_VIRMIDI_CLEAR", "snd_virmidi midi_devs=4", "snd_virmidi", "ls /proc/asound"),
    ("snd-seq-dummy-leftover", "SND_SEQ_DUMMY_CLEAR", "snd_seq_dummy ports=4", "snd_seq_dummy", "ls /proc/asound"),
    ("snd-seq-midi-leftover", "SND_SEQ_MIDI_CLEAR", "snd_seq_midi output_buffer_size=cache", "snd_seq_midi", "ls /proc/asound"),
    ("snd-rawmidi-leftover", "SND_RAWMIDI_CLEAR", "snd_rawmidi output_buffer_size=cache", "snd_rawmidi", "ls /proc/asound"),
    ("snd-timer-leftover", "SND_TIMER_CLEAR", "snd_timer timer=cache", "snd_timer", "ls /proc/asound"),
    ("snd-hrtimer-leftover", "SND_HRTIMER_CLEAR", "snd_hrtimer resolution=cache", "snd_hrtimer", "ls /proc/asound"),
    ("snd-pcm-oss-leftover", "SND_PCM_OSS_CLEAR", "snd_pcm_oss dsp_map=cache", "snd_pcm_oss", "ls /proc/asound"),
    ("snd-mixer-oss-leftover", "SND_MIXER_OSS_CLEAR", "snd_mixer_oss mixer=cache", "snd_mixer_oss", "ls /proc/asound"),
    ("snd-seq-oss-leftover", "SND_SEQ_OSS_CLEAR", "snd_seq_oss maxqlen=cache", "snd_seq_oss", "ls /proc/asound"),
    ("snd-compress-leftover", "SND_COMPRESS_CLEAR", "snd_compress fragment=cache", "snd_compress", "ls /proc/asound"),
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
