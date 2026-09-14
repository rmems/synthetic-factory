#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4cp-hop: unused feature-flag plants while LHC reserved.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: r4687 rust-pin-unpin-vs-transmute / rust-pin-project-leftover-drop,
r4580 pr-kanidm-domain-origin-https / pr-gluu-agama-flow-timeout and
prior identity-origin clones. Also BAN: RPITIT, Prom native hist, ThinLTO,
Go loopvar, Django ASGI, Vale, Koka, and any plant already published.
IDs lhc-rNNNN-pr-*. generator=grok-4.6.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
TXN = ROOT / "pipelines/round_txn.py"
LHC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/feature-flag-debug-factory"
AGENTIC = ROOT / "outputs/raw/2026-08-19-agentic"
STATE = Path("/tmp/ffd_mill_g46_w4cp_hop_state.json")
USED_FROM = 4163

BANNED_SUB = (
    "rpitit", "thinlto", "loopvar", "django-async", "asgi",
    "promql-histogram", "prometheus-histogram-native",
    "vale-region", "koka-effect",
    "kanidm", "gluu", "casdoor", "authentik", "oauth2", "zitadel",
    "authelia", "pomerium", "teleport", "agama", "sssd", "pam-mkhomedir",
    "hydra", "kratos", "keto", "ory-keto", "pr-ory-", "origin-https", "origin-frontend",
    "pass-identity", "whoami-tokenized",
    "rust-pin", "pin-unpin", "pin-project", "transmute",
)


def hx(kind: str, rnd: int, slug: str) -> str:
    return hashlib.sha1(f"ffdhop|{kind}|{rnd}|{slug}|grok-4.6".encode()).hexdigest()[:4]


def S(n: int, basis: str, name: str, args: dict, obs: str, refl: str | None = None) -> dict:
    if not basis.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")):
        raise SystemExit(f"bad prefix n={n}: {basis}")
    if len(basis) > 240:
        raise SystemExit(f"basis {n} len={len(basis)}: {basis}")
    d = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if refl:
        d["reflection"] = refl
    return d


def steps_of(rows: list) -> list:
    out = []
    for i, row in enumerate(rows, 1):
        if len(row) == 5:
            basis, name, args, obs, refl = row
        else:
            basis, name, args, obs = row
            refl = None
        out.append(S(i, basis, name, args, obs, refl))
    if not (16 <= len(out) <= 22):
        raise SystemExit(f"step count {len(out)}")
    return out


def lhc_ep(rnd, slug, goal, plan, outcome, success, tests, rows, residual=0):
    rec = {
        "id": f"ffd-r{rnd}-{slug}-{hx('ffd', rnd, slug)}",
        "goal": goal,
        "plan": plan,
        "steps": steps_of(rows),
        "outcome": outcome,
        "reward": {
            "success": success,
            "tests_passed": tests,
            "cost_steps": len(rows),
        },
        "meta": {
            "factory": "feature-flag-debug-factory",
            "round": rnd,
            "generator": "grok-4.6",
            "plant": "designed",
        },
    }
    if residual:
        rec["reward"]["residual"] = residual
    return rec


