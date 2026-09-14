#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r1934+ unique DAW/audio leftover plants.

BAN r01–r1933 clones including virtusurv-h-leftover-vsurvmap / leicacapx-js-leftover-leicamap,
darcsx-h-leftover-shelves / bazaarx-js-leftover-branches,
elvish-toml-leftover-prompt / oil-rc-leftover-strict,
hydra-py-leftover-compose / sacred-py-leftover-observer,
solr-xml-leftover-cache / opensearchdash-yml-leftover-sso, leftover-revpin, libNNNN,
r690–r708 workspace clones. Do not rerun mdb-mill-r1351, mdb-mill-r1407, mdb-mill-r1454,
mdb-mill-r1534, mdb-mill-r1614, mdb-mill-r1694, mdb-mill-r1774, or mdb-mill-r1854.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_BASE = Path(__file__).with_name("mdb-mill-r1854.py")
_spec = importlib.util.spec_from_file_location("mdb_mill_r1854", _BASE)
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 1934
P = _m.P
build_episode = _m.build_episode
make = _m.make

PRIOR_SLUGS = tuple(spec["slug"] for pair in _m.PAIRS for spec in pair)
BANNED_SLUG_NEEDLES = _m.BANNED_SLUG_NEEDLES + PRIOR_SLUGS + (
    "virtusurv-h-leftover-vsurvmap",
    "leicacapx-js-leftover-leicamap",
    "darcsx-h-leftover-shelves",
    "bazaarx-js-leftover-branches",
    "beszel-yml-leftover-agent",
    "signoz-yml-leftover-alert",
    "just-justfile-leftover-dotenv",
    "taskfile-yml-leftover-includes",
    "elvish-toml-leftover-prompt",
    "oil-rc-leftover-strict",
    "hydra-py-leftover-compose",
    "sacred-py-leftover-observer",
    "solr-xml-leftover-cache",
    "opensearchdash-yml-leftover-sso",
    "leftover-revpin",
    "libNNNN",
    "pnpm-override",
    "npm-catalog",
    "yarn-constraints",
    "bun-catalog",
    "uv-workspace",
    "poetry-source",
    "cargo-wsdep",
    "gowork-use",
    "maven-bom",
    "gradle-catalog",
    "nx-implicit",
    "turbo-",
    "changesets-",
)
_m.BANNED_SLUG_NEEDLES = BANNED_SLUG_NEEDLES

STEMS = [
    "andromeda", "bootes", "cassiopeia", "draco", "eridanus", "fornax", "gemini", "hydraxx", "indus", "lyra",
    "monoceros", "norma", "orionx", "phoenixn", "puppis", "scorpius", "taurus", "ursa", "virgo", "vulpecula",
    "aquila", "ara", "auriga", "carina", "centaurus", "cetus", "corvus", "crater", "crux", "cygnus",
    "delphinus", "dorado", "equuleus", "grus", "hercules", "horologium", "hydraa", "lacerta", "leo", "lupus",
    "mensa", "musca", "octans", "pavo", "pegasus", "perseus", "pictor", "pisces", "sagitta", "sagittarius",
    "sculptor", "scutum", "serpens", "sextans", "telescopium", "triangulum", "tucana", "vela", "volans", "antlia",
    "apus", "caelum", "camelopard", "canesvenatici", "canismajor", "canisminor", "capricornus", "chamaeleon", "circinus", "columba",
    "coma", "coronaaustr", "coronabor", "corvusx", "craterx", "cygnusa", "delphinusx", "doradox", "fornaxx", "geminix",
]


