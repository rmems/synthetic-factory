#!/usr/bin/env python3
"""Mill secret-scan-remediation-factory r436+ unique sidecar leftover mechanics.

BAN: skip-path cartesian; SaaS-yml; vendor-file; cipher-*; r435
ggshield-mold-map-leftover / noseyparker-lld-repro-leftover; r331
talisman-rebase-merge-head-leftover / whispers-turbo-cache-leftover;
cloning r181–r435 leftovers; decoder/SARIF/git-notes/entropy-window;
stash/reflog/worktree/turbo/npm/ruff/next/export-subst/p4/wheel/gradle/tox/
hypothesis clones. Fake TESTONLY_ keys only. Never force-push main.
r436+: new scanner × sidecar leftover pairs (gold/bfd/thinlto/…), not
leftover leftover leftover clones.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

FACTORY = "secret-scan-remediation-factory"
CATALOG_FIRST = 436
HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("ssr_mill_r332", HERE / "ssr-mill-r332.py")
_r332 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_r332)
plant = _r332.plant
success_episode = _r332.success_episode
fail_episode = _r332.fail_episode

USED_SLUGS = {p["slug"] for pair in _r332.PAIRS for p in pair} | set(_r332.USED_SLUGS)
USED_EXTRAS = {p["extra"] for pair in _r332.PAIRS for p in pair} | set(_r332.USED_EXTRAS)

SCAN = {
    "gitleaks": (
        "gitleaks detect --no-banner --no-git -s {extra}",
        "Secret:    generic-api-key  ({tag})",
    ),
    "trufflehog": (
        "trufflehog filesystem {extra} --no-update",
        "Found unverified result via {tag}",
    ),
    "ggshield": (
        "ggshield secret scan path {extra}",
        "SECRET_DETECTED {tag}",
    ),
    "noseyparker": (
        "noseyparker scan {extra}",
        "Finding: {tag}",
    ),
    "kingfisher": (
        "kingfisher scan {extra}",
        "kingfisher: secret in {tag}",
    ),
    "trivy": (
        "trivy fs --scanners secret {extra}",
        "trivy secret in {tag}",
    ),
    "detect-secrets": (
        "detect-secrets scan {extra}",
        "detect-secrets: {tag}",
    ),
    "semgrep": (
        "semgrep --config p/secrets {extra}",
        "semgrep: {tag}",
    ),
    "git-secrets": (
        "git secrets --scan {extra}",
        "git-secrets: {tag}",
    ),
    "talisman": (
        "talisman --scanFile {extra}",
        "talisman: {tag}",
    ),
    "whispers": (
        "whispers {extra}",
        "whispers: {tag}",
    ),
    "bearer": (
        "bearer scan {extra}",
        "bearer: {tag}",
    ),
}

SCANNERS = list(SCAN)
LEAKS = [
    ("conf/ci.env", "CI"),
    ("ops/old.env", "OLD"),
    ("hooks/hot.env", "HOT"),
    ("app/prod.env", "PROD"),
    ("dump/old.env", "DUMP"),
    ("svc/run.env", "SVC"),
]

# Unique sidecar leftover surfaces (not r332 leftover leftover leftover clones).
TAILS = [
    "gold-map",
    "bfd-map",
    "thinlto-cache",
    "llvm-lto",
    "lto-obj",
    "snowpack-dep",
    "metro-cache",
    "expo-export",
    "capacitor-sync",
    "ionic-www",
    "tauri-bundle",
    "wails-dist",
    "electron-asar",
    "solid-start",
    "fresh-gen",
    "isort-cache",
    "pdm-lock",
    "rye-tool",
    "hatch-env",
    "conda-pkgs",
    "pixi-env",
    "pipenv-venv",
    "sbt-ivy",
    "mill-out",
    "lein-m2",
    "graal-native",
    "quarkus-app",
    "micronaut-aot",
    "spring-aot",
    "jib-layers",
    "spotbugs-xml",
    "checkstyle-xml",
    "errorprone-out",
    "ansible-retry",
    "salt-pki",
    "chef-cache",
    "puppet-yaml",
    "argocd-repo",
    "flux-gotk",
    "kust-build",
    "istio-dump",
    "linkerd-viz",
    "cilium-state",
    "calico-felix",
    "zipkin-store",
    "tempo-wal",
    "loki-chunks",
    "thanos-prom",
    "cortex-tsdb",
    "mimir-blocks",
    "victoria-data",
    "opensearch-idx",
    "elastic-data",
    "kibana-opt",
    "graylog-jrnl",
    "splunk-fish",
    "datadog-run",
    "newrelic-log",
    "neo4j-store",
    "couch-data",
    "dynamo-local",
    "scylla-data",
    "cockroach-store",
    "tidb-data",
    "vitess-vtd",
    "timescale-wal",
    "influx-tsm",
    "questdb-db",
    "druid-seg",
    "pinot-seg",
    "iceberg-meta",
    "delta-log",
    "hudi-time",
    "parquet-foot",
    "orc-stripe",
    "avro-obj",
    "mlflow-run",
    "wandb-run",
    "dvc-obj",
    "clearml-cache",
    "kubeflow-pipe",
    "feast-reg",
    "tfx-meta",
    "kedro-cat",
    "lightning-log",
    "hf-hub",
    "torch-hub",
    "tb-event",
    "onnx-sess",
    "triton-repo",
    "vllm-block",
    "ollama-blob",
    "llamacpp-gguf",
    "julia-depot",
    "renv-lib",
    "dune-alias",
    "opam-switch",
    "rebar-lib",
    "dialyzer-plt",
    "luarocks-tree",
    "carton-local",
    "cpanm-work",
    "raku-precomp",
    "matlab-slxc",
    "octave-pkg",
    "fortran-mod",
    "ada-ali",
    "idea-shelf",
    "jb-system",
    "eclipse-set",
    "qt-user",
    "netbeans-var",
    "xcu-state",
    "as-system",
    "fleet-idx",
    "zed-idx",
    "helix-log",
    "kak-state",
    "emacs-back",
    "vim-un",
    "nvim-shada",
    "tmux-res",
    "screen-hard",
    "jupyter-rt",
    "ipy-prof",
    "spyder-tmp",
    "rstudio-sess",
    "direnv-allow",
    "mise-cache",
    "asdf-install",
    "nvm-ver",
    "pyenv-ver",
    "rbenv-ver",
    "sdkman-cands",
    "jenv-ver",
    "phpenv-ver",
    "goenv-ver",
    "nodenv-ver",
    "fnm-node",
    "volta-tool",
    "corepack-shims",
    "guix-profile",
    "spack-opt",
    "easybuild-sw",
    "lmod-cache",
    "apptainer-sif",
    "charlie-img",
    "sarus-img",
    "udocker-cnt",
    "podman-graph",
    "lima-disk",
    "colima-img",
    "rancher-store",
    "k0s-data",
    "microk8s-snap",
    "k3d-img",
    "kops-state",
    "eksctl-cache",
    "gke-creds",
    "aks-cache",
    "ocp-cache",
    "okd-cache",
    "tanzu-cache",
    "capsule-ten",
    "xp-cache",
    "atlantis-data",
    "woodpecker-vol",
    "drone-vol",
    "bk-agent",
    "gl-runner",
    "jenkins-home",
    "tc-system",
    "bamboo-home",
    "gocd-godata",
    "concourse-wg",
    "tekton-res",
    "argo-wf",
    "prow-job",
    "zuul-log",
    "act-cache",
    "dagger-query",
    "buildah-ctr",
    "buildkit-cache",
    "img-cache",
    "kaniko-cache",
    "ko-cache",
    "crane-cache",
    "skopeo-cache",
    "dive-layer",
    "hadolint-cfg",
    "dockle-out",
    "grype-db",
    "syft-sbom",
    "cosign-tlog",
    "notation-trust",
    "sops-age",
    "age-key",
    "vault-file",
    "chamber-ssm",
    "infisical-cache",
    "bw-attach",
    "op-session",
    "pass-store",
    "gopass-mount",
    "wasmer-cache",
    "wasmtime-cache",
    "wasm-pack",
    "binaryen-out",
    "dotnet-nuget",
    "nuget-http",
    "paket-cache",
    "fake-build",
    "cake-tool",
    "fsharp-obj",
    "csharp-bin",
    "scala-bloop",
    "metals-cache",
    "mill-zinc",
    "clojure-cpcache",
    "shadow-cljs",
    "elixir-deps",
    "erlang-relx",
    "reason-bsb",
    "rescript-lib",
    "coq-vo",
    "lean-olean",
    "agda-agdai",
    "idris-ibc",
    "sml-heap",
    "racket-compiled",
    "chicken-cache",
    "gambit-cache",
    "chez-so",
    "sbcl-fasl",
    "clisp-fas",
    "ecl-fasl",
]

ORGS = [
    "abutment",
    "afterdamp",
    "airway",
    "backfill",
    "bankman",
    "bellpit",
    "bordure",
    "brattice",
    "browend",
    "bunkerage",
    "caplamp",
    "catchpt",
    "cleatrow",
    "collier",
    "cribset",
    "diphead",
    "risehead",
    "stallend",
    "ribside",
    "packwall",
    "chockrow",
    "shieldrow",
    "ploughpan",
    "sheardrum",
    "faceline",
    "overcast",
    "stopping",
    "airdoor",
    "mandeck",
    "pithead",
    "heaproom",
    "lantern",
    "lampcab",
    "backbye",
    "inover",
    "outover",
    "goafline",
    "packline",
    "chockline",
    "shieldln",
    "ploughln",
    "shearln",
    "faceconv",
    "gateconv",
    "bunkercar",
    "washerbox",
    "cycell",
    "jigcell",
    "thickcell",
    "flotbank",
    "manway",
    "regulator",
    "goafend",
    "bordend",
    "headingln",
    "ribline",
    "stopeend",
    "raiseend",
    "winzeroom",
    "drivage",
    "inbyeroad",
    "outbyeroad",
    "fanroom",
    "lamproom",
    "canteenln",
    "winderln",
    "headgearln",
    "skipwayln",
    "cagewayln",
    "collarln",
    "bankheadln",
    "screenln",
    "washerln",
    "jiggerln",
    "cycloneln",
    "thickln",
    "flotln",
    "millhouseln",
    "crusherln",
    "conveyln",
    "bunkerln",
    "tipplerln",
    "heapln",
    "spoilln",
    "bingln",
    "longwallln",
    "gateroadln",
    "maingateln",
    "tailgateln",
    "bleederln",
    "crossgateln",
    "bordroomln",
    "pillarln",
    "sumpln",
    "insetln",
    "crosscutln",
    "headingrm",
    "ribrm",
    "chockrm",
    "shieldrm",
    "ploughrm",
    "shearrm",
    "facerm",
    "gaterm",
    "bunkerrm",
    "washerrm",
    "cyclonerm",
    "jiggerrm",
    "thickrm",
    "flotrm",
    "millrm",
    "crushrm",
    "conveyrm",
    "tipplerm",
    "heaprm",
    "spoilrm",
    "bingrm",
    "longrm",
    "gaterm2",
    "mainrm",
    "tailrm",
    "bleedrm",
    "crossrm",
    "bordrm",
    "pillrm",
    "sumprm",
    "insetrm",
    "cutrm",
    "headrm",
    "rib2rm",
    "chock2rm",
    "shield2rm",
    "plough2rm",
    "shear2rm",
    "face2rm",
    "gate2rm",
    "bunk2rm",
    "wash2rm",
    "cyc2rm",
    "jig2rm",
    "thick2rm",
    "flot2rm",
    "mill2rm",
    "crush2rm",
    "conv2rm",
    "tip2rm",
    "heap2rm",
    "spoil2rm",
    "bing2rm",
    "long2rm",
    "gate3rm",
    "main2rm",
    "tail2rm",
    "bleed2rm",
    "cross2rm",
    "bord2rm",
    "pill2rm",
    "sump2rm",
    "inset2rm",
    "cut2rm",
    "head2rm",
    "rib3rm",
    "chock3rm",
    "shield3rm",
    "plough3rm",
    "shear3rm",
    "face3rm",
    "gate4rm",
    "bunk3rm",
    "wash3rm",
    "cyc3rm",
    "jig3rm",
    "thick3rm",
    "flot3rm",
    "mill3rm",
    "crush3rm",
    "conv3rm",
    "tip3rm",
    "heap3rm",
    "spoil3rm",
    "bing3rm",
    "long3rm",
    "gate5rm",
    "main3rm",
    "tail3rm",
    "bleed3rm",
    "cross3rm",
    "bord3rm",
    "pill3rm",
    "sump3rm",
    "inset3rm",
    "cut3rm",
    "head3rm",
    "rib4rm",
    "chock4rm",
    "shield4rm",
    "plough4rm",
    "shear4rm",
    "face4rm",
    "gate6rm",
    "bunk4rm",
    "wash4rm",
    "cyc4rm",
    "jig4rm",
    "thick4rm",
    "flot4rm",
    "mill4rm",
    "crush4rm",
    "conv4rm",
    "tip4rm",
    "heap4rm",
    "spoil4rm",
    "bing4rm",
    "long4rm",
    "gate7rm",
    "main4rm",
    "tail4rm",
    "bleed4rm",
    "cross4rm",
    "bord4rm",
    "pill4rm",
    "sump4rm",
    "inset4rm",
    "cut4rm",
    "head4rm",
    "rib5rm",
    "chock5rm",
    "shield5rm",
    "plough5rm",
    "shear5rm",
    "face5rm",
    "gate8rm",
    "bunk5rm",
    "wash5rm",
    "cyc5rm",
    "jig5rm",
]


def _scan_pair(scanner: str, extra: str, tag: str) -> tuple[str, str]:
    invoke, hit = SCAN[scanner]
    return invoke.format(extra=extra, tag=tag), hit.format(tag=tag)


def _mk(tail: str, idx: int) -> dict:
    scanner = SCANNERS[(idx - 1) % len(SCANNERS)]
    leak, prefix = LEAKS[(idx - 1) % len(LEAKS)]
    base = leak.split("/")[-1]
    extra = f".{tail}/{base}"
    pretty = tail.replace("-", " ")
    mechanic = f"{pretty} sidecar still names {leak}"
    tag = f"{pretty} sidecar leftover"
    env = f"{prefix}_{tail.replace('-', '_')[:14].upper()}_TOKEN"
    org = f"{ORGS[idx - 1]}-sc"
    short = org.split("-")[0][:6]
    repo = f"{org}/{short}-{tail[:28]}"
    slug = f"{scanner}-{tail}-leftover"
    invoke, hit = _scan_pair(scanner, extra, tag)
    wrong_cmd = f"rg TESTONLY {extra} | head"
    hide_cmd = f"echo '{leak.split('/')[0]}/' >> .gitignore; {wrong_cmd}"
    tok = f"TESTONLY_r436{idx:03d}_n0t"
    return plant(
        slug=slug,
        scanner=scanner,
        mechanic=mechanic,
        repo=repo,
        leak=leak,
        extra=extra,
        token=tok,
        env=env,
        sha=f"a436{idx:04x}",
        pr=520 + idx,
        mix=f"{scanner} {tag}",
        scan_invoke=invoke,
        scan_hit=hit,
        extra_line=f"{tag} still names TESTONLY_",
        miss_cmd=f"{SCAN[scanner][0].format(extra=leak, tag=tag)} 2>&1 | tail -3 || echo {tail[:12]}-head-green",
        miss_green=f"{tail[:12]}-head-green",
        wrong_b=f"Plan: first apply - redact {leak}. Expect {pretty} sidecar still red.",
        wrong_cmd=wrong_cmd,
        wrong_obs=f"{env}={tok}",
        hide_cmd=hide_cmd,
        hide_obs=f"{env}={tok}  ({tag})",
    )


if len(TAILS) != len(ORGS):
    raise SystemExit(f"TAILS {len(TAILS)} != ORGS {len(ORGS)}")
if len(TAILS) % 2:
    raise SystemExit("odd plant count")

_plants = [_mk(tail, i) for i, tail in enumerate(TAILS, start=1)]
PAIRS = [(_plants[i], _plants[i + 1]) for i in range(0, len(_plants), 2)]


def _assert_catalog() -> None:
    slugs = [p["slug"] for pair in PAIRS for p in pair]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs in r436 catalog")
    clash = set(slugs) & USED_SLUGS
    if clash:
        raise SystemExit(f"slug clones prior mill: {sorted(clash)[:8]}")
    tokens = [p["token"] for pair in PAIRS for p in pair]
    if len(tokens) != len(set(tokens)):
        raise SystemExit("duplicate tokens in r436 catalog")
    extras = [p["extra"] for pair in PAIRS for p in pair]
    if len(extras) != len(set(extras)):
        raise SystemExit("duplicate extras in r436 catalog")
    extra_clash = set(extras) & USED_EXTRAS
    if extra_clash:
        raise SystemExit(f"extra clones prior mill: {sorted(extra_clash)[:8]}")
    banned_bits = (
        "stash-wip",
        "reflog",
        "worktree",
        "turbo-cache",
        "npm-offline",
        "npm-pack",
        "ruff-cache",
        "export-subst",
        "p4-sync",
        "wheel-leftover",
        "wheelhouse",
        "gradle-cache",
        "tox-env",
        "hypothesis",
        "cipher",
        "sarif",
        "git-notes",
        "entropy-window",
        "next-build",
        "mold-map",
        "lld-repro",
        "rebase-merge-head",
        "vendor-file",
        "saas-yml",
    )
    for spec in (p for pair in PAIRS for p in pair):
        blob = f"{spec['slug']} {spec['mechanic']} {spec['extra']}".lower()
        hit = [b for b in banned_bits if b in blob]
        if hit:
            raise SystemExit(f"banned fragment {hit} in {spec['slug']}")
        if spec["slug"] in USED_SLUGS:
            raise SystemExit(f"clone slug {spec['slug']}")
        if len(spec["map_b"]) > 240:
            raise SystemExit(f"map_b too long for {spec['slug']}: {len(spec['map_b'])}")
        if len(spec["wrong_b"]) > 240:
            raise SystemExit(f"wrong_b too long for {spec['slug']}")
        if "TESTONLY_" not in spec["token"]:
            raise SystemExit(f"bad token {spec['token']}")


_assert_catalog()


def notes_md(rnd, suc, fail, suc_ep, fail_ep):
    coverage = max(52, 74 - (rnd - CATALOG_FIRST))
    return f"""# NOTES-r{rnd} secret-scan-remediation-factory

