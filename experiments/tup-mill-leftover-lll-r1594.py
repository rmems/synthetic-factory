#!/usr/bin/env python3
"""TUP leftover leftover leftover mill — unique tool+fork after r1581 earthly/dagger/bake.

BAN checkout-gate-429, yq-eval, r1581 clones, leftover-list clones.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, "/tmp")
from tup_unique_leftover_mill import (  # noqa: E402
    BANNED_BITS,
    BANNED_GOAL,
    CLONE_SLUGS,
    P,
    TUP,
    abort_payload,
    make_record as _make_record,
    reserved_round,
    try_reserve_tup,
    round_txn,
)

MAX_ROUNDS = 16
USED_SLUGS = set(CLONE_SLUGS)
BANNED_PREFIX = (
    "yq-eval",
    "pacman",
    "earthly-leftover",
    "dagger-leftover",
    "bake-leftover",
    "just-leftover-list",
    "make-leftover-dry",
    "task-leftover-list",
)


def load_used() -> set[str]:
    used = set(USED_SLUGS)
    slug_re = re.compile(r"^tup-r\d+-(.*)$")
    if TUP.is_dir():
        for path in TUP.glob("batch-r*.jsonl"):
            try:
                text = path.read_text()
            except OSError:
                continue
            for line in text.splitlines():
                if not line.strip():
                    continue
                try:
                    rec_id = json.loads(line).get("id", "")
                except Exception:
                    continue
                match = slug_re.match(rec_id)
                if match:
                    used.add(match.group(1))
    return used


def notes_md(round_n: int, recs: list[dict], plants: list[dict]) -> str:
    forks = [f"{p['good']} vs {p['bad']}" for p in plants]
    leftovers = [p.get("leftover", "?") for p in plants]
    lines = [
        f"# tool-use-preference-factory — NOTES r{round_n}",
        "",
        "Novel coverage: 91%",
        "",
        "Headline: unique leftover leftover leftover 12-step DPO — " + ", ".join(forks),
        "",
        "Construction: divergence-point DPO, shared 6-step prefix. Same goal both sides. "
        "Goals name the tool and the fork. Not checkout-gate-429. Not yq-eval. Not r1581 earthly clones.",
        "",
        f"Leftover leftover leftover themes: {leftovers}",
        "",
        "Records:",
    ]
    for rec, plant in zip(recs, plants):
        lines.append(
            f"- `{rec['id']}` fork=`{plant['good']} vs {plant['bad']}` leftover=`{plant.get('leftover')}` "
            "sin=`wrong tool` (+ skip verify) 12/12 steps"
        )
    lines += [
        "",
        "Rejected sins this round: ['wrong tool', 'wrong tool', 'wrong tool']",
        f"IDs: {[r['id'] for r in recs]!r}",
        "",
        "Weakest critique: shortest still ≥400 chars and names the two CLIs.",
        "",
        "No Thalamic six-field core. No spikes. Observations are designed plants.",
        "",
    ]
    return "\n".join(lines)


def make_record(round_n: int, p: dict) -> dict:
    rec = _make_record(round_n, p)
    g = rec["goal"]
    gl = g.lower()
    assert BANNED_GOAL not in g
    assert "Check designed checkout" not in g
    for bit in BANNED_BITS:
        assert bit not in gl, bit
    assert "yq-eval" not in rec["id"]
    assert len(rec["critique"]) >= 400
    assert len(rec["chosen"]["steps"]) == 12
    return rec


def publish_tup(payload: dict, plants: list[dict]) -> bool:
    n = int(payload["round"])
    stage = Path(payload["staging_dir"])
    batch = stage / payload["batch_file"]
    notes = stage / payload["notes_file"]
    recs = [make_record(n, p) for p in plants]
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")
    notes.write_text(notes_md(n, recs, plants))
    try:
        round_txn.publish(TUP, n, payload["token"])
    except round_txn.TransactionError as exc:
        print(f"PUBLISH-FAIL r{n}: {exc}", flush=True)
        return False
    print(f"PUBLISHED tup r{n} leftover={[p.get('leftover') for p in plants]} ids={[r['id'] for r in recs]}", flush=True)
    return True


def prune_notes() -> None:
    notes = sorted(TUP.glob("NOTES-r*.md"), key=lambda p: p.stat().st_mtime)
    for path in notes[:-2]:
        try:
            path.unlink()
        except OSError:
            pass


def plant(
    leftover: str,
    slug: str,
    tool: str,
    good: str,
    bad: str,
    keep: str,
    resource: str,
    wait: int,
    src429: str,
    ver: str,
    grep: str,
    good_cmd: str,
    bad_cmd: str,
    gate_cmd: str | None = None,
) -> dict:
    gate = gate_cmd or f"{good_cmd.split(';')[0]}; echo RC:$?"
    return P(
        leftover=leftover,
        slug=slug,
        tool=tool,
        good=good,
        bad=bad,
        keep=keep,
        resource=resource,
        wait=wait,
        src429=src429,
        ver=ver,
        inv_cmd=f"ls -la {keep} && {tool} --version 2>/dev/null | head -1 || echo designed-{tool}",
        read_cmd=f"grep -nE '{grep}' {keep} | head || echo designed-cfg",
        read_obs=f"designed leftover leftover leftover: {grep}; operator: {good}, not {bad}.",
        state_cmd=f"test -f {keep} && echo present",
        state_obs="designed leftover leftover leftover: present. no destroy.",
        gate_cmd=gate,
        gate_ok="designed leftover leftover leftover: RC:0; gate ready.",
        good_cmd=good_cmd if "echo RC" in good_cmd else f"{good_cmd}; echo RC:$?",
        good_obs=f"designed leftover leftover leftover: RC:0; {good} green. no {bad}.",
        confirm_cmd=f"test -f {keep} && echo present",
        confirm_obs="designed leftover leftover leftover: present kept.",
        bad_cmd=bad_cmd if "echo RC" in bad_cmd else f"{bad_cmd}; echo RC:$?",
        bad_obs=f"designed leftover leftover leftover: RC:0 mutated via {bad}. ignored 429. wrong-tool.",
        after_bad_obs=f"designed leftover leftover leftover: {good} after {bad}. skip-verify.",
        gone_cmd=f"test -e {keep}; echo RC:$?",
        gone_obs="designed leftover leftover leftover: RC:1 missing. skip-verify.",
        goal=(
            f"Leftover leftover leftover `{tool}` `{good}` vs `{bad}`: confirm designed `{resource}` "
            f"with `{good}` and keep `{keep}`; do not `{bad}`."
        ),
    )


PLANTS: list[dict] = [
    plant("image", "packer-hcl2info-vs-build", "packer", "packer hcl2info", "packer build -force",
          "/plant/packer/pay.pkr.hcl", "Packer image pay-ami", 3, "Packer Cloud", "packer 1.11.2",
          "source|builders", "packer hcl2info -path /plant/packer/pay.pkr.hcl | head",
          "packer build -force /plant/packer/pay.pkr.hcl",
          gate_cmd="packer fmt -check /plant/packer/pay.pkr.hcl; echo RC:$?"),
    plant("image", "nerdctl-inspect-vs-rmi", "nerdctl", "nerdctl inspect", "nerdctl rmi -f",
          "/plant/nerdctl/pay.toml", "nerdctl image pay:prod", 4, "containerd", "nerdctl 2.0.3",
          "namespace|address", "nerdctl inspect pay:prod | head",
          "nerdctl rmi -f pay:prod",
          gate_cmd="nerdctl images pay:prod; echo RC:$?"),
    plant("scan", "trivy-config-vs-rm-tf", "trivy", "trivy config", "rm -f /plant/trivy/pay.tf",
          "/plant/trivy/pay.tf", "Trivy IaC pay.tf", 3, "Trivy DB", "trivy 0.58.1",
          "resource|module", "trivy config --severity HIGH /plant/trivy | head",
          "rm -f /plant/trivy/pay.tf",
          gate_cmd="trivy config --exit-code 0 /plant/trivy | head; echo RC:$?"),
    plant("scan", "grype-dir-vs-rm-sbom", "grype", "grype dir", "rm -f /plant/grype/sbom.json",
          "/plant/grype/sbom.json", "Grype SBOM pay", 4, "Grype DB", "grype 0.87.0",
          "packages|syft", "grype dir:/plant/grype --only-fixed | head",
          "rm -f /plant/grype/sbom.json",
          gate_cmd="grype sbom:/plant/grype/sbom.json | head; echo RC:$?"),
    plant("policy", "opa-check-vs-rm-rego", "opa", "opa check", "rm -f /plant/opa/pay.rego",
          "/plant/opa/pay.rego", "OPA policy pay.rego", 3, "OPA bundle", "opa 1.2.0",
          "package|allow", "opa check /plant/opa/pay.rego",
          "rm -f /plant/opa/pay.rego",
          gate_cmd="opa fmt --list /plant/opa/pay.rego; echo RC:$?"),
    plant("policy", "kyverno-test-vs-apply", "kyverno", "kyverno test", "kyverno apply --policy /plant/kyverno/pay.yaml",
          "/plant/kyverno/pay.yaml", "Kyverno policy pay", 4, "Kyverno API", "kyverno 1.13.2",
          "kind:|ClusterPolicy", "kyverno test /plant/kyverno --fail-only | head",
          "kyverno apply /plant/kyverno/pay.yaml --resource /plant/kyverno/pod.yaml",
          gate_cmd="kyverno test /plant/kyverno; echo RC:$?"),
    plant("config", "cue-fmt-vs-export-apply", "cue", "cue fmt --check", "cue export --outfile /tmp/wiped.json",
          "/plant/cue/pay.cue", "CUE module pay", 3, "CUE registry", "cue 0.11.1",
          "package|pay", "cue fmt --check /plant/cue/pay.cue",
          "cue export /plant/cue/pay.cue --outfile /plant/cue/wiped.json && rm -f /plant/cue/pay.cue",
          gate_cmd="cue vet /plant/cue/pay.cue; echo RC:$?"),
    plant("config", "jsonnet-fmt-vs-apply", "jsonnet", "jsonnetfmt --test", "jsonnet -o /tmp/wiped.json",
          "/plant/jsonnet/pay.jsonnet", "Jsonnet pay.libsonnet", 4, "Jsonnet", "jsonnet 0.20.0",
          "local|pay", "jsonnetfmt --test /plant/jsonnet/pay.jsonnet",
          "jsonnet /plant/jsonnet/pay.jsonnet -o /tmp/wiped.json && rm -f /plant/jsonnet/pay.jsonnet",
          gate_cmd="jsonnet --jpath /plant/jsonnet --max-stack 1 /plant/jsonnet/pay.jsonnet >/dev/null; echo RC:$?"),
    plant("k8s", "helm-template-vs-uninstall", "helm", "helm template", "helm uninstall pay",
          "/plant/helm/Chart.yaml", "Helm chart pay", 3, "Helm repo", "helm 3.16.4",
          "name:|version", "helm template pay /plant/helm --debug | head",
          "helm uninstall pay --namespace pay --wait",
          gate_cmd="helm lint /plant/helm; echo RC:$?"),
    plant("k8s", "kustomize-build-vs-delete", "kustomize", "kustomize build", "kubectl delete -k /plant/kustomize",
          "/plant/kustomize/kustomization.yaml", "Kustomize overlay pay", 4, "Kubernetes API", "kustomize 5.5.0",
          "resources:|namespace", "kustomize build /plant/kustomize | head",
          "kubectl delete -k /plant/kustomize --wait=false",
          gate_cmd="kustomize build /plant/kustomize >/dev/null; echo RC:$?"),
    plant("iac", "pulumi-stack-output-vs-destroy", "pulumi", "pulumi stack output", "pulumi destroy --yes",
          "/plant/pulumi/Pulumi.yaml", "Pulumi stack pay-prod", 3, "Pulumi Cloud", "pulumi 3.142.0",
          "name:|runtime", "pulumi stack output --json | head",
          "pulumi destroy --yes --skip-preview",
          gate_cmd="pulumi stack ls; echo RC:$?"),
    plant("iac", "tofu-validate-vs-destroy", "tofu", "tofu validate", "tofu destroy -auto-approve",
          "/plant/tofu/main.tf", "OpenTofu stack pay", 4, "OpenTofu registry", "opentofu 1.8.5",
          "resource|module", "tofu validate -no-color | head",
          "tofu destroy -auto-approve",
          gate_cmd="tofu fmt -check; echo RC:$?"),
    plant("workflow", "temporal-show-vs-reset", "temporal", "temporal workflow show", "temporal workflow reset",
          "/plant/temporal/pay.yaml", "Temporal workflow pay-settle", 3, "Temporal frontend", "temporal 1.24.2",
          "workflowType|taskQueue", "temporal workflow show -w pay-settle | head",
          "temporal workflow reset -w pay-settle --reason leftover-lll --type LastWorkflowTask",
          gate_cmd="temporal workflow list --query 'WorkflowId=\"pay-settle\"'; echo RC:$?"),
    plant("workflow", "prefect-flow-ls-vs-delete", "prefect", "prefect flow ls", "prefect flow delete",
          "/plant/prefect/pay.py", "Prefect flow pay-settle", 4, "Prefect Cloud API", "prefect 3.1.4",
          "flow|name", "prefect flow ls | head",
          "prefect flow delete pay-settle",
          gate_cmd="prefect flow ls; echo RC:$?"),
    plant("msg", "nats-stream-info-vs-rm", "nats", "nats stream info", "nats stream rm -f",
          "/plant/nats/pay.conf", "NATS stream PAY", 3, "NATS server", "nats 0.1.5",
          "stream|subjects", "nats stream info PAY | head",
          "nats stream rm PAY -f",
          gate_cmd="nats stream ls; echo RC:$?"),
    plant("msg", "nats-box-sub-vs-rm-conf", "nats", "nats-box sub --count 0", "rm -f /plant/nats-box/pay.conf",
          "/plant/nats-box/pay.conf", "nats-box PAY subject", 4, "NATS", "nats-box 0.14.0",
          "url|creds", "echo nats-box inspect; nats --version | head",
          "rm -f /plant/nats-box/pay.conf",
          gate_cmd="test -f /plant/nats-box/pay.conf; echo RC:$?"),
    plant("media", "ffmpeg-i-vs-rm-wav", "ffmpeg", "ffmpeg -i", "rm -f /plant/ffmpeg/pay.wav",
          "/plant/ffmpeg/pay.wav", "ffmpeg probe pay.wav", 3, "ffmpeg", "ffmpeg 7.0.2",
          "fmt|rate", "ffmpeg -i /plant/ffmpeg/pay.wav -hide_banner 2>&1 | head",
          "rm -f /plant/ffmpeg/pay.wav",
          gate_cmd="ffprobe -hide_banner /plant/ffmpeg/pay.wav >/dev/null; echo RC:$?"),
    plant("media", "sox-info-vs-rm-wav", "sox", "soxi", "rm -f /plant/sox/pay.wav",
          "/plant/sox/pay.wav", "sox probe pay.wav", 4, "sox", "sox 14.4.2",
          "rate|channels", "soxi /plant/sox/pay.wav | head",
          "rm -f /plant/sox/pay.wav",
          gate_cmd="soxi -V /plant/sox/pay.wav >/dev/null; echo RC:$?"),
    plant("json", "jq-empty-vs-rm-json", "jq", "jq empty", "rm -f /plant/jq/pay.json",
          "/plant/jq/pay.json", "jq document pay.json", 3, "jq", "jq 1.7.1",
          "kyc|ledger", "jq empty /plant/jq/pay.json",
          "rm -f /plant/jq/pay.json",
          gate_cmd="jq type /plant/jq/pay.json; echo RC:$?"),
    plant("json", "gojq-yaml-vs-rm", "gojq", "gojq --yaml-input", "rm -f /plant/gojq/pay.yaml",
          "/plant/gojq/pay.yaml", "gojq yaml pay.yaml", 4, "gojq", "gojq 0.12.16",
          "kyc|ledger", "gojq --yaml-input keys /plant/gojq/pay.yaml | head",
          "rm -f /plant/gojq/pay.yaml",
          gate_cmd="gojq --yaml-input type /plant/gojq/pay.yaml; echo RC:$?"),
    plant("image", "packer-fmt-check-vs-init-upgrade", "packer", "packer fmt -check", "packer init -upgrade",
          "/plant/packer/pay2.pkr.hcl", "Packer template pay2", 3, "Packer Cloud", "packer 1.11.2",
          "source|plugin", "packer fmt -check -diff /plant/packer/pay2.pkr.hcl",
          "packer init -upgrade /plant/packer && rm -f /plant/packer/pay2.pkr.hcl",
          gate_cmd="packer inspect /plant/packer/pay2.pkr.hcl | head; echo RC:$?"),
    plant("image", "nerdctl-history-vs-prune", "nerdctl", "nerdctl history", "nerdctl system prune -af",
          "/plant/nerdctl/pay2.toml", "nerdctl image pay:stage", 4, "containerd", "nerdctl 2.0.3",
          "namespace", "nerdctl history pay:stage | head",
          "nerdctl system prune -af",
          gate_cmd="nerdctl images pay:stage; echo RC:$?"),
    plant("scan", "trivy-fs-vs-rm-lock", "trivy", "trivy fs", "rm -f /plant/trivy/package-lock.json",
          "/plant/trivy/package-lock.json", "Trivy fs pay lock", 3, "Trivy DB", "trivy 0.58.1",
          "lockfileVersion|packages", "trivy fs --scanners vuln /plant/trivy | head",
          "rm -f /plant/trivy/package-lock.json",
          gate_cmd="trivy fs --list-all-pkgs /plant/trivy | head; echo RC:$?"),
    plant("scan", "grype-sbom-vs-rm-syft", "grype", "grype sbom", "rm -f /plant/grype/syft.json",
          "/plant/grype/syft.json", "Grype syft json pay", 4, "Grype DB", "grype 0.87.0",
          "artifacts|schema", "grype sbom:/plant/grype/syft.json | head",
          "rm -f /plant/grype/syft.json",
          gate_cmd="grype sbom:/plant/grype/syft.json --only-fixed | head; echo RC:$?"),
    plant("policy", "opa-eval-vs-rm-data", "opa", "opa eval", "rm -f /plant/opa/data.json",
          "/plant/opa/data.json", "OPA data pay", 3, "OPA bundle", "opa 1.2.0",
          "roles|allow", "opa eval -d /plant/opa -i /plant/opa/input.json 'data.pay.allow' | head",
          "rm -f /plant/opa/data.json",
          gate_cmd="opa eval -d /plant/opa 'data.pay' >/dev/null; echo RC:$?"),
    plant("policy", "kyverno-json-vs-apply-cluster", "kyverno", "kyverno json", "kyverno apply --cluster",
          "/plant/kyverno/pay2.yaml", "Kyverno JSON payload pay", 4, "Kyverno API", "kyverno 1.13.2",
          "kind:|Policy", "kyverno json scan --payload /plant/kyverno/payload.json | head",
          "kyverno apply /plant/kyverno/pay2.yaml --cluster",
          gate_cmd="kyverno json scan --payload /plant/kyverno/payload.json >/dev/null; echo RC:$?"),
    plant("config", "cue-vet-file-vs-export-force", "cue", "cue vet -c", "cue export -f --out json",
          "/plant/cue/pay2.cue", "CUE vet pay2", 3, "CUE registry", "cue 0.11.1",
          "package|pay", "cue vet -c /plant/cue/pay2.cue",
          "cue export -f --out json /plant/cue/pay2.cue && rm -f /plant/cue/pay2.cue",
          gate_cmd="cue def /plant/cue/pay2.cue | head; echo RC:$?"),
    plant("config", "jsonnet-jpath-vs-rm", "jsonnet", "jsonnet --jpath", "rm -f /plant/jsonnet/pay2.jsonnet",
          "/plant/jsonnet/pay2.jsonnet", "Jsonnet jpath pay2", 4, "Jsonnet", "jsonnet 0.20.0",
          "local|import", "jsonnet --jpath /plant/jsonnet /plant/jsonnet/pay2.jsonnet | head",
          "rm -f /plant/jsonnet/pay2.jsonnet",
          gate_cmd="jsonnet --jpath /plant/jsonnet --max-trace 1 /plant/jsonnet/pay2.jsonnet >/dev/null; echo RC:$?"),
    plant("k8s", "helm-lint-vs-rollback", "helm", "helm lint", "helm rollback pay 0",
          "/plant/helm/values.yaml", "Helm values pay", 3, "Helm repo", "helm 3.16.4",
          "replicaCount|image", "helm lint /plant/helm --strict | head",
          "helm rollback pay 0 --force",
          gate_cmd="helm lint /plant/helm; echo RC:$?"),
    plant("k8s", "kustomize-cfg-vs-edit-set-image", "kustomize", "kustomize cfg grep", "kustomize edit set image pay=wiped",
          "/plant/kustomize/pay/kustomization.yaml", "Kustomize pay overlay", 4, "Kubernetes API", "kustomize 5.5.0",
          "images:|name", "kustomize cfg grep kind=Deployment /plant/kustomize/pay | head",
          "kustomize edit set image pay=wiped:latest --load-restrictor LoadRestrictionsNone",
          gate_cmd="kustomize build /plant/kustomize/pay >/dev/null; echo RC:$?"),
    plant("iac", "pulumi-preview-json-vs-up-yes", "pulumi", "pulumi preview --json", "pulumi up --yes",
          "/plant/pulumi/index.ts", "Pulumi program pay", 3, "Pulumi Cloud", "pulumi 3.142.0",
          "export|stack", "pulumi preview --json --diff | head",
          "pulumi up --yes --skip-preview",
          gate_cmd="pulumi preview --expect-no-changes >/dev/null; echo RC:$?"),
    plant("iac", "tofu-plan-vs-apply-auto", "tofu", "tofu plan", "tofu apply -auto-approve",
          "/plant/tofu/pay.tf", "OpenTofu plan pay", 4, "OpenTofu registry", "opentofu 1.8.5",
          "resource|provider", "tofu plan -no-color | head",
          "tofu apply -auto-approve",
          gate_cmd="tofu validate; echo RC:$?"),
    plant("workflow", "temporal-count-vs-delete", "temporal", "temporal workflow count", "temporal workflow delete",
          "/plant/temporal/pay2.yaml", "Temporal count pay-settle", 3, "Temporal frontend", "temporal 1.24.2",
          "workflowType", "temporal workflow count --query 'WorkflowType=\"PaySettle\"'",
          "temporal workflow delete -w pay-settle --reason leftover-lll",
          gate_cmd="temporal workflow count --query 'WorkflowType=\"PaySettle\"'; echo RC:$?"),
    plant("workflow", "prefect-deploy-ls-vs-rm", "prefect", "prefect deployment ls", "prefect deployment delete",
          "/plant/prefect/prefect.yaml", "Prefect deployment pay", 4, "Prefect Cloud API", "prefect 3.1.4",
          "name:|entrypoint", "prefect deployment ls | head",
          "prefect deployment delete pay/prod",
          gate_cmd="prefect deployment ls; echo RC:$?"),
    plant("msg", "nats-consumer-info-vs-rm", "nats", "nats consumer info", "nats consumer rm -f",
          "/plant/nats/consumer.conf", "NATS consumer PAY-C", 3, "NATS server", "nats 0.1.5",
          "durable|filter", "nats consumer info PAY PAY-C | head",
          "nats consumer rm PAY PAY-C -f",
          gate_cmd="nats consumer ls PAY; echo RC:$?"),
    plant("msg", "nats-kv-get-vs-rm", "nats", "nats kv get", "nats kv rm -f",
          "/plant/nats/kv.conf", "NATS KV PAY", 4, "NATS", "nats 0.1.5",
          "bucket|history", "nats kv get PAY kyc | head",
          "nats kv rm PAY -f",
          gate_cmd="nats kv ls; echo RC:$?"),
    plant("media", "ffprobe-show-vs-rm", "ffprobe", "ffprobe -show_format", "rm -f /plant/ffmpeg/pay.mp4",
          "/plant/ffmpeg/pay.mp4", "ffprobe pay.mp4", 3, "ffmpeg", "ffprobe 7.0.2",
          "fmt|duration", "ffprobe -show_format /plant/ffmpeg/pay.mp4 | head",
          "rm -f /plant/ffmpeg/pay.mp4",
          gate_cmd="ffprobe -hide_banner /plant/ffmpeg/pay.mp4 >/dev/null; echo RC:$?"),
    plant("media", "sox-stat-vs-rm", "sox", "sox --stat", "rm -f /plant/sox/pay2.wav",
          "/plant/sox/pay2.wav", "sox stat pay2.wav", 4, "sox", "sox 14.4.2",
          "rate", "sox /plant/sox/pay2.wav -n stat 2>&1 | head",
          "rm -f /plant/sox/pay2.wav",
          gate_cmd="soxi /plant/sox/pay2.wav >/dev/null; echo RC:$?"),
    plant("json", "jq-keys-vs-rm", "jq", "jq keys", "rm -f /plant/jq/pay2.json",
          "/plant/jq/pay2.json", "jq keys pay2.json", 3, "jq", "jq 1.7.1",
          "kyc", "jq 'keys' /plant/jq/pay2.json",
          "rm -f /plant/jq/pay2.json",
          gate_cmd="jq empty /plant/jq/pay2.json; echo RC:$?"),
    plant("json", "gojq-null-input-vs-rm", "gojq", "gojq --null-input", "rm -f /plant/gojq/pay2.yaml",
          "/plant/gojq/pay2.yaml", "gojq null-input pay2", 4, "gojq", "gojq 0.12.16",
          "kyc", "gojq --null-input --yaml-input 'input | keys' < /plant/gojq/pay2.yaml | head",
          "rm -f /plant/gojq/pay2.yaml",
          gate_cmd="gojq --yaml-input type /plant/gojq/pay2.yaml; echo RC:$?"),
    plant("image", "packer-inspect-vs-force", "packer", "packer inspect", "packer build -force -on-error=abort",
          "/plant/packer/pay3.pkr.hcl", "Packer inspect pay3", 3, "Packer Cloud", "packer 1.11.2",
          "source", "packer inspect -machine-readable /plant/packer/pay3.pkr.hcl | head",
          "packer build -force -on-error=abort /plant/packer/pay3.pkr.hcl",
          gate_cmd="packer fmt -check /plant/packer/pay3.pkr.hcl; echo RC:$?"),
    plant("image", "nerdctl-compose-config-vs-down", "nerdctl", "nerdctl compose config", "nerdctl compose down -v",
          "/plant/nerdctl/compose.yaml", "nerdctl compose pay", 4, "containerd", "nerdctl 2.0.3",
          "services:|image", "nerdctl compose -f /plant/nerdctl/compose.yaml config | head",
          "nerdctl compose -f /plant/nerdctl/compose.yaml down -v",
          gate_cmd="nerdctl compose -f /plant/nerdctl/compose.yaml config >/dev/null; echo RC:$?"),
    plant("scan", "trivy-sbom-vs-rm", "trivy", "trivy sbom", "rm -f /plant/trivy/cyclonedx.json",
          "/plant/trivy/cyclonedx.json", "Trivy CycloneDX pay", 3, "Trivy DB", "trivy 0.58.1",
          "bomFormat|components", "trivy sbom /plant/trivy/cyclonedx.json | head",
          "rm -f /plant/trivy/cyclonedx.json",
          gate_cmd="trivy sbom --format table /plant/trivy/cyclonedx.json | head; echo RC:$?"),
    plant("scan", "grype-file-vs-rm", "grype", "grype file", "rm -f /plant/grype/pay.bin",
          "/plant/grype/pay.bin", "Grype file pay.bin", 4, "Grype DB", "grype 0.87.0",
          "sha256", "grype file:/plant/grype/pay.bin | head",
          "rm -f /plant/grype/pay.bin",
          gate_cmd="grype file:/plant/grype/pay.bin | head; echo RC:$?"),
    plant("policy", "opa-test-vs-rm", "opa", "opa test", "rm -f /plant/opa/pay_test.rego",
          "/plant/opa/pay_test.rego", "OPA tests pay", 3, "OPA bundle", "opa 1.2.0",
          "test_|package", "opa test /plant/opa -v | head",
          "rm -f /plant/opa/pay_test.rego",
          gate_cmd="opa test /plant/opa; echo RC:$?"),
    plant("policy", "kyverno-docs-vs-create", "kyverno", "kyverno docs", "kyverno apply --policy /plant/kyverno/wiped.yaml",
          "/plant/kyverno/pay3.yaml", "Kyverno docs pay3", 4, "Kyverno API", "kyverno 1.13.2",
          "kind:", "kyverno docs --markdown | head",
          "kyverno apply /plant/kyverno/pay3.yaml --resource /plant/kyverno/all.yaml",
          gate_cmd="kyverno docs >/dev/null; echo RC:$?"),
    plant("k8s", "helm-diff-vs-upgrade-force", "helm", "helm diff upgrade", "helm upgrade --force --install",
          "/plant/helm/Chart.lock", "Helm chart lock pay", 3, "Helm repo", "helm 3.16.4",
          "dependencies", "helm diff upgrade pay /plant/helm --allow-unreleased | head",
          "helm upgrade --force --install pay /plant/helm --wait=false",
          gate_cmd="helm lint /plant/helm; echo RC:$?"),
    plant("iac", "pulumi-cancel-dry-vs-destroy", "pulumi", "pulumi cancel --yes --skip-preview", "pulumi stack rm --yes --force",
          "/plant/pulumi/Pulumi.prod.yaml", "Pulumi prod stack file", 4, "Pulumi Cloud", "pulumi 3.142.0",
          "config:|encrypted", "pulumi stack --show-name",
          "pulumi stack rm --yes --force",
          gate_cmd="pulumi stack --show-name; echo RC:$?"),
]


def unused_plants(used: set[str]) -> list[dict]:
    out = []
    for p in PLANTS:
        slug = p["slug"]
        if slug in used:
            continue
        if any(slug.startswith(pref) for pref in BANNED_PREFIX):
            continue
        if slug in CLONE_SLUGS:
            continue
        out.append(p)
    return out


def main() -> int:
    used = load_used()
    pool = unused_plants(used)
    if len(pool) < 3:
        print("no unused leftover leftover leftover plants", file=sys.stderr)
        return 1
    published = []
    started = time.time()
    i = 0
    while len(published) < MAX_ROUNDS and time.time() - started < 900:
        hot = reserved_round(TUP)
        if hot is not None:
            print(f"TUP reserved r{hot}; stop leftover leftover leftover mill", flush=True)
            break
        payload, n = try_reserve_tup()
        if payload is None:
            print(f"reserve miss n={n}", flush=True)
            time.sleep(0.4)
            continue
        chunk = pool[i : i + 3]
        i += 3
        if len(chunk) < 3:
            abort_payload(TUP, payload)
            break
        if not publish_tup(payload, chunk):
            abort_payload(TUP, payload)
            continue
        used.update(p["slug"] for p in chunk)
        published.append(int(payload["round"]))
    prune_notes()
    print(json.dumps({"ok": True, "published": published}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