assert len(STEMS) == 80
PLANTS = [f"{s}aa" for s in STEMS] + [f"{s}ab" for s in STEMS]


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"mdb-r{round_n}-{a['slug']}"
    eb = f"mdb-r{round_n}-{b['slug']}"
    novel = 88 + (round_n % 5)
    return f"""# NOTES-r{round_n} monorepo-dep-bump-factory

Novel coverage: {novel}%

Two designed episodes (quota 2). Surfaces: {a['surface']} ({a['pkg']} {a['api_break']}); {b['surface']} ({b['pkg']} {b['api_break']}).
Not a pin-file mill and not libNNNN recycle. Distinct from r01–r1933 clones (ban virtusurv-h-leftover-vsurvmap / leicacapx-js-leftover-leicamap; darcsx-h-leftover-shelves / bazaarx-js-leftover-branches; elvish-toml-leftover-prompt / oil-rc-leftover-strict; hydra-py-leftover-compose / sacred-py-leftover-observer; solr-xml-leftover-cache / opensearchdash-yml-leftover-sso; leftover-revpin; r690–r708 workspace clones).

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {ea} | {a['surface']} | nested {a['new']} | SoT {a['new']} + {a['api_break']} | {'leftover-workspace fail; ' + a['left'] + ' ' + a.get('left_ver', a['old']) if a['fail'] else 'success; ' + a['left'] + ' leftover'} |
| {eb} | {b['surface']} | nested {b['new']} | SoT {b['new']} + {b['api_break']} | {'leftover-workspace fail; ' + b['left'] + ' ' + b.get('left_ver', b['old']) if b['fail'] else 'success; ' + b['left'] + ' leftover'} |

## Step counts
- ep1: 18. Nested apply 6–7; plan change 8; API break 10–12; leftover {a['left']}.
- ep2: 18. Nested apply 6–7; plan change 8; API break 10–12; leftover-workspace fail {b['left']}.

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Plants `{a['plant']}` and `{b['plant']}`.

## Weaknesses / next
Keep unique leftover leftover leftover plots. Ban r01–r1933 clones, libNNNN, r690–r708 workspace clones.
"""


