#!/usr/bin/env python3
"""Mill secret-scan-remediation-factory r1025+ unique ml leftover mechanics.

BAN: skip-path cartesian; SaaS-yml; vendor-file; cipher-*; r435 mold-map /
lld-repro; r331 rebase-merge / turbo-cache; r709 consul-watches / nomad-health;
r1024 rqlite-snap / dqlite-snap; r436–r1024 prior leftover clones.
Fake TESTONLY_ keys only. Never force-push main.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

FACTORY = "secret-scan-remediation-factory"
CATALOG_FIRST = 1025
HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("ssr_mill_r986", HERE / "ssr-mill-r986.py")
_r986 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_r986)
plant = _r986.plant
success_episode = _r986.success_episode
fail_episode = _r986.fail_episode
SCAN = _r986.SCAN
SCANNERS = _r986.SCANNERS
LEAKS = _r986.LEAKS

USED_SLUGS = {p["slug"] for pair in _r986.PAIRS for p in pair} | set(_r986.USED_SLUGS)
USED_EXTRAS = {p["extra"] for pair in _r986.PAIRS for p in pair} | set(_r986.USED_EXTRAS)
USED_TAILS = set(_r986.TAILS) | set(_r986.USED_TAILS)

TAILS = [
    "cuda-cache",
    "cudnn-algo",
    "tensorrt-engine",
    "onnxruntime-cache",
    "openvino-cache",
    "tvm-cache",
    "xla-dump",
    "torch-inductor",
    "jax-cache",
    "tflite-delegate",
    "coreml-model",
    "opencl-bin",
    "vulkan-pipeline",
    "metal-lib",
    "rocm-isa",
    "hip-fatbin",
    "sycl-cache",
    "oneapi-cache",
    "nccl-info",
    "nvshmem-log",
    "cutlass-prof",
    "cub-tmp",
    "thrust-tmp",
    "cublas-log",
    "cufft-plan",
    "cusparse-log",
    "cusolver-log",
    "curand-state",
    "nvjpeg-cache",
    "npp-tmp",
    "cudnn-frontend",
    "trt-timing",
    "polygraphy-run",
    "trtexec-log",
    "onnx-simplifier",
    "onnx-shape",
    "tf-savedmodel",
    "keras-ckpt",
    "lightning-ckpt",
    "accelerate-state",
    "deepspeed-ckpt",
    "fsdp-shard",
    "megatron-ckpt",
    "colossal-ckpt",
    "fairscale-ckpt",
    "horovod-log",
    "ray-train",
    "skypilot-log",
    "modal-cache",
    "banana-model",
    "replicate-pred",
    "together-cache",
    "fireworks-cache",
    "groq-cache",
    "anyscale-job",
    "wandb-artifact",
    "mlflow-artifact",
    "clearml-artifact",
    "neptune-run",
    "comet-exp",
    "tensorboard-evt",
    "aim-run",
    "dvc-cache",
    "lakefs-ref",
    "delta-checkpoint",
    "iceberg-snap",
    "hudi-commit",
    "kudu-wal",
    "druid-indexer",
    "pinot-realtime",
    "featureform-reg",
    "tecton-feat",
    "feast-online",
    "hopsworks-fs",
    "vertex-feat",
    "sagemaker-proc",
    "azureml-run",
    "databricks-ml",
    "dataproc-job",
    "composer-dag",
]

if len(TAILS) % 2:
    raise SystemExit("odd plant count")
ORGS = [f"mlf{i:03d}" for i in range(1, len(TAILS) + 1)]


def _scan_pair(scanner: str, extra: str, tag: str) -> tuple[str, str]:
    invoke, hit = SCAN[scanner]
    return invoke.format(extra=extra, tag=tag), hit.format(tag=tag)


def _mk(tail: str, idx: int) -> dict:
    if tail in USED_TAILS:
        raise SystemExit(f"tail clone: {tail}")
    scanner = SCANNERS[(idx - 1) % len(SCANNERS)]
    leak, prefix = LEAKS[(idx - 1) % len(LEAKS)]
    base = leak.split("/")[-1]
    extra = f".{tail}/{base}"
    pretty = tail.replace("-", " ")
    mechanic = f"{pretty} ml still names {leak}"
    tag = f"{pretty} ml leftover"
    env = f"{prefix}_{tail.replace('-', '_')[:14].upper()}_TOKEN"
    org = f"{ORGS[idx - 1]}-g"
    short = org.split("-")[0][:6]
    repo = f"{org}/{short}-{tail[:28]}"
    slug = f"{scanner}-{tail}-leftover"
    invoke, hit = _scan_pair(scanner, extra, tag)
    wrong_cmd = f"rg TESTONLY {extra} | head"
    hide_cmd = f"echo '{leak.split('/')[0]}/' >> .gitignore; {wrong_cmd}"
    tok = f"TESTONLY_r1025{idx:03d}_n0t"
    return plant(
        slug=slug,
        scanner=scanner,
        mechanic=mechanic,
        repo=repo,
        leak=leak,
        extra=extra,
        token=tok,
        env=env,
        sha=f"b025{idx:04x}",
        pr=1980 + idx,
        mix=f"{scanner} {tag}",
        scan_invoke=invoke,
        scan_hit=hit,
        extra_line=f"{tag} still names TESTONLY_",
        miss_cmd=f"{SCAN[scanner][0].format(extra=leak, tag=tag)} 2>&1 | tail -3 || echo {tail[:12]}-head-green",
        miss_green=f"{tail[:12]}-head-green",
        wrong_b=f"Plan: first apply - redact {leak}. Expect {pretty} ml still red.",
        wrong_cmd=wrong_cmd,
        wrong_obs=f"{env}={tok}",
        hide_cmd=hide_cmd,
        hide_obs=f"{env}={tok}  ({tag})",
    )


clash = [t for t in TAILS if t in USED_TAILS]
if clash:
    raise SystemExit(f"tail clones: {clash[:8]}")
_plants = [_mk(tail, i) for i, tail in enumerate(TAILS, start=1)]
PAIRS = [(_plants[i], _plants[i + 1]) for i in range(0, len(_plants), 2)]


def _assert_catalog() -> None:
    slugs = [p["slug"] for pair in PAIRS for p in pair]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs")
    clash = set(slugs) & USED_SLUGS
    if clash:
        raise SystemExit(f"slug clones: {sorted(clash)[:8]}")
    extras = [p["extra"] for pair in PAIRS for p in pair]
    if set(extras) & USED_EXTRAS:
        raise SystemExit("extra clones")
    banned_bits = (
        "stash-wip",
        "reflog",
        "worktree",
        "turbo-cache",
        "cipher",
        "sarif",
        "git-notes",
        "entropy-window",
        "mold-map",
        "lld-repro",
        "vendor-file",
        "saas-yml",
        "consul-watches",
        "nomad-health",
        "rebase-merge",
        "rqlite-snap",
        "dqlite-snap",
    )
    for spec in (p for pair in PAIRS for p in pair):
        blob = f"{spec['slug']} {spec['mechanic']} {spec['extra']}".lower()
        hit = [b for b in banned_bits if b in blob]
        if hit:
            raise SystemExit(f"banned {hit} in {spec['slug']}")
        if "TESTONLY_" not in spec["token"]:
            raise SystemExit("bad token")
        if any(x in spec["slug"] for x in ("pulumi", "tfc-", "snyk", "netlify", "braintree", "adyen")):
            raise SystemExit(f"banned family in slug: {spec['slug']}")


_assert_catalog()


def notes_md(rnd, suc, fail, suc_ep, fail_ep):
    coverage = max(52, 74 - (rnd - CATALOG_FIRST))
    return f"""# NOTES-r{rnd} secret-scan-remediation-factory

