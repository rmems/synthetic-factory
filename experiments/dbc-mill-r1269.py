#!/usr/bin/env python3
"""Mill docker-build-cache-factory r1269+. Fonts/shapers × PPP/L2TP leftovers.

NEW unique-pair catalog after r1221 quantum/USB-gadget.
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
_spec = importlib.util.spec_from_file_location("dbc_mill_r1221", HERE / "dbc-mill-r1221.py")
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
    "qiskit-terra-cache",
    "usb-f-acm-leftover",
    "amazon-braket-default-sim-cache",
    "s3c-hsudc-leftover",
)

_CRYPTO = [
    ("graphite2-shaper-cache", "GRAPHITE2_HOME", "gr2fonttest", "1.3.14", "1.3.14-post", "include/graphite2/Font.h", "1MB"),
    ("icu4c-data-cache", "ICU_DATA", "icuinfo", "74.2", "76.1", "share/icu/74.2/icudt74l.dat", "32MB"),
    ("fribidi-lib-cache", "FRIBIDI_HOME", "fribidi", "1.0.15", "1.0.16", "include/fribidi/fribidi.h", "1MB"),
    ("libraqm-lib-cache", "RAQM_HOME", "raqm-test", "0.10.1", "0.10.2", "include/raqm.h", "1MB"),
    ("harfbuzz-icu-cache", "HARFBUZZ_HOME", "hb-shape", "9.0.0", "10.4.0", "include/harfbuzz/hb-icu.h", "4MB"),
    ("fontconfig-conf-cache", "FONTCONFIG_PATH", "fc-cache", "2.15.0", "2.16.0", "etc/fonts/fonts.conf", "2MB"),
    ("pango-fc-cache", "PANGO_LIBDIR", "pango-view", "1.54.0", "1.56.3", "lib/pango/1.8.0/modules", "5MB"),
    ("cairo-ft-cache", "CAIRO_HOME", "cairo-trace", "1.18.2", "1.18.4", "include/cairo/cairo-ft.h", "4MB"),
    ("woff2-cli-cache", "WOFF2_HOME", "woff2_compress", "1.0.2", "1.0.2-post", "include/woff2/encode.h", "1MB"),
    ("sfntly-cache", "SFNTLY_HOME", "sfntly", "1.0.0", "1.0.0-post", "include/sfntly/font.h", "2MB"),
    ("otfcc-cli-cache", "OTFCC_HOME", "otfccdump", "0.10.4", "0.10.4-post", "share/otfcc/otfccdump.md", "2MB"),
    ("fonttools-ttx-cache", "FONTTOOLS_HOME", "ttx", "4.53.1", "4.56.0", "lib/python3/dist-packages/fontTools/ttLib", "8MB"),
    ("ufo2ft-cache", "UFO2FT_HOME", "python3", "3.2.8", "3.4.1", "lib/python3/dist-packages/ufo2ft/__init__.py", "2MB"),
    ("glyphslib-cache", "GLYPHSLIB_HOME", "python3", "6.8.1", "6.9.5", "lib/python3/dist-packages/glyphsLib/__init__.py", "3MB"),
    ("afdko-tools-cache", "AFDKO_HOME", "makeotf", "4.0.1", "4.0.2", "share/afdko/resources", "9MB"),
    ("psautohint-cache", "PSAUTOHINT_HOME", "psautohint", "2.4.0", "2.4.0-post", "lib/python3/dist-packages/psautohint/__init__.py", "2MB"),
    ("ttfautohint-cache", "TTFAUTOHINT_HOME", "ttfautohint", "1.8.4", "1.8.4-post", "include/ttfautohint.h", "1MB"),
    ("fontmake-cache", "FONTMAKE_HOME", "fontmake", "3.9.0", "3.10.0", "lib/python3/dist-packages/fontmake/__init__.py", "3MB"),
    ("skia-pathops-cache", "SKIA_PATHOPS_HOME", "python3", "0.8.0", "0.8.0-post", "lib/python3/dist-packages/pathops/__init__.py", "2MB"),
    ("compreffor-cache", "COMPREFFOR_HOME", "compreffor", "0.5.5", "0.5.6", "lib/python3/dist-packages/compreffor/__init__.py", "1MB"),
    ("cu2qu-cache", "CU2QU_HOME", "cu2qu", "1.6.7", "1.6.7-post", "lib/python3/dist-packages/cu2qu/__init__.py", "1MB"),
    ("booleanoperations-cache", "BOOLEANOPERATIONS_HOME", "python3", "0.9.0", "0.9.1", "lib/python3/dist-packages/booleanOperations/__init__.py", "1MB"),
    ("brotli-woff-cache", "BROTLI_HOME", "brotli", "1.1.0", "1.1.0-post", "include/brotli/encode.h", "2MB"),
    ("zopfli-font-cache", "ZOPFLI_HOME", "zopfli", "1.0.3", "1.0.3-post", "include/zopfli/zopfli.h", "1MB"),
    ("ots-sanitize-cache", "OTS_HOME", "ots-sanitize", "9.1.0", "9.2.0", "include/opentype-sanitiser.h", "2MB"),
    ("fontbakery-cache", "FONTBAKERY_HOME", "fontbakery", "0.12.10", "0.13.2", "lib/python3/dist-packages/fontbakery/__init__.py", "6MB"),
    ("gftools-cache", "GFTOOLS_HOME", "gftools", "0.9.68", "0.9.80", "lib/python3/dist-packages/gftools/__init__.py", "4MB"),
    ("nototools-cache", "NOTOTOOLS_HOME", "python3", "0.2.20", "0.2.20-post", "lib/python3/dist-packages/nototools/__init__.py", "3MB"),
    ("uharfbuzz-cache", "UHARFBUZZ_HOME", "python3", "0.40.0", "0.45.1", "lib/python3/dist-packages/uharfbuzz/__init__.py", "3MB"),
    ("rustybuzz-cache", "RUSTYBUZZ_HOME", "rustybuzz", "0.18.0", "0.20.1", "include/rustybuzz.h", "2MB"),
    ("swash-shaper-cache", "SWASH_HOME", "swash", "0.1.19", "0.2.1", "include/swash/shape.h", "2MB"),
    ("cosmic-text-cache", "COSMIC_TEXT_HOME", "cosmic-text", "0.12.1", "0.14.1", "include/cosmic_text.h", "3MB"),
    ("fontdue-cache", "FONTDUE_HOME", "fontdue", "0.9.2", "0.9.3", "include/fontdue.h", "1MB"),
    ("ab-glyph-cache", "AB_GLYPH_HOME", "ab_glyph", "0.2.28", "0.2.29", "include/ab_glyph.h", "1MB"),
    ("ttf-parser-cache", "TTF_PARSER_HOME", "ttf-parser", "0.25.0", "0.25.1", "include/ttf_parser.h", "1MB"),
    ("owned-ttf-cache", "OWNED_TTF_HOME", "owned_ttf", "0.4.1", "0.4.1-post", "include/owned_ttf.h", "1MB"),
    ("tiny-skia-cache", "TINY_SKIA_HOME", "tiny-skia", "0.11.4", "0.11.4-post", "include/tiny_skia.h", "2MB"),
    ("resvg-cli-cache", "RESVG_HOME", "resvg", "0.43.0", "0.45.1", "include/resvg.h", "5MB"),
    ("usvg-cli-cache", "USVG_HOME", "usvg", "0.43.0", "0.45.1", "share/usvg/usvg.md", "3MB"),
    ("msdfgen-cli-cache", "MSDFGEN_HOME", "msdfgen", "1.12", "1.12-post", "include/msdfgen.h", "2MB"),
    ("msdf-atlas-gen-cache", "MSDF_ATLAS_HOME", "msdf-atlas-gen", "1.3", "1.3-post", "include/msdf-atlas-gen.h", "2MB"),
    ("stb-truetype-cache", "STB_TRUETYPE_HOME", "stb-truetype", "2.20", "2.20-post", "include/stb_truetype.h", "1MB"),
    ("freetype-gl-cache", "FREETYPE_GL_HOME", "freetype-gl", "1.0", "1.0-post", "include/freetype-gl.h", "1MB"),
    ("sdf-atlas-cache", "SDF_ATLAS_HOME", "sdf-atlas", "1.0", "1.0-post", "include/sdf_atlas.h", "1MB"),
    ("hb-view-cli-cache", "HB_VIEW_HOME", "hb-view", "9.0.0", "10.4.0", "share/harfbuzz/hb-view.1", "1MB"),
    ("hb-shape-cli-cache", "HB_SHAPE_HOME", "hb-shape", "9.0.0", "10.4.0", "share/harfbuzz/hb-shape.1", "1MB"),
    ("pango-view-cli-cache", "PANGO_VIEW_HOME", "pango-view", "1.54.0", "1.56.3", "share/pango/pango-view.1", "1MB"),
    ("ots-idempotent-cache", "OTS_IDEM_HOME", "ots-idempotent", "9.1.0", "9.2.0", "share/ots/ots-idempotent.md", "1MB"),
]

_GPIO = [
    ("ppp-generic-leftover", "PPP_GENERIC_CLEAR", "ppp_generic debug=1", "ppp_generic", "ls /sys/module/ppp_generic"),
    ("pppoe-leftover", "PPPOE_CLEAR", "pppoe debug=1", "pppoe", "ls /sys/module/pppoe"),
    ("pptp-gre-leftover", "PPTP_CLEAR", "pptp log_level=cache", "pptp", "ls /sys/module/pptp"),
    ("pppox-leftover", "PPPOX_CLEAR", "pppox debug=1", "pppox", "ls /sys/module/pppox"),
    ("ppp-async-leftover", "PPP_ASYNC_CLEAR", "ppp_async debug=1", "ppp_async", "ls /sys/module/ppp_async"),
    ("ppp-synctty-leftover", "PPP_SYNCTTY_CLEAR", "ppp_synctty debug=1", "ppp_synctty", "ls /sys/module/ppp_synctty"),
    ("ppp-deflate-leftover", "PPP_DEFLATE_CLEAR", "ppp_deflate debug=1", "ppp_deflate", "ls /sys/module/ppp_deflate"),
    ("ppp-mppe-leftover", "PPP_MPPE_CLEAR", "ppp_mppe debug=1", "ppp_mppe", "ls /sys/module/ppp_mppe"),
    ("l2tp-ppp-leftover", "L2TP_PPP_CLEAR", "l2tp_ppp debug=1", "l2tp_ppp", "ls /sys/module/l2tp_ppp"),
    ("pppol2tp-leftover", "PPPOL2TP_CLEAR", "l2tp_ppp debug=1", "l2tp_ppp", "ls /sys/module/l2tp_ppp"),
    ("ppp-bsdcomp-leftover", "PPP_BSDCOMP_CLEAR", "ppp_bsdcomp debug=1", "ppp_bsdcomp", "ls /sys/module/ppp_bsdcomp"),
    ("slhc-leftover", "SLHC_CLEAR", "slhc debug=1", "slhc", "ls /sys/module/slhc"),
    ("pppoe-disc-leftover", "PPPOE_DISC_CLEAR", "pppoe discovery=1", "pppoe", "ls /sys/module/pppoe"),
    ("l2tp-core-leftover", "L2TP_CORE_CLEAR", "l2tp_core debug=1", "l2tp_core", "ls /sys/module/l2tp_core"),
    ("l2tp-netlink-leftover", "L2TP_NETLINK_CLEAR", "l2tp_netlink debug=1", "l2tp_netlink", "ls /sys/module/l2tp_netlink"),
    ("l2tp-eth-leftover", "L2TP_ETH_CLEAR", "l2tp_eth debug=1", "l2tp_eth", "ls /sys/module/l2tp_eth"),
    ("l2tp-ip-leftover", "L2TP_IP_CLEAR", "l2tp_ip debug=1", "l2tp_ip", "ls /sys/module/l2tp_ip"),
    ("l2tp-ip6-leftover", "L2TP_IP6_CLEAR", "l2tp_ip6 debug=1", "l2tp_ip6", "ls /sys/module/l2tp_ip6"),
    ("pppoatm-leftover", "PPPOATM_CLEAR", "pppoatm debug=1", "pppoatm", "ls /sys/module/pppoatm"),
    ("ppp-mppe-stateless-leftover", "PPP_MPPE_STATELESS_CLEAR", "ppp_mppe stateless=1", "ppp_mppe", "ls /sys/module/ppp_mppe"),
    ("ppp-deflate-draft-leftover", "PPP_DEFLATE_DRAFT_CLEAR", "ppp_deflate draft=1", "ppp_deflate", "ls /sys/module/ppp_deflate"),
    ("pptp-callmgr-leftover", "PPTP_CALLMGR_CLEAR", "pptp callmgr=cache", "pptp", "ls /sys/module/pptp"),
    ("l2tp-debug-leftover", "L2TP_DEBUG_CLEAR", "l2tp_core debug=cache", "l2tp_core", "ls /sys/module/l2tp_core"),
    ("ppp-unit-leftover", "PPP_UNIT_CLEAR", "ppp_generic unit=cache", "ppp_generic", "ls /sys/class/net/ppp0"),
    ("pppoe-ac-leftover", "PPPOE_AC_CLEAR", "pppoe ac_name=cache", "pppoe", "ls /sys/module/pppoe"),
    ("pppoe-sess-leftover", "PPPOE_SESS_CLEAR", "pppoe sess=cache", "pppoe", "ls /sys/module/pppoe"),
    ("l2tpv3-eth-leftover", "L2TPV3_ETH_CLEAR", "l2tp_eth cookie=cache", "l2tp_eth", "ls /sys/module/l2tp_eth"),
    ("l2tpv3-ip-leftover", "L2TPV3_IP_CLEAR", "l2tp_ip cookie=cache", "l2tp_ip", "ls /sys/module/l2tp_ip"),
    ("ppp-multilink-leftover", "PPP_ML_CLEAR", "ppp_generic mp_shortseq=1", "ppp_generic", "ls /sys/module/ppp_generic"),
    ("ppp-vj-leftover", "PPP_VJ_CLEAR", "slhc vj=1", "slhc", "ls /sys/module/slhc"),
    ("ppp-ccp-leftover", "PPP_CCP_CLEAR", "ppp_deflate ccp=1", "ppp_deflate", "ls /sys/module/ppp_deflate"),
    ("ppp-eap-leftover", "PPP_EAP_CLEAR", "ppp_generic eap=1", "ppp_generic", "ls /sys/module/ppp_generic"),
    ("ppp-chap-leftover", "PPP_CHAP_CLEAR", "ppp_generic chap=1", "ppp_generic", "ls /sys/module/ppp_generic"),
    ("ppp-pap-leftover", "PPP_PAP_CLEAR", "ppp_generic pap=1", "ppp_generic", "ls /sys/module/ppp_generic"),
    ("ppp-lcp-leftover", "PPP_LCP_CLEAR", "ppp_generic lcp=1", "ppp_generic", "ls /sys/module/ppp_generic"),
    ("ppp-ipcp-leftover", "PPP_IPCP_CLEAR", "ppp_generic ipcp=1", "ppp_generic", "ls /sys/module/ppp_generic"),
    ("ppp-ipv6cp-leftover", "PPP_IPV6CP_CLEAR", "ppp_generic ipv6cp=1", "ppp_generic", "ls /sys/module/ppp_generic"),
    ("pptp-gre-seq-leftover", "PPTP_GRE_SEQ_CLEAR", "pptp seq=1", "pptp", "ls /sys/module/pptp"),
    ("l2tp-udp-leftover", "L2TP_UDP_CLEAR", "l2tp_core encap=udp", "l2tp_core", "ls /sys/module/l2tp_core"),
    ("l2tp-seq-leftover", "L2TP_SEQ_CLEAR", "l2tp_core seq=1", "l2tp_core", "ls /sys/module/l2tp_core"),
    ("pppox-pptp-leftover", "PPPOX_PPTP_CLEAR", "pppox proto=pptp", "pppox", "ls /sys/module/pppox"),
    ("pppox-l2tp-leftover", "PPPOX_L2TP_CLEAR", "pppox proto=l2tp", "pppox", "ls /sys/module/pppox"),
    ("pppox-pppoe-leftover", "PPPOX_PPPOE_CLEAR", "pppox proto=pppoe", "pppox", "ls /sys/module/pppox"),
    ("ppp-compress-leftover", "PPP_COMPRESS_CLEAR", "ppp_bsdcomp bits=cache", "ppp_bsdcomp", "ls /sys/module/ppp_bsdcomp"),
    ("ppp-mppe-128-leftover", "PPP_MPPE_128_CLEAR", "ppp_mppe bits=128", "ppp_mppe", "ls /sys/module/ppp_mppe"),
    ("ppp-mppe-40-leftover", "PPP_MPPE_40_CLEAR", "ppp_mppe bits=40", "ppp_mppe", "ls /sys/module/ppp_mppe"),
    ("l2tp-reorder-leftover", "L2TP_REORDER_CLEAR", "l2tp_core reorder=1", "l2tp_core", "ls /sys/module/l2tp_core"),
    ("ppp-syncppp-leftover", "PPP_SYNCPPP_CLEAR", "ppp_synctty sync=1", "ppp_synctty", "ls /sys/module/ppp_synctty"),
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
        mb, f"{sib} (unique {slug.split('-')[0]} cache, not prior NGS/astro/speech/solver/video/mq/quantum catalogs)",
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