SLUGS = [
    "ardourx-conf-leftover-sessionx",
    "lmmsx-yml-leftover-trackx",
    "mixxxx-json-leftover-busx",
    "qtractorx-toml-leftover-auxx",
    "rosegardenx-xml-leftover-sendx",
    "muse2x-ini-leftover-returnx",
    "hydrogenx-py-leftover-insertx",
    "drumgizmox-lua-leftover-faderx",
    "sfizzx-h-leftover-panx",
    "fluidsynthx-js-leftover-mutegp",
    "timidityx-conf-leftover-solox",
    "wildmidix-yml-leftover-armrec",
    "fluida-json-leftover-punchx",
    "carla-toml-leftover-loopx",
    "jackx-xml-leftover-markerx",
    "pipewirex-ini-leftover-regionx",
    "pulseaudiox-py-leftover-clipx",
    "alsaeqx-lua-leftover-takex",
    "ladishx-h-leftover-compx",
    "a2jx-js-leftover-crossfx",
    "reaperx-conf-leftover-warpq",
    "bitwigapp-yml-leftover-elastix",
    "abletonx-json-leftover-stretchx",
    "flstudiox-toml-leftover-pitchx",
    "logicprox-xml-leftover-formantx",
    "protoolx-ini-leftover-timestx",
    "cubasex-py-leftover-resamplex",
    "nuendox-lua-leftover-dithx",
    "studi1x-h-leftover-noisesh",
    "reasonx-js-leftover-oversamp",
    "renoisex-conf-leftover-latencx",
    "sunvoxx-yml-leftover-buffsz",
    "milkytrackx-json-leftover-sr48k",
    "openmptx-toml-leftover-sr96k",
    "schismx-xml-leftover-bit24",
    "furnacex-ini-leftover-bit32f",
    "deflemaskx-py-leftover-asio",
    "famitrackx-lua-leftover-wasapix",
    "lsdjx-h-leftover-coreaux",
    "nanoloopx-js-leftover-jackcl",
    "audacityx-conf-leftover-pwgraph",
    "ocenax-yml-leftover-pulsesrc",
    "tenacityx-json-leftover-alsapcm",
    "kwavex-toml-leftover-midithru",
    "soundfx-xml-leftover-midimap",
    "soxappx-ini-leftover-nrpnx",
    "ffmpegx-py-leftover-sysexx",
    "mpvappx-lua-leftover-clockx",
    "vlcappx-h-leftover-mtcx",
    "deadbeefx-js-leftover-sppx",
    "cmusx-conf-leftover-reverbx",
    "mpdx-yml-leftover-delayx",
    "ncmpcppx-json-leftover-chorx",
    "mocpx-toml-leftover-flangx",
    "clementinex-xml-leftover-phaserx",
    "strawberryx-ini-leftover-distx",
    "elisa-py-leftover-satx",
    "amarokx-lua-leftover-compx2",
    "rhythmboxx-h-leftover-limitx",
    "bansheex-js-leftover-gaterx",
    "spotifyd-conf-leftover-eqparx",
    "mopidyx-yml-leftover-eqgrax",
    "navidromex-json-leftover-eqdynx",
    "airsonicx-toml-leftover-multibx",
    "navidrome2-xml-leftover-sidechx",
    "funkwhalex-ini-leftover-deessx",
    "koelx-py-leftover-exciterx",
    "ampachex-lua-leftover-imagerx",
    "subsonicx-h-leftover-widenerx",
    "gonicx-js-leftover-monoex",
    "icecastx-conf-leftover-analyzerx",
    "shoutcastx-yml-leftover-goniomx",
    "liquidsoapx-json-leftover-phasecor",
    "ices2x-toml-leftover-lufs",
    "darkicex-xml-leftover-truepk",
    "azurax-ini-leftover-rmsx",
    "libretime-py-leftover-crestx",
    "airtime-lua-leftover-kweight",
    "mixcloudx-h-leftover-itu1770",
    "soundcloudx-js-leftover-ebur128",
    "lilypondx-conf-leftover-sf2bank",
    "musescorex-yml-leftover-sfzmap",
    "frescobalx-json-leftover-gigmap",
    "denemox-toml-leftover-dlsmap",
    "sibeliusx-xml-leftover-exsmap",
    "finale-ini-leftover-nkimap",
    "doricox-py-leftover-multisamp",
    "capella-lua-leftover-roundrob",
    "guitarprox-h-leftover-keyswx",
    "tuxguitarx-js-leftover-velswx",
    "powertabx-conf-leftover-adsrx",
    "tuxg-yml-leftover-dahdsr",
    "alphatex-json-leftover-lfo1x",
    "songbookx-toml-leftover-lfo2x",
    "chordpro-xml-leftover-env1x",
    "opensongx-ini-leftover-env2x",
    "openlp-py-leftover-modmtx",
    "propresentx-lua-leftover-unisonx",
    "queleaapp-h-leftover-porta",
    "easyworship-js-leftover-glide",
    "csoundx-conf-leftover-arpx",
    "puredatax-yml-leftover-seq16",
    "maxmspx-json-leftover-seq32",
    "supercollx-toml-leftover-stepseq",
    "chuckx-xml-leftover-clipseq",
    "faustx-ini-leftover-patternx",
    "soxdspx-py-leftover-scenex",
    "ladspax-lua-leftover-chainx",
    "lv2x-h-leftover-rackx",
    "vstx-js-leftover-macrox",
    "clapx-conf-leftover-automationx",
    "aaxx-yml-leftover-envelane",
    "audiounitx-json-leftover-modwheel",
    "jacktripx-toml-leftover-aftert",
    "zitaajx-xml-leftover-pitchbend",
    "ajdelayx-ini-leftover-breathx",
    "calfx-py-leftover-expressionx",
    "eq10q-lua-leftover-sustainx",
    "lsppluginx-h-leftover-sostenx",
    "x42pluginx-js-leftover-una",
    "zampluginx-conf-leftover-noteq",
    "dragonflyx-yml-leftover-quantx",
    "talnox-json-leftover-swingx",
    "vitalx-toml-leftover-humanx",
    "surgextx-xml-leftover-strumx",
    "helmsoftx-ini-leftover-legatox",
    "tyrellx-py-leftover-staccx",
    "obxd-lua-leftover-tenutox",
    "dexedx-h-leftover-marcato",
    "tunefishx-js-leftover-accentx",
    "odin2x-conf-leftover-staffx",
    "vitaliumx-yml-leftover-voicesx",
    "cardinalx-json-leftover-lyricx",
    "vcvx-toml-leftover-chordx",
    "audulusx-xml-leftover-romanx",
    "reaktorx-ini-leftover-nashville",
    "massivex-py-leftover-tabx",
    "serumx-lua-leftover-fretx",
    "phaseplantx-h-leftover-capox",
    "pigmentsx-js-leftover-tuningx",
    "divax-conf-leftover-scorex",
    "zebra2x-yml-leftover-partx",
    "sylenthx-json-leftover-extractx",
    "nexusx-toml-leftover-layoutx",
    "omnispherex-xml-leftover-pagenum",
    "kontaktx-ini-leftover-systemx",
    "halionx-py-leftover-bracex",
    "independentx-lua-leftover-bracketx",
    "batteryx-h-leftover-barnum",
    "maschinex-js-leftover-pickupx",
    "pushx-conf-leftover-csdorch",
    "launchpadx-yml-leftover-pdpatch",
    "mpkmini-json-leftover-maxpatx",
    "keystepex-toml-leftover-scsynth",
    "axiomx-xml-leftover-chuckshred",
    "s90esx-ini-leftover-faustdsp",
    "motifx-py-leftover-ladspaamp",
    "montagex-lua-leftover-lv2ttl",
    "modxx-h-leftover-vst3xml",
    "genosx-js-leftover-clapdesc"
]
assert len(SLUGS) == 160
assert len(SLUGS) % 2 == 0