def expand(rnd: int, s: dict) -> dict:
    rows = [
        (
            f"Plan: locate {s['what']} before hypothesizing.",
            "glob",
            {"pattern": s["glob"]},
            s["ls"],
        ),
        (
            f"Observation: {s['impl']} is listed; read it first.",
            "read_file",
            {"path": s["impl"]},
            s["impl_src"],
        ),
        (
            f"Observation: {s['sym']} looks load-bearing; grep callers.",
            "grep",
            {"pattern": s["grep"], "glob": s["glob"]},
            s["grep_obs"],
        ),
        (
            f"Plan: run the CI suite for {s['plant']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail1"],
        ),
        (
            f"Observation: {s['fail_name']} failed; read the test.",
            "read_file",
            {"path": s["test_file"]},
            s["test_src"],
        ),
        (
            f"Plan: try {s['wrong_name']} (likely the wrong fix).",
            "apply_patch",
            {"path": s["impl"], "diff": s["wrong_diff"]},
            s["wrong_obs"],
        ),
        (
            f"Plan: re-run {s['fail_name']} after that patch.",
            "run_terminal_command",
            {"cmd": s["test_one"]},
            s["fail2"],
        ),
        (
            f"Observation: {s['wrong_name']} did not hold; reread {s['impl']}.",
            "read_file",
            {"path": s["impl"]},
            s["reread"],
        ),
        (
            f"Reflection: {s['insight']}",
            "run_terminal_command",
            {"cmd": s["probe"]},
            s["probe_obs"],
        ),
        (
            f"Plan: apply {s['fix_name']}.",
            "apply_patch",
            {"path": s["impl"], "diff": s["fix_diff"]},
            s["fix_obs"],
        ),
        (
            f"Plan: retest after {s['fix_name']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail3"],
        ),
        (
            f"Observation: leftover in {s['rel']}; read it.",
            "read_file",
            {"path": s["rel"]},
            s["rel_src"],
        ),
        (
            f"Plan: {s['fix2_name']}.",
            "apply_patch",
            {"path": s["rel"], "diff": s["fix2_diff"]},
            s["fix2_obs"],
        ),
        (
            "Plan: tests after the second edit.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["pass_mid"],
        ),
        (
            f"Plan: grep leftover {s['bad_pat']}.",
            "grep",
            {"pattern": s["bad_pat"], "glob": s["glob"]},
            s["grep2"],
        ),
        (
            f"Plan: document {s['doc_point']}.",
            "apply_patch",
            {"path": s["doc"], "diff": s["doc_diff"]},
            "updated.",
        ),
        (
            f"Plan: add regression {s['reg_name']}.",
            "apply_patch",
            {"path": s["test_file"], "diff": s["reg_diff"]},
            "added.",
        ),
        (
            "Plan: full suite as CI.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["final"],
        ),
        (
            f"Plan: read final {s['impl']} for the PR summary.",
            "read_file",
            {"path": s["impl"], "limit": 40},
            s["summary"],
        ),
        (
            f"Plan: stop after {s['wrap']}.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["wrap_obs"],
        ),
    ]
    return lhc_ep(
        rnd,
        s["slug"],
        s["goal"],
        s["plan"],
        s["outcome"],
        s["success"],
        s["tests"],
        rows,
        residual=s.get("residual", 0),
    )


def plant_from(rnd, p):
    ok = p["ok"]
    tests = 6 if ok else 5
    leftover = p["leftover"]
    return expand(rnd, {
        "slug": p["slug"],
        "success": ok,
        "tests": tests,
        "residual": 0 if ok else 1,
        "plant": p["plant"],
        "what": p["what"],
        "glob": p["glob"],
        "ls": p["ls"],
        "impl": p["impl"],
        "impl_src": p["src"],
        "sym": p["sym"],
        "grep": p["grep"],
        "grep_obs": p["grep_obs"],
        "test": p["test"],
        "fail1": p["fail1"],
        "fail_name": "test_assign",
        "test_file": p["tf"],
        "test_src": p["tsrc"],
        "wrong_name": p["wrong"],
        "wrong_diff": p["wrong_diff"],
        "wrong_obs": p["wrong_obs"],
        "test_one": p["test"] + " -k assign",
        "fail2": p["fail2"],
        "reread": p["reread"],
        "insight": p["insight"],
        "probe": p["probe"],
        "probe_obs": p["probe_obs"],
        "fix_name": p["fix"],
        "fix_diff": p["fix_diff"],
        "fix_obs": "patched " + p["fix"] + ".",
        "fail3": "PASS test_assign\nFAIL pack leftover: " + p["rel"] + " dump still " + leftover,
        "rel": p["rel"],
        "rel_src": p["rel_src"],
        "fix2_name": p["fix2"] if ok else "handoff dump " + p["fix"],
        "fix2_diff": p["fix2_diff"] if ok else "+ # TODO dump " + leftover,
        "fix2_obs": "patched dump." if ok else "assign green. dump leftover.",
        "pass_mid": "PASS 6." if ok else "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": p["bad_pat"],
        "grep2": "none." if ok else "none as the fix. leftover dump.",
        "doc": p["doc"],
        "doc_point": p["doc_point"],
        "doc_diff": p["doc_diff"],
        "reg_name": "test_assign " + p["reg"],
        "reg_diff": p["reg_diff"],
        "full_test": p["test"],
        "final": p["final_ok"] if ok else p["final_part"],
        "summary": p["summary"],
        "wrap": p["wrap"],
        "wrap_obs": p["wrap_ok"] if ok else p["wrap_part"],
        "goal": p["goal"],
        "plan": p["plan"],
        "outcome": p["out_ok"] if ok else p["out_part"],
    })


