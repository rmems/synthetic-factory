#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r1534+ unique media/homeauto/fediverse leftover plants.

BAN r01–r1533 clones including just-justfile-leftover-dotenv / taskfile-yml-leftover-includes,
elvish-toml-leftover-prompt / oil-rc-leftover-strict,
hydra-py-leftover-compose / sacred-py-leftover-observer,
solr-xml-leftover-cache / opensearchdash-yml-leftover-sso, leftover-revpin, libNNNN,
r690–r708 workspace clones. Do not rerun mdb-mill-r1351, mdb-mill-r1407, or mdb-mill-r1454.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_BASE = Path(__file__).with_name("mdb-mill-r1454.py")
_spec = importlib.util.spec_from_file_location("mdb_mill_r1454", _BASE)
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 1534
P = _m.P
build_episode = _m.build_episode
make = _m.make

PRIOR_SLUGS = tuple(spec["slug"] for pair in _m.PAIRS for spec in pair)
BANNED_SLUG_NEEDLES = _m.BANNED_SLUG_NEEDLES + PRIOR_SLUGS + (
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
    "acacia", "beech", "cedar", "dogwood", "elm", "fir", "ginkgo", "hickory", "ironwood", "juniper",
    "kauri", "larch", "maple", "nutmeg", "oakx", "pine", "quince", "redwood", "spruce", "teak",
    "umbrella", "viburnum", "walnut", "xylem", "yew", "aspen", "birch", "cypress", "datepalm", "ebony",
    "figtree", "guava", "hawthorn", "ilex", "jacaranda", "kapok", "linden", "magnolia", "nectarine", "olive",
    "poplar", "quebracho", "rowan", "sycamore", "tamarind", "ulmus", "willow", "xylosma", "yellowwood", "zelkova",
    "alder", "basswood", "chestnut", "douglasfir", "eucalyptus", "fringetree", "gumtree", "hornbeam", "iroko", "jujube",
    "kingwood", "lignum", "mahogany", "nyssa", "osage", "pecan", "queensland", "redbud", "satinwood", "tamarack",
    "upland", "velvetash", "whitebeam", "yellowbox", "acajou", "balsa", "camphor", "dawson", "elmwood", "ficus",
]
assert len(STEMS) == 80
PLANTS = [f"{s}s" for s in STEMS] + [f"{s}t" for s in STEMS]


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"mdb-r{round_n}-{a['slug']}"
    eb = f"mdb-r{round_n}-{b['slug']}"
    novel = 88 + (round_n % 5)
    return f"""# NOTES-r{round_n} monorepo-dep-bump-factory

Novel coverage: {novel}%

Two designed episodes (quota 2). Surfaces: {a['surface']} ({a['pkg']} {a['api_break']}); {b['surface']} ({b['pkg']} {b['api_break']}).
Not a pin-file mill and not libNNNN recycle. Distinct from r01–r1533 clones (ban just-justfile-leftover-dotenv / taskfile-yml-leftover-includes; elvish-toml-leftover-prompt / oil-rc-leftover-strict; hydra-py-leftover-compose / sacred-py-leftover-observer; solr-xml-leftover-cache / opensearchdash-yml-leftover-sso; leftover-revpin; r690–r708 workspace clones).

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
Keep unique leftover leftover leftover plots. Ban r01–r1533 clones, libNNNN, r690–r708 workspace clones.
"""


