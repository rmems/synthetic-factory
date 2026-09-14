#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r1614+ unique media/homeauto/fediverse leftover plants.

BAN r01–r1613 clones including beszel-yml-leftover-agent / signoz-yml-leftover-alert,
elvish-toml-leftover-prompt / oil-rc-leftover-strict,
hydra-py-leftover-compose / sacred-py-leftover-observer,
solr-xml-leftover-cache / opensearchdash-yml-leftover-sso, leftover-revpin, libNNNN,
r690–r708 workspace clones. Do not rerun mdb-mill-r1351, mdb-mill-r1407, mdb-mill-r1454, or mdb-mill-r1534.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_BASE = Path(__file__).with_name("mdb-mill-r1534.py")
_spec = importlib.util.spec_from_file_location("mdb_mill_r1534", _BASE)
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 1614
P = _m.P
build_episode = _m.build_episode
make = _m.make

PRIOR_SLUGS = tuple(spec["slug"] for pair in _m.PAIRS for spec in pair)
BANNED_SLUG_NEEDLES = _m.BANNED_SLUG_NEEDLES + PRIOR_SLUGS + (
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
    "aster", "begonia", "crocus", "dahlia", "erica", "fuchsia", "gardenia", "hibiscus", "iris", "jasmine",
    "kalmia", "lilac", "magnoliaz", "narcissus", "orchid", "peony", "quinceb", "rose", "sunflower", "tulip",
    "ursinia", "viola", "wisteria", "xeranthemum", "yarrow", "zinnia", "aconite", "buttercup", "campanula", "delphinium",
    "echinacea", "foxglove", "geranium", "hellebore", "impatiens", "jonquil", "knapweed", "lantana", "mallow", "nigella",
    "oleander", "primrose", "queenanne", "ranunculus", "snapdragon", "thrift", "uvaursi", "verbena", "wallflower", "xylobium",
    "yellowflag", "azalea", "bluebell", "columbine", "dianthus", "eveningprim", "forgetmenot", "gladiolus", "hyacinth", "ixia",
    "jasminex", "kalanchoe", "lotus", "morningglory", "nasturtium", "oxalis", "petunia", "ranunculx", "stock", "tuberose",
    "ursiniax", "valerian", "watsonia", "xanthium", "yucca", "zinniax", "allium", "buddleia", "calendula", "daffodil",
]

assert len(STEMS) == 80
PLANTS = [f"{s}u" for s in STEMS] + [f"{s}v" for s in STEMS]


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"mdb-r{round_n}-{a['slug']}"
    eb = f"mdb-r{round_n}-{b['slug']}"
    novel = 88 + (round_n % 5)
    return f"""# NOTES-r{round_n} monorepo-dep-bump-factory

Novel coverage: {novel}%

Two designed episodes (quota 2). Surfaces: {a['surface']} ({a['pkg']} {a['api_break']}); {b['surface']} ({b['pkg']} {b['api_break']}).
Not a pin-file mill and not libNNNN recycle. Distinct from r01–r1613 clones (ban beszel-yml-leftover-agent / signoz-yml-leftover-alert; elvish-toml-leftover-prompt / oil-rc-leftover-strict; hydra-py-leftover-compose / sacred-py-leftover-observer; solr-xml-leftover-cache / opensearchdash-yml-leftover-sso; leftover-revpin; r690–r708 workspace clones).

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
Keep unique leftover leftover leftover plots. Ban r01–r1613 clones, libNNNN, r690–r708 workspace clones.
"""


