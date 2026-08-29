#!/usr/bin/env python3
"""Reviewed mill-identity reference tables used by ``mill_family.py``.

Pure data, no logic: every mill id prefix and goal-vocabulary term whose
ownership has been independently reviewed and pinned. Split out of
``mill_family.py`` verbatim (byte-identical values) purely to keep that
module's own line count to its resolution logic; every name here is
re-exported from ``mill_family`` so existing ``from mill_family import
REVIEWED_...`` call sites are unaffected.
"""

from __future__ import annotations

# Reviewed generator aliases are independent ownership evidence. The registry
# freezes every prefix observed in the read-only 2026-08-19 agentic census,
# including native aliases and the known cross-destination spills. Unknown
# aliases remain useful for report-only inference, but can never authorize a
# cleaned output until their ownership is reviewed and added here.
REVIEWED_MILL_PREFIX_HOMES = {
    "acm": "api-contract-migration-factory",
    "amc": "agent-memory-compaction-factory",
    "azr": "authz-regression-factory",
    "brw": "browser-tool-use-factory",
    "cei": "csv-excel-ingest-factory",
    "cer": "cascading-error-recovery-factory",
    "crp": "code-review-preference-factory",
    "cst": "cache-stampede-factory",
    "dbc": "docker-build-cache-factory",
    "dbm": "db-migration-repair-factory",
    "dlk": "distributed-lock-factory",
    "dmr": "db-migration-repair-factory",
    "dpr": "data-pipeline-repair-factory",
    "evh": "eval-harness-trajectory-factory",
    "ewr": "email-webhook-retry-factory",
    "ffd": "feature-flag-debug-factory",
    "flk": "flaky-test-quarantine-factory",
    "ftq": "flaky-test-quarantine-factory",
    "gor": "git-ops-recovery-factory",
    "gql": "graphql-nplusone-factory",
    "iac": "infra-as-code-factory",
    "irc": "incident-response-oncall-factory",
    "kcl": "k8s-crashloop-factory",
    "lef": "llm-eval-flakiness-factory",
    "lhc": "long-horizon-coding-factory",
    "lrd": "log-redaction-factory",
    "mac": "multi-agent-coordination-factory",
    "mdb": "monorepo-dep-bump-factory",
    "msd": "mcp-tool-schema-drift-factory",
    "ntp": "notebook-to-pipeline-factory",
    "obs": "observability-debug-factory",
    "pay": "payment-idempotency-factory",
    "pbc": "proto-breaking-change-factory",
    "pci": "prompt-cache-invalidation-factory",
    "pid": "payment-idempotency-factory",
    "pkg": "package-release-factory",
    "qbp": "queue-backpressure-factory",
    "rag": "rag-retrieval-debug-factory",
    "rlb": "rate-limit-backoff-factory",
    "saf": "safety-calibration-factory",
    "sbox": "sandbox-refusal-factory",
    "scr": "ssl-cert-rotation-factory",
    "sir": "search-index-rebuild-factory",
    "srl": "sparse-reward-long-task-factory",
    "ssl": "ssl-cert-rotation-factory",
    "ssr": "secret-scan-remediation-factory",
    "tup": "tool-use-preference-factory",
    "wsr": "websocket-reconnect-factory",
}

# Distinctive vocabulary from the source and destination mills in the frozen
# #44 census. Generic words stay corpus-derived; only generator/product terms
# whose ownership was independently reviewed are pinned here. These signatures
# are also the closed-world boundary for authorizing cleaned output: novel goal
# families in one of these lanes stay unresolved instead of teaching
# themselves through repetition.
REVIEWED_GOAL_TOKEN_HOMES = {
    "crashloopbackoff": "k8s-crashloop-factory",
    "expiry": "cache-stampede-factory",
    "herd": "cache-stampede-factory",
    "liveness": "k8s-crashloop-factory",
    "probe": "k8s-crashloop-factory",
    "refills": "cache-stampede-factory",
    "restart": "k8s-crashloop-factory",
    "singleflight": "cache-stampede-factory",
    "stampede": "cache-stampede-factory",
    "throttling": "rate-limit-backoff-factory",
    "thundering": "cache-stampede-factory",
    "ttl": "cache-stampede-factory",
    "backoff": "rate-limit-backoff-factory",
    "jitter": "rate-limit-backoff-factory",
    "ratelimit": "rate-limit-backoff-factory",
    "retry": "rate-limit-backoff-factory",
    "buildkit": "docker-build-cache-factory",
    "blobcache": "docker-build-cache-factory",
    "cachemount": "docker-build-cache-factory",
    "estargz": "docker-build-cache-factory",
    "exporter": "docker-build-cache-factory",
    "layers": "docker-build-cache-factory",
    "nydus": "docker-build-cache-factory",
    "overlayfs": "docker-build-cache-factory",
    "rafs": "docker-build-cache-factory",
    "solver": "docker-build-cache-factory",
    "stargz": "docker-build-cache-factory",
    "toc": "docker-build-cache-factory",
    "whiteout": "docker-build-cache-factory",
    "analyzer": "graphql-nplusone-factory",
    "costnew": "graphql-nplusone-factory",
    "costold": "graphql-nplusone-factory",
    "edgedb": "graphql-nplusone-factory",
    "globalberth": "graphql-nplusone-factory",
    "globals": "graphql-nplusone-factory",
    "globalyard": "graphql-nplusone-factory",
    "hotchocolate": "graphql-nplusone-factory",
    "makewrapresolvers": "graphql-nplusone-factory",
    "postgraphile": "graphql-nplusone-factory",
    "projection": "graphql-nplusone-factory",
    "wrapmass": "graphql-nplusone-factory",
    "wrappull": "graphql-nplusone-factory",
}

# One record can legitimately cross domain boundaries: a Git recovery task can
# mention retry jitter, an on-call incident can involve stargz, and a coding
# task can repair a cache stampede. These strong anchors distinguish a reviewed
# product signature from generic reviewed words. They never convict a different
# home by themselves: goal-only foreign evidence must still recur as an
# independently clean cohort.
REVIEWED_GOAL_STRONG_ANCHORS = frozenset(
    {
        "singleflight",
        "crashloopbackoff",
        "ratelimit",
        "blobcache",
        "buildkit",
        "cachemount",
        "estargz",
        "nydus",
        "overlayfs",
        "rafs",
        "costnew",
        "costold",
        "edgedb",
        "globalberth",
        "globalyard",
        "hotchocolate",
        "makewrapresolvers",
        "postgraphile",
        "wrapmass",
        "wrappull",
    }
)
