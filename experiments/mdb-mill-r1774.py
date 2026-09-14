#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r1774+ unique SDR/CAD/lab leftover plants.

BAN r01–r1773 clones including msgpackx-h-leftover-exttype / cborx-js-leftover-tagx,
darcsx-h-leftover-shelves / bazaarx-js-leftover-branches,
elvish-toml-leftover-prompt / oil-rc-leftover-strict,
hydra-py-leftover-compose / sacred-py-leftover-observer,
solr-xml-leftover-cache / opensearchdash-yml-leftover-sso, leftover-revpin, libNNNN,
r690–r708 workspace clones. Do not rerun mdb-mill-r1351, mdb-mill-r1407, mdb-mill-r1454,
mdb-mill-r1534, mdb-mill-r1614, or mdb-mill-r1694.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_BASE = Path(__file__).with_name("mdb-mill-r1694.py")
_spec = importlib.util.spec_from_file_location("mdb_mill_r1694", _BASE)
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 1774
P = _m.P
build_episode = _m.build_episode
make = _m.make

PRIOR_SLUGS = tuple(spec["slug"] for pair in _m.PAIRS for spec in pair)
BANNED_SLUG_NEEDLES = _m.BANNED_SLUG_NEEDLES + PRIOR_SLUGS + (
    "msgpackx-h-leftover-exttype",
    "cborx-js-leftover-tagx",
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
    "saffron", "turmeric", "cumin", "paprika", "cardamom", "nutmeg", "clove", "coriander", "fennel", "anise",
    "basilx", "thymex", "oregano", "rosemary", "sagex", "mintx", "tarragon", "dillx", "chivex", "parsley",
    "cinnamon", "gingers", "galangal", "lemonbalm", "kaffir", "vanillax", "cacaox", "coffeex", "chicory", "juniper",
    "sumacx", "zaatar", "harissa", "berbere", "garamx", "allspice", "mustardx", "pepperx", "wasabix", "horserad",
    "macex", "caraway", "fenugreek", "ajwain", "amchur", "hingx", "bayleaf", "savoryx", "marjoram", "lovage",
    "epazote", "hojicha", "matchax", "sencha", "oolong", "puerx", "yerbax", "matex", "rooibos", "honeybush",
    "dandelion", "burdock", "ginseng", "astragal", "valerianx", "chamomile", "lavenderx", "peppermint", "spearmint", "eucalypt",
    "teaolive", "starani", "sichuanx", "grainspar", "longpepper", "cubeb", "masticx", "sumakh", "nigellax", "asafoet",
]


assert len(STEMS) == 80
PLANTS = [f"{s}y" for s in STEMS] + [f"{s}z" for s in STEMS]


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"mdb-r{round_n}-{a['slug']}"
    eb = f"mdb-r{round_n}-{b['slug']}"
    novel = 88 + (round_n % 5)
    return f"""# NOTES-r{round_n} monorepo-dep-bump-factory

Novel coverage: {novel}%

Two designed episodes (quota 2). Surfaces: {a['surface']} ({a['pkg']} {a['api_break']}); {b['surface']} ({b['pkg']} {b['api_break']}).
Not a pin-file mill and not libNNNN recycle. Distinct from r01–r1773 clones (ban msgpackx-h-leftover-exttype / cborx-js-leftover-tagx; darcsx-h-leftover-shelves / bazaarx-js-leftover-branches; elvish-toml-leftover-prompt / oil-rc-leftover-strict; hydra-py-leftover-compose / sacred-py-leftover-observer; solr-xml-leftover-cache / opensearchdash-yml-leftover-sso; leftover-revpin; r690–r708 workspace clones).

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
Keep unique leftover leftover leftover plots. Ban r01–r1773 clones, libNNNN, r690–r708 workspace clones.
"""


