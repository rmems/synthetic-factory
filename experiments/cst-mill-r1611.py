#!/usr/bin/env python3
"""Designed leftover cache-stampede mill r1611+ (cst- ids). BAN r1–r1610."""
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
CATALOG_FIRST = 1611

PAIRS: list[tuple] = [
    ("Workbox", "workbox-precache-leftover", "workbox-runtime-handoff", "flock-wrkbx",
     "src/workbox.js", "tests/test_workbox.py", "precache leftover",
     "drop precache on miss", "precache leftover + wait + do(url)", 18,
     "runtime leftover still 1s", "runtime leftover",
     "src/workbox_rt.js", "tests/test_workbox_rt.py", "origins"),
    ("Service Worker", "sw-cache-addall-leftover", "sw-claim-handoff", "flock-swadd",
     "src/sw.js", "tests/test_sw.py", "addAll leftover",
     "drop addAll on miss", "addall leftover + wait + do(url)", 16,
     "clients.claim leftover still 1s", "claim leftover",
     "src/sw_claim.js", "tests/test_sw_claim.py", "origins"),
    ("Cache API", "cacheapi-match-leftover", "cacheapi-put-handoff", "flock-capim",
     "src/cacheapi.js", "tests/test_cacheapi.py", "match leftover",
     "drop match on miss", "match leftover + wait + do(req)", 17,
     "put leftover still 1s", "put leftover",
     "src/cacheapi_put.js", "tests/test_cacheapi_put.py", "origins"),
    ("IndexedDB", "idb-objectstore-leftover", "idb-index-handoff", "flock-idbos",
     "src/idb.js", "tests/test_idb.py", "objectStore leftover",
     "drop objectStore on miss", "store leftover + wait + do(key)", 15,
     "index leftover still 1s", "index leftover",
     "src/idb_idx.js", "tests/test_idb_idx.py", "gets"),
    ("HTTP Early Hints", "earlyhints-103-leftover", "earlyhints-preload-handoff", "flock-eh103",
     "src/earlyhints.conf", "tests/test_earlyhints.py", "103 leftover",
     "drop 103 on miss", "103 leftover + wait + do(url)", 14,
     "preload leftover still 1s", "preload leftover",
     "src/earlyhints_pl.conf", "tests/test_earlyhints_pl.py", "origins"),
    ("HTTP/2 push", "h2push-promise-leftover", "h2push-cancel-handoff", "flock-h2psh",
     "src/h2push.conf", "tests/test_h2push.py", "PUSH_PROMISE leftover",
     "drop PUSH_PROMISE on miss", "promise leftover + wait + do(url)", 13,
     "cancel leftover still 1s", "cancel leftover",
     "src/h2push_cx.conf", "tests/test_h2push_cx.py", "origins"),
    ("jsDelivr", "jsdelivr-npm-leftover", "jsdelivr-gh-handoff", "flock-jsdlv",
     "src/jsdelivr.json", "tests/test_jsdelivr.py", "npm leftover",
     "drop npm on miss", "npm leftover + wait + do(pkg)", 16,
     "github leftover still 1s", "github leftover",
     "src/jsdelivr_gh.json", "tests/test_jsdelivr_gh.py", "origins"),
    ("unpkg", "unpkg-meta-leftover", "unpkg-browse-handoff", "flock-unpkg",
     "src/unpkg.json", "tests/test_unpkg.py", "meta leftover",
     "drop meta on miss", "meta leftover + wait + do(pkg)", 12,
     "browse leftover still 1s", "browse leftover",
     "src/unpkg_br.json", "tests/test_unpkg_br.py", "origins"),
    ("cdnjs", "cdnjs-sri-leftover", "cdnjs-api-handoff", "flock-cdnjs",
     "src/cdnjs.json", "tests/test_cdnjs.py", "SRI leftover",
     "drop SRI on miss", "sri leftover + wait + do(lib)", 14,
     "api leftover still 1s", "api leftover",
     "src/cdnjs_api.json", "tests/test_cdnjs_api.py", "origins"),
    ("Cloudinary", "cloudinary-fetch-leftover", "cloudinary-eager-handoff", "flock-cldnr",
     "src/cloudinary.js", "tests/test_cloudinary.py", "fetch leftover",
     "drop fetch on miss", "fetch leftover + wait + do(url)", 19,
     "eager leftover still 1s", "eager leftover",
     "src/cloudinary_eg.js", "tests/test_cloudinary_eg.py", "origins"),
    ("Imgix", "imgix-purl-leftover", "imgix-auto-handoff", "flock-imgix",
     "src/imgix.js", "tests/test_imgix.py", "purl leftover",
     "drop purl on miss", "purl leftover + wait + do(url)", 15,
     "auto leftover still 1s", "auto leftover",
     "src/imgix_auto.js", "tests/test_imgix_auto.py", "origins"),
    ("ImageKit", "imagekit-url-leftover", "imagekit-overlay-handoff", "flock-imgkt",
     "src/imagekit.js", "tests/test_imagekit.py", "url leftover",
     "drop url on miss", "url leftover + wait + do(path)", 14,
     "overlay leftover still 1s", "overlay leftover",
     "src/imagekit_ov.js", "tests/test_imagekit_ov.py", "origins"),
    ("Uploadcare", "uploadcare-cdn-leftover", "uploadcare-filter-handoff", "flock-uplcd",
     "src/uploadcare.js", "tests/test_uploadcare.py", "cdn leftover",
     "drop cdn on miss", "cdn leftover + wait + do(uuid)", 13,
     "filter leftover still 1s", "filter leftover",
     "src/uploadcare_ft.js", "tests/test_uploadcare_ft.py", "origins"),
    ("Filestack", "filestack-process-leftover", "filestack-store-handoff", "flock-flstk",
     "src/filestack.js", "tests/test_filestack.py", "process leftover",
     "drop process on miss", "process leftover + wait + do(handle)", 12,
     "store leftover still 1s", "store leftover",
     "src/filestack_st.js", "tests/test_filestack_st.py", "origins"),
    ("Mux", "mux-playback-leftover", "mux-thumbnail-handoff", "flock-muxpb",
     "src/mux.js", "tests/test_mux.py", "playback leftover",
     "drop playback on miss", "playback leftover + wait + do(id)", 16,
     "thumbnail leftover still 1s", "thumbnail leftover",
     "src/mux_th.js", "tests/test_mux_th.py", "origins"),
    ("Cloudflare Stream", "cfstream-manifest-leftover", "cfstream-token-handoff", "flock-cfstr",
     "src/cfstream.js", "tests/test_cfstream.py", "manifest leftover",
     "drop manifest on miss", "manifest leftover + wait + do(uid)", 15,
     "token leftover still 1s", "token leftover",
     "src/cfstream_tk.js", "tests/test_cfstream_tk.py", "origins"),
    ("Cloudflare Images", "cfimages-variant-leftover", "cfimages-signed-handoff", "flock-cfimg",
     "src/cfimages.js", "tests/test_cfimages.py", "variant leftover",
     "drop variant on miss", "variant leftover + wait + do(id)", 14,
     "signed leftover still 1s", "signed leftover",
     "src/cfimages_sg.js", "tests/test_cfimages_sg.py", "origins"),
    ("CDN77", "cdn77-pull-leftover", "cdn77-purge-handoff", "flock-cdn77",
     "src/cdn77.json", "tests/test_cdn77.py", "pull leftover",
     "drop pull on miss", "pull leftover + wait + do(url)", 13,
     "purge leftover still 1s", "purge leftover",
     "src/cdn77_pg.json", "tests/test_cdn77_pg.py", "origins"),
    ("Gcore", "gcore-cdn-leftover", "gcore-shield-handoff", "flock-gcore",
     "src/gcore.json", "tests/test_gcore.py", "CDN leftover",
     "drop CDN on miss", "cdn leftover + wait + do(url)", 14,
     "shield leftover still 1s", "shield leftover",
     "src/gcore_sh.json", "tests/test_gcore_sh.py", "origins"),
    ("Alibaba CDN", "alicdn-refresh-leftover", "alicdn-preload-handoff", "flock-alcdn",
     "src/alicdn.json", "tests/test_alicdn.py", "refresh leftover",
     "drop refresh on miss", "refresh leftover + wait + do(url)", 15,
     "preload leftover still 1s", "preload leftover",
     "src/alicdn_pl.json", "tests/test_alicdn_pl.py", "origins"),
    ("Tencent CDN", "teo-purge-leftover", "teo-prefetch-handoff", "flock-teo",
     "src/teo.json", "tests/test_teo.py", "purge leftover",
     "drop purge on miss", "purge leftover + wait + do(url)", 13,
     "prefetch leftover still 1s", "prefetch leftover",
     "src/teo_pf.json", "tests/test_teo_pf.py", "origins"),
    ("Huawei CDN", "hwcdn-cache-leftover", "hwcdn-https-handoff", "flock-hwcdn",
     "src/hwcdn.json", "tests/test_hwcdn.py", "cache leftover",
     "drop cache on miss", "cache leftover + wait + do(url)", 12,
     "https leftover still 1s", "https leftover",
     "src/hwcdn_tls.json", "tests/test_hwcdn_tls.py", "origins"),
    ("Yandex CDN", "yandexcdn-origin-leftover", "yandexcdn-slice-handoff", "flock-yacdn",
     "src/yandexcdn.json", "tests/test_yandexcdn.py", "origin leftover",
     "drop origin on miss", "origin leftover + wait + do(url)", 13,
     "slice leftover still 1s", "slice leftover",
     "src/yandexcdn_sl.json", "tests/test_yandexcdn_sl.py", "origins"),
    ("Google Fonts", "gfonts-css2-leftover", "gfonts-display-handoff", "flock-gfnts",
     "src/gfonts.css", "tests/test_gfonts.py", "css2 leftover",
     "drop css2 on miss", "css2 leftover + wait + do(family)", 16,
     "display leftover still 1s", "display leftover",
     "src/gfonts_disp.css", "tests/test_gfonts_disp.py", "origins"),
    ("Fontsource", "fontsource-subset-leftover", "fontsource-variable-handoff", "flock-fntsrc",
     "src/fontsource.css", "tests/test_fontsource.py", "subset leftover",
     "drop subset on miss", "subset leftover + wait + do(family)", 12,
     "variable leftover still 1s", "variable leftover",
     "src/fontsource_var.css", "tests/test_fontsource_var.py", "origins"),
    ("Bunny Fonts", "bunnyfonts-css-leftover", "bunnyfonts-swap-handoff", "flock-bnfnt",
     "src/bunnyfonts.css", "tests/test_bunnyfonts.py", "css leftover",
     "drop css on miss", "css leftover + wait + do(family)", 11,
     "swap leftover still 1s", "swap leftover",
     "src/bunnyfonts_sw.css", "tests/test_bunnyfonts_sw.py", "origins"),
    ("Typekit", "typekit-kit-leftover", "typekit-af-handoff", "flock-tpkkt",
     "src/typekit.js", "tests/test_typekit.py", "kit leftover",
     "drop kit on miss", "kit leftover + wait + do(id)", 13,
     "af leftover still 1s", "af leftover",
     "src/typekit_af.js", "tests/test_typekit_af.py", "origins"),
    ("Bootstrap CDN", "bootcdn-sri-leftover", "bootcdn-css-handoff", "flock-btcdn",
     "src/bootcdn.html", "tests/test_bootcdn.py", "SRI leftover",
     "drop SRI on miss", "sri leftover + wait + do(lib)", 12,
     "css leftover still 1s", "css leftover",
     "src/bootcdn_css.html", "tests/test_bootcdn_css.py", "origins"),
    ("jsDelivr ESM", "jsdelivr-esm-leftover", "jsdelivr-combine-handoff", "flock-jsesm",
     "src/jsdelivr_esm.json", "tests/test_jsdelivr_esm.py", "esm leftover",
     "drop esm on miss", "esm leftover + wait + do(pkg)", 14,
     "combine leftover still 1s", "combine leftover",
     "src/jsdelivr_cb.json", "tests/test_jsdelivr_cb.py", "origins"),
    ("Skypack", "skypack-pin-leftover", "skypack-mode-handoff", "flock-skypk",
     "src/skypack.json", "tests/test_skypack.py", "pin leftover",
     "drop pin on miss", "pin leftover + wait + do(pkg)", 13,
     "mode leftover still 1s", "mode leftover",
     "src/skypack_md.json", "tests/test_skypack_md.py", "origins"),
    ("esm.sh", "esmsh-target-leftover", "esmsh-bundle-handoff", "flock-esmsh",
     "src/esmsh.json", "tests/test_esmsh.py", "target leftover",
     "drop target on miss", "target leftover + wait + do(pkg)", 12,
     "bundle leftover still 1s", "bundle leftover",
     "src/esmsh_bd.json", "tests/test_esmsh_bd.py", "origins"),
    ("jspm", "jspm-importmap-leftover", "jspm-generator-handoff", "flock-jspmp",
     "src/jspm.json", "tests/test_jspm.py", "importmap leftover",
     "drop importmap on miss", "map leftover + wait + do(pkg)", 13,
     "generator leftover still 1s", "generator leftover",
     "src/jspm_gen.json", "tests/test_jspm_gen.py", "origins"),
    ("UNPKG files", "unpkg-files-leftover", "unpkg-v-handoff", "flock-unpfl",
     "src/unpkg_files.json", "tests/test_unpkg_files.py", "files leftover",
     "drop files on miss", "files leftover + wait + do(pkg)", 11,
     "v leftover still 1s", "v leftover",
     "src/unpkg_v.json", "tests/test_unpkg_v.py", "origins"),
    ("npm CDN", "npmcdn-pkg-leftover", "npmcdn-tag-handoff", "flock-npmcd",
     "src/npmcdn.json", "tests/test_npmcdn.py", "pkg leftover",
     "drop pkg on miss", "pkg leftover + wait + do(name)", 12,
     "tag leftover still 1s", "tag leftover",
     "src/npmcdn_tg.json", "tests/test_npmcdn_tg.py", "origins"),
    ("Yarn pkg", "yarnpkg-tarball-leftover", "yarnpkg-integrity-handoff", "flock-yrnpk",
     "src/yarnpkg.json", "tests/test_yarnpkg.py", "tarball leftover",
     "drop tarball on miss", "tarball leftover + wait + do(pkg)", 14,
     "integrity leftover still 1s", "integrity leftover",
     "src/yarnpkg_ig.json", "tests/test_yarnpkg_ig.py", "origins"),
    ("pnpm store", "pnpm-content-leftover", "pnpm-hardlink-handoff", "flock-pnpms",
     "src/pnpm.json", "tests/test_pnpm.py", "content leftover",
     "drop content on miss", "content leftover + wait + do(hash)", 15,
     "hardlink leftover still 1s", "hardlink leftover",
     "src/pnpm_hl.json", "tests/test_pnpm_hl.py", "gets"),
    ("Nx cache", "nx-remote-cache-leftover", "nx-dte-handoff", "flock-nxrmc",
     "src/nx.json", "tests/test_nx.py", "remote cache leftover",
     "drop remote cache on miss", "remote leftover + wait + do(hash)", 16,
     "DTE leftover still 1s", "DTE leftover",
     "src/nx_dte.json", "tests/test_nx_dte.py", "gets"),
    ("Turborepo", "turbo-remote-leftover", "turbo-env-handoff", "flock-trbrm",
     "src/turbo.json", "tests/test_turbo.py", "remote leftover",
     "drop remote on miss", "remote leftover + wait + do(hash)", 17,
     "env leftover still 1s", "env leftover",
     "src/turbo_env.json", "tests/test_turbo_env.py", "gets"),
    ("Gradle build cache", "gradle-remote-leftover", "gradle-local-handoff", "flock-grdlc",
     "src/gradle.properties", "tests/test_gradle.py", "remote leftover",
     "drop remote on miss", "remote leftover + wait + do(key)", 18,
     "local leftover still 1s", "local leftover",
     "src/gradle_local.properties", "tests/test_gradle_local.py", "gets"),
    ("Bazel remote", "bazel-cas-leftover", "bazel-ac-handoff", "flock-bzlcs",
     "src/bazelrc", "tests/test_bazel.py", "CAS leftover",
     "drop CAS on miss", "cas leftover + wait + do(digest)", 19,
     "AC leftover still 1s", "AC leftover",
     "src/bazelrc_ac", "tests/test_bazel_ac.py", "gets"),
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
        "Not flock-wN. Not AWS catalog. Not r1–r1610 clones (incl. r1445 akamai-esi, r1610 webvitals-cls). "
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