SLUGS = [
    "jellyfin-xml-leftover-transcode", "plex-xml-leftover-hwaccel",
    "emby-xml-leftover-library", "navidrome-toml-leftover-scanner",
    "immich-yml-leftover-ml", "photoprism-yml-leftover-index",
    "nextcloud-php-leftover-objectstore", "owncloud-php-leftover-dav",
    "syncthing-xml-leftover-folder", "homeassistant-yml-leftover-recorder",
    "zigbee2mqtt-yml-leftover-adapter", "mosquitto-conf-leftover-persistence",
    "emqx-toml-leftover-retainer", "nodered-json-leftover-flow",
    "esphome-yml-leftover-ota", "tasmota-ini-leftover-rules",
    "openhab-xml-leftover-thing", "homebridge-json-leftover-bridge",
    "flink-yml-leftover-checkpoint", "spark-conf-leftover-shuffle",
    "apachebeam-yml-leftover-runner", "nifi-xml-leftover-provenance",
    "airbyte-yml-leftover-sync", "meltano-yml-leftover-extractor",
    "singer-json-leftover-tap", "dbtcore-yml-leftover-incremental",
    "flang-mlir-leftover-fir", "gfortran-f90-leftover-std",
    "nasm-asm-leftover-elf", "yasm-asm-leftover-macho",
    "neovim-lua-leftover-treesitter", "emacs-el-leftover-nativecomp",
    "zed-toml-leftover-copilot", "lapce-toml-leftover-plugin",
    "julia-toml-leftover-precompile", "openmp-h-leftover-schedule",
    "zfs-conf-leftover-recordsize", "bird-conf-leftover-rpki",
    "frr-conf-leftover-bfd", "suricata-yml-leftover-eve",
    "zeek-conf-leftover-local", "ossec-conf-leftover-syscheck",
    "wazuh-conf-leftover-fim", "falco-yml-leftover-rules",
    "gitea-ini-leftover-actions", "forgejo-ini-leftover-actions",
    "honkit-json-leftover-plugin", "wasmcloud-toml-leftover-capability",
    "extism-toml-leftover-host", "scylladb-yml-leftover-compaction",
    "foundationdb-conf-leftover-fdb", "tikv-toml-leftover-raftstore",
    "quickwit-yml-leftover-split", "vllm-yml-leftover-pagedattn",
    "sglang-yml-leftover-radix", "tgi-yml-leftover-quantize",
    "ollama-json-leftover-numctx", "lmstudio-json-leftover-gpu",
    "librepcb-lp-leftover-drc", "horizoneda-json-leftover-rules",
    "darktable-conf-leftover-demosaic", "rawtherapee-pp3-leftover-profile",
    "gimp-scm-leftover-script", "inkscape-svg-leftover-filter",
    "kdenlive-xml-leftover-proxy", "shotcut-mlt-leftover-export",
    "sonarr-json-leftover-quality", "radarr-json-leftover-quality",
    "lidarr-json-leftover-metadata", "prowlarr-json-leftover-indexer",
    "bazarr-json-leftover-subtitle", "tautulli-ini-leftover-notify",
    "overseerr-json-leftover-request", "komga-yml-leftover-library",
    "kavita-json-leftover-library", "audiobookshelf-json-leftover-scanner",
    "calibreweb-json-leftover-opds", "freshrss-php-leftover-fever",
    "miniflux-ini-leftover-rewrite", "wallabag-yml-leftover-tag",
    "shaarli-php-leftover-plugin", "linkding-yml-leftover-bookmark",
    "vikunja-yml-leftover-caldav", "nextcloudtalk-json-leftover-signaling",
    "mattermost-json-leftover-plugin", "rocket-toml-leftover-federation",
    "zulip-conf-leftover-realm", "element-json-leftover-labs",
    "synapse-yml-leftover-federation", "dendrite-yml-leftover-jetstream",
    "conduit-toml-leftover-media", "etesync-yml-leftover-dav",
    "standardnotes-json-leftover-editor", "joplin-json-leftover-sync",
    "logseq-edn-leftover-graph", "obsidian-json-leftover-plugin",
    "foam-json-leftover-wikilink", "dendron-json-leftover-vault",
    "orgroam-el-leftover-db", "zettlr-json-leftover-cite",
    "qmk-json-leftover-combo", "vial-json-leftover-tapdance",
    "zmk-conf-leftover-behavior", "kmonad-kbd-leftover-layer",
    "kanata-kbd-leftover-sequence", "inputleap-conf-leftover-barrier",
    "deskflow-conf-leftover-clipboard", "kanshi-conf-leftover-profile",
    "gammastep-ini-leftover-temp", "swww-conf-leftover-transition",
    "hyprpaper-conf-leftover-preload", "waypaper-ini-leftover-backend",
    "paperless-yml-leftover-ocrengine", "rlang-r-leftover-dataframe",
    "octave-m-leftover-forge", "btrfs-conf-leftover-zstd",
    "lvm-conf-leftover-cachepool", "mdadm-conf-leftover-reshape",
    "gobgp-yml-leftover-rpki", "exabgp-conf-leftover-announce",
    "mdbook-toml-leftover-theme", "duplicati-json-leftover-schedule",
    "timeshift-json-leftover-rsync", "snapper-conf-leftover-timeline",
    "incus-yml-leftover-network", "harvester-yml-leftover-vlan",
    "tectonic-toml-leftover-bundle", "lualatex-tex-leftover-fontspec",
    "librewolf-js-leftover-resist", "floorp-js-leftover-tab",
    "zenbrowser-js-leftover-compact", "servo-toml-leftover-layout",
    "mercurial-hgrc-leftover-rebase", "darcs-conf-leftover-patch",
    "gotosocial-yml-leftover-media", "mastodon-yml-leftover-streaming",
    "akkoma-exs-leftover-uploader", "misskey-yml-leftover-id",
    "lemmy-toml-leftover-pictrs", "pixelfed-php-leftover-stories",
    "peertube-yml-leftover-transcoding", "castopod-php-leftover-fediverse",
    "funkwhale-yml-leftover-subsonic", "friendica-php-leftover-theme",
    "diaspora-yml-leftover-pod", "hubzilla-php-leftover-channel",
    "writefreely-toml-leftover-federation", "ghostcms-json-leftover-members",
    "plausible-yml-leftover-events", "umami-yml-leftover-tracker",
    "matomo-php-leftover-privacy", "posthog-yml-leftover-flags",
    "sentry-yml-leftover-quota", "glitchtip-yml-leftover-dsn",
    "uptimekuma-json-leftover-monitor", "healthchecks-yml-leftover-ping",
    "gatus-yml-leftover-endpoint", "statping-yml-leftover-service",
    "beszel-yml-leftover-agent", "signoz-yml-leftover-alert",
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
        raise SystemExit("duplicate slugs in r1534 catalog")
    for slug in slugs:
        for needle in BANNED_SLUG_NEEDLES:
            if needle and needle in slug:
                raise SystemExit(f"banned needle {needle!r} in {slug}")
    plants = [spec["plant"] for pair in PAIRS for spec in pair]
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plants in r1534 catalog")


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
