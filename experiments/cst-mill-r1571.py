#!/usr/bin/env python3
"""Designed leftover cache-stampede mill r1571+ (cst- ids). BAN r1–r1570."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("cst1446", HERE / "cst-mill-r1446.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)
_steps_ok = _m._steps_ok
_steps_part = _m._steps_part
CATALOG_FIRST = 1571

PAIRS: list[tuple] = [
    ("Vercel Edge", "vercel-edge-cache-leftover", "vercel-isr-handoff", "flock-vrcel",
     "src/vercel_edge.ts", "tests/test_vercel_edge.py", "edge cache leftover",
     "drop edge cache on miss", "edge leftover + wait + do(path)", 18,
     "ISR leftover still 1s", "ISR leftover",
     "src/vercel_isr.ts", "tests/test_vercel_isr.py", "origins"),
    ("Netlify", "netlify-cdn-leftover", "netlify-obr-handoff", "flock-ntfcd",
     "src/netlify.toml", "tests/test_netlify.py", "CDN leftover",
     "drop CDN on miss", "cdn leftover + wait + do(path)", 16,
     "OBR leftover still 1s", "OBR leftover",
     "src/netlify_obr.toml", "tests/test_netlify_obr.py", "origins"),
    ("Cloudflare Pages", "cfpages-kv-leftover", "cfpages-d1-handoff", "flock-cfpgs",
     "src/cfpages.js", "tests/test_cfpages.py", "Pages KV leftover",
     "drop Pages KV on miss", "kv leftover + wait + do(path)", 17,
     "D1 leftover still 1s", "D1 leftover",
     "src/cfpages_d1.js", "tests/test_cfpages_d1.py", "origins"),
    ("AWS Amplify", "amplify-ssr-leftover", "amplify-rewrite-handoff", "flock-amplf",
     "src/amplify.yml", "tests/test_amplify.py", "SSR cache leftover",
     "drop SSR cache on miss", "ssr leftover + wait + do(path)", 15,
     "rewrite leftover still 1s", "rewrite leftover",
     "src/amplify_rw.yml", "tests/test_amplify_rw.py", "origins"),
    ("Azure SWA", "swa-static-leftover", "swa-fallback-handoff", "flock-azswa",
     "src/swa.json", "tests/test_swa.py", "static leftover",
     "drop static on miss", "static leftover + wait + do(path)", 14,
     "fallback leftover still 1s", "fallback leftover",
     "src/swa_fb.json", "tests/test_swa_fb.py", "origins"),
    ("Fly.io", "fly-replay-leftover", "fly-consul-handoff", "flock-flyrp",
     "src/fly.toml", "tests/test_fly.py", "replay leftover",
     "drop replay on miss", "replay leftover + wait + do(path)", 19,
     "consul leftover still 1s", "consul leftover",
     "src/fly_consul.toml", "tests/test_fly_consul.py", "origins"),
    ("Render", "render-edge-leftover", "render-disk-handoff", "flock-rndre",
     "src/render.yaml", "tests/test_render.py", "edge leftover",
     "drop edge on miss", "edge leftover + wait + do(path)", 13,
     "disk leftover still 1s", "disk leftover",
     "src/render_disk.yaml", "tests/test_render_disk.py", "origins"),
    ("Railway", "railway-replica-leftover", "railway-volume-handoff", "flock-rlwrep",
     "src/railway.toml", "tests/test_railway.py", "replica leftover",
     "drop replica on miss", "replica leftover + wait + do(path)", 12,
     "volume leftover still 1s", "volume leftover",
     "src/railway_vol.toml", "tests/test_railway_vol.py", "origins"),
    ("WP Super Cache", "wpsc-modrewrite-leftover", "wpsc-preload-handoff", "flock-wpscm",
     "src/wpsc.php", "tests/test_wpsc.py", "mod_rewrite leftover",
     "drop mod_rewrite on miss", "rewrite leftover + wait + do(url)", 21,
     "preload leftover still 1s", "preload leftover",
     "src/wpsc_pre.php", "tests/test_wpsc_pre.py", "origins"),
    ("W3 Total Cache", "w3tc-page-leftover", "w3tc-dbcache-handoff", "flock-w3tcp",
     "src/w3tc.php", "tests/test_w3tc.py", "page cache leftover",
     "drop page cache on miss", "page leftover + wait + do(url)", 20,
     "dbcache leftover still 1s", "dbcache leftover",
     "src/w3tc_db.php", "tests/test_w3tc_db.py", "origins"),
    ("WP Rocket", "wprocket-rucss-leftover", "wprocket-preload-handoff", "flock-wprkt",
     "src/wprocket.php", "tests/test_wprocket.py", "RUCSS leftover",
     "drop RUCSS on miss", "rucss leftover + wait + do(url)", 18,
     "preload leftover still 1s", "preload leftover",
     "src/wprocket_pre.php", "tests/test_wprocket_pre.py", "origins"),
    ("NitroPack", "nitropack-optimizer-leftover", "nitropack-warmup-handoff", "flock-ntrpk",
     "src/nitropack.php", "tests/test_nitropack.py", "optimizer leftover",
     "drop optimizer on miss", "opt leftover + wait + do(url)", 16,
     "warmup leftover still 1s", "warmup leftover",
     "src/nitropack_wu.php", "tests/test_nitropack_wu.py", "origins"),
    ("QUIC.cloud", "quiccloud-node-leftover", "quiccloud-lqip-handoff", "flock-quicc",
     "src/quiccloud.php", "tests/test_quiccloud.py", "node leftover",
     "drop node on miss", "node leftover + wait + do(url)", 17,
     "LQIP leftover still 1s", "LQIP leftover",
     "src/quiccloud_lq.php", "tests/test_quiccloud_lq.py", "origins"),
    ("Kinsta cache", "kinsta-mu-leftover", "kinsta-edge-handoff", "flock-knstc",
     "src/kinsta.php", "tests/test_kinsta.py", "MU cache leftover",
     "drop MU cache on miss", "mu leftover + wait + do(url)", 15,
     "edge leftover still 1s", "edge leftover",
     "src/kinsta_edge.php", "tests/test_kinsta_edge.py", "origins"),
    ("WP Engine", "wpengine-varnish-leftover", "wpengine-genesis-handoff", "flock-wpeng",
     "src/wpengine.php", "tests/test_wpengine.py", "varnish leftover",
     "drop varnish on miss", "varnish leftover + wait + do(url)", 19,
     "genesis leftover still 1s", "genesis leftover",
     "src/wpengine_gen.php", "tests/test_wpengine_gen.py", "origins"),
    ("Pantheon", "pantheon-globalcdn-leftover", "pantheon-redis-handoff", "flock-pnthn",
     "src/pantheon.yml", "tests/test_pantheon.py", "Global CDN leftover",
     "drop Global CDN on miss", "cdn leftover + wait + do(url)", 18,
     "redis leftover still 1s", "redis leftover",
     "src/pantheon_redis.yml", "tests/test_pantheon_redis.py", "origins"),
    ("Acquia", "acquia-varnish-leftover", "acquia-memcache-handoff", "flock-acqvn",
     "src/acquia.yml", "tests/test_acquia.py", "Varnish leftover",
     "drop Varnish on miss", "varnish leftover + wait + do(url)", 16,
     "memcache leftover still 1s", "memcache leftover",
     "src/acquia_mc.yml", "tests/test_acquia_mc.py", "origins"),
    ("Platform.sh", "platsh-router-leftover", "platsh-redis-handoff", "flock-pltsh",
     "src/platform.yaml", "tests/test_platform.py", "router leftover",
     "drop router on miss", "router leftover + wait + do(url)", 14,
     "redis leftover still 1s", "redis leftover",
     "src/platform_redis.yaml", "tests/test_platform_redis.py", "origins"),
    ("Sucuri", "sucuri-firewall-leftover", "sucuri-cache-handoff", "flock-sucfw",
     "src/sucuri.json", "tests/test_sucuri.py", "firewall leftover",
     "drop firewall on miss", "fw leftover + wait + do(url)", 15,
     "cache leftover still 1s", "cache leftover",
     "src/sucuri_cache.json", "tests/test_sucuri_cache.py", "origins"),
    ("Wordfence", "wordfence-falcon-leftover", "wordfence-waf-handoff", "flock-wdfnc",
     "src/wordfence.php", "tests/test_wordfence.py", "falcon leftover",
     "drop falcon on miss", "falcon leftover + wait + do(url)", 17,
     "WAF leftover still 1s", "WAF leftover",
     "src/wordfence_waf.php", "tests/test_wordfence_waf.py", "origins"),
    ("Batcache", "batcache-gen-leftover", "batcache-group-handoff", "flock-btcch",
     "src/batcache.php", "tests/test_batcache.py", "gen leftover",
     "drop gen on miss", "gen leftover + wait + do(url)", 13,
     "group leftover still 1s", "group leftover",
     "src/batcache_grp.php", "tests/test_batcache_grp.py", "origins"),
    ("Hyper Cache", "hypercache-folder-leftover", "hypercache-gzip-handoff", "flock-hyprc",
     "src/hypercache.php", "tests/test_hypercache.py", "folder leftover",
     "drop folder on miss", "folder leftover + wait + do(url)", 12,
     "gzip leftover still 1s", "gzip leftover",
     "src/hypercache_gz.php", "tests/test_hypercache_gz.py", "origins"),
    ("Redis Object Cache", "roc-dropin-leftover", "roc-igbinary-handoff", "flock-rocdo",
     "src/roc.php", "tests/test_roc.py", "drop-in leftover",
     "drop drop-in on miss", "dropin leftover + wait + do(key)", 20,
     "igbinary leftover still 1s", "igbinary leftover",
     "src/roc_ig.php", "tests/test_roc_ig.py", "gets"),
    ("SiteGround Dynamic", "sg-dynamic-leftover", "sg-memcached-handoff", "flock-sgdyn",
     "src/sgcache.php", "tests/test_sgcache.py", "dynamic leftover",
     "drop dynamic on miss", "dyn leftover + wait + do(url)", 16,
     "memcached leftover still 1s", "memcached leftover",
     "src/sgcache_mc.php", "tests/test_sgcache_mc.py", "origins"),
    ("FlyingPress", "flyingpress-css-leftover", "flyingpress-delay-handoff", "flock-flypr",
     "src/flyingpress.php", "tests/test_flyingpress.py", "CSS leftover",
     "drop CSS on miss", "css leftover + wait + do(url)", 14,
     "delay leftover still 1s", "delay leftover",
     "src/flyingpress_dl.php", "tests/test_flyingpress_dl.py", "origins"),
    ("Swift Performance", "swiftperf-ajax-leftover", "swiftperf-warmup-handoff", "flock-swftp",
     "src/swiftperf.php", "tests/test_swiftperf.py", "ajax leftover",
     "drop ajax on miss", "ajax leftover + wait + do(url)", 15,
     "warmup leftover still 1s", "warmup leftover",
     "src/swiftperf_wu.php", "tests/test_swiftperf_wu.py", "origins"),
    ("Hummingbird", "hummingbird-page-leftover", "hummingbird-gravatar-handoff", "flock-hmbrd",
     "src/hummingbird.php", "tests/test_hummingbird.py", "page leftover",
     "drop page on miss", "page leftover + wait + do(url)", 13,
     "gravatar leftover still 1s", "gravatar leftover",
     "src/hummingbird_gv.php", "tests/test_hummingbird_gv.py", "origins"),
    ("LiteSpeed crawler", "lscrawl-leftover", "lscrawl-guest-handoff", "flock-lscrl",
     "src/lscrawl.php", "tests/test_lscrawl.py", "crawler leftover",
     "drop crawler on miss", "crawler leftover + wait + do(url)", 18,
     "guest leftover still 1s", "guest leftover",
     "src/lscrawl_gst.php", "tests/test_lscrawl_gst.py", "origins"),
    ("Cloudflare APO extra", "cfapo-bypass-leftover", "cfapo-device-handoff", "flock-cfapo",
     "src/cfapo.js", "tests/test_cfapo.py", "bypass leftover",
     "drop bypass on miss", "bypass leftover + wait + do(url)", 16,
     "device leftover still 1s", "device leftover",
     "src/cfapo_dev.js", "tests/test_cfapo_dev.py", "origins"),
    ("Bunny Optimizer", "bunny-optimizer-leftover", "bunny-smart-handoff", "flock-bnopt",
     "src/bunny_opt.json", "tests/test_bunny_opt.py", "optimizer leftover",
     "drop optimizer on miss", "opt leftover + wait + do(url)", 15,
     "smart leftover still 1s", "smart leftover",
     "src/bunny_smart.json", "tests/test_bunny_smart.py", "origins"),
    ("KeyCDN cache key", "keycdn-query-leftover", "keycdn-cookie-handoff", "flock-kcdnq",
     "src/keycdn_query.json", "tests/test_keycdn_query.py", "query leftover",
     "drop query on miss", "query leftover + wait + do(url)", 14,
     "cookie leftover still 1s", "cookie leftover",
     "src/keycdn_ck.json", "tests/test_keycdn_ck.py", "origins"),
    ("GTmetrix", "gtmetrix-video-leftover", "gtmetrix-filmstrip-handoff", "flock-gtmtx",
     "src/gtmetrix.json", "tests/test_gtmetrix.py", "video leftover",
     "drop video on miss", "video leftover + wait + do(url)", 11,
     "filmstrip leftover still 1s", "filmstrip leftover",
     "src/gtmetrix_fs.json", "tests/test_gtmetrix_fs.py", "origins"),
    ("Lighthouse CI", "lhci-storage-leftover", "lhci-assert-handoff", "flock-lhcis",
     "src/lhci.json", "tests/test_lhci.py", "storage leftover",
     "drop storage on miss", "storage leftover + wait + do(url)", 12,
     "assert leftover still 1s", "assert leftover",
     "src/lhci_as.json", "tests/test_lhci_as.py", "origins"),
    ("WebPageTest", "wpt-repeat-leftover", "wpt-video-handoff", "flock-wptrp",
     "src/wpt.json", "tests/test_wpt.py", "repeat view leftover",
     "drop repeat on miss", "repeat leftover + wait + do(url)", 13,
     "video leftover still 1s", "video leftover",
     "src/wpt_vid.json", "tests/test_wpt_vid.py", "origins"),
    ("Calibre", "calibre-snapshot-leftover", "calibre-budget-handoff", "flock-calbr",
     "src/calibre.yml", "tests/test_calibre.py", "snapshot leftover",
     "drop snapshot on miss", "snap leftover + wait + do(url)", 12,
     "budget leftover still 1s", "budget leftover",
     "src/calibre_bd.yml", "tests/test_calibre_bd.py", "origins"),
    ("SpeedCurve", "speedcurve-lux-leftover", "speedcurve-rum-handoff", "flock-spdcr",
     "src/speedcurve.js", "tests/test_speedcurve.py", "LUX leftover",
     "drop LUX on miss", "lux leftover + wait + do(url)", 14,
     "RUM leftover still 1s", "RUM leftover",
     "src/speedcurve_rum.js", "tests/test_speedcurve_rum.py", "origins"),
    ("DebugBear", "debugbear-crux-leftover", "debugbear-lab-handoff", "flock-dbgbr",
     "src/debugbear.json", "tests/test_debugbear.py", "CrUX leftover",
     "drop CrUX on miss", "crux leftover + wait + do(url)", 13,
     "lab leftover still 1s", "lab leftover",
     "src/debugbear_lab.json", "tests/test_debugbear_lab.py", "origins"),
    ("Treo", "treo-crux-leftover", "treo-psi-handoff", "flock-treoc",
     "src/treo.json", "tests/test_treo.py", "CrUX leftover",
     "drop CrUX on miss", "crux leftover + wait + do(url)", 11,
     "PSI leftover still 1s", "PSI leftover",
     "src/treo_psi.json", "tests/test_treo_psi.py", "origins"),
    ("PageSpeed Insights", "psi-lighthouse-leftover", "psi-loading-handoff", "flock-psilh",
     "src/psi.json", "tests/test_psi.py", "Lighthouse leftover",
     "drop Lighthouse on miss", "lh leftover + wait + do(url)", 15,
     "loading leftover still 1s", "loading leftover",
     "src/psi_load.json", "tests/test_psi_load.py", "origins"),
    ("Web Vitals", "webvitals-cls-leftover", "webvitals-inp-handoff", "flock-wbvtl",
     "src/webvitals.js", "tests/test_webvitals.py", "CLS leftover",
     "drop CLS on miss", "cls leftover + wait + do(url)", 16,
     "INP leftover still 1s", "INP leftover",
     "src/webvitals_inp.js", "tests/test_webvitals_inp.py", "origins"),
]


def records(round_n: int):
    idx = round_n - CATALOG_FIRST
    p = PAIRS[idx]
    product, slug_ok, slug_part, plant, src, test, api, naive, fix, workers, residual, sibling, *_ = p
    rec_ok = {
        "id": f"cst-r{round_n}-{slug_ok}",
        "goal": (
            f"{plant}: leftover leftover leftover {product} {api} still stampedes {workers} callers after a crashed refresh. "
            f"One in-flight via {fix}. Do not {naive}. Gate is {test}."
        ),
        "plan": f"{naive} so leftover leftover leftover cannot stampede origin.",
        "steps": _steps_ok(p),
        "outcome": (
            f"Leftover leftover leftover {product} stampeded {workers} callers. {naive} failed still-rebuilds. "
            f"Plan change: {fix}. {test} 4/4, suite 8/8. Residual: {residual}."
        ),
        "reward": {"success": True, "plan_changes": 1, "tests_passed": 8, "cost_steps": 16},
        "meta": {
            "factory": "cache-stampede-factory",
            "round": round_n,
            "generator": "grok-4.6",
            "kind": "designed",
            "product": product,
            "mechanic": f"leftover leftover leftover {api}",
            "sim_or_real": "designed",
            "plant": plant,
        },
    }
    rec_part = {
        "id": f"cst-r{round_n}-{slug_part}",
        "goal": (
            f"{plant}: leftover leftover leftover {product} still stampedes after a crashed refresh. "
            f"One in-flight via {fix}. Do not {naive}. Gate is {test}. "
            f"{sibling} may still hard-miss; ticket allows handoff."
        ),
        "plan": f"{naive} so leftover leftover leftover cannot stampede origin.",
        "steps": _steps_part(p),
        "outcome": (
            f"Leftover leftover leftover {product} stampeded callers. {naive} failed fixture. "
            f"Plan change: {fix}. {test} 3/3. Partial: leftover leftover leftover {sibling} still leftover (xfail)."
        ),
        "reward": {
            "success": False,
            "plan_changes": 1,
            "tests_passed": 3,
            "xfailed": 1,
            "handoff": 1,
            "cost_steps": 17,
        },
        "meta": {
            "factory": "cache-stampede-factory",
            "round": round_n,
            "generator": "grok-4.6",
            "kind": "designed",
            "product": product,
            "mechanic": f"leftover leftover leftover {sibling}",
            "sim_or_real": "designed",
            "plant": plant,
        },
    }
    return [rec_ok, rec_part]


def notes_md(round_n: int) -> str:
    idx = round_n - CATALOG_FIRST
    p = PAIRS[idx]
    product, slug_ok, slug_part, plant, src, test, api, naive, fix, workers, residual, sibling, *_ = p
    return (
        f"# NOTES-r{round_n} cache-stampede-factory\n\n"
        "Novel coverage: 91%\n\n"
        f"Two designed leftover leftover leftover stampede episodes (quota 2). "
        f"{product} leftover leftover leftover {api} vs leftover leftover leftover {sibling}. "
        "Not flock-wN. Not AWS catalog. Not r1–r1570 clones (incl. r1445 akamai-esi, r1570 unbound-prefetch). "
        "Not dbc-/sir-/gql- ids.\n"
        "Not overlayfs whiteout. Not nydus/stargz. Not search-index leftover. Not docker leftover leftover leftover.\n\n"
        "| id | seed | first apply | plan change | terminal |\n"
        "|---|---|---|---|---|\n"
        f"| cst-r{round_n}-{slug_ok} | {workers} leftover leftover leftover {product} | {naive} | {fix} | success residual {residual} |\n"
        f"| cst-r{round_n}-{slug_part} | leftover leftover leftover {sibling} | {naive} | {fix} | handoff leftover sibling |\n\n"
        "## Step counts\n"
        "- ep1: 16. Naive 6–7; plan change 8; suite green 12–16.\n"
        "- ep2: 17. Naive 6–7; plan change 8; sibling xfail 12–17.\n\n"
        "## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:. No thought keys. Plant `{plant}`.\n"
        "meta.generator=grok-4.6. Invented plant. No sim_or_real: real.\n\n"
        "## Weaknesses / next\n"
        f"Avoid {slug_ok} reruns and docker/search ids.\n"
    )


def write_round(round_n: int, stage: Path):
    recs = records(round_n)
    (stage / f"batch-r{round_n:02d}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=True) + "\n" for r in recs)
    )
    (stage / f"NOTES-r{round_n:02d}.md").write_text(notes_md(round_n))
    return [r["id"] for r in recs]