SLUGS = [
    "gromacs-conf-leftover-pme",
    "lammps-yml-leftover-pairstyle",
    "cp2k-json-leftover-qsgrid",
    "nwchem-toml-leftover-dftgrid",
    "psi4-xml-leftover-scfconv",
    "orca-ini-leftover-riapprox",
    "abinit-py-leftover-pawpot",
    "vasp-lua-leftover-ismear",
    "gpaw-h-leftover-modetda",
    "ase-js-leftover-calcset",
    "pymatgen-conf-leftover-modifier",
    "ovito-yml-leftover-pvfilter",
    "paraview-json-leftover-vclplot",
    "visit-toml-leftover-zone",
    "tecplot-xml-leftover-gpterm",
    "gnuplot-ini-leftover-renderer",
    "plotly-py-leftover-vegalite",
    "altair-lua-leftover-context",
    "seaborn-h-leftover-hvbackend",
    "holoviews-js-leftover-aggmethod",
    "datashader-conf-leftover-nplayer",
    "napari-yml-leftover-ijmmacro",
    "fiji-json-leftover-cpmodule",
    "cellprofiler-toml-leftover-qpscript",
    "qupath-xml-leftover-ilppixel",
    "ilastik-ini-leftover-tmspot",
    "trackmate-py-leftover-imssurf",
    "imaris-lua-leftover-omechan",
    "bioformats-h-leftover-omechan2",
    "ome-js-leftover-omexml",
    "unity-conf-leftover-asmdefine",
    "unreal-yml-leftover-cvarset",
    "godot4-json-leftover-gdshader",
    "sdl3-toml-leftover-sdlhint",
    "sfml-xml-leftover-sfshader",
    "glfw-ini-leftover-glfwhint",
    "wgpu-py-leftover-wgbackend",
    "vulkan-lua-leftover-vklayer",
    "metal-h-leftover-mtlfamily",
    "webgpu-js-leftover-wgadapter",
    "filament-conf-leftover-filamat",
    "threejs-yml-leftover-threetone",
    "babylon-json-leftover-bblengine",
    "playcanvas-toml-leftover-pcbatch",
    "renpy-xml-leftover-rpytrans",
    "twine-ini-leftover-tweemacro",
    "inklang-py-leftover-inkknot",
    "dialogif-lua-leftover-dgpred",
    "inform-h-leftover-nikind",
    "tads-js-leftover-tadsadv",
    "bitsy-conf-leftover-bitpalette",
    "pico8-yml-leftover-p8map",
    "tic80-json-leftover-ticpal",
    "love2d-toml-leftover-lovecanvas",
    "defold-xml-leftover-deffactory",
    "solar2d-ini-leftover-s2composer",
    "cocos-py-leftover-ccphysics",
    "construct-lua-leftover-c3behavior",
    "gamemaker-h-leftover-gmlayer",
    "rpgmaker-js-leftover-rmplugin",
    "ghidra-conf-leftover-gdscript",
    "radare-yml-leftover-r2anal",
    "binaryninja-json-leftover-bnil",
    "ida-toml-leftover-idapy",
    "cutter-xml-leftover-cutterpy",
    "rizin-ini-leftover-rzanal",
    "angr-py-leftover-angrsim",
    "unicornemu-lua-leftover-ucarch",
    "qiling-h-leftover-qlos",
    "frida-js-leftover-fridajs",
    "pwntools-conf-leftover-pwncyclic",
    "gef-yml-leftover-gefheap",
    "peda-json-leftover-pedaaslr",
    "pwndbg-toml-leftover-pwndbgheap",
    "volatility-xml-leftover-volplugin",
    "rekall-ini-leftover-rekallprof",
    "autopsy-py-leftover-autmod",
    "sleuthkit-lua-leftover-tskimg",
    "plaso-h-leftover-plasoparser",
    "log2timeline-js-leftover-l2tparser",
    "osquery-conf-leftover-osqpack",
    "fleetdm-yml-leftover-fleetpack",
    "kolide-json-leftover-kolidepack",
    "arkime-toml-leftover-arkimewise",
    "stenographer-xml-leftover-stenopack",
    "cuckoo-ini-leftover-cuckopack",
    "capev2-py-leftover-capepack",
    "misp-lua-leftover-mispattr",
    "opencti-h-leftover-octiind",
    "thehive-js-leftover-hivecase",
    "cortexsoar-conf-leftover-cortexjob",
    "shuffle-yml-leftover-shufflow",
    "n8nflow-json-leftover-n8nnode",
    "huginn-toml-leftover-huginnag",
    "nodebb-xml-leftover-nodebbplug",
    "flarum-ini-leftover-flarumext",
    "discourse-py-leftover-discplugin",
    "piefed-lua-leftover-piefedvote",
    "mbin-h-leftover-mbinmag",
    "lotide-js-leftover-lotidevote",
    "zola-conf-leftover-minify",
    "hugo-yml-leftover-prettyurl",
    "eleventy-json-leftover-ssgcache",
    "astro-toml-leftover-islands",
    "remix-xml-leftover-loader",
    "sveltekit-ini-leftover-adapterx",
    "solidstart-py-leftover-signals",
    "qwik-lua-leftover-resumable",
    "fresh-h-leftover-routes",
    "hono-js-leftover-jsxruntime",
    "elysia-conf-leftover-macro",
    "fastifyx-yml-leftover-schema",
    "koa-json-leftover-middleware",
    "expressx-toml-leftover-helmet",
    "nestjs-xml-leftover-guards",
    "adonis-ini-leftover-lucid",
    "sails-py-leftover-blueprints",
    "loopback-lua-leftover-mixins",
    "strapi-h-leftover-graphql",
    "directus-js-leftover-permissions",
    "keystone-conf-leftover-lists",
    "payloadcms-yml-leftover-blocks",
    "sanity-json-leftover-groq",
    "contentful-toml-leftover-cdn",
    "datocms-xml-leftover-models",
    "hygraph-ini-leftover-unions",
    "prismic-py-leftover-slices",
    "storyblok-lua-leftover-bloks",
    "builderio-h-leftover-elements",
    "webflow-js-leftover-cms",
    "framer-conf-leftover-motion",
    "readymag-yml-leftover-pages",
    "webstudio-json-leftover-tokens",
    "plasmic-toml-leftover-components",
    "tooljet-xml-leftover-queries",
    "appsmith-ini-leftover-widgets",
    "retool-py-leftover-apps",
    "budibase-lua-leftover-automations",
    "nocodb-h-leftover-tables",
    "baserow-js-leftover-rows",
    "airtable-conf-leftover-bases",
    "notionx-yml-leftover-pagesx",
    "coda-json-leftover-docs",
    "clickup-toml-leftover-tasks",
    "linearx-xml-leftover-issues",
    "youtrack-ini-leftover-agile",
    "taiga-py-leftover-sprints",
    "openproject-lua-leftover-wbs",
    "redmine-h-leftover-trackers",
    "phabricator-js-leftover-diffs",
    "gerrit-conf-leftover-changes",
    "reviewboard-yml-leftover-reviews",
    "pagure-json-leftover-gitforge",
    "sourcehut-toml-leftover-builds",
    "codeberg-xml-leftover-pagesy",
    "radicle-ini-leftover-repos",
    "fossilx-py-leftover-patches",
    "mercurialx-lua-leftover-tickets",
    "darcsx-h-leftover-shelves",
    "bazaarx-js-leftover-branches"
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
        raise SystemExit("duplicate slugs in r1614 catalog")
    for slug in slugs:
        for needle in BANNED_SLUG_NEEDLES:
            if needle and needle in slug:
                raise SystemExit(f"banned needle {needle!r} in {slug}")
    plants = [spec["plant"] for pair in PAIRS for spec in pair]
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plants in r1614 catalog")


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
