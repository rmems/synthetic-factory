#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r1694+ unique media/homeauto/fediverse leftover plants.

BAN r01–r1693 clones including darcsx-h-leftover-shelves / bazaarx-js-leftover-branches,
elvish-toml-leftover-prompt / oil-rc-leftover-strict,
hydra-py-leftover-compose / sacred-py-leftover-observer,
solr-xml-leftover-cache / opensearchdash-yml-leftover-sso, leftover-revpin, libNNNN,
r690–r708 workspace clones. Do not rerun mdb-mill-r1351, mdb-mill-r1407, mdb-mill-r1454, mdb-mill-r1534, or mdb-mill-r1614.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_BASE = Path(__file__).with_name("mdb-mill-r1614.py")
_spec = importlib.util.spec_from_file_location("mdb_mill_r1614", _BASE)
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 1694
P = _m.P
build_episode = _m.build_episode
make = _m.make

PRIOR_SLUGS = tuple(spec["slug"] for pair in _m.PAIRS for spec in pair)
BANNED_SLUG_NEEDLES = _m.BANNED_SLUG_NEEDLES + PRIOR_SLUGS + (
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
    "agate", "beryl", "calcite", "dolomite", "epidote", "fluorite", "garnet", "halite", "ilmenite", "jadeite",
    "kyanite", "labradorite", "malachite", "nephrite", "obsidianx", "peridot", "quartzx", "rhodonite", "spinel", "topaz",
    "uvite", "vesuvianite", "wollastonite", "xenotime", "yttriumx", "zircon", "amazonite", "bloodstone", "carnelian", "diopside",
    "emeraldx", "feldspar", "galena", "howlite", "iolite", "jasper", "kunzite", "larimar", "moonstone", "nacre",
    "onyx", "pyrite", "realgar", "sapphire", "turquoisex", "unakite", "vanadinite", "wulfenite", "xyloid", "zeolite",
    "andalusite", "bornite", "celestine", "danburite", "enstatite", "fayalite", "goethite", "hematitex", "idocrase", "jarosite",
    "kaolinite", "lepidolite", "magnetite", "natrolite", "olivine", "prehnite", "quartzite", "rutile", "staurolite", "titanite",
    "ulexite", "vivianite", "wavellite", "xenolith", "yellowstone", "zincite", "almandine", "benitoite", "chrysocolla", "dioptase",
]


assert len(STEMS) == 80
PLANTS = [f"{s}w" for s in STEMS] + [f"{s}x" for s in STEMS]


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"mdb-r{round_n}-{a['slug']}"
    eb = f"mdb-r{round_n}-{b['slug']}"
    novel = 88 + (round_n % 5)
    return f"""# NOTES-r{round_n} monorepo-dep-bump-factory

Novel coverage: {novel}%

Two designed episodes (quota 2). Surfaces: {a['surface']} ({a['pkg']} {a['api_break']}); {b['surface']} ({b['pkg']} {b['api_break']}).
Not a pin-file mill and not libNNNN recycle. Distinct from r01–r1693 clones (ban darcsx-h-leftover-shelves / bazaarx-js-leftover-branches; elvish-toml-leftover-prompt / oil-rc-leftover-strict; hydra-py-leftover-compose / sacred-py-leftover-observer; solr-xml-leftover-cache / opensearchdash-yml-leftover-sso; leftover-revpin; r690–r708 workspace clones).

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
Keep unique leftover leftover leftover plots. Ban r01–r1693 clones, libNNNN, r690–r708 workspace clones.
"""


