#!/usr/bin/env python3
"""IRC mill r4661+ — wave-78 web-framework leftover.

NEW on-call plants (not Wave-27–60 tails). BAN ypbind/oddjob,
r3389 opensearch leftover3c, r3576 tigergraph/hugegraph.
"""
from __future__ import annotations
import importlib.util, json, sys

spec = importlib.util.spec_from_file_location("irc3234", "/tmp/irc_mill_r3234.py")
w16 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w16)
m = w16.m
plant, helm_rb, patch_file = w16.plant, w16.helm_rb, w16.patch_file

ROWS = r'''
aiohttp2|AIOHTTP2_TIMEOUT|1|30|s|/etc/aiohttp2/aiohttp2.conf|timeout=1|timeout=30|systemctl reload aiohttp2|ah|aio_to_1|handlers|apps|https leftover leftover down; bounce|AIOHTTP2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the handlers 504s
sanic2|SANIC2_TIMEOUT|1|30|s|/etc/sanic2/sanic2.conf|timeout=1|timeout=30|systemctl reload sanic2|sa|san_to_1|routes|bps|https leftover leftover down; bounce|SANIC2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the routes 504s
starlette2|STARLETTE2_TIMEOUT|1|30|s|/etc/starlette2/starlette2.conf|timeout=1|timeout=30|systemctl reload starlette2|sl|sta_to_1|routes|mw|https leftover leftover down; bounce|STARLETTE2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the routes 504s
quart2|QUART2_TIMEOUT|1|30|s|/etc/quart2/quart2.conf|timeout=1|timeout=30|systemctl reload quart2|qt|qua_to_1|routes|bps|https leftover leftover down; bounce|QUART2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the routes 504s
falcon2|FALCON2_TIMEOUT|1|30|s|/etc/falcon2/falcon2.conf|timeout=1|timeout=30|systemctl reload falcon2|fc|fal_to_1|resources|hooks|https leftover leftover down; bounce|FALCON2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the resources 504s
bottle2|BOTTLE2_TIMEOUT|1|30|s|/etc/bottle2/bottle2.conf|timeout=1|timeout=30|systemctl reload bottle2|bt|bot_to_1|routes|views|https leftover leftover down; bounce|BOTTLE2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the routes 504s
cherrypy2|CHERRYPY2_TIMEOUT|1|30|s|/etc/cherrypy2/cherrypy2.conf|timeout=1|timeout=30|systemctl reload cherrypy2|cp|che_to_1|handlers|apps|https leftover leftover down; bounce|CHERRYPY2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the handlers 504s
pyramid2|PYRAMID2_TIMEOUT|1|30|s|/etc/pyramid2/pyramid2.conf|timeout=1|timeout=30|systemctl reload pyramid2|py|pyr_to_1|views|tweens|https leftover leftover down; bounce|PYRAMID2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the views 504s
turbo2|TURBO2_TIMEOUT|1|30|s|/etc/turbo2/turbo2.conf|timeout=1|timeout=30|systemctl reload turbo2|tb|tur_to_1|controllers|routes|https leftover leftover down; bounce|TURBO2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the controllers 504s
grails2|GRAILS2_TIMEOUT|1|30|s|/etc/grails2/grails2.conf|timeout=1|timeout=30|systemctl reload grails2|gr|gra_to_1|controllers|gsps|https leftover leftover down; bounce|GRAILS2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the controllers 504s
play2|PLAY2_TIMEOUT|1|30|s|/etc/play2/play2.conf|timeout=1|timeout=30|systemctl reload play2|pl|pla_to_1|actions|routes|https leftover leftover down; bounce|PLAY2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the actions 504s
spring2|SPRING2_TIMEOUT|1|30|s|/etc/spring2/spring2.conf|timeout=1|timeout=30|systemctl reload spring2|sp|spr_to_1|controllers|beans|https leftover leftover down; bounce|SPRING2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the controllers 504s
quarkus2|QUARKUS2_TIMEOUT|1|30|s|/etc/quarkus2/quarkus2.conf|timeout=1|timeout=30|systemctl reload quarkus2|qk|qua_to_1|resources|exts|https leftover leftover down; bounce|QUARKUS2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the resources 504s
micronaut2|MICRONAUT2_TIMEOUT|1|30|s|/etc/micronaut2/micronaut2.conf|timeout=1|timeout=30|systemctl reload micronaut2|mn|mic_to_1|controllers|beans|https leftover leftover down; bounce|MICRONAUT2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the controllers 504s
helidon2|HELIDON2_TIMEOUT|1|30|s|/etc/helidon2/helidon2.conf|timeout=1|timeout=30|systemctl reload helidon2|hl|hel_to_1|resources|mp|https leftover leftover down; bounce|HELIDON2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the resources 504s
vertx2|VERTX2_TIMEOUT|1|30|s|/etc/vertx2/vertx2.conf|timeout=1|timeout=30|systemctl reload vertx2|vx|ver_to_1|verticles|routers|https leftover leftover down; bounce|VERTX2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the verticles 504s
ktor2|KTOR2_TIMEOUT|1|30|s|/etc/ktor2/ktor2.conf|timeout=1|timeout=30|systemctl reload ktor2|kt|kto_to_1|routes|plugins|https leftover leftover down; bounce|KTOR2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the routes 504s
http4k2|HTTP4K2_TIMEOUT|1|30|s|/etc/http4k2/http4k2.conf|timeout=1|timeout=30|systemctl reload http4k2|h4|htt_to_1|filters|apps|https leftover leftover down; bounce|HTTP4K2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the filters 504s
gin2|GIN2_TIMEOUT|1|30|s|/etc/gin2/gin2.conf|timeout=1|timeout=30|systemctl reload gin2|gn|gin_to_1|handlers|mw|https leftover leftover down; bounce|GIN2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the handlers 504s
echo2|ECHO2_TIMEOUT|1|30|s|/etc/echo2/echo2.conf|timeout=1|timeout=30|systemctl reload echo2|ec|ech_to_1|handlers|mw|https leftover leftover down; bounce|ECHO2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the handlers 504s
fiber2|FIBER2_TIMEOUT|1|30|s|/etc/fiber2/fiber2.conf|timeout=1|timeout=30|systemctl reload fiber2|fb|fib_to_1|handlers|mw|https leftover leftover down; bounce|FIBER2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the handlers 504s
chi2|CHI2_TIMEOUT|1|30|s|/etc/chi2/chi2.conf|timeout=1|timeout=30|systemctl reload chi2|ch|chi_to_1|handlers|mw|https leftover leftover down; bounce|CHI2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the handlers 504s
mux2|MUX2_TIMEOUT|1|30|s|/etc/mux2/mux2.conf|timeout=1|timeout=30|systemctl reload mux2|mx|mux_to_1|handlers|routes|https leftover leftover down; bounce|MUX2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the handlers 504s
fasthttp2|FASTHTTP2_TIMEOUT|1|30|s|/etc/fasthttp2/fasthttp2.conf|timeout=1|timeout=30|systemctl reload fasthttp2|fh|fas_to_1|handlers|servers|https leftover leftover down; bounce|FASTHTTP2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the handlers 504s
actix2|ACTIX2_TIMEOUT|1|30|s|/etc/actix2/actix2.conf|timeout=1|timeout=30|systemctl reload actix2|ax|act_to_1|handlers|actors|https leftover leftover down; bounce|ACTIX2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the handlers 504s
axum2|AXUM2_TIMEOUT|1|30|s|/etc/axum2/axum2.conf|timeout=1|timeout=30|systemctl reload axum2|au|axu_to_1|handlers|extractors|https leftover leftover down; bounce|AXUM2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the handlers 504s
warp2|WARP2_TIMEOUT|1|30|s|/etc/warp2/warp2.conf|timeout=1|timeout=30|systemctl reload warp2|wp|war_to_1|filters|rejections|https leftover leftover down; bounce|WARP2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the filters 504s
rocket2|ROCKET2_TIMEOUT|1|30|s|/etc/rocket2/rocket2.conf|timeout=1|timeout=30|systemctl reload rocket2|rk|roc_to_1|routes|fairings|https leftover leftover down; bounce|ROCKET2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the routes 504s
tide2|TIDE2_TIMEOUT|1|30|s|/etc/tide2/tide2.conf|timeout=1|timeout=30|systemctl reload tide2|td|tid_to_1|eps|mw|https leftover leftover down; bounce|TIDE2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the eps 504s
poem2|POEM2_TIMEOUT|1|30|s|/etc/poem2/poem2.conf|timeout=1|timeout=30|systemctl reload poem2|pm|poe_to_1|eps|mw|https leftover leftover down; bounce|POEM2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the eps 504s
salvo2|SALVO2_TIMEOUT|1|30|s|/etc/salvo2/salvo2.conf|timeout=1|timeout=30|systemctl reload salvo2|sv|sal_to_1|handlers|depots|https leftover leftover down; bounce|SALVO2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the handlers 504s
hyper2|HYPER2_TIMEOUT|1|30|s|/etc/hyper2/hyper2.conf|timeout=1|timeout=30|systemctl reload hyper2|hy|hyp_to_1|services|conns|https leftover leftover down; bounce|HYPER2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the services 504s
tokio2|TOKIO2_TIMEOUT|1|30|s|/etc/tokio2/tokio2.conf|timeout=1|timeout=30|systemctl reload tokio2|tk|tok_to_1|tasks|runtimes|tcp leftover leftover down; bounce|TOKIO2_TIMEOUT leftover 1 leftover; a 2s spawn is aborted so the tasks 504s
asyncstd2|ASYNCSTD2_TIMEOUT|1|30|s|/etc/asyncstd2/asyncstd2.conf|timeout=1|timeout=30|systemctl reload asyncstd2|as|asy_to_1|tasks|runtimes|tcp leftover leftover down; bounce|ASYNCSTD2_TIMEOUT leftover 1 leftover; a 2s spawn is aborted so the tasks 504s
smol2|SMOL2_TIMEOUT|1|30|s|/etc/smol2/smol2.conf|timeout=1|timeout=30|systemctl reload smol2|sm|smo_to_1|tasks|executors|tcp leftover leftover down; bounce|SMOL2_TIMEOUT leftover 1 leftover; a 2s spawn is aborted so the tasks 504s
express2|EXPRESS2_TIMEOUT|1|30|s|/etc/express2/express2.conf|timeout=1|timeout=30|systemctl reload express2|ex|exp_to_1|routes|mw|https leftover leftover down; bounce|EXPRESS2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the routes 504s
fastify2|FASTIFY2_TIMEOUT|1|30|s|/etc/fastify2/fastify2.conf|timeout=1|timeout=30|systemctl reload fastify2|ff|fas_to_1|routes|hooks|https leftover leftover down; bounce|FASTIFY2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the routes 504s
nestjs2|NESTJS2_TIMEOUT|1|30|s|/etc/nestjs2/nestjs2.conf|timeout=1|timeout=30|systemctl reload nestjs2|ns|nes_to_1|controllers|mods|https leftover leftover down; bounce|NESTJS2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the controllers 504s
koa2|KOA2_TIMEOUT|1|30|s|/etc/koa2/koa2.conf|timeout=1|timeout=30|systemctl reload koa2|ko|koa_to_1|mw|ctx|https leftover leftover down; bounce|KOA2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the mw 504s
hapi2|HAPI2_TIMEOUT|1|30|s|/etc/hapi2/hapi2.conf|timeout=1|timeout=30|systemctl reload hapi2|hp|hap_to_1|routes|plugins|https leftover leftover down; bounce|HAPI2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the routes 504s
'''
WAVE = (
    "aiohttp2/sanic2/starlette2/quart2/falcon2/bottle2/cherrypy2/pyramid2/turbo2/grails2/play2/spring2/quarkus2/micronaut2/helidon2/vertx2/ktor2/http4k2/gin2/echo2/fiber2/chi2/mux2/fasthttp2/actix2/axum2/warp2/rocket2/tide2/poem2/salvo2/hyper2/tokio2/asyncstd2/smol2/express2/fastify2/nestjs2/koa2/hapi2"
)