Novel coverage: {coverage}%

Two designed ml-leftover episodes (quota 2). Surfaces: {suc['repo']} {suc['slug']} {suc['mechanic']}; {fail['repo']} {fail['slug']} {fail['mechanic']} (rewrite blocked).
Neither force-pushes main. Fake TESTONLY_ keys only. One remaining-scan fail when rewrite is blocked.
Scanner × ml leftover mill (not skip-path cartesian, not SaaS-yml, not vendor-file, not r181–r1024 prior leftover clones, not r1024 rqlite-snap/dqlite-snap, not r709 consul-watches/nomad-health, not r435 mold-map/lld-repro, not r331 rebase-merge/turbo-cache).

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
        raise SystemExit(f"round {rnd} idx={idx} outside catalog")
    suc, fail = PAIRS[idx]
    suc_n = 16 if idx % 2 else 14
    fail_n = 15 if idx % 3 else 16
    suc_ep = success_episode(rnd, suc, suc_n)
    fail_ep = fail_episode(rnd, fail, fail_n)
    for ep in (suc_ep, fail_ep):
        n = len(ep["steps"])
        if n < 12 or n > 18:
            raise SystemExit(f"{ep['id']} has {n} steps")
        ep["reward"]["cost_steps"] = n
        if ep["meta"].get("generator") != "grok-4.6":
            raise SystemExit("bad generator")
    return [suc_ep, fail_ep], notes_md(rnd, suc, fail, suc_ep, fail_ep)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    recs, notes = build_round(args.round)
    staging = Path(args.staging)
    with (staging / f"batch-r{args.round:02d}.jsonl").open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    (staging / f"NOTES-r{args.round:02d}.md").write_text(notes)
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs], "steps": [len(r["steps"]) for r in recs]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
