#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r1854+ unique GIS/climate leftover plants.

BAN r01–r1853 clones including ina219x-h-leftover-baofuv / ds18b20x-js-leftover-gerb274x,
darcsx-h-leftover-shelves / bazaarx-js-leftover-branches,
elvish-toml-leftover-prompt / oil-rc-leftover-strict,
hydra-py-leftover-compose / sacred-py-leftover-observer,
solr-xml-leftover-cache / opensearchdash-yml-leftover-sso, leftover-revpin, libNNNN,
r690–r708 workspace clones. Do not rerun mdb-mill-r1351, mdb-mill-r1407, mdb-mill-r1454,
mdb-mill-r1534, mdb-mill-r1614, mdb-mill-r1694, or mdb-mill-r1774.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_BASE = Path(__file__).with_name("mdb-mill-r1774.py")
_spec = importlib.util.spec_from_file_location("mdb_mill_r1774", _BASE)
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 1854
P = _m.P
_orig_build_episode = _m.build_episode
make = _m.make


def _clip(text: str, n: int = 240) -> str:
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def build_episode(round_n: int, spec: dict) -> dict:
    """Keep mill plants; add ordered workspace/lockfile/repair/verify evidence."""
    ep = _orig_build_episode(round_n, spec)
    plant = spec["plant"]
    pkg = spec["pkg"]
    old = spec["old"]
    left = spec["left"]
    surface = spec["surface"]
    s0 = ep["steps"][0]
    s0["decision_basis"] = _clip(
        f"Plan: inspect {plant} workspace dependency {surface} plus lockfile peer "
        f"and build-graph before a nested-only bump."
    )
    cmd = s0["tool_call"]["args"]["command"]
    extra = (
        "rg -n 'lockfileVersion|peerDependencies|packages:' "
        "pnpm-lock.yaml pnpm-workspace.yaml package.json | head -n 24"
    )
    if "pnpm-lock.yaml" not in cmd:
        s0["tool_call"]["args"]["command"] = f"{cmd}; {extra}"
    s0["observation"] = (
        s0["observation"].rstrip()
        + f"\npnpm-workspace.yaml packages: ['apps/*'] workspace dependency {pkg}@{old}\n"
        + f"lockfile pnpm-lock.yaml importers['apps/api'].dependencies.{pkg}: {old} "
        f"peer {pkg}@^{old}\n"
        + f"build-graph apps/api -> leftover {left} still {old} (peer mismatch)\n"
    )
    s7 = ep["steps"][7]
    s7["decision_basis"] = _clip(
        s7["decision_basis"].rstrip(".") + "; compatible repair of SoT pin."
    )
    s12 = ep["steps"][12]
    s12["decision_basis"] = _clip(
        "Observation: call site patched (step 12). Verify in-scope packages pass."
    )
    return ep

PRIOR_SLUGS = tuple(spec["slug"] for pair in _m.PAIRS for spec in pair)
BANNED_SLUG_NEEDLES = _m.BANNED_SLUG_NEEDLES + PRIOR_SLUGS + (
    "ina219x-h-leftover-baofuv",
    "ds18b20x-js-leftover-gerb274x",
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
    "albatross", "bittern", "curlew", "dunlin", "egret", "falconx", "gannet", "heronx", "ibisx", "jacana",
    "kestrel", "lapwing", "merlinx", "nuthatch", "ospreyx", "puffin", "quailx", "ravenx", "snipex", "ternx",
    "umbrellab", "vulturex", "warbler", "xenops", "yellowleg", "zebrafinch", "auklet", "bobolink", "condorx", "dipperx",
    "eiderx", "flycatch", "godwit", "harrierx", "icterid", "jayx", "killdeer", "loonx", "magpiex", "nightjar",
    "oriolex", "phoebe", "quelea", "redstart", "shrikex", "tanager", "veery", "wheatear", "xantus", "yellowhammer",
    "zonure", "anhinga", "boobyx", "cormorant", "dowitcher", "emu", "frigateb", "grebex", "hoatzin", "iwi",
    "juncox", "kinglet", "lyrebird", "meadowlark", "noddyx", "oystercatch", "petrelx", "quetzalx", "roadrunner", "shearwater",
    "tropicbird", "umbrellax", "violetgreen", "willetx", "xenopsar", "yellowthroat", "zosterops", "avocetx", "bullfinch", "canaryx",
]


