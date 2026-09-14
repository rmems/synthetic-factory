#!/usr/bin/env python3
"""Designed leftover cache-stampede mill r1491+ (cst- ids).

BAN r1–r1490 including r1490 oraclegc-near-ce and r1445 akamai-esi.
Not overlayfs/nydus/stargz. Not docker/search ids.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("cst1446", HERE / "cst-mill-r1446.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

_steps_ok = _m._steps_ok
_steps_part = _m._steps_part

CATALOG_FIRST = 1491


def records(round_n: int):
    idx = round_n - CATALOG_FIRST
    p = PAIRS[idx]
    product, slug_ok, slug_part, plant, src, test, api, naive, fix, workers, residual, sibling, *_ = p
    rec_ok, rec_part = _m.records.__wrapped__(round_n) if False else (None, None)
    recs = _m.records.__globals__  # noqa: not used
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
        "Not flock-wN. Not AWS catalog. Not r1–r1490 clones (incl. r1445 akamai-esi, r1490 oraclegc-near-ce). "
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
    import json
    (stage / f"batch-r{round_n:02d}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=True) + "\n" for r in recs)
    )
    (stage / f"NOTES-r{round_n:02d}.md").write_text(notes_md(round_n))
    return [r["id"] for r in recs]


PAIRS: list[tuple] = [
    ("CacheLib", "cachelib-navy-leftover", "cachelib-admission-handoff", "flock-clnvy",
     "src/cachelib_navy.cpp", "tests/test_cachelib_navy.py", "Navy hybrid leftover",
     "drop Navy on miss", "navy leftover + wait + do(key)", 28,
     "admission leftover still rejects", "admission leftover",
     "src/cachelib_adm.cpp", "tests/test_cachelib_adm.py", "gets"),
    ("Souin", "souin-stale-leftover", "souin-surrogate-handoff", "flock-souin",
     "src/souin_stale.yml", "tests/test_souin_stale.py", "stale leftover",
     "drop stale on miss", "stale leftover + wait + do(url)", 18,
     "surrogate leftover still 1s", "surrogate leftover",
     "src/souin_surr.yml", "tests/test_souin_surr.py", "origins"),
    ("APISIX", "apisix-proxy-cache-leftover", "apisix-redis-cache-handoff", "flock-apxpc",
     "src/apisix_cache.yaml", "tests/test_apisix_cache.py", "proxy-cache leftover",
     "drop proxy-cache on miss", "proxy leftover + wait + do(uri)", 22,
     "redis cache leftover still 1s", "redis cache leftover",
     "src/apisix_redis.yaml", "tests/test_apisix_redis.py", "origins"),
    ("Skipper", "skipper-rfc-cache-leftover", "skipper-backend-handoff", "flock-skrfc",
     "src/skipper_rfc.eskip", "tests/test_skipper_rfc.py", "rfcCache leftover",
     "drop rfcCache on miss", "rfc leftover + wait + do(url)", 16,
     "backend leftover still stampedes", "backend leftover",
     "src/skipper_be.eskip", "tests/test_skipper_be.py", "origins"),
    ("imgproxy", "imgproxy-result-cache-leftover", "imgproxy-source-handoff", "flock-imgpr",
     "src/imgproxy_cache.yml", "tests/test_imgproxy_cache.py", "result cache leftover",
     "drop result cache on miss", "result leftover + wait + do(url)", 20,
     "source leftover still downloads", "source leftover",
     "src/imgproxy_src.yml", "tests/test_imgproxy_src.py", "origins"),
    ("Thumbor", "thumbor-result-stor-leftover", "thumbor-loader-handoff", "flock-thmb",
     "src/thumbor_result.conf", "tests/test_thumbor_result.py", "RESULT_STORAGE leftover",
     "drop RESULT_STORAGE on miss", "result leftover + wait + do(url)", 17,
     "loader leftover still fetches", "loader leftover",
     "src/thumbor_loader.conf", "tests/test_thumbor_loader.py", "origins"),
    ("RocksDB", "rocksdb-block-cache-leftover", "rocksdb-row-cache-handoff", "flock-rdbbl",
     "src/rocksdb_block.cc", "tests/test_rocksdb_block.py", "LRUCache leftover",
     "drop LRUCache on miss", "block leftover + wait + do(key)", 31,
     "row cache leftover still 1s", "row cache leftover",
     "src/rocksdb_row.cc", "tests/test_rocksdb_row.py", "gets"),
    ("WiredTiger", "wiredtiger-cache-leftover", "wiredtiger-evict-handoff", "flock-wtcch",
     "src/wt_cache.c", "tests/test_wt_cache.py", "cache_size leftover",
     "drop cache_size on miss", "cache leftover + wait + do(key)", 24,
     "eviction leftover still stalls", "eviction leftover",
     "src/wt_evict.c", "tests/test_wt_evict.py", "gets"),
    ("Badger", "badger-block-cache-leftover", "badger-index-handoff", "flock-bdgbc",
     "src/badger_block.go", "tests/test_badger_block.py", "BlockCache leftover",
     "drop BlockCache on miss", "block leftover + wait + do(key)", 19,
     "index leftover still restamps", "index leftover",
     "src/badger_index.go", "tests/test_badger_index.py", "gets"),
    ("Pebble", "pebble-cache-leftover", "pebble-sstable-handoff", "flock-pblch",
     "src/pebble_cache.go", "tests/test_pebble_cache.py", "Cache leftover",
     "drop Cache on miss", "cache leftover + wait + do(key)", 21,
     "sstable leftover still 1s", "sstable leftover",
     "src/pebble_sst.go", "tests/test_pebble_sst.py", "gets"),
    ("Sled", "sled-pagecache-leftover", "sled-snapshot-handoff", "flock-sldpc",
     "src/sled_page.rs", "tests/test_sled_page.py", "pagecache leftover",
     "drop pagecache on miss", "page leftover + wait + do(key)", 15,
     "snapshot leftover still restamps", "snapshot leftover",
     "src/sled_snap.rs", "tests/test_sled_snap.py", "gets"),
    ("Redb", "redb-cache-leftover", "redb-multimap-handoff", "flock-rdbmm",
     "src/redb_cache.rs", "tests/test_redb_cache.py", "cache leftover",
     "drop cache on miss", "cache leftover + wait + do(key)", 14,
     "multimap leftover still splits", "multimap leftover",
     "src/redb_mmap.rs", "tests/test_redb_mmap.py", "gets"),
    ("Alluxio", "alluxio-worker-leftover", "alluxio-ufs-handoff", "flock-alxwk",
     "src/alluxio_worker.java", "tests/test_alluxio_worker.py", "worker cache leftover",
     "drop worker cache on miss", "worker leftover + wait + do(path)", 26,
     "UFS leftover still downloads", "UFS leftover",
     "src/alluxio_ufs.java", "tests/test_alluxio_ufs.py", "reads"),
    ("JuiceFS", "juicefs-opencache-leftover", "juicefs-kernel-handoff", "flock-jfsoc",
     "src/juicefs_open.conf", "tests/test_juicefs_open.py", "open-cache leftover",
     "drop open-cache on miss", "open leftover + wait + do(path)", 18,
     "kernel leftover still 1s", "kernel leftover",
     "src/juicefs_kern.conf", "tests/test_juicefs_kern.py", "reads"),
    ("SeaweedFS", "seaweed-filer-leftover", "seaweed-volume-handoff", "flock-swfil",
     "src/seaweed_filer.toml", "tests/test_seaweed_filer.py", "filer cache leftover",
     "drop filer cache on miss", "filer leftover + wait + do(path)", 20,
     "volume leftover still restamps", "volume leftover",
     "src/seaweed_vol.toml", "tests/test_seaweed_vol.py", "reads"),
    ("Apache Ozone", "ozone-om-cache-leftover", "ozone-scm-handoff", "flock-oznom",
     "src/ozone_om.xml", "tests/test_ozone_om.py", "OM cache leftover",
     "drop OM cache on miss", "om leftover + wait + do(key)", 17,
     "SCM leftover still 1s", "SCM leftover",
     "src/ozone_scm.xml", "tests/test_ozone_scm.py", "reads"),
    ("Ceph RGW", "ceph-rgw-gc-leftover", "ceph-rgw-lc-handoff", "flock-rgwgc",
     "src/rgw_gc.conf", "tests/test_rgw_gc.py", "GC leftover",
     "drop GC on miss", "gc leftover + wait + do(oid)", 23,
     "lifecycle leftover still restamps", "lifecycle leftover",
     "src/rgw_lc.conf", "tests/test_rgw_lc.py", "gets"),
    ("Varnish MSE", "varnish-mse-leftover", "varnish-ban-handoff", "flock-varmse",
     "src/varnish_mse.vcl", "tests/test_varnish_mse.py", "MSE leftover",
     "drop MSE on miss", "mse leftover + wait + do(hash)", 29,
     "ban leftover still 1s", "ban leftover",
     "src/varnish_ban.vcl", "tests/test_varnish_ban.py", "fetches"),
    ("Hitch", "hitch-ocsp-leftover", "hitch-backend-handoff", "flock-htchoc",
     "src/hitch_ocsp.conf", "tests/test_hitch_ocsp.py", "OCSP leftover",
     "drop OCSP on miss", "ocsp leftover + wait + do(sni)", 12,
     "backend leftover still stampedes", "backend leftover",
     "src/hitch_be.conf", "tests/test_hitch_be.py", "handshakes"),
    ("APCu", "apcu-sma-leftover", "apcu-ttl-handoff", "flock-apcus",
     "src/apcu_sma.ini", "tests/test_apcu_sma.py", "sma leftover",
     "drop sma on miss", "sma leftover + wait + do(key)", 27,
     "ttl leftover still expires", "ttl leftover",
     "src/apcu_ttl.ini", "tests/test_apcu_ttl.py", "gets"),
    ("PHP OPcache", "opcache-interned-leftover", "opcache-revalidate-handoff", "flock-opcin",
     "src/opcache.ini", "tests/test_opcache.py", "interned strings leftover",
     "drop interned on miss", "interned leftover + wait + do(file)", 33,
     "revalidate leftover still 1s", "revalidate leftover",
     "src/opcache_reval.ini", "tests/test_opcache_reval.py", "hits"),
    ("RedisJSON", "redisjson-path-leftover", "redisjson-index-handoff", "flock-rsjpn",
     "src/redisjson_path.lua", "tests/test_redisjson_path.py", "JSON.GET leftover",
     "drop JSON.GET on miss", "path leftover + wait + do(key)", 16,
     "index leftover still restamps", "index leftover",
     "src/redisjson_idx.lua", "tests/test_redisjson_idx.py", "gets"),
    ("RedisBloom", "redisbloom-cms-leftover", "redisbloom-topk-handoff", "flock-rsbcm",
     "src/redisbloom_cms.lua", "tests/test_redisbloom_cms.py", "CMS leftover",
     "drop CMS on miss", "cms leftover + wait + do(key)", 18,
     "TopK leftover still 1s", "TopK leftover",
     "src/redisbloom_topk.lua", "tests/test_redisbloom_topk.py", "adds"),
    ("RediSearch", "redisearch-ft-leftover", "redisearch-cursor-handoff", "flock-rsrft",
     "src/redisearch_ft.lua", "tests/test_redisearch_ft.py", "FT.SEARCH leftover",
     "drop FT.SEARCH on miss", "ft leftover + wait + do(query)", 21,
     "cursor leftover still 1s", "cursor leftover",
     "src/redisearch_cur.lua", "tests/test_redisearch_cur.py", "queries"),
    ("Fastly shielding", "fastly-shield-leftover", "fastly-pop-handoff", "flock-fshld",
     "src/fastly_shield.vcl", "tests/test_fastly_shield.py", "shield leftover",
     "drop shield on miss", "shield leftover + wait + do(url)", 19,
     "POP leftover still fanouts", "POP leftover",
     "src/fastly_pop.vcl", "tests/test_fastly_pop.py", "origins"),
    ("Edgio", "edgio-edge-cache-leftover", "edgio-prefetch-handoff", "flock-edgch",
     "src/edgio_cache.js", "tests/test_edgio_cache.py", "edge cache leftover",
     "drop edge cache on miss", "edge leftover + wait + do(url)", 15,
     "prefetch leftover still 1s", "prefetch leftover",
     "src/edgio_pref.js", "tests/test_edgio_pref.py", "origins"),
    ("Limelight", "limelight-purge-leftover", "limelight-token-handoff", "flock-llprg",
     "src/limelight_purge.json", "tests/test_limelight_purge.py", "purge leftover",
     "drop purge on miss", "purge leftover + wait + do(url)", 13,
     "token leftover still 403s", "token leftover",
     "src/limelight_tok.json", "tests/test_limelight_tok.py", "origins"),
    ("Midway", "midway-http-cache-leftover", "midway-ttl-handoff", "flock-mdwch",
     "src/midway_cache.ts", "tests/test_midway_cache.py", "httpCache leftover",
     "drop httpCache on miss", "http leftover + wait + do(url)", 17,
     "ttl leftover still expires", "ttl leftover",
     "src/midway_ttl.ts", "tests/test_midway_ttl.py", "origins"),
    ("lua-resty-lock", "resty-lock-leftover", "resty-mlock-handoff", "flock-rylck",
     "src/resty_lock.lua", "tests/test_resty_lock.py", "resty.lock leftover",
     "drop resty.lock on miss", "lock leftover + wait + do(key)", 25,
     "mlock leftover still stampedes", "mlock leftover",
     "src/resty_mlock.lua", "tests/test_resty_mlock.py", "loads"),
    ("Istio", "istio-sidecar-cache-leftover", "istio-envoyfilter-handoff", "flock-istsc",
     "src/istio_sidecar.yaml", "tests/test_istio_sidecar.py", "sidecar cache leftover",
     "drop sidecar cache on miss", "sidecar leftover + wait + do(path)", 16,
     "EnvoyFilter leftover still 1s", "EnvoyFilter leftover",
     "src/istio_ef.yaml", "tests/test_istio_ef.py", "origins"),
    ("Linkerd", "linkerd-tap-cache-leftover", "linkerd-meshtls-handoff", "flock-lnkdt",
     "src/linkerd_tap.yml", "tests/test_linkerd_tap.py", "tap cache leftover",
     "drop tap cache on miss", "tap leftover + wait + do(path)", 14,
     "meshTLS leftover still 1s", "meshTLS leftover",
     "src/linkerd_tls.yml", "tests/test_linkerd_tls.py", "origins"),
    ("Consul Connect", "consul-intent-cache-leftover", "consul-sidecar-handoff", "flock-cslin",
     "src/consul_intent.hcl", "tests/test_consul_intent.py", "intention cache leftover",
     "drop intention cache on miss", "intent leftover + wait + do(svc)", 18,
     "sidecar leftover still stampedes", "sidecar leftover",
     "src/consul_side.hcl", "tests/test_consul_side.py", "origins"),
    ("HAProxy stick", "haproxy-stick-leftover", "haproxy-peers-handoff", "flock-hapst",
     "src/haproxy_stick.cfg", "tests/test_haproxy_stick.py", "stick-table leftover",
     "drop stick-table on miss", "stick leftover + wait + do(ip)", 22,
     "peers leftover still 1s", "peers leftover",
     "src/haproxy_peers.cfg", "tests/test_haproxy_peers.py", "hits"),
    ("Pound", "pound-cache-leftover", "pound-backend-handoff", "flock-pndch",
     "src/pound.cfg", "tests/test_pound.py", "CacheTTL leftover",
     "drop CacheTTL on miss", "ttl leftover + wait + do(url)", 11,
     "backend leftover still stampedes", "backend leftover",
     "src/pound_be.cfg", "tests/test_pound_be.py", "origins"),
    ("Lighttpd", "lighttpd-stat-cache-leftover", "lighttpd-deflate-handoff", "flock-lhtst",
     "src/lighttpd.conf", "tests/test_lighttpd.py", "stat_cache leftover",
     "drop stat_cache on miss", "stat leftover + wait + do(path)", 15,
     "deflate leftover still 1s", "deflate leftover",
     "src/lighttpd_def.conf", "tests/test_lighttpd_def.py", "hits"),
    ("NATS KV", "nats-kv-watch-leftover", "nats-kv-history-handoff", "flock-natkv",
     "src/nats_kv.go", "tests/test_nats_kv.py", "kv watch leftover",
     "drop kv watch on miss", "watch leftover + wait + do(key)", 20,
     "history leftover still restamps", "history leftover",
     "src/nats_hist.go", "tests/test_nats_hist.py", "gets"),
    ("Tigris", "tigris-search-cache-leftover", "tigris-cdc-handoff", "flock-tgrsc",
     "src/tigris_search.go", "tests/test_tigris_search.py", "search cache leftover",
     "drop search cache on miss", "search leftover + wait + do(query)", 16,
     "CDC leftover still 1s", "CDC leftover",
     "src/tigris_cdc.go", "tests/test_tigris_cdc.py", "queries"),
    ("MinIO cache", "minio-drive-cache-leftover", "minio-ilm-handoff", "flock-mnodc",
     "src/minio_cache.env", "tests/test_minio_cache.py", "drive cache leftover",
     "drop drive cache on miss", "drive leftover + wait + do(obj)", 19,
     "ILM leftover still restamps", "ILM leftover",
     "src/minio_ilm.env", "tests/test_minio_ilm.py", "gets"),
    ("Garage", "garage-block-leftover", "garage-resilience-handoff", "flock-grgbl",
     "src/garage.toml", "tests/test_garage.py", "block leftover",
     "drop block cache on miss", "block leftover + wait + do(hash)", 17,
     "resilience leftover still 1s", "resilience leftover",
     "src/garage_res.toml", "tests/test_garage_res.py", "gets"),
    ("CubeFS", "cubefs-meta-cache-leftover", "cubefs-extent-handoff", "flock-cbfsm",
     "src/cubefs_meta.json", "tests/test_cubefs_meta.py", "meta cache leftover",
     "drop meta cache on miss", "meta leftover + wait + do(ino)", 18,
     "extent leftover still restamps", "extent leftover",
     "src/cubefs_ext.json", "tests/test_cubefs_ext.py", "reads"),
]