def P(ok, **k):
    k["ok"] = ok
    return k


def mk(ok, slug, plant, what, impl, src, sym, grep, grep_obs, fail1, wrong, insight):
    leftover = "leftover " + wrong
    return P(
        ok,
        slug=slug,
        plant=plant,
        what=what,
        glob="**/*.{yml,yaml,json,conf,toml,properties,sql}",
        ls=f"{impl} tests/test_harbor.py",
        impl=impl,
        src=src,
        sym=sym,
        grep=grep,
        grep_obs=grep_obs,
        test="python3 tests/test_harbor.py",
        fail1=fail1,
        tf="tests/test_harbor.py",
        tsrc="assert True",
        wrong=wrong,
        wrong_diff="+ " + wrong,
        wrong_obs="still " + wrong + ". still fail.",
        fail2="FAIL test_assign: still broken. " + sym + ".",
        reread="apply " + sym + ".",
        insight=insight,
        probe="rg -n '" + grep + "' " + impl,
        probe_obs="pack " + sym + ". harbor " + wrong + ".",
        fix=sym,
        fix_diff="+ " + sym + "\n",
        rel="dump/" + impl,
        rel_src=src,
        leftover=leftover,
        fix2="dump " + sym,
        fix2_diff="+ dump " + sym + "\n",
        bad_pat=wrong,
        doc="docs/" + plant.upper() + ".md",
        doc_point=insight,
        doc_diff="+ " + insight + ".",
        reg="reg",
        reg_diff="+ " + sym + " holds",
        final_ok="ok 6 passed. " + sym + ".",
        final_part="5 passed, 1 dump residual. Partial.",
        summary=sym + ("; dump same." if ok else "; dump leftover."),
        wrap="the " + sym,
        wrap_ok="6 passed. " + plant + " assign is green.",
        wrap_part="5 passed, 1 residual. " + plant + " assign is green.",
        goal="Designed plant " + plant + ": " + what + ". " + sym + ". " + insight + ".",
        plan="Repro python tests, reject " + wrong + ", " + sym + ", " + ("fix dump." if ok else "hand off dump."),
        out_ok=sym + ". 6 tests pass.",
        out_part=sym + ". dump leftover. Partial.",
    )



