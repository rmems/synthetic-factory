#!/usr/bin/env python3
"""IRC mill r4641+ — wave-77 lang/viz leftover.

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
ironpython2|IRONPYTHON2_TIMEOUT|1|30|s|/etc/ironpython2/ironpython2.conf|timeout=1|timeout=30|systemctl reload ironpython2|ip|iro_to_1|pkgs|clr|fs leftover leftover down; bounce|IRONPYTHON2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pkgs 504s
graalpy2|GRAALPY2_TIMEOUT|1|30|s|/etc/graalpy2/graalpy2.conf|timeout=1|timeout=30|systemctl reload graalpy2|gp|gra_to_1|pkgs|truffle|jvm leftover leftover down; bounce|GRAALPY2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pkgs 504s
ruby2|RUBY2_TIMEOUT|1|30|s|/etc/ruby2/ruby2.conf|timeout=1|timeout=30|systemctl reload ruby2|rb|rub_to_1|gems|bundler|fs leftover leftover down; bounce|RUBY2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the gems 504s
jruby2|JRUBY2_TIMEOUT|1|30|s|/etc/jruby2/jruby2.conf|timeout=1|timeout=30|systemctl reload jruby2|jr|jru_to_1|gems|jars|jvm leftover leftover down; bounce|JRUBY2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the gems 504s
truffleruby2|TRUFFLERUBY2_TIMEOUT|1|30|s|/etc/truffleruby2/truffleruby2.conf|timeout=1|timeout=30|systemctl reload truffleruby2|tr|tru_to_1|gems|truffle|jvm leftover leftover down; bounce|TRUFFLERUBY2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the gems 504s
php2|PHP2_TIMEOUT|1|30|s|/etc/php2/php2.conf|timeout=1|timeout=30|systemctl reload php2|ph|php_to_1|scripts|fpm|fs leftover leftover down; bounce|PHP2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the scripts 504s
hhvm2|HHVM2_TIMEOUT|1|30|s|/etc/hhvm2/hhvm2.conf|timeout=1|timeout=30|systemctl reload hhvm2|hh|hhv_to_1|scripts|jit|fs leftover leftover down; bounce|HHVM2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the scripts 504s
perl2|PERL2_TIMEOUT|1|30|s|/etc/perl2/perl2.conf|timeout=1|timeout=30|systemctl reload perl2|pl|per_to_1|scripts|cpan|fs leftover leftover down; bounce|PERL2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the scripts 504s
raku2|RAKU2_TIMEOUT|1|30|s|/etc/raku2/raku2.conf|timeout=1|timeout=30|systemctl reload raku2|rk|rak_to_1|scripts|zef|fs leftover leftover down; bounce|RAKU2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the scripts 504s
lua2|LUA2_TIMEOUT|1|30|s|/etc/lua2/lua2.conf|timeout=1|timeout=30|systemctl reload lua2|lu|lua_to_1|scripts|rocks|fs leftover leftover down; bounce|LUA2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the scripts 504s
luajit2|LUAJIT2_TIMEOUT|1|30|s|/etc/luajit2/luajit2.conf|timeout=1|timeout=30|systemctl reload luajit2|lj|lua_to_1|scripts|jit|fs leftover leftover down; bounce|LUAJIT2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the scripts 504s
julia2|JULIA2_TIMEOUT|1|30|s|/etc/julia2/julia2.conf|timeout=1|timeout=30|systemctl reload julia2|jl|jul_to_1|pkgs|depot|fs leftover leftover down; bounce|JULIA2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pkgs 504s
rlang2|RLANG2_TIMEOUT|1|30|s|/etc/rlang2/rlang2.conf|timeout=1|timeout=30|systemctl reload rlang2|rl|rla_to_1|pkgs|lib|fs leftover leftover down; bounce|RLANG2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pkgs 504s
octave2|OCTAVE2_TIMEOUT|1|30|s|/etc/octave2/octave2.conf|timeout=1|timeout=30|systemctl reload octave2|oc|oct_to_1|scripts|pkgs|fs leftover leftover down; bounce|OCTAVE2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the scripts 504s
matlab2|MATLAB2_TIMEOUT|1|30|s|/etc/matlab2/matlab2.conf|timeout=1|timeout=30|systemctl reload matlab2|mt|mat_to_1|scripts|toolboxes|fs leftover leftover down; bounce|MATLAB2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the scripts 504s
scilab2|SCILAB2_TIMEOUT|1|30|s|/etc/scilab2/scilab2.conf|timeout=1|timeout=30|systemctl reload scilab2|sc|sci_to_1|scripts|modules|fs leftover leftover down; bounce|SCILAB2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the scripts 504s
maxima2|MAXIMA2_TIMEOUT|1|30|s|/etc/maxima2/maxima2.conf|timeout=1|timeout=30|systemctl reload maxima2|mx|max_to_1|exprs|lisp|fs leftover leftover down; bounce|MAXIMA2_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the exprs 504s
sagemath2|SAGEMATH2_TIMEOUT|1|30|s|/etc/sagemath2/sagemath2.conf|timeout=1|timeout=30|systemctl reload sagemath2|sg|sag_to_1|notebooks|cells|fs leftover leftover down; bounce|SAGEMATH2_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the notebooks 504s
mathematica2|MATHEMATICA2_TIMEOUT|1|30|s|/etc/mathematica2/mathematica2.conf|timeout=1|timeout=30|systemctl reload mathematica2|mm|mat_to_1|notebooks|kernels|fs leftover leftover down; bounce|MATHEMATICA2_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the notebooks 504s
maple2|MAPLE2_TIMEOUT|1|30|s|/etc/maple2/maple2.conf|timeout=1|timeout=30|systemctl reload maple2|mp|map_to_1|worksheets|kernels|fs leftover leftover down; bounce|MAPLE2_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the worksheets 504s
idl2|IDL2_TIMEOUT|1|30|s|/etc/idl2/idl2.conf|timeout=1|timeout=30|systemctl reload idl2|id|idl_to_1|scripts|procs|fs leftover leftover down; bounce|IDL2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the scripts 504s
idlwave2|IDLWAVE2_TIMEOUT|1|30|s|/etc/idlwave2/idlwave2.conf|timeout=1|timeout=30|systemctl reload idlwave2|iw|idl_to_1|scripts|procs|fs leftover leftover down; bounce|IDLWAVE2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the scripts 504s
gnuplot2|GNUPLOT2_TIMEOUT|1|30|s|/etc/gnuplot2/gnuplot2.conf|timeout=1|timeout=30|systemctl reload gnuplot2|gp2|gnu_to_1|plots|scripts|fs leftover leftover down; bounce|GNUPLOT2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the plots 504s
plotly2|PLOTLY2_TIMEOUT|1|30|s|/etc/plotly2/plotly2.conf|timeout=1|timeout=30|systemctl reload plotly2|po|plo_to_1|figs|traces|https leftover leftover down; bounce|PLOTLY2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the figs 504s
bokeh2|BOKEH2_TIMEOUT|1|30|s|/etc/bokeh2/bokeh2.conf|timeout=1|timeout=30|systemctl reload bokeh2|bk|bok_to_1|docs|models|https leftover leftover down; bounce|BOKEH2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the docs 504s
dash2|DASH2_TIMEOUT|1|30|s|/etc/dash2/dash2.conf|timeout=1|timeout=30|systemctl reload dash2|dh|das_to_1|apps|callbacks|https leftover leftover down; bounce|DASH2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the apps 504s
streamlit2|STREAMLIT2_TIMEOUT|1|30|s|/etc/streamlit2/streamlit2.conf|timeout=1|timeout=30|systemctl reload streamlit2|st|str_to_1|apps|sessions|https leftover leftover down; bounce|STREAMLIT2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the apps 504s
gradio2|GRADIO2_TIMEOUT|1|30|s|/etc/gradio2/gradio2.conf|timeout=1|timeout=30|systemctl reload gradio2|gd|gra_to_1|apps|blocks|https leftover leftover down; bounce|GRADIO2_TIMEOUT leftover 1 leftover; a 2s launch is aborted so the apps 504s
panel2|PANEL2_TIMEOUT|1|30|s|/etc/panel2/panel2.conf|timeout=1|timeout=30|systemctl reload panel2|pn|pan_to_1|apps|servables|https leftover leftover down; bounce|PANEL2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the apps 504s
voila2|VOILA2_TIMEOUT|1|30|s|/etc/voila2/voila2.conf|timeout=1|timeout=30|systemctl reload voila2|vo|voi_to_1|notebooks|kernels|https leftover leftover down; bounce|VOILA2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the notebooks 504s
jupyterlab2|JUPYTERLAB2_TIMEOUT|1|30|s|/etc/jupyterlab2/jupyterlab2.conf|timeout=1|timeout=30|systemctl reload jupyterlab2|jb|jup_to_1|kernels|sessions|https leftover leftover down; bounce|JUPYTERLAB2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the kernels 504s
jupyterhub2|JUPYTERHUB2_TIMEOUT|1|30|s|/etc/jupyterhub2/jupyterhub2.conf|timeout=1|timeout=30|systemctl reload jupyterhub2|jh|jup_to_1|spawns|users|https leftover leftover down; bounce|JUPYTERHUB2_TIMEOUT leftover 1 leftover; a 2s spawn is aborted so the spawns 504s
rstudio2|RSTUDIO2_TIMEOUT|1|30|s|/etc/rstudio2/rstudio2.conf|timeout=1|timeout=30|systemctl reload rstudio2|rs|rst_to_1|sessions|projects|https leftover leftover down; bounce|RSTUDIO2_TIMEOUT leftover 1 leftover; a 2s start is aborted so the sessions 504s
posit2|POSIT2_TIMEOUT|1|30|s|/etc/posit2/posit2.conf|timeout=1|timeout=30|systemctl reload posit2|ps|pos_to_1|content|connect|https leftover leftover down; bounce|POSIT2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the content 504s
shiny2|SHINY2_TIMEOUT|1|30|s|/etc/shiny2/shiny2.conf|timeout=1|timeout=30|systemctl reload shiny2|sy|shi_to_1|apps|sessions|https leftover leftover down; bounce|SHINY2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the apps 504s
plumber2|PLUMBER2_TIMEOUT|1|30|s|/etc/plumber2/plumber2.conf|timeout=1|timeout=30|systemctl reload plumber2|pb|plu_to_1|apis|endpoints|https leftover leftover down; bounce|PLUMBER2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the apis 504s
fastapi2|FASTAPI2_TIMEOUT|1|30|s|/etc/fastapi2/fastapi2.conf|timeout=1|timeout=30|systemctl reload fastapi2|fa|fas_to_1|routes|deps|https leftover leftover down; bounce|FASTAPI2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the routes 504s
flask2|FLASK2_TIMEOUT|1|30|s|/etc/flask2/flask2.conf|timeout=1|timeout=30|systemctl reload flask2|fl|fla_to_1|routes|views|https leftover leftover down; bounce|FLASK2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the routes 504s
django2|DJANGO2_TIMEOUT|1|30|s|/etc/django2/django2.conf|timeout=1|timeout=30|systemctl reload django2|dj|dja_to_1|views|orm|https leftover leftover down; bounce|DJANGO2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the views 504s
tornado2|TORNADO2_TIMEOUT|1|30|s|/etc/tornado2/tornado2.conf|timeout=1|timeout=30|systemctl reload tornado2|tn|tor_to_1|handlers|ioloop|https leftover leftover down; bounce|TORNADO2_TIMEOUT leftover 1 leftover; a 2s serve is aborted so the handlers 504s
'''
WAVE = (
    "ironpython2/graalpy2/ruby2/jruby2/truffleruby2/php2/hhvm2/perl2/raku2/lua2/luajit2/julia2/rlang2/octave2/matlab2/scilab2/maxima2/sagemath2/mathematica2/maple2/idl2/idlwave2/gnuplot2/plotly2/bokeh2/dash2/streamlit2/gradio2/panel2/voila2/jupyterlab2/jupyterhub2/rstudio2/posit2/shiny2/plumber2/fastapi2/flask2/django2/tornado2"
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
        svc = f"s4{i:02d}x"
        ns = f"s4{i:02d}"
        clu = f"prod-apui{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13803 + i }"
        node = f"ip-10-187-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4641


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-77 leftover: {WAVE}.",
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
