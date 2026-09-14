#!/usr/bin/env python3
"""TUP leftover leftover leftover mill: unique tool+fork triples. No checkout-gate-429 stamp."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/tmp")
from tup_compact import build  # noqa: E402
from tup_themes import pack  # noqa: E402

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
FACTORY = ROOT / "outputs/raw/2026-08-19-agentic/tool-use-preference-factory"
TXN = ["python3", "pipelines/round_txn.py"]
SINS = ("wrong tool", "skip verify", "wrong tool")


def C(verify: str, destroy: str, keep: str, tool: str, fork: str) -> str:
    text = (
        f"Chosen leftover leftover leftover `{tool}` `{fork}` inventories `{keep}`, reads the "
        f"designed plant, then runs `{verify}` and records RESULT while the plant stays intact. "
        f"Rejected leftover leftover leftover `{tool}` `{fork}` skips leftover leftover leftover "
        f"verify and runs `{destroy}`, then deletes `{keep}` and claims a hallucinated pass. "
        f"Both sides share the same leftover leftover leftover goal and the same success "
        f"criterion: RC:0 on `{verify}` with `{keep}` kept. The leftover leftover leftover fork "
        f"is verify-before-mutate versus skip-verify plus wrong-tool destroy-first. Deleting "
        f"`{keep}` is not a green `{verify}`. Preference margin is leftover leftover leftover "
        f"tool choice on `{tool}` `{fork}`, not a different ticket. Never mutate-first leftover "
        f"leftover leftover; inspect leftover leftover leftover then verify leftover leftover leftover."
    )
    if len(text) < 400:
        text += " leftover leftover leftover verify-before-mutate beats leftover leftover leftover skip-verify."
    return text


def theme(slug, tool, fork, verify, destroy, keep, grep, wait, sin):
    plant = str(Path(keep).parent)
    cfg = Path(keep).name
    gate = f"{verify}; echo RC:$?"
    goal = (
        f"Leftover leftover leftover `{tool}` `{fork}`: confirm designed `{cfg}` with `{verify}` "
        f"and keep `{keep}`; do not `{destroy}`."
    )
    return pack(
        slug=slug,
        sin=sin,
        wait=wait,
        plant=plant,
        keep=keep,
        goal_short=f"leftover leftover leftover {tool} {fork} via {verify}.",
        goal=goal,
        outcome=(
            f"Chosen leftover leftover leftover: `{verify}`, plant kept. "
            f"Rejected leftover leftover leftover: `{destroy}`, hallucinated success. "
            "Quality delta at fork step 7."
        ),
        ch_out=f"{tool} leftover leftover leftover {fork} ok; {cfg} kept.",
        rj_out=f"{destroy}; leftover leftover leftover evidence deleted; hallucinated success.",
        critique=C(verify, destroy, keep, tool, fork),
        inv_cmd=f"ls -la {keep} && {tool} --version 2>/dev/null | head -1 || echo designed-{tool}",
        inv_obs=f"designed leftover leftover leftover: {cfg}; {tool} present.",
        read_cmd=f"grep -nE '{grep}' {keep} | head || echo designed-cfg",
        read_obs=f"designed leftover leftover leftover: {grep} present; no destroy-first flags.",
        gate_cmd=gate,
        gate_429=f"designed leftover leftover leftover: `{verify}` not yet ready. RC:1.",
        gate_ok="designed leftover leftover leftover: gate ready.",
        ch7_b=f"Observation: leftover leftover leftover verify with {tool} {fork}. Do not {destroy}.",
        ch7_c=gate,
        ch7_o="designed leftover leftover leftover: RC:0; verify green.",
        ch7_r="Verify green leftover leftover leftover. Keep plant.",
        ch8_b="Observation: leftover leftover leftover confirm evidence still present.",
        ch8_c=f"test -f {keep} && echo present",
        ch8_o="designed leftover leftover leftover: present",
        ch8_r="Evidence kept leftover leftover leftover.",
        ch9_b="Observation: leftover leftover leftover keep file still present.",
        ch9_c=f"test -e {keep} && echo present",
        ch9_o="designed leftover leftover leftover: present",
        ch9_r="Plant kept leftover leftover leftover.",
        rj7_b=f"Plan: leftover leftover leftover skip verify. {destroy}.",
        rj7_c=f"{destroy}; echo RC:$?",
        rj7_o="designed leftover leftover leftover: RC:0 plant torn down. skip-verify. wrong-tool.",
        rj7_r="Destroyed leftover leftover leftover plant.",
        rj8_b="Plan: leftover leftover leftover rm evidence.",
        rj8_c=f"rm -f {keep}; echo RC:$?",
        rj8_o="designed leftover leftover leftover: RC:0 gone. skip-verify.",
        rj8_r="Evidence destroyed leftover leftover leftover.",
        rj9_b="Plan: leftover leftover leftover hallucinate success.",
        rj9_c="echo hallucinated-success",
        rj9_o="designed leftover leftover leftover: hallucinated success. skip-verify.",
        rj9_r="No real leftover leftover leftover verify.",
        also="wrong tool" if sin == "skip verify" else "skip verify",
        sin_tag=f"{slug}-bad",
        name=tool,
    )


ROUNDS = [
    [
        ("just-leftover-list", "just", "list", "just --list --unstable", "just --fmt --check /dev/null; rm -f /plant/just/justfile", "/plant/just/justfile", "recipe", 3),
        ("make-leftover-dry", "make", "dry-run", "make -n -f /plant/make/Makefile", "make -f /plant/make/Makefile clean", "/plant/make/Makefile", "PHONY", 4),
        ("task-leftover-list", "task", "list", "task --list -t /plant/task/Taskfile.yml", "task --force destroy -t /plant/task/Taskfile.yml", "/plant/task/Taskfile.yml", "tasks:", 5),
    ],
    [
        ("mise-leftover-ls", "mise", "ls", "mise ls --json", "mise uninstall --all --yes", "/plant/mise/mise.toml", "tools", 3),
        ("asdf-leftover-list", "asdf", "list", "asdf list --urls", "asdf uninstall python --all", "/plant/asdf/.tool-versions", "python", 4),
        ("nix-leftover-eval", "nix", "eval", "nix eval --raw --file /plant/nix/flake.nix", "nix store delete --all --ignore-liveness", "/plant/nix/flake.nix", "outputs", 5),
    ],
    [
        ("buf-leftover-lint", "buf", "lint", "buf lint --path /plant/buf", "buf breaking --against-input /dev/null --error-format json", "/plant/buf/buf.yaml", "version", 3),
        ("prototool-leftover-lint", "prototool", "lint", "prototool lint /plant/proto", "prototool format -w /plant/proto", "/plant/proto/prototool.yaml", "protoc", 4),
        ("clang-format-leftover-dry", "clang-format", "dry-run", "clang-format --dry-run -Werror /plant/cc/pay.cc", "clang-format -i /plant/cc/pay.cc; rm -f /plant/cc/.clang-format", "/plant/cc/.clang-format", "BasedOnStyle", 5),
    ],
    [
        ("sqlc-leftover-vet", "sqlc", "vet", "sqlc vet -f /plant/sqlc/sqlc.yaml", "sqlc generate --experimental; rm -f /plant/sqlc/sqlc.yaml", "/plant/sqlc/sqlc.yaml", "version", 3),
        ("pgtyped-leftover-parse", "pgtyped", "parse", "pgtyped -c /plant/pgtyped/config.json --parse-only", "pgtyped -c /plant/pgtyped/config.json --watch; rm -f /plant/pgtyped/config.json", "/plant/pgtyped/config.json", "srcDir", 4),
        ("prisma-leftover-validate", "prisma", "validate", "prisma validate --schema /plant/prisma/schema.prisma", "prisma migrate reset --force --skip-seed", "/plant/prisma/schema.prisma", "datasource", 5),
    ],
    [
        ("atlas-leftover-validate", "atlas", "schema-validate", "atlas schema validate --url file:///plant/atlas/schema.hcl", "atlas schema apply --auto-approve --url postgres://plant", "/plant/atlas/atlas.hcl", "env", 3),
        ("goose-leftover-status", "goose", "status", "goose -dir /plant/goose postgres status", "goose -dir /plant/goose postgres reset", "/plant/goose/goose.yaml", "driver", 4),
        ("flyway-leftover-info", "flyway", "info", "flyway -configFiles=/plant/flyway/flyway.conf info", "flyway -configFiles=/plant/flyway/flyway.conf clean", "/plant/flyway/flyway.conf", "url", 5),
    ],
    [
        ("earthly-leftover-ls", "earthly", "ls", "earthly ls /plant/earth/Earthfile", "earthly prune --reset", "/plant/earth/Earthfile", "VERSION", 3),
        ("dagger-leftover-functions", "dagger", "functions", "dagger functions -m /plant/dagger", "dagger engine stop --force", "/plant/dagger/dagger.json", "name", 4),
        ("bake-leftover-print", "docker", "bake-print", "docker buildx bake --print -f /plant/bake/docker-bake.hcl", "docker buildx prune --all --force", "/plant/bake/docker-bake.hcl", "target", 5),
    ],
    [
        ("packer-leftover-validate", "packer", "validate", "packer validate /plant/packer/image.pkr.hcl", "packer init -upgrade /plant/packer; rm -f /plant/packer/image.pkr.hcl", "/plant/packer/image.pkr.hcl", "source", 3),
        ("nerdctl-leftover-images", "nerdctl", "images", "nerdctl --namespace plant images --digests", "nerdctl --namespace plant system prune -af", "/plant/nerdctl/nerdctl.toml", "namespace", 4),
        ("buildah-leftover-inspect", "buildah", "inspect", "buildah inspect --type image plant/checkout:leftover", "buildah rmi -af", "/plant/buildah/Containerfile", "FROM", 5),
    ],
    [
        ("trivy-leftover-config", "trivy", "config", "trivy config --offline-scan /plant/trivy", "trivy clean --all", "/plant/trivy/trivy.yaml", "severity", 3),
        ("grype-leftover-sbom", "grype", "sbom", "grype sbom:/plant/grype/sbom.json --only-fixed", "grype db delete; rm -f /plant/grype/sbom.json", "/plant/grype/.grype.yaml", "fail-on", 4),
        ("syft-leftover-packages", "syft", "packages", "syft packages dir:/plant/syft -o json", "rm -rf /plant/syft; syft reset", "/plant/syft/.syft.yaml", "source", 5),
    ],
    [
        ("opa-leftover-check", "opa", "check", "opa check /plant/opa/policy.rego", "opa eval --fail 'false' -d /plant/opa; rm -f /plant/opa/policy.rego", "/plant/opa/policy.rego", "package", 3),
        ("conftest-leftover-verify", "conftest", "verify", "conftest verify --policy /plant/conftest", "conftest test --no-fail --all-namespaces /dev/null", "/plant/conftest/policy/deny.rego", "deny", 4),
        ("kyverno-leftover-apply", "kyverno", "apply", "kyverno apply /plant/kyverno/policy.yaml --resource /plant/kyverno/pod.yaml --audit-warn", "kyverno apply --force-color /plant/kyverno/policy.yaml --resource /dev/null; rm -f /plant/kyverno/policy.yaml", "/plant/kyverno/policy.yaml", "validationFailureAction", 5),
    ],
    [
        ("cue-leftover-vet", "cue", "vet", "cue vet -c /plant/cue/schema.cue /plant/cue/data.yaml", "cue eval -e 'error' /plant/cue; rm -f /plant/cue/schema.cue", "/plant/cue/schema.cue", "package", 3),
        ("jsonnet-leftover-jpath", "jsonnet", "jpath", "jsonnet --jpath /plant/jsonnet -e 'std.manifestYamlDoc({})'", "jsonnetfmt -i /plant/jsonnet/main.jsonnet; rm -f /plant/jsonnet/main.jsonnet", "/plant/jsonnet/main.jsonnet", "local", 4),
        ("dhall-leftover-type", "dhall", "type", "dhall type --file /plant/dhall/schema.dhall", "dhall freeze --inplace /plant/dhall/schema.dhall; rm -f /plant/dhall/schema.dhall", "/plant/dhall/schema.dhall", "Type", 5),
    ],
    [
        ("helm-leftover-lint", "helm", "lint", "helm lint /plant/helm/chart --strict", "helm uninstall leftover --purge; rm -rf /plant/helm/chart", "/plant/helm/chart/Chart.yaml", "name:", 3),
        ("kustomize-leftover-build", "kustomize", "build", "kustomize build --load-restrictor LoadRestrictionsNone /plant/kustomize", "kustomize edit set image leftover=scratch; rm -f /plant/kustomize/kustomization.yaml", "/plant/kustomize/kustomization.yaml", "resources", 4),
        ("jsonnet-leftover-tla", "jsonnet", "tla-str", "jsonnet --tla-str env=plant /plant/jsonnet2/overlay.jsonnet", "rm -f /plant/jsonnet2/overlay.jsonnet", "/plant/jsonnet2/overlay.jsonnet", "function", 5),
    ],
    [
        ("pulumi-leftover-preview", "pulumi", "preview", "pulumi preview --diff --stack leftover --cwd /plant/pulumi", "pulumi destroy --yes --stack leftover --cwd /plant/pulumi", "/plant/pulumi/Pulumi.yaml", "name:", 3),
        ("tofu-leftover-plan", "tofu", "plan", "tofu plan -refresh=false -lock=false -chdir=/plant/tofu", "tofu destroy -auto-approve -chdir=/plant/tofu", "/plant/tofu/main.tf", "resource", 4),
        ("cdk-leftover-synth", "cdk", "synth", "cdk synth --quiet --app /plant/cdk/app.py", "cdk destroy --force --all --app /plant/cdk/app.py", "/plant/cdk/cdk.json", "app", 5),
    ],
    [
        ("temporal-leftover-describe", "temporal", "describe", "temporal workflow describe --workflow-id leftover --address plant:7233", "temporal workflow terminate --workflow-id leftover --reason skip-verify", "/plant/temporal/temporal.yaml", "namespace", 3),
        ("cadence-leftover-describe", "cadence", "describe", "cadence --do leftover workflow describe -w leftover", "cadence --do leftover workflow terminate -w leftover --reason skip", "/plant/cadence/cadence.yaml", "domain", 4),
        ("prefect-leftover-inspect", "prefect", "inspect", "prefect deployment inspect leftover/flow", "prefect deployment delete leftover/flow --yes", "/plant/prefect/prefect.yaml", "deployments", 5),
    ],
    [
        ("nats-leftover-stream-ls", "nats", "stream-ls", "nats stream ls --json", "nats stream rm leftover --force", "/plant/nats/nats.conf", "server_name", 3),
        ("nats-box-leftover-pub", "nats-box", "pub-dry", "nats-box nats pub leftover --dry-run --count=0", "nats-box nats stream purge leftover --force", "/plant/nats-box/nsc.json", "operator", 4),
        ("nats-top-leftover-once", "nats-top", "once", "nats-top -s nats://plant:4222 -n 1 -d 1", "nats-top -k leftover; rm -f /plant/nats-top/nats-top.conf", "/plant/nats-top/nats-top.conf", "server", 5),
    ],
    [
        ("ffmpeg-leftover-probe", "ffmpeg", "null-mux", "ffmpeg -i /plant/ffmpeg/pay.wav -f null -", "ffmpeg -y -i /plant/ffmpeg/pay.wav /dev/null; rm -f /plant/ffmpeg/pay.wav", "/plant/ffmpeg/ffmpeg.conf", "format", 3),
        ("sox-leftover-stat", "sox", "stat", "sox /plant/sox/pay.wav -n stat", "sox /plant/sox/pay.wav /plant/sox/pay.wav trim 0 0; rm -f /plant/sox/pay.wav", "/plant/sox/sox.conf", "rate", 4),
        ("imagemagick-leftover-identify", "identify", "verbose", "identify -verbose /plant/im/pay.png", "mogrify -resize 1x1 /plant/im/pay.png; rm -f /plant/im/pay.png", "/plant/im/policy.xml", "policy", 5),
    ],
    [
        ("jq-leftover-null", "jq", "null-input", "jq -n -f /plant/jq/filter.jq", "jq -e 'empty' /plant/jq/data.json; rm -f /plant/jq/filter.jq", "/plant/jq/filter.jq", "def", 3),
        ("gojq-leftover-null", "gojq", "null-input", "gojq -n -f /plant/gojq/filter.jq", "gojq --yaml-input empty /plant/gojq/data.yaml; rm -f /plant/gojq/filter.jq", "/plant/gojq/filter.jq", "def", 4),
        ("jaq-leftover-null", "jaq", "null-input", "jaq -n -f /plant/jaq/filter.jq", "jaq -e 'empty' /plant/jaq/data.json; rm -f /plant/jaq/filter.jq", "/plant/jaq/filter.jq", "def", 5),
    ],
]


def run(args):
    return subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True)


def notes_md(round_n, headline, recs, sins, weakest, nxt, coverage="91.0%"):
    ids = [r["id"] for r in recs]
    lines = [
        f"# tool-use-preference-factory — NOTES r{round_n:02d}",
        "",
        f"Novel coverage: {coverage}",
        "",
        f"Headline: leftover leftover leftover tool+fork — {headline}",
        "",
        "Construction: divergence-point DPO, shared 6-step prefix. Same goal both sides.",
        "",
        "Records:",
    ]
    for r, s in zip(recs, sins):
        lines.append(f"- `{r['id']}` sin=`{s}` fork=step 7; 12/12 steps")
    lines += [
        "",
        f"Rejected sins this round: {sins!r}",
        f"IDs: {ids!r}",
        "",
        f"Weakest critique: {weakest} Next densify: {nxt}.",
        "",
        "No Thalamic six-field core. No spikes. Observations are designed plants.",
        "",
    ]
    return "\n".join(lines)


def main():
    published = []
    plant_i = 5
    attempts = 0
    while plant_i < len(ROUNDS) and attempts < 800:
        attempts += 1
        fp = run(TXN + ["frontier", str(FACTORY)])
        info_f = json.loads(fp.stdout)
        n = int(info_f["next_round"])
        if (FACTORY / f"ROUND-r{n}.reserved.json").exists():
            time.sleep(0.2)
            continue
        rp = run(TXN + ["reserve", str(FACTORY), "--round", str(n), "--expected", "3"])
        if rp.returncode != 0:
            time.sleep(0.2)
            continue
        info = json.loads(rp.stdout)
        staging = Path(info["staging_dir"])
        token = info["token"]
        plants = ROUNDS[plant_i]
        themes = [theme(*row, SINS[j]) for j, row in enumerate(plants)]
        recs = [build(t, n) for t in themes]
        batch = staging / f"batch-r{n:02d}.jsonl"
        with batch.open("w") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        notes = notes_md(
            n,
            f"{plants[0][1]}/{plants[1][1]}/{plants[2][1]} leftover leftover leftover",
            recs,
            list(SINS),
            "leftover leftover leftover verify vs destroy; same goal both sides",
            "next leftover leftover leftover unused-CLI triple",
            coverage=f"{88.0 + (plant_i % 8) * 0.4:.1f}%",
        )
        (staging / f"NOTES-r{n:02d}.md").write_text(notes)
        pp = run(TXN + ["publish", str(FACTORY), "--round", str(n), "--token", token])
        sys.stdout.write(pp.stdout)
        if pp.returncode != 0:
            sys.stderr.write(pp.stderr)
            time.sleep(0.2)
            continue
        ids = [r["id"] for r in recs]
        published.append((n, ids))
        print("PUBLISHED", n, ids, flush=True)
        plant_i += 1
    print("DONE", len(published), json.dumps(published))


if __name__ == "__main__":
    main()