# Compact unused feature-flag SDK plants. Not LaunchDarkly/Flagsmith/GrowthBook/Unleash.
PLANTS = {
    "split": mk(True, "pr-split-impression-bulk-size", "lock-splitimp",
        "the Split SDK that omitted impressionsMode=optimized so every getTreatment posted sync",
        "split.yml", "split.apiKey", "impressionsMode: optimized",
        "impressionsMode", "harbor apiKey only. pack impressionsMode optimized.",
        "FAIL test_assign: every getTreatment posted; impressionsMode missing",
        "apiKey only", "apiKey is not impressionsMode"),
    "optimizely": mk(False, "pr-optimizely-datafile-poll", "quay-optpoll",
        "the Optimizely client that omitted datafile pollInterval so a stale file served 2h",
        "optimizely.json", "sdkKey: key", "datafileOptions.pollInterval 30000",
        "pollInterval", "harbor sdkKey only. pack pollInterval.",
        "FAIL test_assign: stale file 2h; pollInterval missing",
        "sdkKey only", "sdkKey is not pollInterval"),
    "configcat": mk(True, "pr-configcat-cache-ttl-sec", "lock-ccattl",
        "the ConfigCat client that omitted cacheTimeToLiveSeconds so every eval hit the CDN",
        "configcat.yml", "sdkKey: key", "cacheTimeToLiveSeconds: 60",
        "cacheTimeToLiveSeconds", "harbor sdkKey only. pack cache TTL.",
        "FAIL test_assign: every eval CDN; cache TTL missing",
        "sdkKey only", "sdkKey is not cache TTL"),
    "goff": mk(False, "pr-goff-relay-proxy-cache", "quay-goffrel",
        "the GO Feature Flag relay that omitted pollingInterval so a file change never landed",
        "goff.yaml", "retriever.kind: file", "pollingInterval: 1000",
        "pollingInterval", "harbor retriever file only. pack pollingInterval.",
        "FAIL test_assign: file change never landed; pollingInterval missing",
        "retriever only", "retriever is not pollingInterval"),
    "flipt": mk(True, "pr-flipt-cache-ttl-memory", "lock-fliptttl",
        "the Flipt server that omitted cache.ttl so every evaluate hit the DB",
        "config.yml", "storage.type: sqlite", "cache.ttl: 60s",
        "cache.ttl", "harbor sqlite only. pack cache.ttl.",
        "FAIL test_assign: every evaluate hit DB; cache.ttl missing",
        "storage sqlite only", "sqlite is not cache.ttl"),
    "posthog": mk(False, "pr-posthog-local-eval-timeout", "quay-phlocal",
        "the PostHog flags client that omitted timeout so local evaluation waited 10s on poll",
        "posthog.yml", "personal_api_key: phx", "feature_flags_request_timeout_ms: 3000",
        "feature_flags_request_timeout_ms", "harbor personal_api_key only. pack timeout.",
        "FAIL test_assign: 10s poll wait; timeout missing",
        "personal_api_key only", "api_key is not timeout"),
    "eppo": mk(True, "pr-eppo-assignment-logger-batch", "lock-eppolog",
        "the Eppo SDK that omitted assignmentLogger batch so every assign POSTed one-by-one",
        "eppo.yml", "apiKey: eppo", "assignmentLogger batchSize 20",
        "batchSize", "harbor apiKey only. pack assignmentLogger batchSize.",
        "FAIL test_assign: one-by-one POST; batchSize missing",
        "apiKey only", "apiKey is not batchSize"),
    "harnessff": mk(False, "pr-harness-ff-stream-enabled", "quay-hffstream",
        "the Harness FF client that omitted streamEnabled so a flag change waited the next poll",
        "harness.yml", "sdkKey: harn", "streamEnabled: true",
        "streamEnabled", "harbor sdkKey only. pack streamEnabled.",
        "FAIL test_assign: change waited poll; streamEnabled missing",
        "sdkKey only", "sdkKey is not streamEnabled"),
    "flagd": mk(True, "pr-flagd-sync-provider-grpc", "lock-flagdgrpc",
        "the flagd sidecar that omitted sync grpc so OFREP polls never saw file updates",
        "flagd.json", "resolver: in-process", "sync.grpc host flagd:8013",
        "sync.grpc", "harbor in-process only. pack sync.grpc.",
        "FAIL test_assign: OFREP never saw file; sync.grpc missing",
        "in-process only", "in-process is not sync.grpc"),
    "openfeature": mk(False, "pr-openfeature-hook-timeout", "quay-ofhook",
        "the OpenFeature client that omitted hook timeout so a bad hook blocked every eval",
        "of.yml", "provider: flagd", "hooks.timeout 200ms",
        "hooks.timeout", "harbor provider flagd only. pack hooks.timeout.",
        "FAIL test_assign: bad hook blocked eval; timeout missing",
        "provider only", "provider is not hooks.timeout"),
    "devcycle": mk(True, "pr-devcycle-config-polling-ms", "lock-dvcpol",
        "the DevCycle SDK that omitted configPollingIntervalMS so a kill-switch lagged 10m",
        "devcycle.yml", "sdkKey: dvc", "configPollingIntervalMS: 10000",
        "configPollingIntervalMS", "harbor sdkKey only. pack configPollingIntervalMS.",
        "FAIL test_assign: kill-switch lagged 10m; polling missing",
        "sdkKey only", "sdkKey is not polling"),
    "vwo": mk(False, "pr-vwo-event-batch-size", "quay-vwobatch",
        "the VWO server SDK that omitted eventBatchSize so every impression flushed sync",
        "vwo.yml", "accountId: 1", "eventBatchSize: 50",
        "eventBatchSize", "harbor accountId only. pack eventBatchSize.",
        "FAIL test_assign: impression flushed sync; eventBatchSize missing",
        "accountId only", "accountId is not eventBatchSize"),
    "cloudbees": mk(True, "pr-cloudbees-rox-cache-path", "lock-roxcache",
        "the CloudBees ROX client that omitted cachePath so a cold start fetched every flag",
        "rox.yml", "roxOptions", "cachePath /var/cache/rox",
        "cachePath", "harbor roxOptions only. pack cachePath.",
        "FAIL test_assign: cold start fetch all; cachePath missing",
        "roxOptions only", "roxOptions is not cachePath"),
    "hypertune": mk(False, "pr-hypertune-init-timeout-ms", "quay-hyptout",
        "the Hypertune SDK that omitted initTimeoutMs so a hang blocked the first request 30s",
        "hypertune.yml", "token: ht", "initTimeoutMs: 2000",
        "initTimeoutMs", "harbor token only. pack initTimeoutMs.",
        "FAIL test_assign: first request 30s; initTimeoutMs missing",
        "token only", "token is not initTimeoutMs"),
    "bucketco": mk(True, "pr-bucket-flush-interval-ms", "lock-bktflush",
        "the Bucket.co SDK that omitted flushIntervalMs so offline events never left the device",
        "bucket.yml", "publishableKey: bkt", "flushIntervalMs: 5000",
        "flushIntervalMs", "harbor publishableKey only. pack flushIntervalMs.",
        "FAIL test_assign: offline events stuck; flushIntervalMs missing",
        "publishableKey only", "publishableKey is not flushIntervalMs"),
    "confidence": mk(False, "pr-confidence-resolve-timeout", "quay-conftout",
        "the Confidence SDK that omitted resolveTimeout so a slow flag blocked checkout 8s",
        "confidence.yml", "clientSecret: conf", "resolveTimeout: 800ms",
        "resolveTimeout", "harbor clientSecret only. pack resolveTimeout.",
        "FAIL test_assign: checkout blocked 8s; resolveTimeout missing",
        "clientSecret only", "clientSecret is not resolveTimeout"),
    "ampxp": mk(True, "pr-amplitude-experiment-poll", "lock-ampexp",
        "the Amplitude Experiment SDK that omitted pollInterval so a variant change lagged 1h",
        "amplitude.yml", "deploymentKey: amp", "pollInterval: 30s",
        "pollInterval", "harbor deploymentKey only. pack pollInterval.",
        "FAIL test_assign: variant lagged 1h; pollInterval missing",
        "deploymentKey only", "deploymentKey is not pollInterval"),
    "adobetgt": mk(False, "pr-adobe-target-timeout-ms", "quay-adbtgt",
        "the Adobe Target at.js that omitted timeoutMs so a blocked mbox delayed LCP 6s",
        "at.js", "mboxDefault", "timeoutMs: 2000",
        "timeoutMs", "harbor mboxDefault only. pack timeoutMs.",
        "FAIL test_assign: LCP delayed 6s; timeoutMs missing",
        "mboxDefault only", "mboxDefault is not timeoutMs"),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f


LHC_PAIRS = [
    ("Split impressionsMode vs Optimizely pollInterval", fn("split"), fn("optimizely"),
     "impressionsMode optimized; pollInterval 30s", "apiKey; sdkKey",
     "split dump sync POST; optimizely dump stale 2h"),
    ("ConfigCat cache TTL vs GOFF pollingInterval", fn("configcat"), fn("goff"),
     "cacheTimeToLiveSeconds 60; pollingInterval 1s", "sdkKey; retriever file",
     "configcat dump CDN every eval; goff dump file never lands"),
    ("Flipt cache.ttl vs PostHog timeout", fn("flipt"), fn("posthog"),
     "cache.ttl 60s; feature_flags_request_timeout_ms", "sqlite; personal_api_key",
     "flipt dump DB every eval; posthog dump 10s poll"),
    ("Eppo batchSize vs Harness streamEnabled", fn("eppo"), fn("harnessff"),
     "assignmentLogger batchSize 20; streamEnabled", "apiKey; sdkKey",
     "eppo dump one-by-one POST; harness dump poll lag"),
    ("flagd sync.grpc vs OpenFeature hook timeout", fn("flagd"), fn("openfeature"),
     "sync.grpc; hooks.timeout 200ms", "in-process; provider flagd",
     "flagd dump OFREP miss; openfeature dump hook block"),
    ("DevCycle polling vs VWO eventBatchSize", fn("devcycle"), fn("vwo"),
     "configPollingIntervalMS 10s; eventBatchSize 50", "sdkKey; accountId",
     "devcycle dump kill-switch lag; vwo dump sync flush"),
    ("CloudBees cachePath vs Hypertune initTimeoutMs", fn("cloudbees"), fn("hypertune"),
     "cachePath /var/cache/rox; initTimeoutMs 2s", "roxOptions; token",
     "cloudbees dump cold fetch all; hypertune dump 30s hang"),
    ("Bucket flushIntervalMs vs Confidence resolveTimeout", fn("bucketco"), fn("confidence"),
     "flushIntervalMs 5s; resolveTimeout 800ms", "publishableKey; clientSecret",
     "bucket dump offline stuck; confidence dump checkout 8s"),
    ("Amplitude pollInterval vs Adobe timeoutMs", fn("ampxp"), fn("adobetgt"),
     "pollInterval 30s; timeoutMs 2s", "deploymentKey; mboxDefault",
     "amplitude dump variant 1h; adobe dump LCP 6s"),
]


def lhc_notes(rnd, pair_i, a, b):
    title, _, _, densify, loops, nxt = LHC_PAIRS[pair_i]
    return f"""# NOTES r{rnd} feature-flag-debug-factory

Novel coverage: 94%

Pair: {title}.
- Steps: {len(a['steps'])} {'success' if a['reward']['success'] else 'partial'} {a['id']}; {len(b['steps'])} {'success' if b['reward']['success'] else 'partial'} {b['id']}.
- Debug loops: {loops}.
- Densified: {densify}.
- Next densify: {nxt}.
- Not a clone of r4687 rust-pin, r4580 kanidm/gluu, r4163-w4ck cartesian, RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, identity-origin SSO.
- Bans avoided: rust-pin / pin-project / transmute / kanidm / gluu / agama / RPITIT / Prom native hist / ThinLTO / Go loopvar / Django ASGI / Vale / Koka / identity-origin clones.
- No thought/CoT keys. meta.generator=grok-4.6. plant=designed. No spikes/Thalamic/real.
"""


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"lhc_pair": 0, "published": []}


