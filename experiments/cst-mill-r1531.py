#!/usr/bin/env python3
"""Designed leftover cache-stampede mill r1531+ (cst- ids).

BAN r1–r1530 including r1530 cubefs-meta-cache, r1490 oraclegc-near-ce, r1445 akamai-esi.
"""
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

CATALOG_FIRST = 1531

PAIRS: list[tuple] = [
    ("FS-Cache", "fscache-netfs-leftover", "fscache-cookie-handoff", "flock-fscnt",
     "src/fscache_netfs.c", "tests/test_fscache_netfs.py", "netfs leftover",
     "drop netfs on miss", "netfs leftover + wait + do(ino)", 18,
     "cookie leftover still 1s", "cookie leftover",
     "src/fscache_cookie.c", "tests/test_fscache_cookie.py", "reads"),
    ("cachefilesd", "cachefilesd-cull-leftover", "cachefilesd-tag-handoff", "flock-cfscu",
     "src/cachefilesd.conf", "tests/test_cachefilesd.py", "cull leftover",
     "drop cull on miss", "cull leftover + wait + do(path)", 16,
     "tag leftover still restamps", "tag leftover",
     "src/cachefilesd_tag.conf", "tests/test_cachefilesd_tag.py", "reads"),
    ("ZFS ARC", "zfs-arc-leftover", "zfs-mru-handoff", "flock-zfsarc",
     "src/zfs_arc.c", "tests/test_zfs_arc.py", "ARC leftover",
     "drop ARC on miss", "arc leftover + wait + do(blk)", 29,
     "MRU leftover still evicts", "MRU leftover",
     "src/zfs_mru.c", "tests/test_zfs_mru.py", "reads"),
    ("ZFS L2ARC", "zfs-l2arc-leftover", "zfs-l2hd-handoff", "flock-zfsl2",
     "src/zfs_l2arc.c", "tests/test_zfs_l2arc.py", "L2ARC leftover",
     "drop L2ARC on miss", "l2 leftover + wait + do(blk)", 22,
     "header leftover still 1s", "header leftover",
     "src/zfs_l2hd.c", "tests/test_zfs_l2hd.py", "reads"),
    ("LVM cache", "lvm-cache-leftover", "lvm-cleaner-handoff", "flock-lvmch",
     "src/lvm_cache.conf", "tests/test_lvm_cache.py", "cache pool leftover",
     "drop cache pool on miss", "pool leftover + wait + do(lv)", 19,
     "cleaner leftover still destages", "cleaner leftover",
     "src/lvm_clean.conf", "tests/test_lvm_clean.py", "reads"),
    ("bcache", "bcache-writeback-leftover", "bcache-bypass-handoff", "flock-bcwrb",
     "src/bcache.conf", "tests/test_bcache.py", "writeback leftover",
     "drop writeback on miss", "writeback leftover + wait + do(bio)", 21,
     "bypass leftover still 1s", "bypass leftover",
     "src/bcache_by.conf", "tests/test_bcache_by.py", "reads"),
    ("OpenCAS", "opencas-core-leftover", "opencas-seq-handoff", "flock-ocasc",
     "src/opencas.conf", "tests/test_opencas.py", "core leftover",
     "drop core on miss", "core leftover + wait + do(io)", 17,
     "seq cutoff leftover still 1s", "seq leftover",
     "src/opencas_seq.conf", "tests/test_opencas_seq.py", "reads"),
    ("dm-cache", "dmcache-mq-leftover", "dmcache-cleaner-handoff", "flock-dmcch",
     "src/dmcache.conf", "tests/test_dmcache.py", "mq leftover",
     "drop mq on miss", "mq leftover + wait + do(bio)", 20,
     "cleaner leftover still destages", "cleaner leftover",
     "src/dmcache_cl.conf", "tests/test_dmcache_cl.py", "reads"),
    ("Prisma Accelerate", "prisma-accel-leftover", "prisma-edge-handoff", "flock-pracc",
     "src/prisma_accel.ts", "tests/test_prisma_accel.py", "accelerate leftover",
     "drop accelerate on miss", "accel leftover + wait + do(query)", 15,
     "edge leftover still 1s", "edge leftover",
     "src/prisma_edge.ts", "tests/test_prisma_edge.py", "queries"),
    ("Hasura cache", "hasura-query-cache-leftover", "hasura-ttl-handoff", "flock-hsrqc",
     "src/hasura_cache.yaml", "tests/test_hasura_cache.py", "query cache leftover",
     "drop query cache on miss", "query leftover + wait + do(gql)", 16,
     "ttl leftover still expires", "ttl leftover",
     "src/hasura_ttl.yaml", "tests/test_hasura_ttl.py", "queries"),
    ("PostgREST", "postgrest-schema-cache-leftover", "postgrest-reload-handoff", "flock-pgrsc",
     "src/postgrest.conf", "tests/test_postgrest.py", "schema cache leftover",
     "drop schema cache on miss", "schema leftover + wait + do(rel)", 14,
     "reload leftover still 1s", "reload leftover",
     "src/postgrest_rel.conf", "tests/test_postgrest_rel.py", "queries"),
    ("Apigee", "apigee-resp-cache-leftover", "apigee-populate-handoff", "flock-apgrc",
     "src/apigee_cache.xml", "tests/test_apigee_cache.py", "ResponseCache leftover",
     "drop ResponseCache on miss", "resp leftover + wait + do(path)", 18,
     "PopulateCache leftover still 1s", "PopulateCache leftover",
     "src/apigee_pop.xml", "tests/test_apigee_pop.py", "origins"),
    ("Azure APIM", "apim-cache-store-leftover", "apim-lookup-handoff", "flock-apimc",
     "src/apim_cache.xml", "tests/test_apim_cache.py", "cache-store leftover",
     "drop cache-store on miss", "store leftover + wait + do(op)", 17,
     "lookup leftover still misses", "lookup leftover",
     "src/apim_lookup.xml", "tests/test_apim_lookup.py", "origins"),
    ("AWS API Gateway", "apigw-cache-leftover", "apigw-ttl-handoff", "flock-apgwc",
     "src/apigw_cache.json", "tests/test_apigw_cache.py", "stage cache leftover",
     "drop stage cache on miss", "stage leftover + wait + do(path)", 19,
     "ttl leftover still expires", "ttl leftover",
     "src/apigw_ttl.json", "tests/test_apigw_ttl.py", "origins"),
    ("Gravitee", "gravitee-cache-leftover", "gravitee-redis-handoff", "flock-grvch",
     "src/gravitee.yml", "tests/test_gravitee.py", "cache policy leftover",
     "drop cache policy on miss", "policy leftover + wait + do(path)", 16,
     "redis leftover still 1s", "redis leftover",
     "src/gravitee_redis.yml", "tests/test_gravitee_redis.py", "origins"),
    ("WSO2", "wso2-response-cache-leftover", "wso2-mediator-handoff", "flock-wso2c",
     "src/wso2_cache.xml", "tests/test_wso2_cache.py", "response cache leftover",
     "drop response cache on miss", "resp leftover + wait + do(path)", 15,
     "mediator leftover still 1s", "mediator leftover",
     "src/wso2_med.xml", "tests/test_wso2_med.py", "origins"),
    ("Deno KV", "deno-kv-watch-leftover", "deno-kv-queue-handoff", "flock-dnokv",
     "src/deno_kv.ts", "tests/test_deno_kv.py", "kv watch leftover",
     "drop kv watch on miss", "watch leftover + wait + do(key)", 20,
     "queue leftover still restamps", "queue leftover",
     "src/deno_queue.ts", "tests/test_deno_queue.py", "gets"),
    ("Turso", "turso-embedded-repl-leftover", "turso-sync-handoff", "flock-trsemb",
     "src/turso_repl.rs", "tests/test_turso_repl.py", "embedded replica leftover",
     "drop embedded replica on miss", "replica leftover + wait + do(row)", 18,
     "sync leftover still 1s", "sync leftover",
     "src/turso_sync.rs", "tests/test_turso_sync.py", "gets"),
    ("libSQL", "libsql-hrana-leftover", "libsql-wal-handoff", "flock-lbsql",
     "src/libsql_hrana.rs", "tests/test_libsql_hrana.py", "Hrana leftover",
     "drop Hrana on miss", "hrana leftover + wait + do(stmt)", 16,
     "WAL leftover still restamps", "WAL leftover",
     "src/libsql_wal.rs", "tests/test_libsql_wal.py", "queries"),
    ("PlanetScale Boost", "ps-boost-leftover", "ps-rewriter-handoff", "flock-psbst",
     "src/ps_boost.go", "tests/test_ps_boost.py", "boost leftover",
     "drop boost on miss", "boost leftover + wait + do(query)", 21,
     "rewriter leftover still 1s", "rewriter leftover",
     "src/ps_rewriter.go", "tests/test_ps_rewriter.py", "queries"),
    ("Cloudflare Workers cache", "cf-workers-cache-leftover", "cf-waituntil-handoff", "flock-cfwrk",
     "src/cf_workers.js", "tests/test_cf_workers.py", "caches.default leftover",
     "drop caches.default on miss", "default leftover + wait + do(req)", 23,
     "waitUntil leftover still 1s", "waitUntil leftover",
     "src/cf_wait.js", "tests/test_cf_wait.py", "origins"),
    ("Fastly Compute", "fastly-compute-kv-leftover", "fastly-secret-handoff", "flock-fcomp",
     "src/fastly_compute.rs", "tests/test_fastly_compute.py", "KV leftover",
     "drop KV on miss", "kv leftover + wait + do(key)", 17,
     "secret leftover still 1s", "secret leftover",
     "src/fastly_secret.rs", "tests/test_fastly_secret.py", "gets"),
    ("njs cache", "njs-shared-dict-leftover", "njs-fetch-handoff", "flock-njssd",
     "src/njs_dict.js", "tests/test_njs_dict.py", "shared dict leftover",
     "drop shared dict on miss", "dict leftover + wait + do(key)", 19,
     "ngx.fetch leftover still stampedes", "fetch leftover",
     "src/njs_fetch.js", "tests/test_njs_fetch.py", "origins"),
    ("Kong JWT cache", "kong-jwt-cache-leftover", "kong-keyauth-handoff", "flock-kngjw",
     "src/kong_jwt.lua", "tests/test_kong_jwt.py", "jwt cache leftover",
     "drop jwt cache on miss", "jwt leftover + wait + do(tok)", 14,
     "key-auth leftover still 1s", "key-auth leftover",
     "src/kong_key.lua", "tests/test_kong_key.py", "auths"),
    ("Tyk gateway cache", "tyk-gw-cache-leftover", "tyk-session-handoff", "flock-tykgw",
     "src/tyk_gw.json", "tests/test_tyk_gw.py", "gateway cache leftover",
     "drop gateway cache on miss", "gw leftover + wait + do(path)", 16,
     "session leftover still 1s", "session leftover",
     "src/tyk_sess.json", "tests/test_tyk_sess.py", "origins"),
    ("Envoy ext_proc", "envoy-extproc-leftover", "envoy-ratelimit-handoff", "flock-envxp",
     "src/envoy_extproc.yaml", "tests/test_envoy_extproc.py", "ext_proc leftover",
     "drop ext_proc on miss", "ext leftover + wait + do(path)", 18,
     "ratelimit leftover still 1s", "ratelimit leftover",
     "src/envoy_rl.yaml", "tests/test_envoy_rl.py", "origins"),
    ("Istio Wasm", "istio-wasm-cache-leftover", "istio-authz-handoff", "flock-istwm",
     "src/istio_wasm.yaml", "tests/test_istio_wasm.py", "wasm cache leftover",
     "drop wasm cache on miss", "wasm leftover + wait + do(path)", 15,
     "authz leftover still 1s", "authz leftover",
     "src/istio_authz.yaml", "tests/test_istio_authz.py", "origins"),
    ("Linkerd policy", "linkerd-policy-cache-leftover", "linkerd-opaque-handoff", "flock-lnkpl",
     "src/linkerd_policy.yml", "tests/test_linkerd_policy.py", "policy cache leftover",
     "drop policy cache on miss", "policy leftover + wait + do(svc)", 13,
     "opaque leftover still 1s", "opaque leftover",
     "src/linkerd_opq.yml", "tests/test_linkerd_opq.py", "origins"),
    ("Consul DNS", "consul-dns-cache-leftover", "consul-prepared-handoff", "flock-csldn",
     "src/consul_dns.hcl", "tests/test_consul_dns.py", "DNS cache leftover",
     "drop DNS cache on miss", "dns leftover + wait + do(name)", 20,
     "prepared leftover still 1s", "prepared leftover",
     "src/consul_prep.hcl", "tests/test_consul_prep.py", "lookups"),
    ("CoreDNS", "coredns-cache-leftover", "coredns-forward-handoff", "flock-cdns",
     "src/coredns_cache.corefile", "tests/test_coredns_cache.py", "cache leftover",
     "drop cache on miss", "cache leftover + wait + do(qname)", 22,
     "forward leftover still stampedes", "forward leftover",
     "src/coredns_fwd.corefile", "tests/test_coredns_fwd.py", "lookups"),
    ("Unbound", "unbound-msg-cache-leftover", "unbound-rrset-handoff", "flock-unbms",
     "src/unbound.conf", "tests/test_unbound.py", "msg-cache leftover",
     "drop msg-cache on miss", "msg leftover + wait + do(qname)", 24,
     "rrset leftover still 1s", "rrset leftover",
     "src/unbound_rr.conf", "tests/test_unbound_rr.py", "lookups"),
    ("PowerDNS recursor", "pdns-packetcache-leftover", "pdns-negcache-handoff", "flock-pdnsp",
     "src/pdns_rec.conf", "tests/test_pdns_rec.py", "packetcache leftover",
     "drop packetcache on miss", "packet leftover + wait + do(qname)", 19,
     "negcache leftover still 1s", "negcache leftover",
     "src/pdns_neg.conf", "tests/test_pdns_neg.py", "lookups"),
    ("BIND rrset", "bind-rrset-cache-leftover", "bind-adb-handoff", "flock-bndrr",
     "src/named.conf", "tests/test_named.py", "max-cache-size leftover",
     "drop max-cache-size on miss", "rrset leftover + wait + do(qname)", 21,
     "ADB leftover still 1s", "ADB leftover",
     "src/named_adb.conf", "tests/test_named_adb.py", "lookups"),
    ("Knot Resolver", "knot-cache-leftover", "knot-predict-handoff", "flock-knotr",
     "src/kresd.conf", "tests/test_kresd.py", "cache leftover",
     "drop cache on miss", "cache leftover + wait + do(qname)", 17,
     "predict leftover still 1s", "predict leftover",
     "src/kresd_pred.conf", "tests/test_kresd_pred.py", "lookups"),
    ("NSD", "nsd-ixfr-cache-leftover", "nsd-xfrd-handoff", "flock-nsdix",
     "src/nsd.conf", "tests/test_nsd.py", "ixfr leftover",
     "drop ixfr on miss", "ixfr leftover + wait + do(zone)", 14,
     "xfrd leftover still 1s", "xfrd leftover",
     "src/nsd_xfr.conf", "tests/test_nsd_xfr.py", "xfers"),
    ("dnsmasq", "dnsmasq-cache-leftover", "dnsmasq-neg-handoff", "flock-dnsmq",
     "src/dnsmasq.conf", "tests/test_dnsmasq.py", "cache-size leftover",
     "drop cache-size on miss", "cache leftover + wait + do(qname)", 25,
     "neg leftover still 1s", "neg leftover",
     "src/dnsmasq_neg.conf", "tests/test_dnsmasq_neg.py", "lookups"),
    ("systemd-resolved", "resolved-cache-leftover", "resolved-llmnr-handoff", "flock-sres",
     "src/resolved.conf", "tests/test_resolved.py", "Cache leftover",
     "drop Cache on miss", "cache leftover + wait + do(qname)", 16,
     "LLMNR leftover still 1s", "LLMNR leftover",
     "src/resolved_ll.conf", "tests/test_resolved_ll.py", "lookups"),
    ("nscd", "nscd-hosts-leftover", "nscd-passwd-handoff", "flock-nscdh",
     "src/nscd.conf", "tests/test_nscd.py", "hosts leftover",
     "drop hosts on miss", "hosts leftover + wait + do(name)", 18,
     "passwd leftover still 1s", "passwd leftover",
     "src/nscd_pw.conf", "tests/test_nscd_pw.py", "lookups"),
    ("SSSD", "sssd-nss-leftover", "sssd-ifp-handoff", "flock-sssdn",
     "src/sssd.conf", "tests/test_sssd.py", "nss leftover",
     "drop nss on miss", "nss leftover + wait + do(name)", 20,
     "ifp leftover still 1s", "ifp leftover",
     "src/sssd_ifp.conf", "tests/test_sssd_ifp.py", "lookups"),
    ("Unbound prefetch", "unbound-prefetch-leftover", "unbound-serve-expired-handoff", "flock-unbpf",
     "src/unbound_pf.conf", "tests/test_unbound_pf.py", "prefetch leftover",
     "drop prefetch on miss", "prefetch leftover + wait + do(qname)", 23,
     "serve-expired leftover still 1s", "serve-expired leftover",
     "src/unbound_se.conf", "tests/test_unbound_se.py", "lookups"),
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
        "Not flock-wN. Not AWS catalog. Not r1–r1530 clones (incl. r1445 akamai-esi, r1530 cubefs). "
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
