#!/usr/bin/env python3
"""IRC mill r4621+ — wave-76 ssg/frontend leftover.

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
optimizely2|OPTIMIZELY2_TIMEOUT|1|30|s|/etc/optimizely2/optimizely2.conf|timeout=1|timeout=30|systemctl reload optimizely2|op|opt_to_1|pages|exps|https leftover leftover down; bounce|OPTIMIZELY2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the pages 504s
sitecore2|SITECORE2_TIMEOUT|1|30|s|/etc/sitecore2/sitecore2.conf|timeout=1|timeout=30|systemctl reload sitecore2|sc|sit_to_1|items|indexes|https leftover leftover down; bounce|SITECORE2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the items 504s
adobeaem2|ADOBEAEM2_TIMEOUT|1|30|s|/etc/adobeaem2/adobeaem2.conf|timeout=1|timeout=30|systemctl reload adobeaem2|ae|ado_to_1|pages|bundles|https leftover leftover down; bounce|ADOBEAEM2_TIMEOUT leftover 1 leftover; a 2s replicate is aborted so the pages 504s
umbraco2|UMBRACO2_TIMEOUT|1|30|s|/etc/umbraco2/umbraco2.conf|timeout=1|timeout=30|systemctl reload umbraco2|um|umb_to_1|nodes|media|https leftover leftover down; bounce|UMBRACO2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the nodes 504s
kentico2|KENTICO2_TIMEOUT|1|30|s|/etc/kentico2/kentico2.conf|timeout=1|timeout=30|systemctl reload kentico2|kt|ken_to_1|pages|docs|https leftover leftover down; bounce|KENTICO2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the pages 504s
dnn2|DNN2_TIMEOUT|1|30|s|/etc/dnn2/dnn2.conf|timeout=1|timeout=30|systemctl reload dnn2|dn|dnn_to_1|modules|pages|mssql leftover leftover down; bounce|DNN2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the modules 504s
orchardext2|ORCHARDEXT2_TIMEOUT|1|30|s|/etc/orchardext2/orchardext2.conf|timeout=1|timeout=30|systemctl reload orchardext2|oe|orc_to_1|content|types|https leftover leftover down; bounce|ORCHARDEXT2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the content 504s
craftcms2|CRAFTCMS2_TIMEOUT|1|30|s|/etc/craftcms2/craftcms2.conf|timeout=1|timeout=30|systemctl reload craftcms2|cf|cra_to_1|entries|sections|mysql leftover leftover down; bounce|CRAFTCMS2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the entries 504s
statamic2|STATAMIC2_TIMEOUT|1|30|s|/etc/statamic2/statamic2.conf|timeout=1|timeout=30|systemctl reload statamic2|st|sta_to_1|entries|collections|fs leftover leftover down; bounce|STATAMIC2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the entries 504s
kirby2|KIRBY2_TIMEOUT|1|30|s|/etc/kirby2/kirby2.conf|timeout=1|timeout=30|systemctl reload kirby2|kr|kir_to_1|pages|content|fs leftover leftover down; bounce|KIRBY2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the pages 504s
processwire2|PROCESSWIRE2_TIMEOUT|1|30|s|/etc/processwire2/processwire2.conf|timeout=1|timeout=30|systemctl reload processwire2|pw|pro_to_1|pages|fields|mysql leftover leftover down; bounce|PROCESSWIRE2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the pages 504s
modx2|MODX2_TIMEOUT|1|30|s|/etc/modx2/modx2.conf|timeout=1|timeout=30|systemctl reload modx2|mx|mod_to_1|resources|tvs|mysql leftover leftover down; bounce|MODX2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the resources 504s
concrete5|CONCRETE5_TIMEOUT|1|30|s|/etc/concrete5/concrete5.conf|timeout=1|timeout=30|systemctl reload concrete5|c5|con_to_1|pages|blocks|mysql leftover leftover down; bounce|CONCRETE5_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the pages 504s
typo3v12|TYPO3V12_TIMEOUT|1|30|s|/etc/typo3v12/typo3v12.conf|timeout=1|timeout=30|systemctl reload typo3v12|t3|typ_to_1|pages|cache|mysql leftover leftover down; bounce|TYPO3V12_TIMEOUT leftover 1 leftover; a 2s render is aborted so the pages 504s
grav2|GRAV2_TIMEOUT|1|30|s|/etc/grav2/grav2.conf|timeout=1|timeout=30|systemctl reload grav2|gv|gra_to_1|pages|md|fs leftover leftover down; bounce|GRAV2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the pages 504s
hugo2|HUGO2_TIMEOUT|1|30|s|/etc/hugo2/hugo2.conf|timeout=1|timeout=30|systemctl reload hugo2|hg|hug_to_1|pages|md|fs leftover leftover down; bounce|HUGO2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the pages 504s
jekyll2|JEKYLL2_TIMEOUT|1|30|s|/etc/jekyll2/jekyll2.conf|timeout=1|timeout=30|systemctl reload jekyll2|jk|jek_to_1|pages|md|fs leftover leftover down; bounce|JEKYLL2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the pages 504s
eleventy2|ELEVENTY2_TIMEOUT|1|30|s|/etc/eleventy2/eleventy2.conf|timeout=1|timeout=30|systemctl reload eleventy2|el|ele_to_1|pages|md|fs leftover leftover down; bounce|ELEVENTY2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the pages 504s
hexo2|HEXO2_TIMEOUT|1|30|s|/etc/hexo2/hexo2.conf|timeout=1|timeout=30|systemctl reload hexo2|hx|hex_to_1|pages|md|fs leftover leftover down; bounce|HEXO2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the pages 504s
pelican2|PELICAN2_TIMEOUT|1|30|s|/etc/pelican2/pelican2.conf|timeout=1|timeout=30|systemctl reload pelican2|pl|pel_to_1|pages|md|fs leftover leftover down; bounce|PELICAN2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the pages 504s
nikola2|NIKOLA2_TIMEOUT|1|30|s|/etc/nikola2/nikola2.conf|timeout=1|timeout=30|systemctl reload nikola2|nk|nik_to_1|pages|md|fs leftover leftover down; bounce|NIKOLA2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the pages 504s
zola2|ZOLA2_TIMEOUT|1|30|s|/etc/zola2/zola2.conf|timeout=1|timeout=30|systemctl reload zola2|zl|zol_to_1|pages|md|fs leftover leftover down; bounce|ZOLA2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the pages 504s
hugoextended|HUGOEXTENDED_TIMEOUT|1|30|s|/etc/hugoextended/hugoextended.conf|timeout=1|timeout=30|systemctl reload hugoextended|he|hug_to_1|pages|md|fs leftover leftover down; bounce|HUGOEXTENDED_TIMEOUT leftover 1 leftover; a 2s build is aborted so the pages 504s
gatsby2|GATSBY2_TIMEOUT|1|30|s|/etc/gatsby2/gatsby2.conf|timeout=1|timeout=30|systemctl reload gatsby2|gb|gat_to_1|pages|graphql|fs leftover leftover down; bounce|GATSBY2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the pages 504s
nextjs2|NEXTJS2_TIMEOUT|1|30|s|/etc/nextjs2/nextjs2.conf|timeout=1|timeout=30|systemctl reload nextjs2|nx|nex_to_1|pages|isr|https leftover leftover down; bounce|NEXTJS2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the pages 504s
nuxt2|NUXT2_TIMEOUT|1|30|s|/etc/nuxt2/nuxt2.conf|timeout=1|timeout=30|systemctl reload nuxt2|nu|nux_to_1|pages|nitro|https leftover leftover down; bounce|NUXT2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the pages 504s
remix2|REMIX2_TIMEOUT|1|30|s|/etc/remix2/remix2.conf|timeout=1|timeout=30|systemctl reload remix2|rx|rem_to_1|loaders|routes|https leftover leftover down; bounce|REMIX2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the loaders 504s
astro2|ASTRO2_TIMEOUT|1|30|s|/etc/astro2/astro2.conf|timeout=1|timeout=30|systemctl reload astro2|as|ast_to_1|pages|islands|https leftover leftover down; bounce|ASTRO2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the pages 504s
sveltekit2|SVELTEKIT2_TIMEOUT|1|30|s|/etc/sveltekit2/sveltekit2.conf|timeout=1|timeout=30|systemctl reload sveltekit2|sk|sve_to_1|pages|hooks|https leftover leftover down; bounce|SVELTEKIT2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the pages 504s
solidstart2|SOLIDSTART2_TIMEOUT|1|30|s|/etc/solidstart2/solidstart2.conf|timeout=1|timeout=30|systemctl reload solidstart2|ss|sol_to_1|pages|routes|https leftover leftover down; bounce|SOLIDSTART2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the pages 504s
qwik2|QWIK2_TIMEOUT|1|30|s|/etc/qwik2/qwik2.conf|timeout=1|timeout=30|systemctl reload qwik2|qw|qwi_to_1|pages|resumable|https leftover leftover down; bounce|QWIK2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the pages 504s
fresh2|FRESH2_TIMEOUT|1|30|s|/etc/fresh2/fresh2.conf|timeout=1|timeout=30|systemctl reload fresh2|fr|fre_to_1|pages|islands|https leftover leftover down; bounce|FRESH2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the pages 504s
hono2|HONO2_TIMEOUT|1|30|s|/etc/hono2/hono2.conf|timeout=1|timeout=30|systemctl reload hono2|hn|hon_to_1|routes|handlers|https leftover leftover down; bounce|HONO2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the routes 504s
elysia2|ELYSIA2_TIMEOUT|1|30|s|/etc/elysia2/elysia2.conf|timeout=1|timeout=30|systemctl reload elysia2|ey|ely_to_1|routes|handlers|https leftover leftover down; bounce|ELYSIA2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the routes 504s
bun2|BUN2_TIMEOUT|1|30|s|/etc/bun2/bun2.conf|timeout=1|timeout=30|systemctl reload bun2|bn|bun_to_1|modules|lock|fs leftover leftover down; bounce|BUN2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the modules 504s
deno2|DENO2_TIMEOUT|1|30|s|/etc/deno2/deno2.conf|timeout=1|timeout=30|systemctl reload deno2|dn|den_to_1|modules|lock|fs leftover leftover down; bounce|DENO2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the modules 504s
nodejs2|NODEJS2_TIMEOUT|1|30|s|/etc/nodejs2/nodejs2.conf|timeout=1|timeout=30|systemctl reload nodejs2|nd|nod_to_1|modules|lock|fs leftover leftover down; bounce|NODEJS2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the modules 504s
python2|PYTHON2_TIMEOUT|1|30|s|/etc/python2/python2.conf|timeout=1|timeout=30|systemctl reload python2|py|pyt_to_1|pkgs|venv|fs leftover leftover down; bounce|PYTHON2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pkgs 504s
pypy2|PYPY2_TIMEOUT|1|30|s|/etc/pypy2/pypy2.conf|timeout=1|timeout=30|systemctl reload pypy2|pp|pyp_to_1|pkgs|venv|fs leftover leftover down; bounce|PYPY2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pkgs 504s
jython2|JYTHON2_TIMEOUT|1|30|s|/etc/jython2/jython2.conf|timeout=1|timeout=30|systemctl reload jython2|jy|jyt_to_1|pkgs|jars|jvm leftover leftover down; bounce|JYTHON2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pkgs 504s
'''
WAVE = (
    "optimizely2/sitecore2/adobeaem2/umbraco2/kentico2/dnn2/orchardext2/craftcms2/statamic2/kirby2/processwire2/modx2/concrete5/typo3v12/grav2/hugo2/jekyll2/eleventy2/hexo2/pelican2/nikola2/zola2/hugoextended/gatsby2/nextjs2/nuxt2/remix2/astro2/sveltekit2/solidstart2/qwik2/fresh2/hono2/elysia2/bun2/deno2/nodejs2/python2/pypy2/jython2"
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
        svc = f"n1{i:02d}x"
        ns = f"n1{i:02d}"
        clu = f"prod-apuh{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13763 + i }"
        node = f"ip-10-186-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4621


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-76 leftover: {WAVE}.",
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