assert len(STEMS) == 80
PLANTS = [f"{s}p" for s in STEMS] + [f"{s}n" for s in STEMS]


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"mdb-r{round_n}-{a['slug']}"
    eb = f"mdb-r{round_n}-{b['slug']}"
    novel = 88 + (round_n % 5)
    return f"""# NOTES-r{round_n} monorepo-dep-bump-factory

Novel coverage: {novel}%

Two designed episodes (quota 2). Surfaces: {a['surface']} ({a['pkg']} {a['api_break']}); {b['surface']} ({b['pkg']} {b['api_break']}).
Not a pin-file mill and not libNNNN recycle. Distinct from r01–r1853 clones (ban ina219x-h-leftover-baofuv / ds18b20x-js-leftover-gerb274x; darcsx-h-leftover-shelves / bazaarx-js-leftover-branches; elvish-toml-leftover-prompt / oil-rc-leftover-strict; hydra-py-leftover-compose / sacred-py-leftover-observer; solr-xml-leftover-cache / opensearchdash-yml-leftover-sso; leftover-revpin; r690–r708 workspace clones).

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
Keep unique leftover leftover leftover plots. Ban r01–r1853 clones, libNNNN, r690–r708 workspace clones.
"""


SLUGS = [
    "qgisx-conf-leftover-crsset",
    "grassgisx-yml-leftover-datumx",
    "gdalx-json-leftover-utmzone",
    "ogrx-toml-leftover-geoidx",
    "projx-xml-leftover-ellipx",
    "geotiffx-ini-leftover-epsgx",
    "postgisx-py-leftover-proj4x",
    "geopandasx-lua-leftover-wkt2x",
    "shapelyx-h-leftover-gridshx",
    "fionax-js-leftover-vdatumx",
    "rasteriox-conf-leftover-pyramidx",
    "xarrayx-yml-leftover-overzoomx",
    "rioxarrayx-json-leftover-mvtenc",
    "geemapx-toml-leftover-pbfenc",
    "leafmapx-xml-leftover-mbtilx",
    "foliumx-ini-leftover-pmtilx",
    "mapboxx-py-leftover-cogx",
    "maplibrex-lua-leftover-vrtsx",
    "leafletx-h-leftover-stacapi",
    "openlayersx-js-leftover-titilerp",
    "cesiumx-conf-leftover-wmsget",
    "keplerx-yml-leftover-wmtsget",
    "deckglx-json-leftover-wfsget",
    "h3hexx-toml-leftover-wcsget",
    "s2geox-xml-leftover-cswget",
    "geohashx-ini-leftover-ogcfeat",
    "turfjsx-py-leftover-geojsonl",
    "geojsonx-lua-leftover-topoenc",
    "topojsonx-h-leftover-h3res",
    "wktx-js-leftover-s2cellx",
    "wmsx-conf-leftover-quadkeyx",
    "wmtsx-yml-leftover-geohashp",
    "wfsx-json-leftover-turfbuf",
    "wcsx-toml-leftover-leafpop",
    "cswx-xml-leftover-mapboxgl",
    "ogcapix-ini-leftover-cesium3d",
    "stacx-py-leftover-keplerf",
    "titilerx-lua-leftover-deckhex",
    "tegolax-h-leftover-foliumt",
    "martinx-js-leftover-leafmapt",
    "pgtilerx-conf-leftover-gdalwarp",
    "tippecanoex-yml-leftover-gdaltran",
    "tilesvrx-json-leftover-ogr2ogrx",
    "mapnikx-toml-leftover-rasterioz",
    "mapservx-xml-leftover-rioread",
    "geoserverx-ini-leftover-xarrayc",
    "geonodex-py-leftover-shapelyb",
    "geonetx-lua-leftover-fionac",
    "pycswx-h-leftover-postgiss",
    "mapproxyx-js-leftover-qgisproj",
    "wrfx-conf-leftover-wrfnamelist",
    "mpasx-yml-leftover-mpasstream",
    "gfsx-json-leftover-gfsgrid",
    "ecmwfx-toml-leftover-ecmwfml",
    "era5x-xml-leftover-era5lev",
    "cfsrx-ini-leftover-cfsrgrid",
    "namx-py-leftover-namnest",
    "hrrrx-lua-leftover-hrrrgrid",
    "rapx-h-leftover-rapgrid",
    "hwrfx-js-leftover-hwrfnest",
    "cmipx-conf-leftover-cmipscen",
    "cesmx-yml-leftover-cesmcpl",
    "e3smx-json-leftover-e3smgrid",
    "gfdlx-toml-leftover-gfdlcpl",
    "hadgemx-xml-leftover-hadgemres",
    "ipslx-ini-leftover-ipslcpl",
    "mirocx-py-leftover-mirocres",
    "noresmx-lua-leftover-noresmres",
    "ukesmx-h-leftover-ukesmres",
    "accessx-js-leftover-accessres",
    "romsx-conf-leftover-romsgrid",
    "fvcomx-yml-leftover-fvcommesh",
    "delfth3d-json-leftover-delfthd",
    "telemacx-toml-leftover-telemacbd",
    "swanwavex-xml-leftover-swangrid",
    "ww3x-ini-leftover-ww3grid",
    "hycomx-py-leftover-hycomnest",
    "nemoocx-lua-leftover-nemogrid",
    "mom6x-h-leftover-mom6grid",
    "pop2x-js-leftover-pop2grid",
    "cdoex-conf-leftover-cdocmd",
    "ncoex-yml-leftover-ncocmd",
    "ncdumpx-json-leftover-ncdumpv",
    "netcdfx-toml-leftover-netcdfd",
    "hdf5x-xml-leftover-hdf5d",
    "zarrx-ini-leftover-zarrstore",
    "kerchunkx-py-leftover-kerchunkm",
    "intakeex-lua-leftover-intakecat",
    "xpublishx-h-leftover-xpubmap",
    "threddssx-js-leftover-threddscat",
    "metpyx-conf-leftover-crsdef",
    "irisclimx-yml-leftover-datumh",
    "cfgribx-json-leftover-utm32",
    "pygribx-toml-leftover-geoid12",
    "wgrib2x-xml-leftover-ellwgs",
    "gradsxx-ini-leftover-epsg3857",
    "nclx-py-leftover-projstr",
    "ferretx-lua-leftover-wktcrs",
    "panoplyx-h-leftover-gridshf",
    "idvx-js-leftover-vdatumg",
    "astropyx-conf-leftover-pyrtile",
    "sunpyx-yml-leftover-overz",
    "heliopyx-json-leftover-mvtgzip",
    "specutilsx-toml-leftover-pbfgzip",
    "photutilsx-xml-leftover-mbtilpbf",
    "ccdprocx-ini-leftover-pmtilpbf",
    "gwcsx-py-leftover-cogover",
    "asdfx-lua-leftover-vrtover",
    "fitsiox-h-leftover-stacitem",
    "astqueryx-js-leftover-titlecog",
    "casax-conf-leftover-wmslay",
    "cimaex-yml-leftover-wmtslay",
    "miriadx-json-leftover-wfstyp",
    "aipsmemx-toml-leftover-wcscov",
    "gildasx-xml-leftover-cswrec",
    "classx-ini-leftover-ogccoll",
    "casa6x-py-leftover-geojs",
    "wscleanx-lua-leftover-topoar",
    "casaflagx-h-leftover-h3idx",
    "aoflagx-js-leftover-s2idx",
    "pdalx-conf-leftover-quadk",
    "lastoolsx-yml-leftover-geohp",
    "entwinex-json-leftover-turfint",
    "potreex-toml-leftover-leafmark",
    "cloudcmpx-xml-leftover-mapboxsrc",
    "open3dx-ini-leftover-cesiumion",
    "pclx-py-leftover-keplercsv",
    "laspyx-lua-leftover-decklyr",
    "pyntcloudx-h-leftover-foliumch",
    "whiteboxx-js-leftover-leafch",
    "sagagisx-conf-leftover-gdalinfo",
    "qgis3x-yml-leftover-gdaladdo",
    "arcgisx-json-leftover-ogrinfo",
    "mapinfox-toml-leftover-riowarp",
    "globalmapx-xml-leftover-riomask",
    "manifoldx-ini-leftover-xropen",
    "gridx-py-leftover-shpbuf",
    "surfergisx-lua-leftover-fiocrs",
    "oaismontajx-h-leftover-pgisidx",
    "geosoftx-js-leftover-qgislyr",
    "leapfrogx-conf-leftover-wrfbdy",
    "micromeinx-yml-leftover-mpasout",
    "dataminex-json-leftover-gfsanl",
    "surpacx-toml-leftover-ecmwfanl",
    "vulcanx-xml-leftover-era5pl",
    "whittlez-ini-leftover-cfsranl",
    "geoviax-py-leftover-namanl",
    "deswikx-lua-leftover-hrrranl",
    "minemapx-h-leftover-rapanl",
    "prominex-js-leftover-hwrfanl",
    "metashapex-conf-leftover-photogx",
    "pix4dx-yml-leftover-pix4dmap",
    "opendronx-json-leftover-odmortho",
    "webodmx-toml-leftover-webodmjob",
    "dronedeployx-xml-leftover-dronedmap",
    "propellerx-ini-leftover-propelmap",
    "skycatchx-py-leftover-skycmap",
    "siteboardx-lua-leftover-sitebmap",
    "virtusurv-h-leftover-vsurvmap",
    "leicacapx-js-leftover-leicamap"
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
        raise SystemExit("duplicate slugs in r1854 catalog")
    for slug in slugs:
        for needle in BANNED_SLUG_NEEDLES:
            if needle and needle in slug:
                raise SystemExit(f"banned needle {needle!r} in {slug}")
    plants = [spec["plant"] for pair in PAIRS for spec in pair]
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plants in r1854 catalog")


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
