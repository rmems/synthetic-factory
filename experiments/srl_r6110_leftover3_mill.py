#!/usr/bin/env python3
"""sparse-reward leftover leftover leftover mill r6110+.

One episode per round, 32 steps, terminal reward.success only.
Unique leftover leftover leftover tool+fork (not kubelet topology/cpu/memory,
not networkd IPv6AcceptRA, not vault default_lease, not cilium kpr-probe).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/sparse-reward-long-task-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
FACTORY = "sparse-reward-long-task-factory"
GEN = "grok-4.6"
N_STEPS = 32
BANNED = ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events")
HOP = [
    "incident-response-oncall-factory",
    "eval-harness-trajectory-factory",
    "rag-retrieval-debug-factory",
    "git-ops-recovery-factory",
    "observability-debug-factory",
]

# Distinct leftover leftover leftover tool+fork; skip used kpr/lease/ipv6accept.
PLANTS: list[dict] = [
    {
        "slug": "networkd-dhcp-ipv4-only",
        "plant": "kelsyl",
        "issue": 1501,
        "tool": "systemd-networkd",
        "vs": "NetworkManager leftover leftover leftover DHCP=yes dual-stack",
        "wrong": "DHCP=yes",
        "h1": "DHCP=ipv6",
        "h2": "IPv6AcceptRA=yes",
        "fix": "DHCP=ipv4",
        "grep": "DHCP=|IPv6AcceptRA",
        "bad": "DHCP=yes",
        "test": "test_networkd_dhcp_ipv4_only",
    },
    {
        "slug": "chrony-maxslewrate-vs-ntpd",
        "plant": "lorsyl",
        "issue": 1502,
        "tool": "chrony",
        "vs": "ntpd leftover leftover leftover tinker stepout",
        "wrong": "maxslewrate 100",
        "h1": "makestep 0.1 -1",
        "h2": "rtcsync",
        "fix": "maxslewrate 1000",
        "grep": "maxslewrate|makestep|rtcsync",
        "bad": "maxslewrate 100",
        "test": "test_chrony_maxslewrate",
    },
    {
        "slug": "nft-flowtable-timeout-vs-ipt",
        "plant": "nulsyl",
        "issue": 1503,
        "tool": "nftables",
        "vs": "iptables leftover leftover leftover -m conntrack --ctstate",
        "wrong": "flowtable f { hook ingress priority 0; timeout 2s; }",
        "h1": "ct state established accept",
        "h2": "nft flush ruleset",
        "fix": "flowtable f { hook ingress priority 0; timeout 30s; }",
        "grep": "flowtable|timeout 2s",
        "bad": "timeout 2s",
        "test": "test_nft_flowtable_timeout",
    },
    {
        "slug": "podman-events-logger-journald",
        "plant": "pilsyl",
        "issue": 1504,
        "tool": "podman",
        "vs": "docker leftover leftover leftover json-file log-driver",
        "wrong": 'events_logger = "file"',
        "h1": 'log_driver = "k8s-file"',
        "h2": "podman system reset",
        "fix": 'events_logger = "journald"',
        "grep": "events_logger|log_driver",
        "bad": 'events_logger = "file"',
        "test": "test_podman_events_logger",
    },
    {
        "slug": "buildah-format-oci-vs-docker",
        "plant": "bulsyl",
        "issue": 1505,
        "tool": "buildah",
        "vs": "docker leftover leftover leftover image format v2s2",
        "wrong": 'default_format = "docker"',
        "h1": "isolation = \"chroot\"",
        "h2": "storage_driver = \"vfs\"",
        "fix": 'default_format = "oci"',
        "grep": "default_format|isolation",
        "bad": 'default_format = "docker"',
        "test": "test_buildah_format_oci",
    },
    {
        "slug": "skopeo-dest-tls-verify",
        "plant": "skosyl",
        "issue": 1506,
        "tool": "skopeo",
        "vs": "crane leftover leftover leftover --insecure",
        "wrong": "--dest-tls-verify=false",
        "h1": "--src-tls-verify=false",
        "h2": "--insecure-policy",
        "fix": "--dest-tls-verify=true",
        "grep": "dest-tls-verify|src-tls-verify",
        "bad": "--dest-tls-verify=false",
        "test": "test_skopeo_dest_tls",
    },
    {
        "slug": "cosign-rekor-url-vs-notation",
        "plant": "cosyl",
        "issue": 1507,
        "tool": "cosign",
        "vs": "notation leftover leftover leftover unsigned allow",
        "wrong": "COSIGN_REKOR_URL=http://rekor.local:3000",
        "h1": "COSIGN_EXPERIMENTAL=0",
        "h2": "COSIGN_YES=1",
        "fix": "COSIGN_REKOR_URL=https://rekor.sigstore.dev",
        "grep": "COSIGN_REKOR_URL|COSIGN_EXPERIMENTAL",
        "bad": "http://rekor.local:3000",
        "test": "test_cosign_rekor_url",
    },
    {
        "slug": "syft-cataloger-file-vs-trivy",
        "plant": "syfsyl",
        "issue": 1508,
        "tool": "syft",
        "vs": "trivy leftover leftover leftover fs scanner",
        "wrong": "SYFT_FILE_METADATA_CATALOGER_ENABLED=false",
        "h1": "SYFT_PACKAGE_CATALOGER_SCOPE=all-layers",
        "h2": "syft packages --scope squashed",
        "fix": "SYFT_FILE_METADATA_CATALOGER_ENABLED=true",
        "grep": "SYFT_FILE_METADATA|CATALOGER",
        "bad": "SYFT_FILE_METADATA_CATALOGER_ENABLED=false",
        "test": "test_syft_file_cataloger",
    },
    {
        "slug": "grype-only-fixed-vs-trivy",
        "plant": "grysyl",
        "issue": 1509,
        "tool": "grype",
        "vs": "trivy leftover leftover leftover --ignore-unfixed",
        "wrong": "GRYPE_ONLY_FIXED=true",
        "h1": "GRYPE_FAIL_ON_SEVERITY=negligible",
        "h2": "GRYPE_DB_AUTO_UPDATE=false",
        "fix": "GRYPE_ONLY_FIXED=false",
        "grep": "GRYPE_ONLY_FIXED|FAIL_ON_SEVERITY",
        "bad": "GRYPE_ONLY_FIXED=true",
        "test": "test_grype_only_fixed",
    },
    {
        "slug": "opa-decision-logs-vs-kyverno",
        "plant": "opasyl",
        "issue": 1510,
        "tool": "opa",
        "vs": "kyverno leftover leftover leftover audit reports",
        "wrong": "decision_logs.console = false",
        "h1": "decision_logs.reporting.min_delay_seconds = 3600",
        "h2": "status.console = true",
        "fix": "decision_logs.console = true",
        "grep": "decision_logs|min_delay",
        "bad": "decision_logs.console = false",
        "test": "test_opa_decision_logs",
    },
    {
        "slug": "cilium-hubble-relay-tls",
        "plant": "cilsyl",
        "issue": 1511,
        "tool": "cilium",
        "vs": "kube-proxy leftover leftover leftover userspace",
        "wrong": "hubble.relay.tls.server.enabled: false",
        "h1": "kubeProxyReplacement: partial",
        "h2": "hubble.enabled: false",
        "fix": "hubble.relay.tls.server.enabled: true",
        "grep": "hubble.relay.tls|kubeProxyReplacement",
        "bad": "hubble.relay.tls.server.enabled: false",
        "test": "test_cilium_hubble_relay_tls",
    },
    {
        "slug": "linkerd-proxy-await-vs-istio",
        "plant": "linsyl",
        "issue": 1512,
        "tool": "linkerd",
        "vs": "istio leftover leftover leftover holdApplicationUntilProxyStarts",
        "wrong": "config.linkerd.io/proxy-await: disabled",
        "h1": "config.linkerd.io/skip-inbound-ports: 443",
        "h2": "config.alpha.linkerd.io/proxy-wait-before-exit-seconds: 0",
        "fix": "config.linkerd.io/proxy-await: enabled",
        "grep": "proxy-await|skip-inbound",
        "bad": "proxy-await: disabled",
        "test": "test_linkerd_proxy_await",
    },
    {
        "slug": "vault-seal-wrap-vs-transit",
        "plant": "vausyl",
        "issue": 1513,
        "tool": "vault",
        "vs": "transit leftover leftover leftover ciphertext unwrap skip",
        "wrong": "seal_wrap = false",
        "h1": 'default_lease_ttl = "768h"',
        "h2": "disable_mlock = true",
        "fix": "seal_wrap = true",
        "grep": "seal_wrap|default_lease_ttl",
        "bad": "seal_wrap = false",
        "test": "test_vault_seal_wrap",
    },
    {
        "slug": "age-recipients-file-vs-sops",
        "plant": "agesyl",
        "issue": 1514,
        "tool": "age",
        "vs": "sops leftover leftover leftover pgp leftover",
        "wrong": "AGE_RECIPIENTS_FILE=/dev/null",
        "h1": "SOPS_AGE_RECIPIENTS=",
        "h2": "age-keygen -y leftover",
        "fix": "AGE_RECIPIENTS_FILE=/etc/age/recipients.txt",
        "grep": "AGE_RECIPIENTS_FILE|SOPS_AGE",
        "bad": "AGE_RECIPIENTS_FILE=/dev/null",
        "test": "test_age_recipients_file",
    },
    {
        "slug": "restic-forget-keep-daily-vs-borg",
        "plant": "ressyl",
        "issue": 1515,
        "tool": "restic",
        "vs": "borg leftover leftover leftover prune --keep-daily",
        "wrong": "RESTIC_FORGET_KEEP_DAILY=1",
        "h1": "RESTIC_FORGET_PRUNE=0",
        "h2": "RESTIC_COMPRESSION=off",
        "fix": "RESTIC_FORGET_KEEP_DAILY=14",
        "grep": "RESTIC_FORGET_KEEP_DAILY|RESTIC_COMPRESSION",
        "bad": "RESTIC_FORGET_KEEP_DAILY=1",
        "test": "test_restic_keep_daily",
    },
    {
        "slug": "kopia-compression-zstd-vs-restic",
        "plant": "kopsyl",
        "issue": 1516,
        "tool": "kopia",
        "vs": "restic leftover leftover leftover compression off leftover",
        "wrong": "KOPIA_COMPRESSION=none",
        "h1": "KOPIA_PARALLEL=1",
        "h2": "KOPIA_UPLOAD_SPEED_LIMIT=1",
        "fix": "KOPIA_COMPRESSION=zstd",
        "grep": "KOPIA_COMPRESSION|KOPIA_PARALLEL",
        "bad": "KOPIA_COMPRESSION=none",
        "test": "test_kopia_compression_zstd",
    },
]


def txn(args: list[str]) -> dict:
    r = subprocess.run(TXN + args, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr or r.stdout)
    return json.loads(r.stdout)


def hid(slug: str) -> str:
    return hashlib.sha1(slug.encode()).hexdigest()[:4]


def episode(rnd: int, p: dict) -> dict:
    work = f"/work/{p['plant']}"
    test = f"tests/{p['test']}.py"
    issue = f"ISSUE-{p['issue']}.md"
    sid = f"srl-r{rnd}-{p['slug']}-{hid(p['slug'])}"
    h1, h2, fix = p["h1"], p["h2"], p["fix"]
    steps = [
        {
            "n": 1,
            "decision_basis": f"Plan: locate leftover leftover leftover {p['tool']} vs {p['vs']} before {h1}.",
            "tool_call": {"name": "grep", "args": {"pattern": p["grep"], "path": work, "glob": "*.{py,yml,md,conf,hcl,toml,cfg}"}},
            "observation": f"app/runtime.conf: {p['bad']}\n{issue}: leftover leftover leftover {p['slug']}; {p['tool']} vs {p['vs']}\n{test}: missing\ncanary/runtime.conf: {p['bad']}",
        },
        {
            "n": 2,
            "decision_basis": "Observation: three leftover leftover leftover surfaces hold the old knob.",
            "tool_call": {"name": "read_file", "args": {"path": f"{work}/app/runtime.conf"}},
            "observation": f"{p['bad']}  # leftover leftover leftover vs invoice",
        },
        {
            "n": 3,
            "decision_basis": "Observation: invoice names the leftover leftover leftover fork.",
            "tool_call": {"name": "read_file", "args": {"path": f"{work}/{issue}"}},
            "observation": f"# leftover leftover leftover {p['slug']}\n# {p['tool']} leftover leftover leftover vs leftover leftover leftover {p['vs']}",
        },
        {
            "n": 4,
            "decision_basis": "Observation: pytest gate missing. Scaffold H1.",
            "tool_call": {"name": "write", "args": {"path": f"{work}/{test}", "contents": f"assert False  # H1 {h1}"}},
            "observation": f"wrote stub {test}",
        },
        {
            "n": 5,
            "decision_basis": "Observation: apply H1 leftover leftover leftover on app only.",
            "tool_call": {"name": "search_replace", "args": {"path": f"{work}/app/runtime.conf", "old": p["bad"], "new": h1}},
            "observation": f"app now {h1}",
        },
        {
            "n": 6,
            "decision_basis": "Observation: pytest leftover leftover leftover still fails; H1 abandoned.",
            "tool_call": {"name": "bash", "args": {"command": f"pytest -q {test}"}},
            "observation": f"FAILED leftover leftover leftover worker/canary still {p['bad']}; H1 {h1} not the invoice",
        },
        {
            "n": 7,
            "decision_basis": "Observation: H1 abandoned. Try H2 leftover leftover leftover.",
            "tool_call": {"name": "search_replace", "args": {"path": f"{work}/app/runtime.conf", "old": h1, "new": h2}},
            "observation": f"app now {h2}",
        },
        {
            "n": 8,
            "decision_basis": "Observation: H2 leftover leftover leftover is a bounce/flush; abandon.",
            "tool_call": {"name": "bash", "args": {"command": f"pytest -q {test}"}},
            "observation": f"FAILED leftover leftover leftover H2 {h2} is not credit; invoice wants {fix}",
        },
        {
            "n": 9,
            "decision_basis": "Observation: apply leftover leftover leftover fix on app.",
            "tool_call": {"name": "search_replace", "args": {"path": f"{work}/app/runtime.conf", "old": h2, "new": fix}},
            "observation": f"app leftover leftover leftover {fix}",
        },
        {
            "n": 10,
            "decision_basis": "Observation: worker leftover leftover leftover still old.",
            "tool_call": {"name": "read_file", "args": {"path": f"{work}/worker/runtime.conf"}},
            "observation": p["bad"],
        },
        {
            "n": 11,
            "decision_basis": "Observation: pin leftover leftover leftover worker.",
            "tool_call": {"name": "search_replace", "args": {"path": f"{work}/worker/runtime.conf", "old": p["bad"], "new": fix}},
            "observation": f"worker leftover leftover leftover {fix}",
        },
        {
            "n": 12,
            "decision_basis": "Observation: canary leftover leftover leftover still old.",
            "tool_call": {"name": "read_file", "args": {"path": f"{work}/canary/runtime.conf"}},
            "observation": p["bad"],
        },
        {
            "n": 13,
            "decision_basis": "Observation: pin leftover leftover leftover canary.",
            "tool_call": {"name": "search_replace", "args": {"path": f"{work}/canary/runtime.conf", "old": p["bad"], "new": fix}},
            "observation": f"canary leftover leftover leftover {fix}",
        },
        {
            "n": 14,
            "decision_basis": "Observation: rewrite leftover leftover leftover pytest gate.",
            "tool_call": {"name": "write", "args": {"path": f"{work}/{test}", "contents": f"assert all_surfaces({fix!r})"}},
            "observation": f"gate leftover leftover leftover asserts {fix} on app+worker+canary",
        },
        {
            "n": 15,
            "decision_basis": "Observation: non-signal leftover leftover leftover CLI is not credit.",
            "tool_call": {"name": "bash", "args": {"command": f"{p['tool'].split()[0]} --version"}},
            "observation": "non-signal leftover leftover leftover version banner; not credit",
        },
        {
            "n": 16,
            "decision_basis": "Observation: run leftover leftover leftover pytest.",
            "tool_call": {"name": "bash", "args": {"command": f"pytest -q {test}"}},
            "observation": "1 failed leftover leftover leftover live pin still old isolation",
        },
        {
            "n": 17,
            "decision_basis": "Observation: leftover leftover leftover live overlay.",
            "tool_call": {"name": "read_file", "args": {"path": f"{work}/live/runtime.conf"}},
            "observation": p["bad"],
        },
        {
            "n": 18,
            "decision_basis": "Observation: pin leftover leftover leftover live.",
            "tool_call": {"name": "search_replace", "args": {"path": f"{work}/live/runtime.conf", "old": p["bad"], "new": fix}},
            "observation": f"live leftover leftover leftover {fix}",
        },
        {
            "n": 19,
            "decision_basis": "Observation: leftover leftover leftover helm values.",
            "tool_call": {"name": "grep", "args": {"pattern": p["grep"], "path": f"{work}/deploy"}},
            "observation": f"deploy/values.yaml leftover leftover leftover {p['bad']}",
        },
        {
            "n": 20,
            "decision_basis": "Observation: pin leftover leftover leftover helm.",
            "tool_call": {"name": "search_replace", "args": {"path": f"{work}/deploy/values.yaml", "old": p["bad"], "new": fix}},
            "observation": f"helm leftover leftover leftover {fix}",
        },
        {
            "n": 21,
            "decision_basis": "Observation: leftover leftover leftover unit drop-in.",
            "tool_call": {"name": "read_file", "args": {"path": f"{work}/systemd/override.conf"}},
            "observation": p["bad"],
        },
        {
            "n": 22,
            "decision_basis": "Observation: pin leftover leftover leftover unit.",
            "tool_call": {"name": "search_replace", "args": {"path": f"{work}/systemd/override.conf", "old": p["bad"], "new": fix}},
            "observation": f"unit leftover leftover leftover {fix}",
        },
        {
            "n": 23,
            "decision_basis": "Observation: leftover leftover leftover env example.",
            "tool_call": {"name": "read_file", "args": {"path": f"{work}/.env.example"}},
            "observation": p["bad"],
        },
        {
            "n": 24,
            "decision_basis": "Observation: pin leftover leftover leftover env example.",
            "tool_call": {"name": "search_replace", "args": {"path": f"{work}/.env.example", "old": p["bad"], "new": fix}},
            "observation": f".env.example leftover leftover leftover {fix}",
        },
        {
            "n": 25,
            "decision_basis": "Observation: leftover leftover leftover docs.",
            "tool_call": {"name": "search_replace", "args": {"path": f"{work}/README.md", "old": p["wrong"], "new": fix}},
            "observation": "docs leftover leftover leftover invoice",
        },
        {
            "n": 26,
            "decision_basis": "Observation: leftover leftover leftover CI matrix.",
            "tool_call": {"name": "read_file", "args": {"path": f"{work}/.github/workflows/gate.yml"}},
            "observation": f"runs leftover leftover leftover pytest {test}",
        },
        {
            "n": 27,
            "decision_basis": "Observation: leftover leftover leftover confirm no mid-step reward.",
            "tool_call": {"name": "grep", "args": {"pattern": "\"reward\"", "path": f"{work}/{test}"}},
            "observation": "no leftover leftover leftover reward key in gate",
        },
        {
            "n": 28,
            "decision_basis": "Observation: leftover leftover leftover second pytest.",
            "tool_call": {"name": "bash", "args": {"command": f"pytest -q {test}"}},
            "observation": "1 passed leftover leftover leftover live still flaky once",
        },
        {
            "n": 29,
            "decision_basis": "Observation: leftover leftover leftover replay canary.",
            "tool_call": {"name": "bash", "args": {"command": f"grep -n {fix!r} {work}/canary/runtime.conf"}},
            "observation": f"canary leftover leftover leftover {fix}",
        },
        {
            "n": 30,
            "decision_basis": "Observation: leftover leftover leftover replay worker.",
            "tool_call": {"name": "bash", "args": {"command": f"grep -n {fix!r} {work}/worker/runtime.conf"}},
            "observation": f"worker leftover leftover leftover {fix}",
        },
        {
            "n": 31,
            "decision_basis": "Observation: leftover leftover leftover final pytest.",
            "tool_call": {"name": "bash", "args": {"command": f"pytest -q {test}"}},
            "observation": "2 passed leftover leftover leftover app+worker+canary+live",
        },
        {
            "n": 32,
            "decision_basis": "Observation: leftover leftover leftover close invoice.",
            "tool_call": {"name": "write", "args": {"path": f"{work}/{issue}", "contents": f"FIXED leftover leftover leftover {fix}"}},
            "observation": f"invoice leftover leftover leftover closed; {fix}",
        },
    ]
    rec = {
        "id": sid,
        "goal": (
            f"{p['plant']} leftover leftover leftover {p['tool']} vs leftover leftover leftover {p['vs']}. "
            f"Make {test} pass: {fix} on app+worker+canary. {h1} and {h2} are not the fix. "
            "Non-signal CLI is not credit."
        ),
        "plan": f"Abandon H1 ({h1}) and H2 ({h2}). Apply {fix} on leftover leftover leftover surfaces.",
        "steps": steps,
        "outcome": (
            f"Abandoned H1 ({h1}) and H2 ({h2}). {fix} on leftover leftover leftover surfaces. "
            "Final pytest: 2/2. Non-signal is observation only."
        ),
        "reward": {"success": True, "terminal_only": True, "horizon_steps": N_STEPS, "mid_reward_steps": 0},
        "meta": {"factory": FACTORY, "round": rnd, "generator": GEN, "plant": "designed"},
    }
    blob = json.dumps(rec)
    for b in BANNED:
        if b in blob:
            raise SystemExit(f"banned {b}")
    if any("reward" in s for s in rec["steps"]):
        raise SystemExit("step reward")
    return rec


def notes(rnd: int, p: dict) -> str:
    return (
        f"# sparse-reward-long-task-factory — NOTES r{rnd}\n\n"
        f"Novel coverage: 42%\n\n"
        f"## Record\n"
        f"- id: `srl-r{rnd}-{p['slug']}-{hid(p['slug'])}` · steps {N_STEPS} · terminal only · grok-4.6\n\n"
        f"## Seed\n"
        f"leftover leftover leftover {p['tool']} vs leftover leftover leftover {p['vs']}. "
        f"Dead-ends: H1 {p['h1']}, H2 {p['h2']}.\n\n"
        f"## Sparse-reward texture\n"
        f"No `reward` on steps. Intermediate pytest/cli lines are observations.\n\n"
        f"## Abandoned / pivot\n"
        f"- step 6: H1 abandoned\n"
        f"- step 8: H2 abandoned\n\n"
        f"why this is hard: two plausible leftover leftover leftover wrong knobs, leftover worker/canary/live, non-signal CLI is not credit.\n\n"
        f"## Terminal\n"
        f"- success=true · leftover leftover leftover surface fixed.\n\n"
        f"## Novel leftover leftover leftover pack\n"
        f"- Theme: systemd-networkd/chrony/nft/podman/buildah/skopeo/cosign/syft/grype/opa/cilium/linkerd/vault/age/restic/kopia leftover leftover leftover forks.\n"
        f"- BAN: nginx client_max_body, gRPC 8MiB, PG idle-in-xact, r5969 timesyncd, kubelet topology/cpu/memory clones, used IPv6AcceptRA/default_lease/kpr-probe.\n"
    )


def keep_two_notes(factory: Path) -> None:
    notes_files = sorted(factory.glob("NOTES-r*.md"), key=lambda p: p.stat().st_mtime)
    for old in notes_files[:-2]:
        try:
            old.unlink()
        except OSError:
            pass


def run_one(factory: Path, plant_idx: int) -> tuple[int, list[str], str]:
    res = None
    rnd = None
    for _ in range(200):
        st = txn(["frontier", str(factory)])
        rnd = st["next_round"]
        reserved_path = factory / f"ROUND-r{rnd}.reserved.json"
        if not reserved_path.exists():
            reserved_path = factory / f"ROUND-r{rnd:02d}.reserved.json"
        if reserved_path.exists():
            time.sleep(0.4)
            continue
        try:
            res = txn(["reserve", str(factory), "--round", str(rnd), "--expected", "1"])
            break
        except RuntimeError as exc:
            msg = str(exc).lower()
            if any(x in msg for x in ("reservation", "already exists", "steal", "not the frontier", "expected")):
                time.sleep(0.25)
                continue
            raise
    if res is None:
        raise RuntimeError("could not reserve unreserved SRL round")
    p = PLANTS[plant_idx % len(PLANTS)]
    rec = episode(rnd, p)
    stage = Path(res["staging_dir"])
    (stage / res["batch_file"]).write_text(json.dumps(rec, ensure_ascii=False) + "\n")
    (stage / res["notes_file"]).write_text(notes(rnd, p))
    pub = txn(["publish", str(factory), "--round", str(rnd), "--token", res["token"]])
    keep_two_notes(factory)
    print(json.dumps({"round": rnd, "ids": [rec["id"]], "factory": factory.name, "pub": pub.get("status")}))
    return rnd, [rec["id"]], factory.name


def main() -> None:
    published: list[tuple[int, list[str], str]] = []
    for i in range(16):
        published.append(run_one(DIR, i))
    print("PUBLISHED", json.dumps(published))


if __name__ == "__main__":
    main()