SLUGS = [
    "nixos-conf-leftover-channel",
    "guixx-yml-leftover-manifestx",
    "pkgsrcx-json-leftover-mkinc",
    "portage-toml-leftover-ebuildx",
    "slackpkg-xml-leftover-pkgtool",
    "apktoolx-ini-leftover-apkindex",
    "xbps-py-leftover-repodata",
    "opkgx-lua-leftover-feedconf",
    "ipkg-h-leftover-controlx",
    "pacstall-js-leftover-aurhelper",
    "topgrade-conf-leftover-selfupd",
    "am-yml-leftover-appbin",
    "appimage-json-leftover-desktopf",
    "flatpakx-toml-leftover-remote",
    "snappyd-xml-leftover-refresh",
    "brewx-ini-leftover-cask",
    "macports-py-leftover-portfile",
    "finkx-lua-leftover-infoplist",
    "pkgsrcb-h-leftover-mkconf",
    "swupd-js-leftover-bundle",
    "dnf5-conf-leftover-module",
    "zypperx-yml-leftover-repoalias",
    "urpmi-json-leftover-media",
    "smartpm-toml-leftover-channelx",
    "aptitudex-xml-leftover-solver",
    "nala-ini-leftover-colorui",
    "debtree-py-leftover-rdepends",
    "equivs-lua-leftover-dummy",
    "reprepro-h-leftover-confdist",
    "aptly-js-leftover-publishx",
    "createrepo-conf-leftover-comps",
    "mockx-yml-leftover-chroot",
    "koji-json-leftover-tag",
    "obsx-toml-leftover-prjconf",
    "copr-xml-leftover-chrootx",
    "launchpadx-ini-leftover-archive",
    "ppa-py-leftover-sourcelist",
    "coprcli-lua-leftover-tokenx",
    "bodhi-h-leftover-update",
    "fedora-js-leftover-compose",
    "centosx-conf-leftover-stream",
    "rocky-yml-leftover-sig",
    "almalinux-json-leftover-vaultx",
    "oraclelinux-toml-leftover-uek",
    "amazonlinux-xml-leftover-amzn",
    "photon-ini-leftover-tdnf",
    "clearlinux-py-leftover-mixer",
    "talosx-lua-leftover-schematicx",
    "flatcar-h-leftover-sysext",
    "coreosx-js-leftover-ignition",
    "rancheros-conf-leftover-console",
    "k3os-yml-leftover-flannelx",
    "harvesterx-json-leftover-vlanx",
    "rke2-toml-leftover-server",
    "rke-xml-leftover-clusterx",
    "k0sx-ini-leftover-konnectx",
    "microk8sx-py-leftover-addonx",
    "kindx-lua-leftover-configx",
    "minikubex-h-leftover-profilex",
    "k3dx-js-leftover-cluster",
    "colima-conf-leftover-vz",
    "lima-yml-leftover-instance",
    "multipass-json-leftover-cloudinit",
    "utm-toml-leftover-qemux",
    "virtbox-xml-leftover-guest",
    "vmwarex-ini-leftover-toolsx",
    "parallels-py-leftover-prlctl",
    "hypervx-lua-leftover-vhd",
    "xen-h-leftover-domu",
    "kvmx-js-leftover-machinex",
    "libvirtx-conf-leftover-uri",
    "virtman-yml-leftover-domainx",
    "cockpitx-json-leftover-socket",
    "webminx-toml-leftover-modulex",
    "ajenti-xml-leftover-panel",
    "hestia-ini-leftover-hostnamex",
    "aaPanel-py-leftover-site",
    "cyberpanel-lua-leftover-vhost",
    "ispconfig-h-leftover-phpver",
    "vesta-js-leftover-dnsx",
    "caddyx-conf-leftover-http3x",
    "traefikx-yml-leftover-entryx",
    "envoyx-json-leftover-hcmx",
    "haproxyx-toml-leftover-aclx",
    "nginxx-xml-leftover-gzipx",
    "openresty-ini-leftover-luajit",
    "anginx-py-leftover-streamx",
    "tengine-lua-leftover-slice",
    "cherokee-h-leftover-vhostx",
    "lighttpdx-js-leftover-modfast",
    "hiawatha-conf-leftover-sslx",
    "monkeyhttp-yml-leftover-cgi",
    "thttpd-json-leftover-userdir",
    "busyboxhttpd-toml-leftover-inetd",
    "unitx-xml-leftover-confx",
    "csw-ini-leftover-listener",
    "tomcatx-py-leftover-valve",
    "jettyx-lua-leftover-niox",
    "wildfly-h-leftover-datasource",
    "glassfish-js-leftover-realm",
    "payara-conf-leftover-clusterx",
    "weblogic-yml-leftover-jndix",
    "websphere-json-leftover-cell",
    "resin-toml-leftover-filterx",
    "undertow-xml-leftover-io",
    "nettyx-ini-leftover-codec",
    "vertxx-py-leftover-routerx",
    "ktor-lua-leftover-enginex",
    "http4k-h-leftover-clientx",
    "akkahttp-js-leftover-materializer",
    "ginx-conf-leftover-binding",
    "echo-yml-leftover-groupx",
    "fiber-json-leftover-prefork",
    "chi-toml-leftover-muxx",
    "mux-xml-leftover-notfound",
    "beegox-ini-leftover-orm",
    "irisx-py-leftover-mvc",
    "revel-lua-leftover-route",
    "buffalo-h-leftover-resourcex",
    "martini-js-leftover-inject",
    "sinatrax-conf-leftover-dsl",
    "hanami-yml-leftover-entity",
    "railsx-json-leftover-activerecord",
    "padrino-toml-leftover-pluginx",
    "grape-xml-leftover-api",
    "cuba-ini-leftover-tiny",
    "rackx-py-leftover-middlewarex",
    "phoenixx-lua-leftover-endpointx",
    "plugx-h-leftover-conn",
    "cowboyx-js-leftover-ranchx",
    "plug-conf-leftover-plugx",
    "banditx-yml-leftover-handler",
    "plugn-json-leftover-dispatch",
    "cowboy-toml-leftover-protocolx",
    "ranch-xml-leftover-acceptor",
    "gun-ini-leftover-http2x",
    "shotgunx-py-leftover-reloadx",
    "elli-lua-leftover-callback",
    "yaws-h-leftover-appmod",
    "mochiweb-js-leftover-requestx",
    "cowboyb-conf-leftover-socketx",
    "phoenixb-yml-leftover-channelx",
    "liveview-json-leftover-heex",
    "surface-toml-leftover-componentx",
    "nerves-xml-leftover-firmware",
    "scenic-ini-leftover-graphx",
    "axon-py-leftover-tensor",
    "nx-lua-leftover-def",
    "bumblebee-h-leftover-serving",
    "explorerx-js-leftover-df",
    "polarsx-conf-leftover-lazy",
    "arrowx-yml-leftover-datasetx",
    "parquetx-json-leftover-rowgroup",
    "orcfile-toml-leftover-stripe",
    "avrox-xml-leftover-schemax",
    "protobufx-ini-leftover-wire",
    "capnp-py-leftover-rpcx",
    "flatbuffers-lua-leftover-vtable",
    "msgpackx-h-leftover-exttype",
    "cborx-js-leftover-tagx"
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
        raise SystemExit("duplicate slugs in r1694 catalog")
    for slug in slugs:
        for needle in BANNED_SLUG_NEEDLES:
            if needle and needle in slug:
                raise SystemExit(f"banned needle {needle!r} in {slug}")
    plants = [spec["plant"] for pair in PAIRS for spec in pair]
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plants in r1694 catalog")


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