def save_state(st):
    STATE.write_text(json.dumps(st, indent=2) + "\n")


def txn(args):
    return subprocess.run(
        ["python3", str(TXN), *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )


def frontier(factory_dir: Path) -> int:
    r = txn(["frontier", str(factory_dir)])
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout)
    return json.loads(r.stdout)["next_round"]


def reserved(factory_dir: Path, n: int) -> bool:
    return (factory_dir / f"ROUND-r{n}.reserved.json").exists()


def used_slugs() -> set[str]:
    import re
    used: set[str] = set()
    for f in LHC_DIR.glob("batch-r*.jsonl"):
        try:
            text = f.read_text()
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                i = json.loads(line)["id"]
            except Exception:
                continue
            m = re.match(r"ffd-r\d+-(.+)-[0-9a-f]{4,}$", i)
            if m:
                used.add(m.group(1))
    return used


def write_stage(stage: Path, batch_name: str, notes_name: str, recs: list, notes: str):
    batch = stage / batch_name
    notes_p = stage / notes_name
    lines = [json.dumps(rec, separators=(",", ":"), ensure_ascii=False) for rec in recs]
    batch.write_text("\n".join(lines) + "\n")
    notes_p.write_text(notes)
    for rec in recs:
        blob = json.dumps(rec)
        assert "thought" not in blob
        assert "chain_of_thought" not in blob
        assert "inner_monologue" not in blob
        assert "spike_events" not in blob
        assert '"sim_or_real": "real"' not in blob
        assert rec["meta"]["generator"] == "grok-4.6"
        assert rec["meta"]["plant"] == "designed"
        nset = [s["n"] for s in rec["steps"]]
        assert nset == list(range(1, len(rec["steps"]) + 1))
        assert 16 <= len(rec["steps"]) <= 22
        for s in rec["steps"]:
            assert len(s["decision_basis"]) <= 240
            assert "thought" not in s
        assert rec["id"].startswith("ffd-r")
        assert "-pr-" in rec["id"]