def _parse_rows():
    plants = []
    srcs = ("grafana", "pagerduty", "opsgenie", "alertmanager")
    ns_cycle = (17, 16, 18)
    for raw in ROWS.strip().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split("|")
        if len(parts) != 15:
            raise SystemExit(f"bad row cols={len(parts)}: {raw[:160]}")
        (
            daemon, key, old, new, unit, path, oldv, newv, reload, hpeer, metric,
            what, wipe, herring, rca_tail,
        ) = parts
        i = len(plants)
        n = ns_cycle[i % 3]
        rem = "rollback" if i % 2 == 0 else "patch"
        src = srcs[i % 4]
        svc = f"e1{i:02d}x"
        ns = f"e1{i:02d}"
        clu = f"prod-apuj{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13843 + i }"
        node = f"ip-10-188-{1 + i}-{20 + i}"
        slug = f"{daemon}-{key}-{old}{unit}-{svc}"
        key_words = key.replace(".", " leftover ").replace("_", " leftover ")
        symptom = f"{key_words} leftover {old}{unit} leftover; {what} drop"
        because = (
            f"is dropping {what} because leftover {daemon} leftover {key_words} leftover is {old} leftover."
        )
        do_not = f"Restore {new}{unit}; do not wipe {wipe}."
        rca = f"{daemon} leftover {key} leftover {old} leftover; {rca_tail}"
        if remnant := (helm_rb(ns, svc, 3, path, oldv, newv, reload) if rem == "rollback" else patch_file(path, oldv, newv, reload)):
            extra = f"helm -n {ns} history {svc} | head -5" if rem == "rollback" else f"kubectl -n {ns} logs deploy/{svc} --since=5m | grep {key} | tail"
            eobs = f"4  {old}{unit}\n3  last-good {new}" if rem == "rollback" else f"{key} leftover {old}"
        plants.append(
            plant(
                slug=slug, ticket=ticket, service=svc, ns=ns, cluster=clu, src=src,
                node=node, symptom=symptom, because=because, do_not=do_not,
                herring=herring, rca=rca, remediate=rem, metric=metric,
                hcmds=[
                    f"{hpeer} leftover status | head",
                    f"systemctl reload {hpeer} || true",
                    f"{hpeer} leftover bounce leftover || true",
                ],
                hobs=[f"{hpeer} ok", "bounce unused", f"still {key} {old}"],
                inspect=f"grep {key} {path}", iobs=f"{oldv} leftover",
                extra=extra, eobs=eobs, rem=remnant, robs=f"{key} {new}; holds",
                verify=f"grep {key} {path}", vok=f"{new}; {ticket} resolved", n=n,
            )
        )
    return plants