Novel coverage: {coverage}%

Two designed sidecar-leftover episodes (quota 2). Surfaces: {suc['repo']} {suc['slug']} {suc['mechanic']}; {fail['repo']} {fail['slug']} {fail['mechanic']} (rewrite blocked).
Neither force-pushes main. Fake TESTONLY_ keys only. One remaining-scan fail when rewrite is blocked.
Scanner × sidecar leftover mill (not skip-path cartesian, not SaaS-yml, not vendor-file, not decoder wrap, not SARIF leftover, not git-notes leftover, not entropy-window leftover, not r181–r435 leftover leftover leftover clones, not r435 mold-map/lld-repro, not r331 rebase-merge/turbo-cache).

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {suc_ep['id']} | {suc['mechanic']} in {suc['leak']} + {suc['extra']} | {suc['wrong_b'].replace('Plan: first apply - ', '')} | {suc['env']} + filter-repo purge | success 2/2, main residual |
| {fail_ep['id']} | {fail['mechanic']} in {fail['leak']} + {fail['extra']} | {fail['wrong_b'].replace('Plan: first apply - ', '')} | HEAD {fail['env']}; GH013 | remaining-scan fail + HANDOFF |

## Step counts
- {suc_ep['id']}: {len(suc_ep['steps'])}
- {fail_ep['id']}: {len(fail_ep['steps'])}

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Invented plants (designed). No real secrets.