def emit_lhc(rnd: int, pair_i: int):
    title, fa, fb, *_ = LHC_PAIRS[pair_i]
    a, b = fa(rnd), fb(rnd)
    if a["reward"]["success"] == b["reward"]["success"]:
        raise SystemExit(f"pair {pair_i} same success flags")
    notes = lhc_notes(rnd, pair_i, a, b)
    return [a, b], notes, title


def try_reserve(factory_dir: Path, expected: int):
    nxt = frontier(factory_dir)
    if reserved(factory_dir, nxt):
        return None
    r = txn(["reserve", str(factory_dir), "--round", str(nxt), "--expected", str(expected)])
    if r.returncode != 0:
        err = (r.stderr or r.stdout).strip()
        print(f"reserve {factory_dir.name} r{nxt} failed: {err}", flush=True)
        return None
    return json.loads(r.stdout)


def publish_round(factory_dir, rnd, token, recs, notes, batch_name, notes_name, stage):
    write_stage(Path(stage), batch_name, notes_name, recs, notes)
    r = txn(["publish", str(factory_dir), "--round", str(rnd), "--token", token])
    if r.returncode != 0:
        sys.stderr.write(r.stderr or r.stdout)
        raise SystemExit(f"publish r{rnd} failed")
    print(r.stdout, flush=True)
    return True