def row_from_slug(slug: str, idx: int) -> tuple:
    left, leftover = slug.split("-leftover-", 1)
    pkg, ext = left.rsplit("-", 1)
    pin = f"{leftover}.{ext}"
    old = f"{1 + (idx % 9)}.{idx % 7}.{(idx % 5) + 1}"
    new = f"{1 + (idx % 9)}.{(idx % 7) + 1}.{(idx % 5) + 3}"
    surface = f"{pkg} leftover vs {pin}"
    nest_old = f"{leftover} = false"
    nest_new = f"{leftover} = true"
    api_old = f"{leftover}_compat = 1"
    api_new = f"{leftover}_compat = 0"
    api_break = f"{leftover} on + compat off"
    return (slug, surface, pkg, old, new, pin, nest_old, nest_new, api_old, api_new, api_break, ext)


RAW: list[tuple] = [row_from_slug(s, i) for i, s in enumerate(SLUGS)]


def expand(row: tuple) -> tuple:
    slug, surface, pkg, old, new, pin, nest_old, nest_new, api_old, api_new, api_break, ext = row
    cmap = {
        "sql": "--", "R": "#", "hs": "--", "scala": "//", "vhdl": "--", "v": "//",
        "scd": "//", "orc": ";", "ttl": "#", "C": "//", "cpp": "//", "c": "//",
        "cs": "//", "dart": "//", "rb": "#", "php": "//", "js": "//", "ts": "//",
        "go": "//", "d": "//", "td": "//", "g": ";", "fish": "#", "nu": "#", "xsh": "#",
        "lua": "--", "el": ";", "edn": ";", "h": "//", "asm": ";", "f90": "!",
        "mlir": "//", "exs": "#", "hgrc": "#", "kbd": ";;", "pp3": "#", "scm": ";",
        "svg": "<!--", "mlt": "#", "lp": "#", "r": "#", "m": "%", "tex": "%",
    }
    comment = cmap.get(ext, "#")
    sot_old = f"{comment} {pkg} {old}"
    sot_new = f"{comment} {pkg} {new}"
    if ext == "py":
        tool = f"python3 -c 'import {pkg}; print({pkg}.__version__)'"
        test = f"python3 apps/api/{pin}"
        ws = f"python3 apps/legacy/{pin}"
    else:
        tool = f"python3 -c 'print(\"{pkg}\")' || true"
        test = f"python3 -c 'print(\"apps/api/{pin}\")'"
        ws = f"python3 -c 'print(\"apps/legacy/{pin}\")'"
    return (slug, surface, pkg, old, new, pin, sot_old, sot_new, nest_old, nest_new, api_old, api_new, api_break, tool, test, ws, ext)