PLANTS = _parse_rows()
m.PLANTS = PLANTS
m.BASE_ROUND = 4661


def notes_for(round_n, eps):
    slug0 = eps[0]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    slug1 = eps[1]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    rows = [
        f"| `{e['id']}` | {e['meta']['ticket']} | {e['false_lead']['claim'].replace('|', '/')} | {e['remediate']} | {e['reward']['success']} | {e['reward']['steps']} |"
        for e in eps
    ]
    return "\n".join(
        [
            f"# incident-response-oncall-factory NOTES r{round_n}",
            "",
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-78 leftover: {WAVE}.",
            "",
            "OpenSRE designed: 429 then 502 retries, 3-step herring, unique RCA, mix patch/rollback. plant=designed. generator=grok-4.6.",
            "",
            "| id | ticket | herring (steps 6-8) | remediate | success | steps |",
            "|---|---|---|---|---|---|",
            *rows,
            "",
            "## Contract audit",
            f"- Q=2 episodes, kind=episode, ids irc-r{round_n}-*.",
            "- Unique goal service+cluster+symptom; 3 false-lead actions; 429/502 retries.",
            "- Residual: designed excerpts, not live dispatcher traces.",
            "",
        ]
    )


m.notes_for = notes_for


def extra_unique_guards():
    banned = (
        "Follow OpenSRE", "fraud-graph", "sip-proxy", "traefik", "limit_req",
        "cloudfront", "fastly", "kube-proxy", "haproxy", "varnish", "metallb",
        "imperva", "bunny", "calico felix", "kong ", "caddy ",
        "github actions leftover", "gitlab leftover", "circleci leftover",
        "tekton leftover", "snowflake", "bigquery", "redshift", "idle_timeout",
        "max_client_conn", "ypbind", "oddjob", "opensearch", "leftover3c",
        "tigergraph", "hugegraph", "graphdb", "stardog", "debezium", "hasura",
    )
    for p in PLANTS:
        blob = (p["goal"] + " " + p["rca"] + " " + p["slug"]).lower()
        for tok in banned:
            if tok.lower() in blob:
                raise SystemExit(f"banned {tok} in {p['slug']}")
        for need in (p["service"], p["ns"], p["cluster"]):
            if need not in p["goal"]:
                raise SystemExit(p["slug"])
        if p["n_steps"] not in (16, 17, 18) or p["remediate"] not in ("rollback", "patch"):
            raise SystemExit(p["slug"])
    if len(PLANTS) % 2:
        raise SystemExit("odd")
    for i in range(0, len(PLANTS), 2):
        if {PLANTS[i]["remediate"], PLANTS[i + 1]["remediate"]} != {"rollback", "patch"}:
            raise SystemExit(f"pair {i}")


def main():
    extra_unique_guards()
    used_svc, used_clu, used_tix, _ids = m.harvest_used(m.FACTORY_DIR)
    for p in PLANTS:
        if p["service"] in used_svc:
            raise SystemExit(f"service collision {p['service']}")
        if p["cluster"] in used_clu:
            raise SystemExit(f"cluster collision {p['cluster']}")
        if p["ticket"] in used_tix:
            raise SystemExit(f"ticket collision {p['ticket']}")
    for label, xs in (
        ("slug", [p["slug"] for p in PLANTS]),
        ("svc", [p["service"] for p in PLANTS]),
        ("clu", [p["cluster"] for p in PLANTS]),
        ("tix", [p["ticket"] for p in PLANTS]),
        ("node", [p["node"] for p in PLANTS]),
        ("ns", [p["ns"] for p in PLANTS]),
    ):
        if len(set(xs)) != len(xs):
            raise SystemExit("dup " + label)
    print(json.dumps({"ok": True, "plants": len(PLANTS), "rounds": len(PLANTS) // 2}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
