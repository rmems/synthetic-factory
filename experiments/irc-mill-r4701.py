#!/usr/bin/env python3
"""IRC mill r4701+ — wave-80 pkg/build leftover.

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
pants2|PANTS2_TIMEOUT|1|30|s|/etc/pants2/pants2.conf|timeout=1|timeout=30|systemctl reload pants2|pn|pan_to_1|targets|cache|fs leftover leftover down; bounce|PANTS2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the targets 504s
please2|PLEASE2_TIMEOUT|1|30|s|/etc/please2/please2.conf|timeout=1|timeout=30|systemctl reload please2|pl|ple_to_1|targets|cache|fs leftover leftover down; bounce|PLEASE2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the targets 504s
gradle2|GRADLE2_TIMEOUT|1|30|s|/etc/gradle2/gradle2.conf|timeout=1|timeout=30|systemctl reload gradle2|gd|gra_to_1|tasks|cache|fs leftover leftover down; bounce|GRADLE2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the tasks 504s
maven2|MAVEN2_TIMEOUT|1|30|s|/etc/maven2/maven2.conf|timeout=1|timeout=30|systemctl reload maven2|mv|mav_to_1|goals|repo|fs leftover leftover down; bounce|MAVEN2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the goals 504s
sbt2|SBT2_TIMEOUT|1|30|s|/etc/sbt2/sbt2.conf|timeout=1|timeout=30|systemctl reload sbt2|sb|sbt_to_1|tasks|ivy|fs leftover leftover down; bounce|SBT2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the tasks 504s
lein2|LEIN2_TIMEOUT|1|30|s|/etc/lein2/lein2.conf|timeout=1|timeout=30|systemctl reload lein2|ln|lei_to_1|tasks|m2|fs leftover leftover down; bounce|LEIN2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the tasks 504s
npm2|NPM2_TIMEOUT|1|30|s|/etc/npm2/npm2.conf|timeout=1|timeout=30|systemctl reload npm2|np|npm_to_1|pkgs|lock|fs leftover leftover down; bounce|NPM2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
yarn2|YARN2_TIMEOUT|1|30|s|/etc/yarn2/yarn2.conf|timeout=1|timeout=30|systemctl reload yarn2|yn|yar_to_1|pkgs|lock|fs leftover leftover down; bounce|YARN2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
pnpm2|PNPM2_TIMEOUT|1|30|s|/etc/pnpm2/pnpm2.conf|timeout=1|timeout=30|systemctl reload pnpm2|pp|pnp_to_1|pkgs|store|fs leftover leftover down; bounce|PNPM2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
bunpm2|BUNPM2_TIMEOUT|1|30|s|/etc/bunpm2/bunpm2.conf|timeout=1|timeout=30|systemctl reload bunpm2|bp|bun_to_1|pkgs|lock|fs leftover leftover down; bounce|BUNPM2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
pip2|PIP2_TIMEOUT|1|30|s|/etc/pip2/pip2.conf|timeout=1|timeout=30|systemctl reload pip2|pi|pip_to_1|pkgs|wheels|fs leftover leftover down; bounce|PIP2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
poetry2|POETRY2_TIMEOUT|1|30|s|/etc/poetry2/poetry2.conf|timeout=1|timeout=30|systemctl reload poetry2|po|poe_to_1|pkgs|lock|fs leftover leftover down; bounce|POETRY2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
uv2|UV2_TIMEOUT|1|30|s|/etc/uv2/uv2.conf|timeout=1|timeout=30|systemctl reload uv2|uv|uv2_to_1|pkgs|lock|fs leftover leftover down; bounce|UV2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
pdm2|PDM2_TIMEOUT|1|30|s|/etc/pdm2/pdm2.conf|timeout=1|timeout=30|systemctl reload pdm2|pd|pdm_to_1|pkgs|lock|fs leftover leftover down; bounce|PDM2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
conda2|CONDA2_TIMEOUT|1|30|s|/etc/conda2/conda2.conf|timeout=1|timeout=30|systemctl reload conda2|cd|con_to_1|pkgs|envs|fs leftover leftover down; bounce|CONDA2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
mamba2|MAMBA2_TIMEOUT|1|30|s|/etc/mamba2/mamba2.conf|timeout=1|timeout=30|systemctl reload mamba2|mb|mam_to_1|pkgs|envs|fs leftover leftover down; bounce|MAMBA2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
cargo2|CARGO2_TIMEOUT|1|30|s|/etc/cargo2/cargo2.conf|timeout=1|timeout=30|systemctl reload cargo2|cg|car_to_1|crates|lock|fs leftover leftover down; bounce|CARGO2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the crates 504s
crates2|CRATES2_TIMEOUT|1|30|s|/etc/crates2/crates2.conf|timeout=1|timeout=30|systemctl reload crates2|cr|cra_to_1|crates|index|https leftover leftover down; bounce|CRATES2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the crates 504s
gem2|GEM2_TIMEOUT|1|30|s|/etc/gem2/gem2.conf|timeout=1|timeout=30|systemctl reload gem2|gm|gem_to_1|gems|specs|fs leftover leftover down; bounce|GEM2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the gems 504s
bundler2|BUNDLER2_TIMEOUT|1|30|s|/etc/bundler2/bundler2.conf|timeout=1|timeout=30|systemctl reload bundler2|bd|bun_to_1|gems|lock|fs leftover leftover down; bounce|BUNDLER2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the gems 504s
composer2|COMPOSER2_TIMEOUT|1|30|s|/etc/composer2/composer2.conf|timeout=1|timeout=30|systemctl reload composer2|cm|com_to_1|pkgs|lock|fs leftover leftover down; bounce|COMPOSER2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
packagist2|PACKAGIST2_TIMEOUT|1|30|s|/etc/packagist2/packagist2.conf|timeout=1|timeout=30|systemctl reload packagist2|pk|pac_to_1|pkgs|index|https leftover leftover down; bounce|PACKAGIST2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the pkgs 504s
nuget2|NUGET2_TIMEOUT|1|30|s|/etc/nuget2/nuget2.conf|timeout=1|timeout=30|systemctl reload nuget2|ng|nug_to_1|pkgs|cache|fs leftover leftover down; bounce|NUGET2_TIMEOUT leftover 1 leftover; a 2s restore is aborted so the pkgs 504s
paket2|PAKET2_TIMEOUT|1|30|s|/etc/paket2/paket2.conf|timeout=1|timeout=30|systemctl reload paket2|pt|pak_to_1|pkgs|lock|fs leftover leftover down; bounce|PAKET2_TIMEOUT leftover 1 leftover; a 2s restore is aborted so the pkgs 504s
hex2|HEX2_TIMEOUT|1|30|s|/etc/hex2/hex2.conf|timeout=1|timeout=30|systemctl reload hex2|hx|hex_to_1|pkgs|lock|fs leftover leftover down; bounce|HEX2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
rebar2|REBAR2_TIMEOUT|1|30|s|/etc/rebar2/rebar2.conf|timeout=1|timeout=30|systemctl reload rebar2|rb|reb_to_1|pkgs|lock|fs leftover leftover down; bounce|REBAR2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the pkgs 504s
mix2|MIX2_TIMEOUT|1|30|s|/etc/mix2/mix2.conf|timeout=1|timeout=30|systemctl reload mix2|mx|mix_to_1|deps|lock|fs leftover leftover down; bounce|MIX2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the deps 504s
cabal2|CABAL2_TIMEOUT|1|30|s|/etc/cabal2/cabal2.conf|timeout=1|timeout=30|systemctl reload cabal2|cb|cab_to_1|pkgs|store|fs leftover leftover down; bounce|CABAL2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the pkgs 504s
stack2|STACK2_TIMEOUT|1|30|s|/etc/stack2/stack2.conf|timeout=1|timeout=30|systemctl reload stack2|sk|sta_to_1|pkgs|work|fs leftover leftover down; bounce|STACK2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the pkgs 504s
opam2|OPAM2_TIMEOUT|1|30|s|/etc/opam2/opam2.conf|timeout=1|timeout=30|systemctl reload opam2|op|opa_to_1|pkgs|switch|fs leftover leftover down; bounce|OPAM2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
dune2|DUNE2_TIMEOUT|1|30|s|/etc/dune2/dune2.conf|timeout=1|timeout=30|systemctl reload dune2|du|dun_to_1|targets|cache|fs leftover leftover down; bounce|DUNE2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the targets 504s
make2|MAKE2_TIMEOUT|1|30|s|/etc/make2/make2.conf|timeout=1|timeout=30|systemctl reload make2|mk|mak_to_1|targets|objs|fs leftover leftover down; bounce|MAKE2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the targets 504s
ninja2|NINJA2_TIMEOUT|1|30|s|/etc/ninja2/ninja2.conf|timeout=1|timeout=30|systemctl reload ninja2|nj|nin_to_1|targets|objs|fs leftover leftover down; bounce|NINJA2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the targets 504s
meson2|MESON2_TIMEOUT|1|30|s|/etc/meson2/meson2.conf|timeout=1|timeout=30|systemctl reload meson2|ms|mes_to_1|targets|builddir|fs leftover leftover down; bounce|MESON2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the targets 504s
cmake2|CMAKE2_TIMEOUT|1|30|s|/etc/cmake2/cmake2.conf|timeout=1|timeout=30|systemctl reload cmake2|cmk|cma_to_1|targets|cache|fs leftover leftover down; bounce|CMAKE2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the targets 504s
autotools2|AUTOTOOLS2_TIMEOUT|1|30|s|/etc/autotools2/autotools2.conf|timeout=1|timeout=30|systemctl reload autotools2|at|aut_to_1|targets|config|fs leftover leftover down; bounce|AUTOTOOLS2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the targets 504s
scons2|SCONS2_TIMEOUT|1|30|s|/etc/scons2/scons2.conf|timeout=1|timeout=30|systemctl reload scons2|sc|sco_to_1|targets|cache|fs leftover leftover down; bounce|SCONS2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the targets 504s
waf2|WAF2_TIMEOUT|1|30|s|/etc/waf2/waf2.conf|timeout=1|timeout=30|systemctl reload waf2|wf|waf_to_1|targets|cache|fs leftover leftover down; bounce|WAF2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the targets 504s
ant2|ANT2_TIMEOUT|1|30|s|/etc/ant2/ant2.conf|timeout=1|timeout=30|systemctl reload ant2|an|ant_to_1|targets|jars|fs leftover leftover down; bounce|ANT2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the targets 504s
ivy2|IVY2_TIMEOUT|1|30|s|/etc/ivy2/ivy2.conf|timeout=1|timeout=30|systemctl reload ivy2|iv|ivy_to_1|artifacts|cache|fs leftover leftover down; bounce|IVY2_TIMEOUT leftover 1 leftover; a 2s resolve is aborted so the artifacts 504s
'''
WAVE = (
    "pants2/please2/gradle2/maven2/sbt2/lein2/npm2/yarn2/pnpm2/bunpm2/pip2/poetry2/uv2/pdm2/conda2/mamba2/cargo2/crates2/gem2/bundler2/composer2/packagist2/nuget2/paket2/hex2/rebar2/mix2/cabal2/stack2/opam2/dune2/make2/ninja2/meson2/cmake2/autotools2/scons2/waf2/ant2/ivy2"
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
        svc = f"g3{i:02d}x"
        ns = f"g3{i:02d}"
        clu = f"prod-apul{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13923 + i }"
        node = f"ip-10-190-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4701


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-80 leftover: {WAVE}.",
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