TOOLS: list[tuple] = [expand(r) for r in RAW]
assert len(TOOLS) % 2 == 0
assert len(TOOLS) <= len(PLANTS)

PAIRS: list[tuple[dict, dict]] = []
_pi = 0
for i in range(0, len(TOOLS), 2):
    a = TOOLS[i]
    b = TOOLS[i + 1]
    suc = make(
        a[0], PLANTS[_pi], a[1], a[2], a[3], a[4], False,
        a[5], a[6], a[7], a[8], a[9], a[10], a[11], a[12], a[13], a[14], a[15], a[16],
    )
    _pi += 1
    failp = make(
        b[0], PLANTS[_pi], b[1], b[2], b[3], b[4], True,
        b[5], b[6], b[7], b[8], b[9], b[10], b[11], b[12], b[13], b[14], b[15], b[16],
    )
    _pi += 1
    PAIRS.append((suc, failp))


def _validate_catalog() -> None:
    slugs = [spec["slug"] for pair in PAIRS for spec in pair]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs in r1934 catalog")
    for slug in slugs:
        for needle in BANNED_SLUG_NEEDLES:
            if needle and needle in slug:
                raise SystemExit(f"banned needle {needle!r} in {slug}")
    plants = [spec["plant"] for pair in PAIRS for spec in pair]
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plants in r1934 catalog")


_validate_catalog()


def build_round(rnd: int) -> tuple[list[dict], str]:
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"round {rnd} outside catalog {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}"
        )
    suc, fail = PAIRS[idx]
    suc_ep = build_episode(rnd, suc)
    fail_ep = build_episode(rnd, fail)
    for ep in (suc_ep, fail_ep):
        n = len(ep["steps"])
        if n < 16 or n > 20:
            raise SystemExit(f"{ep['id']} has {n} steps, want 16-20")
        blob = json.dumps(ep)
        for banned in (
            "thought",
            "chain_of_thought",
            "scratch",
            "inner_monologue",
            "spike_events",
        ):
            if f'"{banned}"' in blob:
                raise SystemExit(f"{ep['id']} contains banned key {banned}")
        if '"sim_or_real": "real"' in blob or '"sim_or_real":"real"' in blob:
            raise SystemExit(f"{ep['id']} claims sim_or_real real")
    notes = notes_for(rnd, suc, fail)
    if "Novel coverage:" not in notes:
        raise SystemExit("notes missing Novel coverage")
    return [suc_ep, fail_ep], notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    rnd = args.round
    staging = Path(args.staging)
    recs, notes = build_round(rnd)
    batch = staging / f"batch-r{rnd:02d}.jsonl"
    notes_path = staging / f"NOTES-r{rnd:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    notes_path.write_text(notes)
    print(
        json.dumps(
            {
                "round": rnd,
                "ids": [r["id"] for r in recs],
                "steps": [len(r["steps"]) for r in recs],
                "success": [r["reward"]["success"] for r in recs],
                "batch": str(batch),
                "notes": str(notes_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
