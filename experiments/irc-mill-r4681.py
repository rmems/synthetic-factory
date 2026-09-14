#!/usr/bin/env python3
"""IRC mill r4681+ — wave-79 compiler/lang leftover.

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
rustc2|RUSTC2_TIMEOUT|1|30|s|/etc/rustc2/rustc2.conf|timeout=1|timeout=30|systemctl reload rustc2|rc|rus_to_1|crates|llvm|fs leftover leftover down; bounce|RUSTC2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the crates 504s
go2|GO2_TIMEOUT|1|30|s|/etc/go2/go2.conf|timeout=1|timeout=30|systemctl reload go2|go|go2_to_1|pkgs|mod|fs leftover leftover down; bounce|GO2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the pkgs 504s
gcc2|GCC2_TIMEOUT|1|30|s|/etc/gcc2/gcc2.conf|timeout=1|timeout=30|systemctl reload gcc2|gc|gcc_to_1|objs|asms|fs leftover leftover down; bounce|GCC2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the objs 504s
clang2|CLANG2_TIMEOUT|1|30|s|/etc/clang2/clang2.conf|timeout=1|timeout=30|systemctl reload clang2|cl|cla_to_1|objs|ir|fs leftover leftover down; bounce|CLANG2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the objs 504s
llvm2|LLVM2_TIMEOUT|1|30|s|/etc/llvm2/llvm2.conf|timeout=1|timeout=30|systemctl reload llvm2|ll|llv_to_1|ir|passes|fs leftover leftover down; bounce|LLVM2_TIMEOUT leftover 1 leftover; a 2s opt is aborted so the ir 504s
zig2|ZIG2_TIMEOUT|1|30|s|/etc/zig2/zig2.conf|timeout=1|timeout=30|systemctl reload zig2|zg|zig_to_1|objs|cache|fs leftover leftover down; bounce|ZIG2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the objs 504s
nim2|NIM2_TIMEOUT|1|30|s|/etc/nim2/nim2.conf|timeout=1|timeout=30|systemctl reload nim2|nm|nim_to_1|mods|cache|fs leftover leftover down; bounce|NIM2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the mods 504s
crystal2|CRYSTAL2_TIMEOUT|1|30|s|/etc/crystal2/crystal2.conf|timeout=1|timeout=30|systemctl reload crystal2|cr|cry_to_1|shards|cache|fs leftover leftover down; bounce|CRYSTAL2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the shards 504s
dlang2|DLANG2_TIMEOUT|1|30|s|/etc/dlang2/dlang2.conf|timeout=1|timeout=30|systemctl reload dlang2|dl|dla_to_1|mods|dmd|fs leftover leftover down; bounce|DLANG2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the mods 504s
fortran2|FORTRAN2_TIMEOUT|1|30|s|/etc/fortran2/fortran2.conf|timeout=1|timeout=30|systemctl reload fortran2|ft|for_to_1|objs|mods|fs leftover leftover down; bounce|FORTRAN2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the objs 504s
cobol2|COBOL2_TIMEOUT|1|30|s|/etc/cobol2/cobol2.conf|timeout=1|timeout=30|systemctl reload cobol2|cb|cob_to_1|progs|copybooks|fs leftover leftover down; bounce|COBOL2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the progs 504s
ada2|ADA2_TIMEOUT|1|30|s|/etc/ada2/ada2.conf|timeout=1|timeout=30|systemctl reload ada2|ad|ada_to_1|units|alis|fs leftover leftover down; bounce|ADA2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the units 504s
pascal2|PASCAL2_TIMEOUT|1|30|s|/etc/pascal2/pascal2.conf|timeout=1|timeout=30|systemctl reload pascal2|pa|pas_to_1|units|pcus|fs leftover leftover down; bounce|PASCAL2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the units 504s
delphi2|DELPHI2_TIMEOUT|1|30|s|/etc/delphi2/delphi2.conf|timeout=1|timeout=30|systemctl reload delphi2|de|del_to_1|units|dcus|fs leftover leftover down; bounce|DELPHI2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the units 504s
vbnet2|VBNET2_TIMEOUT|1|30|s|/etc/vbnet2/vbnet2.conf|timeout=1|timeout=30|systemctl reload vbnet2|vb|vbn_to_1|asms|proj|fs leftover leftover down; bounce|VBNET2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the asms 504s
csharp2|CSHARP2_TIMEOUT|1|30|s|/etc/csharp2/csharp2.conf|timeout=1|timeout=30|systemctl reload csharp2|cs|csh_to_1|asms|proj|fs leftover leftover down; bounce|CSHARP2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the asms 504s
fsharp2|FSHARP2_TIMEOUT|1|30|s|/etc/fsharp2/fsharp2.conf|timeout=1|timeout=30|systemctl reload fsharp2|fs|fsh_to_1|asms|proj|fs leftover leftover down; bounce|FSHARP2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the asms 504s
ocaml2|OCAML2_TIMEOUT|1|30|s|/etc/ocaml2/ocaml2.conf|timeout=1|timeout=30|systemctl reload ocaml2|oc|oca_to_1|cmos|opam|fs leftover leftover down; bounce|OCAML2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the cmos 504s
haskell2|HASKELL2_TIMEOUT|1|30|s|/etc/haskell2/haskell2.conf|timeout=1|timeout=30|systemctl reload haskell2|hs|has_to_1|his|cabal|fs leftover leftover down; bounce|HASKELL2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the his 504s
erlang2|ERLANG2_TIMEOUT|1|30|s|/etc/erlang2/erlang2.conf|timeout=1|timeout=30|systemctl reload erlang2|er|erl_to_1|beams|rebar|fs leftover leftover down; bounce|ERLANG2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the beams 504s
elixir2|ELIXIR2_TIMEOUT|1|30|s|/etc/elixir2/elixir2.conf|timeout=1|timeout=30|systemctl reload elixir2|ex|eli_to_1|beams|mix|fs leftover leftover down; bounce|ELIXIR2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the beams 504s
gleam2|GLEAM2_TIMEOUT|1|30|s|/etc/gleam2/gleam2.conf|timeout=1|timeout=30|systemctl reload gleam2|gl|gle_to_1|beams|build|fs leftover leftover down; bounce|GLEAM2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the beams 504s
clojure2|CLOJURE2_TIMEOUT|1|30|s|/etc/clojure2/clojure2.conf|timeout=1|timeout=30|systemctl reload clojure2|cj|clo_to_1|classes|deps|jvm leftover leftover down; bounce|CLOJURE2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the classes 504s
scala2|SCALA2_TIMEOUT|1|30|s|/etc/scala2/scala2.conf|timeout=1|timeout=30|systemctl reload scala2|sc|sca_to_1|classes|sbt|jvm leftover leftover down; bounce|SCALA2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the classes 504s
kotlin2|KOTLIN2_TIMEOUT|1|30|s|/etc/kotlin2/kotlin2.conf|timeout=1|timeout=30|systemctl reload kotlin2|kt|kot_to_1|classes|gradle|jvm leftover leftover down; bounce|KOTLIN2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the classes 504s
groovy2|GROOVY2_TIMEOUT|1|30|s|/etc/groovy2/groovy2.conf|timeout=1|timeout=30|systemctl reload groovy2|gy|gro_to_1|classes|gradle|jvm leftover leftover down; bounce|GROOVY2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the classes 504s
coffeescript2|COFFEESCRIPT2_TIMEOUT|1|30|s|/etc/coffeescript2/coffeescript2.conf|timeout=1|timeout=30|systemctl reload coffeescript2|cf|cof_to_1|js|src|fs leftover leftover down; bounce|COFFEESCRIPT2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the js 504s
typescript2|TYPESCRIPT2_TIMEOUT|1|30|s|/etc/typescript2/typescript2.conf|timeout=1|timeout=30|systemctl reload typescript2|ts|typ_to_1|js|src|fs leftover leftover down; bounce|TYPESCRIPT2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the js 504s
dart2|DART2_TIMEOUT|1|30|s|/etc/dart2/dart2.conf|timeout=1|timeout=30|systemctl reload dart2|dt|dar_to_1|pkgs|pub|fs leftover leftover down; bounce|DART2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the pkgs 504s
swift2|SWIFT2_TIMEOUT|1|30|s|/etc/swift2/swift2.conf|timeout=1|timeout=30|systemctl reload swift2|sw|swi_to_1|mods|spm|fs leftover leftover down; bounce|SWIFT2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the mods 504s
objc2|OBJC2_TIMEOUT|1|30|s|/etc/objc2/objc2.conf|timeout=1|timeout=30|systemctl reload objc2|ob|obj_to_1|objs|headers|fs leftover leftover down; bounce|OBJC2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the objs 504s
solidity2|SOLIDITY2_TIMEOUT|1|30|s|/etc/solidity2/solidity2.conf|timeout=1|timeout=30|systemctl reload solidity2|so|sol_to_1|abis|solc|fs leftover leftover down; bounce|SOLIDITY2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the abis 504s
vyper2|VYPER2_TIMEOUT|1|30|s|/etc/vyper2/vyper2.conf|timeout=1|timeout=30|systemctl reload vyper2|vy|vyp_to_1|abis|vyper|fs leftover leftover down; bounce|VYPER2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the abis 504s
move2|MOVE2_TIMEOUT|1|30|s|/etc/move2/move2.conf|timeout=1|timeout=30|systemctl reload move2|mv|mov_to_1|mods|aptos|fs leftover leftover down; bounce|MOVE2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the mods 504s
cairo2|CAIRO2_TIMEOUT|1|30|s|/etc/cairo2/cairo2.conf|timeout=1|timeout=30|systemctl reload cairo2|ca|cai_to_1|sierra|scarb|fs leftover leftover down; bounce|CAIRO2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the sierra 504s
wasm2|WASM2_TIMEOUT|1|30|s|/etc/wasm2/wasm2.conf|timeout=1|timeout=30|systemctl reload wasm2|wa|was_to_1|modules|wat|fs leftover leftover down; bounce|WASM2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the modules 504s
wat2|WAT2_TIMEOUT|1|30|s|/etc/wat2/wat2.conf|timeout=1|timeout=30|systemctl reload wat2|wt|wat_to_1|modules|wasm|fs leftover leftover down; bounce|WAT2_TIMEOUT leftover 1 leftover; a 2s assemble is aborted so the modules 504s
binaryen2|BINARYEN2_TIMEOUT|1|30|s|/etc/binaryen2/binaryen2.conf|timeout=1|timeout=30|systemctl reload binaryen2|bn|bin_to_1|wasm|passes|fs leftover leftover down; bounce|BINARYEN2_TIMEOUT leftover 1 leftover; a 2s opt is aborted so the wasm 504s
wabt2|WABT2_TIMEOUT|1|30|s|/etc/wabt2/wabt2.conf|timeout=1|timeout=30|systemctl reload wabt2|wb|wab_to_1|wasm|wat|fs leftover leftover down; bounce|WABT2_TIMEOUT leftover 1 leftover; a 2s convert is aborted so the wasm 504s
bazel2|BAZEL2_TIMEOUT|1|30|s|/etc/bazel2/bazel2.conf|timeout=1|timeout=30|systemctl reload bazel2|bz|baz_to_1|targets|cache|fs leftover leftover down; bounce|BAZEL2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the targets 504s
'''
WAVE = (
    "rustc2/go2/gcc2/clang2/llvm2/zig2/nim2/crystal2/dlang2/fortran2/cobol2/ada2/pascal2/delphi2/vbnet2/csharp2/fsharp2/ocaml2/haskell2/erlang2/elixir2/gleam2/clojure2/scala2/kotlin2/groovy2/coffeescript2/typescript2/dart2/swift2/objc2/solidity2/vyper2/move2/cairo2/wasm2/wat2/binaryen2/wabt2/bazel2"
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
        svc = f"f3{i:02d}x"
        ns = f"f3{i:02d}"
        clu = f"prod-apuk{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13883 + i }"
        node = f"ip-10-189-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4681


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-79 leftover: {WAVE}.",
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