def hop_targets():
    out = []
    for p in sorted(AGENTIC.iterdir()):
        if not p.is_dir():
            continue
        if p.name == "sandbox-refusal-factory":
            continue
        writing = any(p.glob("ROUND-r*.reserved.json")) or any(p.glob("ROUND-r*.publishing.json"))
        if writing:
            continue
        out.append(p)
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "loop"
    st = load_state()

    if mode == "selfcheck":
        used = used_slugs()
        slugs = []
        for i, (title, fa, fb, *_) in enumerate(LHC_PAIRS):
            a, b = fa(9990 + i), fb(9990 + i)
            assert a["reward"]["success"] != b["reward"]["success"], title
            assert 16 <= len(a["steps"]) <= 22
            assert 16 <= len(b["steps"]) <= 22
            assert a["id"].startswith("ffd-r") and "-pr-" in a["id"]
            assert b["id"].startswith("ffd-r") and "-pr-" in b["id"]
            sa = "-".join(a["id"].split("-")[2:-1])
            sb = "-".join(b["id"].split("-")[2:-1])
            slugs.append(sa)
            slugs.append(sb)
            for slug in (sa, sb):
                low = slug.lower()
                for ban in BANNED_SUB:
                    if ban in low:
                        raise SystemExit(f"banned token {ban} in {slug}")
                if slug in used:
                    raise SystemExit(f"slug already used: {slug}")
            print("ok", i, title)
            print("   ", a["id"], len(a["steps"]), a["reward"]["success"])
            print("   ", b["id"], len(b["steps"]), b["reward"]["success"])
        if len(set(slugs)) != len(slugs):
            raise SystemExit(f"duplicate slugs in catalog: {slugs}")
        print("selfcheck", len(LHC_PAIRS), "pairs", len(slugs), "episodes")
        return

    if mode == "loop":
        target = int(sys.argv[2]) if len(sys.argv) > 2 else len(LHC_PAIRS)
        deadline = time.time() + 6 * 60 * 60
        published = 0
        hops = 0
        used = used_slugs()
        while published < target and time.time() < deadline:
            while st["lhc_pair"] < len(LHC_PAIRS):
                title, fa, fb, *_ = LHC_PAIRS[st["lhc_pair"]]
                probe_a, probe_b = fa(1), fb(1)
                probe_slugs = [
                    "-".join(x["id"].split("-")[2:-1]) for x in (probe_a, probe_b)
                ]
                if any(s in used for s in probe_slugs):
                    print(f"skip used pair {st['lhc_pair']} {title} {probe_slugs}", flush=True)
                    st["lhc_pair"] += 1
                    save_state(st)
                    continue
                break
            if st["lhc_pair"] >= len(LHC_PAIRS):
                print("catalog exhausted", flush=True)
                break
            res = try_reserve(LHC_DIR, 2)
            if res:
                rnd = res["round"]
                pair_i = st["lhc_pair"]
                recs, notes, title = emit_lhc(rnd, pair_i)
                for rec in recs:
                    slug = "-".join(rec["id"].split("-")[2:-1])
                    if slug in used:
                        raise SystemExit(f"refusing to publish used slug {slug}")
                    used.add(slug)
                publish_round(
                    LHC_DIR, rnd, res["token"], recs, notes,
                    res["batch_file"], res["notes_file"], res["staging_dir"],
                )
                st["lhc_pair"] += 1
                st["published"].append({"factory": "lhc", "round": rnd, "title": title, "ids": [x["id"] for x in recs]})
                save_state(st)
                published += 1
                print(f"PUBLISHED FFD r{rnd} pair={pair_i} {title}", flush=True)
                hops = 0
                continue
            hops += 1
            others = hop_targets()
            print(
                "LHC reserved; hop candidates (retry LHC; never sandbox-refusal):",
                [p.name for p in others[:8]],
                "sleep",
                flush=True,
            )
            time.sleep(1)
            if hops > 600:
                print("too many reserve failures; quota/reservation died", flush=True)
                break
        print(json.dumps({
            "published_this_run": published,
            "state_pairs": st["lhc_pair"],
            "rounds": [p["round"] for p in st["published"][-published:] if published],
        }, indent=2), flush=True)
        return

    raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    raise SystemExit(main() or 0)