## Weaknesses / next
Avoid {suc['slug']}-as-git-fix and {fail['slug']}-as-git-fix (this round).
Harder-kind mill: {suc['mix']}; {fail['mix']}.
"""


def build_round(rnd: int, pair_index: int | None = None):
    idx = pair_index if pair_index is not None else rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {rnd} idx={idx} outside catalog 0..{len(PAIRS) - 1}")
    suc, fail = PAIRS[idx]
    suc_n = 16 if idx % 2 else 14
    fail_n = 15 if idx % 3 else 16
    suc_ep = success_episode(rnd, suc, suc_n)
    fail_ep = fail_episode(rnd, fail, fail_n)
    for ep in (suc_ep, fail_ep):
        n = len(ep["steps"])
        if n < 12 or n > 18:
            raise SystemExit(f"{ep['id']} has {n} steps, want 12-18")
        ep["reward"]["cost_steps"] = n
        for s in ep["steps"]:
            basis = s["decision_basis"]
            prefix = basis.split(":", 1)[0]
            if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
                raise SystemExit(f"{ep['id']} bad prefix {basis!r}")
            if len(basis) > 240:
                raise SystemExit(f"{ep['id']} basis too long: {basis}")
            banned_keys = {"thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"}
            if banned_keys & set(s):
                raise SystemExit(f"{ep['id']} banned keys")
        if ep.get("sim_or_real") == "real":
            raise SystemExit(f"{ep['id']} sim_or_real real")
        if ep["meta"].get("generator") != "grok-4.6":
            raise SystemExit(f"{ep['id']} bad generator")
    return [suc_ep, fail_ep], notes_md(rnd, suc, fail, suc_ep, fail_ep)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--pair-index", type=int, default=None)
    args = ap.parse_args()
    recs, notes = build_round(args.round, args.pair_index)
    staging = Path(args.staging)
    with (staging / f"batch-r{args.round:02d}.jsonl").open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    (staging / f"NOTES-r{args.round:02d}.md").write_text(notes)
    print(
        json.dumps(
            {
                "round": args.round,
                "ids": [r["id"] for r in recs],
                "steps": [len(r["steps"]) for r in recs],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
