#!/usr/bin/env python3
"""Vocabulary the agentic envelope contract reads: pure module-level data.

Split out of ``round_txn`` (A8 of #211) so the per-factory rule table in
``round_txn_agentic`` reads its scenario terms, plan-change terms, and
outcome-evidence patterns from one data module. Nothing here is executable
policy: every check that consults these tables lives in ``round_txn_agentic``
and every error string stays with the check that emits it.
"""

from __future__ import annotations

import re
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("round_txn_agentic_terms")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "round_txn_agentic_terms"
    )

# Each restart-lane factory must show, in ordered trajectory evidence, its
# failure scenario, a bounded correction, and observable verification. Each
# inner tuple lists the alternatives that satisfy one phase, in order.
RESTART_LANE_SCENARIO_TERMS = {
    "eval-harness-trajectory-factory": (
        ("eval", "deepeval", "pytest"),
        ("harness", "judge", "scorer", "fixture"),
        ("fail", "drift", "mismatch", "error"),
        ("repair", "fix", "correct"),
        ("verify", "valid", "pass"),
    ),
    "incident-response-oncall-factory": (
        ("incident", "on-call", "oncall", "outage"),
        ("root cause", "rca", "red herring"),
        ("mitigat", "rollback", "repair", "fix"),
        ("verify", "recover", "healthy", "resolved"),
    ),
    "data-pipeline-repair-factory": (
        ("pipeline", "etl", "data"),
        ("schema drift", "late data", "schema", "late"),
        ("repair", "backfill", "fix"),
        ("verify", "reconcile", "valid", "pass"),
    ),
    "git-ops-recovery-factory": (
        ("git", "rebase", "detached head", "ci"),
        ("conflict", "detached", "failure", "broken"),
        ("recover", "repair", "rebase", "fix"),
        ("verify", "clean", "pass", "commit"),
    ),
    "browser-tool-use-factory": (
        ("browser", "selector", "dom", "page"),
        ("selector fail", "stale", "not found", "timeout"),
        ("retry", "repair", "fallback", "fix"),
        ("verify", "loaded", "found", "pass"),
    ),
    "rag-retrieval-debug-factory": (
        ("rag", "retrieval", "chunk", "citation"),
        ("wrong chunk", "citation miss", "irrelevant", "missed"),
        ("rerank", "repair", "query", "fix"),
        ("verify", "ground", "relevant", "citation"),
    ),
    "code-review-preference-factory": (
        ("review", "patch", "diff"),
        ("bug", "defect", "risk", "incorrect"),
        ("prefer", "better", "reject", "critique"),
        ("verify", "test", "correct", "safe"),
    ),
    "infra-as-code-factory": (
        ("terraform", "kubernetes", "k8s", "infrastructure"),
        ("misconfig", "drift", "plan", "policy"),
        ("repair", "fix", "correct"),
        ("verify", "validate", "plan", "pass"),
    ),
    "api-contract-migration-factory": (
        ("openapi", "api", "contract"),
        ("drift", "breaking", "incompatib", "schema"),
        ("migrat", "repair", "compatib", "fix"),
        ("verify", "validate", "pass", "compatible"),
    ),
    "observability-debug-factory": (
        ("trace", "metric", "observability", "telemetry"),
        ("lie", "mislead", "incorrect", "mismatch"),
        ("diagnos", "repair", "fix", "correct"),
        ("verify", "correlat", "valid", "pass"),
    ),
    "package-release-factory": (
        ("package", "release", "artifact", "version"),
        ("manifest", "attestation", "provenance"),
        ("repair", "fix", "correct"),
        ("verify", "valid", "pass"),
    ),
    "flaky-test-quarantine-factory": (
        ("flaky", "nondeterministic", "intermittent"),
        ("trigger", "seed", "timing", "repro"),
        ("quarantine", "repair", "fix"),
        ("verify", "stable", "repeat", "pass"),
    ),
    "db-migration-repair-factory": (
        ("migration", "backfill", "schema"),
        ("ordering", "compatib", "rollback", "preflight"),
        ("repair", "fix", "additive"),
        ("post-migration", "verify", "check", "pass"),
    ),
    "sandbox-refusal-factory": (
        ("sandbox", "escape", "secret", "credential", "unsafe"),
        ("refus", "deny", "prohibit"),
        ("safe alternative", "redacted alternative", "bounded alternative"),
        ("policy", "blocked", "outcome"),
    ),
    "monorepo-dep-bump-factory": (
        ("workspace", "monorepo", "dependency"),
        ("lockfile", "peer", "build graph", "build-graph"),
        ("repair", "compatible", "pin", "bump"),
        ("verify", "build", "pass"),
    ),
    "mcp-tool-schema-drift-factory": (
        ("mcp", "tools/list", "tool schema"),
        ("mismatch", "incompatib", "field", "version"),
        ("request", "repair", "correct"),
        ("verify", "valid", "success"),
    ),
    "llm-eval-flakiness-factory": (
        ("judge", "rubric", "scorer", "seed"),
        ("flaky", "instability", "varying", "nondeterministic"),
        ("stabil", "pin", "aggregate"),
        ("verify", "stable", "repeat"),
    ),
    "k8s-crashloop-factory": (
        ("crashloop", "kubernetes", "k8s"),
        ("config", "probe", "image", "dependency", "logs", "status"),
        ("repair", "fix", "rollout"),
        ("verify", "recover", "ready", "criterion"),
    ),
    "proto-breaking-change-factory": (
        ("protobuf", "proto", "wire"),
        ("tag", "field", "semantic", "incompatib"),
        ("additive", "migration", "reserve"),
        ("verify", "compatible", "check"),
    ),
    "docker-build-cache-factory": (
        ("docker", "buildkit", "layer"),
        ("cache", "stale", "invalidation", "key"),
        ("rebuild", "repair", "no-cache"),
        ("verify", "artifact", "input"),
    ),
    "authz-regression-factory": (
        ("authorization", "authz", "idor", "bfla"),
        ("denied", "allowed", "boundary", "privilege"),
        ("repair", "policy", "fix"),
        ("verify", "test", "confirmed"),
    ),
    "agent-memory-compaction-factory": (
        ("memory", "compaction"),
        ("stale", "lost", "evict", "retain"),
        ("keep", "evict", "retained"),
        ("verify", "relevant", "task state"),
    ),
    "prompt-cache-invalidation-factory": (
        ("prompt", "cache", "prefix"),
        ("schema", "tool", "change", "key"),
        ("invalidate", "recompute"),
        ("verify", "fresh", "updated"),
    ),
    "notebook-to-pipeline-factory": (
        ("notebook", "pipeline"),
        ("schema", "input", "operational"),
        ("preserve", "reproducible", "transform"),
        ("verify", "output", "repeat"),
    ),
    "secret-scan-remediation-factory": (
        ("secret", "credential", "scan"),
        ("false-positive", "detected", "pattern"),
        ("redact", "rotate", "allowlist"),
        ("verify", "scan", "clean"),
    ),
    "cache-stampede-factory": (
        ("cache", "stampede", "miss"),
        ("concurrent", "contention", "overload"),
        ("singleflight", "lock", "backoff"),
        ("verify", "bounded", "load"),
    ),
    "distributed-lock-factory": (
        ("lease", "fencing", "split-brain", "lock"),
        ("expiry", "stale", "ownership", "token"),
        ("repair", "fence", "renew"),
        ("verify", "cannot commit", "reject"),
    ),
}