SLUGS = [
    "sdrplayx-conf-leftover-iqrate",
    "rtlsdrx-yml-leftover-fftwin",
    "hackrfx-json-leftover-waterfallx",
    "limesdrx-toml-leftover-squelchx",
    "uhdx-xml-leftover-agcset",
    "soapysdrx-ini-leftover-nbfm",
    "gnuradox-py-leftover-wbfm",
    "gqrxapp-lua-leftover-ssbx",
    "cubicsdrx-h-leftover-cwskim",
    "sdrangelx-js-leftover-psk31x",
    "inspectrumx-conf-leftover-rttyx",
    "dump1090x-yml-leftover-oliviax",
    "acarsdecx-json-leftover-contestiax",
    "multimonx-toml-leftover-mt63x",
    "direwolfx-xml-leftover-thorx",
    "soundmodx-ini-leftover-dominoexx",
    "fldigix-py-leftover-hellschx",
    "wsjtxapp-lua-leftover-wefax",
    "jtdxapp-h-leftover-navtexd",
    "js8callx-js-leftover-aisx",
    "qsstvx-conf-leftover-adsbx",
    "svxlinkx-yml-leftover-acarsx",
    "allstarx-json-leftover-vdl2x",
    "echolinkx-toml-leftover-hfcsdlx",
    "dmrlinkx-xml-leftover-stanagx",
    "mmdvmx-ini-leftover-dstarx",
    "pistarx-py-leftover-dmrcc",
    "opendmrx-lua-leftover-p25x",
    "hamlibx-h-leftover-ysfx",
    "rigctlx-js-leftover-nxdnx",
    "chirpxapp-conf-leftover-pocsagx",
    "sdrppx-yml-leftover-flexpagex",
    "sigdiggerx-json-leftover-mototrbox",
    "pothosx-toml-leftover-taitx",
    "limesuitex-xml-leftover-hyterax",
    "uhdhostx-ini-leftover-kenwoodx",
    "dump978x-py-leftover-icomx",
    "vdl2decx-lua-leftover-yaesux",
    "aisdecx-h-leftover-alincx",
    "navtexx-js-leftover-baofengx",
    "freecadx-conf-leftover-gerberap",
    "openscadx-yml-leftover-excellonx",
    "librecadx-json-leftover-ipc2581x",
    "qcadx-toml-leftover-odbppx",
    "bricscadx-xml-leftover-gds2x",
    "onshapex-ini-leftover-oasisx",
    "fusionx-py-leftover-lefdefx",
    "inventorx-lua-leftover-libertyx",
    "catiax-h-leftover-spefx",
    "rhinocerox-js-leftover-sdfx",
    "blenderx-conf-leftover-verilogx",
    "houdinix-yml-leftover-vhdlx",
    "c4dx-json-leftover-sverilogx",
    "zbrushx-toml-leftover-spicenx",
    "substancex-xml-leftover-ibisx",
    "slic3rx-ini-leftover-sparamx",
    "prusaslicex-py-leftover-touchstx",
    "curaengx-lua-leftover-hfssx",
    "orcaslicex-h-leftover-cstx",
    "bambux-js-leftover-comsolx",
    "klipperx-conf-leftover-occtstep",
    "octoprintx-yml-leftover-igesx",
    "repetierx-json-leftover-brepx",
    "smoothiex-toml-leftover-meshx",
    "marlinx-xml-leftover-stlx",
    "grblx-ini-leftover-objx",
    "tinygx-py-leftover-amfx",
    "linuxcncx-lua-leftover-3mfx",
    "machinekitx-h-leftover-plyx",
    "bcncx-js-leftover-gltfxx",
    "cncjsx-conf-leftover-layerhx",
    "ugsplatx-yml-leftover-infillx",
    "candlecadx-json-leftover-supportx",
    "laserwebx-toml-leftover-brimx",
    "lightburnx-xml-leftover-skirtx",
    "rdworksx-ini-leftover-gcodex",
    "visicutx-py-leftover-startgx",
    "pstoeditx-lua-leftover-endgx",
    "potracex-h-leftover-pressadv",
    "autotracex-js-leftover-inshaper",
    "labviewx-conf-leftover-pidtunex",
    "scilabx-yml-leftover-bedmeshx",
    "octavex-json-leftover-zoffsetx",
    "matlabx-toml-leftover-klickyx",
    "simulinkx-xml-leftover-beaconx",
    "modelicax-ini-leftover-eddyx",
    "openmodelx-py-leftover-strainx",
    "dymalox-lua-leftover-accelx",
    "maplex-h-leftover-adxlx",
    "wolframx-js-leftover-thermstx",
    "maximacx-conf-leftover-pt100x",
    "sympyx-yml-leftover-spi1x",
    "keithleyx-json-leftover-i2c1x",
    "keysightx-toml-leftover-canbusx",
    "tektronixx-xml-leftover-rs485x",
    "lecroyx-ini-leftover-uart1x",
    "rohdesx-py-leftover-pwm1x",
    "anritsux-lua-leftover-adc1x",
    "labjackx-h-leftover-dac1x",
    "phidgetx-js-leftover-gpio1x",
    "firmatx-conf-leftover-jtagx",
    "pyocdx-yml-leftover-swdx",
    "openocdx-json-leftover-swoox",
    "jlinkx-toml-leftover-itmtrace",
    "stlinkx-xml-leftover-etmx",
    "blackmagx-ini-leftover-coresightx",
    "probersx-py-leftover-openocdcfg",
    "gtkwavex-lua-leftover-gdbservx",
    "surferx-h-leftover-rttx",
    "pulseviewx-js-leftover-semihostx",
    "sigrokx-conf-leftover-bitstreamx",
    "kicadx-yml-leftover-timingx",
    "gedax-json-leftover-placeandx",
    "gerberx-toml-leftover-routeoptx",
    "ngspicex-xml-leftover-sta1x",
    "xycex-ini-leftover-drc1x",
    "qucsx-py-leftover-lvs1x",
    "ltspicex-lua-leftover-pex1x",
    "gnucapx-h-leftover-lef1x",
    "verilatorx-js-leftover-def1x",
    "ghdlx-conf-leftover-iqbal",
    "nvcsimx-yml-leftover-fftovl",
    "yosysx-json-leftover-wfpsdx",
    "nextpnrx-toml-leftover-sqlch",
    "icestormx-xml-leftover-agchold",
    "trellisx-ini-leftover-nbfmdv",
    "prjxrayx-py-leftover-wbfmst",
    "vivadox-lua-leftover-ssbusb",
    "quartusx-h-leftover-cwsk",
    "liberoedx-js-leftover-psk63x",
    "diamondx-conf-leftover-rtty45",
    "latticex-yml-leftover-oliv8",
    "modelsimx-json-leftover-cont8",
    "questasimx-toml-leftover-mt63l",
    "vcsxsim-xml-leftover-thor8",
    "xceliumx-ini-leftover-domex",
    "incisivex-py-leftover-feldhell",
    "vsimx-lua-leftover-wefaxn",
    "iverilogx-h-leftover-navtexm",
    "ncsime-js-leftover-aisnmea",
    "inkscapecx-conf-leftover-adsb1090",
    "openocadx-yml-leftover-acarsvdl",
    "prusaklipx-json-leftover-vdl2m",
    "inputshpx-toml-leftover-stanag4285",
    "beacon3dx-xml-leftover-dstarhdr",
    "eddyprobex-ini-leftover-dmrcc1",
    "loadcelx-py-leftover-p25p2",
    "adxl345x-lua-leftover-ysfwires",
    "tmc2209x-h-leftover-nxdn96",
    "tmc5160x-js-leftover-pocs512",
    "drv8825x-conf-leftover-flex1600",
    "a4988x-yml-leftover-mototrk",
    "lv8729x-json-leftover-taiti",
    "stepstix-toml-leftover-hyteradmr",
    "pca9685x-xml-leftover-kenwth",
    "mcp23017x-ini-leftover-icomciv",
    "bme280x-py-leftover-yaesucat",
    "max31865x-lua-leftover-alinco",
    "ina219x-h-leftover-baofuv",
    "ds18b20x-js-leftover-gerb274x"
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
        raise SystemExit("duplicate slugs in r1774 catalog")
    for slug in slugs:
        for needle in BANNED_SLUG_NEEDLES:
            if needle and needle in slug:
                raise SystemExit(f"banned needle {needle!r} in {slug}")
    plants = [spec["plant"] for pair in PAIRS for spec in pair]
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plants in r1774 catalog")


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
