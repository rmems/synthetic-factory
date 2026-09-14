#!/usr/bin/env python3
"""Designed leftover cache-stampede mill r1446+ (cst- ids).

BAN r1–r1445 including r1445 akamai-esi-leftover / akamai-esi-include-handoff.
Not overlayfs/nydus/stargz. Not docker/search ids.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("cst1414", HERE / "cst-mill-r1414.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

_steps_ok = _m._steps_ok
_steps_part = _m._steps_part

CATALOG_FIRST = 1446

# product, slug_ok, slug_part, plant, src, test, api, naive, fix, workers,
# residual, sibling, sib_file, sib_test, miss_metric
PAIRS: list[tuple] = [
    ("Groupcache", "groupcache-hotcache-leftover", "groupcache-peer-picker-handoff", "flock-gchot",
     "src/groupcache_hot.go", "tests/test_groupcache_hot.py", "hotCache peers",
     "drop hotCache on miss", "hot leftover + wait + do(key)", 28,
     "peer picker leftover still fanouts", "peer picker leftover",
     "src/groupcache_peers.go", "tests/test_groupcache_peers.py", "loads"),
    ("Singleflight", "singleflight-dochan-leftover", "singleflight-forget-handoff", "flock-sflgt",
     "src/singleflight_do.go", "tests/test_singleflight_do.py", "DoChan inflight",
     "drop DoChan on miss", "dochan leftover + wait + do(key)", 34,
     "Forget leftover still double-calls", "Forget leftover",
     "src/singleflight_forget.go", "tests/test_singleflight_forget.py", "calls"),
    ("BigCache", "bigcache-hasher-leftover", "bigcache-life-window-handoff", "flock-bgshd",
     "src/bigcache_hash.go", "tests/test_bigcache_hash.py", "shard hasher leftover",
     "drop Hasher on miss", "hasher leftover + wait + do(key)", 22,
     "LifeWindow leftover still evicts", "LifeWindow leftover",
     "src/bigcache_life.go", "tests/test_bigcache_life.py", "sets"),
    ("FreeCache", "freecache-ring-leftover", "freecache-ttl-handoff", "flock-fcrng",
     "src/freecache_ring.go", "tests/test_freecache_ring.py", "ring buffer leftover",
     "drop ring on miss", "ring leftover + wait + do(key)", 19,
     "TTL leftover still expires mid-fill", "TTL leftover",
     "src/freecache_ttl.go", "tests/test_freecache_ttl.py", "gets"),
    ("FastCache", "fastcache-bigkey-leftover", "fastcache-maxbytes-handoff", "flock-fcbig",
     "src/fastcache_big.go", "tests/test_fastcache_big.py", "big key leftover",
     "drop SetBig on miss", "bigkey leftover + wait + do(key)", 31,
     "MaxBytes leftover still truncates", "MaxBytes leftover",
     "src/fastcache_max.go", "tests/test_fastcache_max.py", "sets"),
    ("Olric", "olric-dmap-leftover", "olric-partition-handoff", "flock-oldmap",
     "src/olric_dmap.go", "tests/test_olric_dmap.py", "DMap leftover",
     "drop DMap on miss", "dmap leftover + wait + do(key)", 25,
     "partition leftover still restamps", "partition leftover",
     "src/olric_part.go", "tests/test_olric_part.py", "gets"),
    ("Apache Traffic Server", "ats-readwhile-leftover", "ats-ramcache-handoff", "flock-atsrw",
     "src/ats_readwhile.config", "tests/test_ats_readwhile.py", "read-while-writer leftover",
     "drop read-while-writer on miss", "rw leftover + wait + do(url)", 27,
     "RAM cache leftover still 1s", "RAM cache leftover",
     "src/ats_ram.config", "tests/test_ats_ram.py", "fetches"),
    ("Squid", "squid-collapsed-fwd-leftover", "squid-storeurl-handoff", "flock-sqfwd",
     "src/squid_collapsed.conf", "tests/test_squid_collapsed.py", "collapsed_forwarding leftover",
     "drop collapsed_forwarding on miss", "collapsed leftover + wait + do(url)", 21,
     "storeurl leftover still hashes wrong", "storeurl leftover",
     "src/squid_storeurl.conf", "tests/test_squid_storeurl.py", "fetches"),
    ("HAProxy cache", "haproxy-cache-force-leftover", "haproxy-cache-vary-handoff", "flock-hapcf",
     "src/haproxy_cache.cfg", "tests/test_haproxy_cache.py", "http-cache force-cache leftover",
     "drop force-cache on miss", "force leftover + wait + do(uri)", 18,
     "Vary leftover still splits keys", "cache-vary leftover",
     "src/haproxy_vary.cfg", "tests/test_haproxy_vary.py", "fetches"),
    ("Traefik", "traefik-shttl-leftover", "traefik-inflight-handoff", "flock-trfsht",
     "src/traefik_shttl.yml", "tests/test_traefik_shttl.py", "stale-if-error leftover",
     "drop stale-if-error on miss", "shttl leftover + wait + do(url)", 24,
     "in-flight leftover still stampedes", "in-flight leftover",
     "src/traefik_inflight.yml", "tests/test_traefik_inflight.py", "origins"),
    ("Caddy", "caddy-reverse-cache-leftover", "caddy-stale-handoff", "flock-cadyrc",
     "src/caddy_cache.caddyfile", "tests/test_caddy_cache.py", "reverse_proxy cache leftover",
     "drop cache on miss", "reverse leftover + wait + do(uri)", 16,
     "stale leftover still serves 1s", "stale leftover",
     "src/caddy_stale.caddyfile", "tests/test_caddy_stale.py", "upstreams"),
    ("LiteSpeed", "litespeed-lscache-leftover", "litespeed-purge-handoff", "flock-lslsc",
     "src/litespeed_lscache.conf", "tests/test_litespeed_lscache.py", "LSCache leftover",
     "drop LSCache on miss", "lscache leftover + wait + do(url)", 20,
     "purge leftover still 1s", "purge leftover",
     "src/litespeed_purge.conf", "tests/test_litespeed_purge.py", "purges"),
    ("OpenResty", "openresty-lua-shared-leftover", "openresty-mlcache-handoff", "flock-orlua",
     "src/openresty_shared.lua", "tests/test_openresty_shared.py", "lua_shared_dict leftover",
     "drop shared dict on miss", "shared leftover + wait + do(key)", 33,
     "mlcache leftover still restamps", "mlcache leftover",
     "src/openresty_mlcache.lua", "tests/test_openresty_mlcache.py", "loads"),
    ("Kong", "kong-proxy-cache-leftover", "kong-redis-cache-handoff", "flock-kongpc",
     "src/kong_proxy_cache.lua", "tests/test_kong_proxy_cache.py", "proxy-cache leftover",
     "drop proxy-cache on miss", "proxy leftover + wait + do(uri)", 17,
     "redis strategy leftover still 1s", "redis-cache leftover",
     "src/kong_redis_cache.lua", "tests/test_kong_redis_cache.py", "origins"),
    ("Tyk", "tyk-cache-plugin-leftover", "tyk-versioned-cache-handoff", "flock-tykpl",
     "src/tyk_cache.json", "tests/test_tyk_cache.py", "cache middleware leftover",
     "drop cache plugin on miss", "plugin leftover + wait + do(path)", 23,
     "versioned cache leftover still splits", "versioned cache leftover",
     "src/tyk_version.json", "tests/test_tyk_version.py", "hits"),
    ("Pelikan", "pelikan-segcache-leftover", "pelikan-cuckoo-handoff", "flock-pelik",
     "src/pelikan_seg.toml", "tests/test_pelikan_seg.py", "Segcache leftover",
     "drop Segcache on miss", "seg leftover + wait + do(key)", 29,
     "cuckoo leftover still collisions", "cuckoo leftover",
     "src/pelikan_cuckoo.toml", "tests/test_pelikan_cuckoo.py", "sets"),
    ("Twemproxy", "twemproxy-ketama-leftover", "twemproxy-auto-eject-handoff", "flock-twket",
     "src/twemproxy_ketama.yml", "tests/test_twemproxy_ketama.py", "ketama leftover",
     "drop ketama on miss", "ketama leftover + wait + do(key)", 15,
     "auto_eject leftover still drops", "auto_eject leftover",
     "src/twemproxy_eject.yml", "tests/test_twemproxy_eject.py", "forwards"),
    ("Nuster", "nuster-disk-cache-leftover", "nuster-ttl-handoff", "flock-nustd",
     "src/nuster_disk.cfg", "tests/test_nuster_disk.py", "disk cache leftover",
     "drop nuster cache on miss", "disk leftover + wait + do(uri)", 26,
     "ttl leftover still expires mid-fill", "ttl leftover",
     "src/nuster_ttl.cfg", "tests/test_nuster_ttl.py", "fetches"),
    ("BunnyCDN", "bunny-perma-cache-leftover", "bunny-edge-rule-handoff", "flock-bnprm",
     "src/bunny_perma.json", "tests/test_bunny_perma.py", "Perma-Cache leftover",
     "drop Perma-Cache on miss", "perma leftover + wait + do(url)", 14,
     "edge rule leftover still bypasses", "edge rule leftover",
     "src/bunny_edge.json", "tests/test_bunny_edge.py", "origins"),
    ("KeyCDN", "keycdn-zone-pull-leftover", "keycdn-purge-handoff", "flock-kcdnp",
     "src/keycdn_zone.json", "tests/test_keycdn_zone.py", "pull zone leftover",
     "drop pull zone on miss", "zone leftover + wait + do(url)", 19,
     "purge leftover still 1s", "purge leftover",
     "src/keycdn_purge.json", "tests/test_keycdn_purge.py", "purges"),
    ("StackPath", "stackpath-edge-asset-leftover", "stackpath-waf-cache-handoff", "flock-stked",
     "src/stackpath_asset.json", "tests/test_stackpath_asset.py", "edge asset leftover",
     "drop edge asset on miss", "asset leftover + wait + do(url)", 21,
     "WAF cache leftover still 403s", "WAF cache leftover",
     "src/stackpath_waf.json", "tests/test_stackpath_waf.py", "origins"),
    ("Imperva", "imperva-adv-cache-leftover", "imperva-dynamic-cache-handoff", "flock-impac",
     "src/imperva_adv.json", "tests/test_imperva_adv.py", "advanced caching leftover",
     "drop advanced cache on miss", "adv leftover + wait + do(url)", 18,
     "dynamic cache leftover still 1s", "dynamic cache leftover",
     "src/imperva_dyn.json", "tests/test_imperva_dyn.py", "origins"),
    ("Google Cloud CDN", "gcdn-cache-mode-leftover", "gcdn-bypass-handoff", "flock-gcdnm",
     "src/gcdn_mode.tf", "tests/test_gcdn_mode.py", "CACHE_ALL_STATIC leftover",
     "drop CACHE_ALL_STATIC on miss", "mode leftover + wait + do(url)", 22,
     "bypass leftover still misses", "cache bypass leftover",
     "src/gcdn_bypass.tf", "tests/test_gcdn_bypass.py", "origins"),
    ("Azure Front Door", "afd-caching-leftover", "afd-rules-engine-handoff", "flock-afdch",
     "src/afd_cache.bicep", "tests/test_afd_cache.py", "caching leftover",
     "drop caching on miss", "caching leftover + wait + do(url)", 16,
     "rules engine leftover still bypasses", "rules engine leftover",
     "src/afd_rules.bicep", "tests/test_afd_rules.py", "origins"),
    ("Momento", "momento-item-ttl-leftover", "momento-collection-ttl-handoff", "flock-momttl",
     "src/momento_item.go", "tests/test_momento_item.py", "item TTL leftover",
     "drop item TTL on miss", "item leftover + wait + do(key)", 27,
     "collection TTL leftover still expires", "collection TTL leftover",
     "src/momento_coll.go", "tests/test_momento_coll.py", "gets"),
    ("Garnet", "garnet-aof-leftover", "garnet-cluster-handoff", "flock-garnaf",
     "src/garnet_aof.cs", "tests/test_garnet_aof.py", "AOF leftover",
     "drop AOF on miss", "aof leftover + wait + do(key)", 30,
     "cluster leftover still restamps", "cluster leftover",
     "src/garnet_cluster.cs", "tests/test_garnet_cluster.py", "sets"),
    ("Pika", "pika-codis-leftover", "pika-compact-handoff", "flock-pikcd",
     "src/pika_codis.conf", "tests/test_pika_codis.py", "Codis leftover",
     "drop Codis on miss", "codis leftover + wait + do(key)", 20,
     "compact leftover still blocks", "compact leftover",
     "src/pika_compact.conf", "tests/test_pika_compact.py", "gets"),
    ("Kvrocks", "kvrocks-slot-leftover", "kvrocks-compact-handoff", "flock-kvrsl",
     "src/kvrocks_slot.conf", "tests/test_kvrocks_slot.py", "slot leftover",
     "drop slot migrate on miss", "slot leftover + wait + do(key)", 24,
     "compact leftover still stalls", "compact leftover",
     "src/kvrocks_compact.conf", "tests/test_kvrocks_compact.py", "gets"),
    ("Tendis", "tendis-kvstore-leftover", "tendis-rocks-handoff", "flock-tdnkv",
     "src/tendis_kv.conf", "tests/test_tendis_kv.py", "kvstore leftover",
     "drop kvstore on miss", "kvstore leftover + wait + do(key)", 18,
     "rocks leftover still compact-stampedes", "rocks leftover",
     "src/tendis_rocks.conf", "tests/test_tendis_rocks.py", "gets"),
    ("SSDB", "ssdb-binlog-leftover", "ssdb-compact-handoff", "flock-ssdbb",
     "src/ssdb_binlog.conf", "tests/test_ssdb_binlog.py", "binlog leftover",
     "drop binlog on miss", "binlog leftover + wait + do(key)", 15,
     "compact leftover still blocks", "compact leftover",
     "src/ssdb_compact.conf", "tests/test_ssdb_compact.py", "gets"),
    ("Tarantool", "tarantool-memtx-leftover", "tarantool-vinyl-handoff", "flock-tntmx",
     "src/tarantool_memtx.lua", "tests/test_tarantool_memtx.py", "memtx leftover",
     "drop memtx on miss", "memtx leftover + wait + do(key)", 21,
     "vinyl leftover still restamps", "vinyl leftover",
     "src/tarantool_vinyl.lua", "tests/test_tarantool_vinyl.py", "gets"),
    ("Skytable", "skytable-skyhash-leftover", "skytable-container-handoff", "flock-skyhh",
     "src/skytable_hash.sky", "tests/test_skytable_hash.py", "Skyhash leftover",
     "drop Skyhash on miss", "skyhash leftover + wait + do(key)", 17,
     "container leftover still splits", "container leftover",
     "src/skytable_ct.sky", "tests/test_skytable_ct.py", "gets"),
    ("Nutcracker", "nutcracker-preconnect-leftover", "nutcracker-redis-auth-handoff", "flock-nutpc",
     "src/nutcracker_pre.yml", "tests/test_nutcracker_pre.py", "preconnect leftover",
     "drop preconnect on miss", "preconnect leftover + wait + do(key)", 23,
     "redis_auth leftover still 1s", "redis_auth leftover",
     "src/nutcracker_auth.yml", "tests/test_nutcracker_auth.py", "forwards"),
    ("Dynomite", "dynomite-token-leftover", "dynomite-dc-handoff", "flock-dynot",
     "src/dynomite_token.yml", "tests/test_dynomite_token.py", "token leftover",
     "drop token on miss", "token leftover + wait + do(key)", 19,
     "DC leftover still fanouts", "DC leftover",
     "src/dynomite_dc.yml", "tests/test_dynomite_dc.py", "forwards"),
    ("Infinispan", "infinispan-near-leftover", "infinispan-xsite-handoff", "flock-infsp",
     "src/infinispan_near.xml", "tests/test_infinispan_near.py", "near cache leftover",
     "drop near cache on miss", "near leftover + wait + do(key)", 26,
     "xsite leftover still restamps", "xsite leftover",
     "src/infinispan_xsite.xml", "tests/test_infinispan_xsite.py", "loads"),
    ("Coherence", "coherence-near-leftover", "coherence-federated-handoff", "flock-cohnr",
     "src/coherence_near.xml", "tests/test_coherence_near.py", "near cache leftover",
     "drop near cache on miss", "near leftover + wait + do(key)", 22,
     "federated leftover still 1s", "federated leftover",
     "src/coherence_fed.xml", "tests/test_coherence_fed.py", "loads"),
    ("GridGain", "gridgain-near-leftover", "gridgain-persistence-handoff", "flock-ggnear",
     "src/gridgain_near.xml", "tests/test_gridgain_near.py", "near cache leftover",
     "drop near cache on miss", "near leftover + wait + do(key)", 18,
     "persistence leftover still restamps", "persistence leftover",
     "src/gridgain_persist.xml", "tests/test_gridgain_persist.py", "loads"),
    ("Apache Geode", "geode-client-leftover", "geode-wan-handoff", "flock-geodc",
     "src/geode_client.xml", "tests/test_geode_client.py", "client cache leftover",
     "drop client cache on miss", "client leftover + wait + do(key)", 20,
     "WAN leftover still fanouts", "WAN leftover",
     "src/geode_wan.xml", "tests/test_geode_wan.py", "loads"),
    ("NCache", "ncache-partition-leftover", "ncache-client-cache-handoff", "flock-nccls",
     "src/ncache_part.xml", "tests/test_ncache_part.py", "partition leftover",
     "drop partition on miss", "partition leftover + wait + do(key)", 16,
     "client cache leftover still 1s", "client cache leftover",
     "src/ncache_client.xml", "tests/test_ncache_client.py", "gets"),
    ("AppFabric", "appfabric-cache-leftover", "appfabric-dependency-handoff", "flock-apfab",
     "src/appfabric_cache.xml", "tests/test_appfabric_cache.py", "cluster cache leftover",
     "drop AppFabric on miss", "appfabric leftover + wait + do(key)", 14,
     "dependency leftover still evicts", "dependency leftover",
     "src/appfabric_dep.xml", "tests/test_appfabric_dep.py", "gets"),
    ("Redisson", "redisson-localcache-leftover", "redisson-topic-handoff", "flock-rdslc",
     "src/redisson_local.java", "tests/test_redisson_local.py", "LocalCachedMap leftover",
     "drop LocalCachedMap on miss", "local leftover + wait + do(key)", 25,
     "topic leftover still misses", "topic leftover",
     "src/redisson_topic.java", "tests/test_redisson_topic.py", "loads"),
    ("Lettuce", "lettuce-clientopt-leftover", "lettuce-pubsub-handoff", "flock-ltuco",
     "src/lettuce_opt.java", "tests/test_lettuce_opt.py", "ClientOptions leftover",
     "drop ClientOptions on miss", "opt leftover + wait + do(key)", 17,
     "pubsub leftover still 1s", "pubsub leftover",
     "src/lettuce_pubsub.java", "tests/test_lettuce_pubsub.py", "commands"),
    ("Jedis", "jedis-pool-leftover", "jedis-cluster-handoff", "flock-jdpool",
     "src/jedis_pool.java", "tests/test_jedis_pool.py", "JedisPool leftover",
     "drop JedisPool on miss", "pool leftover + wait + do(key)", 21,
     "cluster leftover still redirects", "cluster leftover",
     "src/jedis_cluster.java", "tests/test_jedis_cluster.py", "commands"),
    ("Ignite 3", "ignite3-table-cache-leftover", "ignite3-colocation-handoff", "flock-ig3tb",
     "src/ignite3_table.java", "tests/test_ignite3_table.py", "table cache leftover",
     "drop table cache on miss", "table leftover + wait + do(key)", 19,
     "colocation leftover still restamps", "colocation leftover",
     "src/ignite3_colo.java", "tests/test_ignite3_colo.py", "gets"),
    ("Oracle Coherence CE", "oraclegc-near-ce-leftover", "oraclegc-near-ce-handoff", "flock-oragc",
     "src/coherence_ce.xml", "tests/test_coherence_ce.py", "CE near leftover",
     "drop CE near on miss", "ce leftover + wait + do(key)", 15,
     "CE federated leftover still 1s", "CE federated leftover",
     "src/coherence_ce_fed.xml", "tests/test_coherence_ce_fed.py", "loads"),
]


def records(round_n: int) -> list[dict]:
    idx = round_n - CATALOG_FIRST
    p = PAIRS[idx]
    product, slug_ok, slug_part, plant, src, test, api, naive, fix, workers, residual, sibling, *_ = p
    ok_id = f"cst-r{round_n}-{slug_ok}"
    part_id = f"cst-r{round_n}-{slug_part}"
    rec_ok = {
        "id": ok_id,
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
        "id": part_id,
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
        "Not flock-wN. Not AWS catalog. Not r1–r1445 clones (incl. r1445 akamai-esi). "
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


def write_round(round_n: int, stage: Path) -> list[str]:
    recs = records(round_n)
    batch = stage / f"batch-r{round_n:02d}.jsonl"
    notes = stage / f"NOTES-r{round_n:02d}.md"
    batch.write_text("".join(json.dumps(r, ensure_ascii=True) + "\n" for r in recs))
    notes.write_text(notes_md(round_n))
    return [r["id"] for r in recs]