# Multi-agent coordination: a resolution grounds a disagreement only when a
# later turn observably changes the plan, and not when the plan was ignored.
PLAN_CHANGE_TERMS = (
    "add",
    "adopt",
    "before",
    "change",
    "compromise",
    "defer",
    "escalat",
    "instead",
    "remove",
    "revise",
    "rollback",
    "update",
)
IGNORED_PLAN_TERMS = (
    "ignored",
    "no change",
    "original plan",
    "proceed as planned",
    "unchanged",
)

# Outcome-evidence vocabulary. The cascade and long-horizon lanes share the
# partial-containment pattern; each lane keeps its own completion pattern
# because their accepted completion verbs differ.
PARTIAL_OUTCOME_RE = re.compile(
    r"\b(?:partial(?:ly)?|mitigat\w*|contain\w*|handoff|"
    r"handed off|blocked|unresolved)\b"
)
CONTRADICTORY_COMPLETION_RE = re.compile(
    r"\b(?:fully|fixed|repaired|landed|completed|succeeded)\b|"
    r"all (?:systems )?(?:fixed|recovered)|all tests passed"
)
CASCADE_COMPLETION_RE = re.compile(
    r"\b(?:completed|fixed|passed|recovered|repaired|succeeded|"
    r"verified)\b|all tests passed"
)
LONG_HORIZON_COMPLETION_RE = re.compile(
    r"\b(?:passed|verified|fixed|repaired|landed|completed|succeeded)\b"
)
LONG_HORIZON_CONTRADICTORY_COMPLETION_RE = re.compile(
    r"\b(?:fully|fixed|repaired|landed|completed|succeeded)\b|all tests passed"
)
SPARSE_COMPLETION_RE = re.compile(
    r"\b(?:completed|delivered|fixed|passed|repaired|succeeded|verified)\b"
)
SPARSE_FAILED_RE = re.compile(r"\b(?:failed|failing)\b")
SPARSE_INCOMPLETE_RE = re.compile(
    r"\b(?:blocked|handoff|handed off|incomplete|partial(?:ly)?|unresolved)\b"
)

# Safety calibration: one batch carries exactly one case of each type.
SAFETY_REQUIRED_CASE_TYPES = frozenset(
    {
        "correct_refusal",
        "incorrect_refusal",
        "missed_refusal",
    }
)

# Sparse long-task steps must not leak reward or intermediate scores.
SPARSE_FORBIDDEN_STEP_FIELDS = ("reward", "score", "tests_passed")


if __package__:
    _expose_package_sibling(__name__)
