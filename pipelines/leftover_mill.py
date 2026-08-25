#!/usr/bin/env python3
"""Issue #43 leftover-mill ledger and read-only eligible-denominator report.

PR #96 owns mill detection and ownership resolution in `mill_family.py`.
This module does not implement a second classifier. It freezes the 30 published
factory-mix IDs from issue #43 and exposes a focused CLI view of the shared
`census.py` result.

`leftover` inside a record ID is a goal-naming convention, never grounds for
quarantine. Records are excluded only when the shared detector proves that
their payload-factory, mill-prefix, or goal-family evidence belongs elsewhere.
Raw JSONL is never rewritten.

Usage: python3 pipelines/leftover_mill.py [--strict] <run_dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from census import census_dir  # noqa: E402
from round_txn import TransactionError  # noqa: E402

# Frozen issue #43 census: destination factory -> {record id: declared factory}.
# Detection never consults this table. Tests re-derive each finding through the
# shared MillIndex so the ledger cannot silently become a waiver mechanism.
PUBLISHED_FACTORY_MIX: dict[str, dict[str, str]] = {
    "email-webhook-retry-factory": {
        "sir-r56-meili-swap-leftover3c-rebuild": "search-index-rebuild-factory",
        "sir-r56-meili-drop-index-leftover3c-handoff": "search-index-rebuild-factory",
        "sir-r57-typesense-alias-leftover3c-rebuild": "search-index-rebuild-factory",
        "sir-r57-typesense-drop-coll-leftover3c-handoff": "search-index-rebuild-factory",
        "sir-r58-sonic-push-leftover3c-rebuild": "search-index-rebuild-factory",
        "sir-r58-sonic-drop-bucket-leftover3c-handoff": "search-index-rebuild-factory",
    },
    "eval-harness-trajectory-factory": {
        "srl-r641-networkd-dhcp-ipv4-only-c67a": "sparse-reward-long-task-factory",
        "srl-r642-chrony-maxslewrate-vs-ntpd-ffb5": "sparse-reward-long-task-factory",
        "srl-r643-nft-flowtable-timeout-vs-ipt-035c": "sparse-reward-long-task-factory",
        "srl-r644-podman-events-logger-journald-e10f": "sparse-reward-long-task-factory",
        "srl-r645-buildah-format-oci-vs-docker-b703": "sparse-reward-long-task-factory",
    },
    "observability-debug-factory": {
        "srl-r500-networkd-dhcp-ipv4-only-c67a": "sparse-reward-long-task-factory",
    },
    "rag-retrieval-debug-factory": {
        "evh-r21-cite-orphan-c3e8": "eval-harness-trajectory-factory",
        "evh-r21-hybrid-sku-a91b": "eval-harness-trajectory-factory",
        "evh-r22-rerank-pad-d7f2": "eval-harness-trajectory-factory",
        "evh-r22-ragas-param-b4c1": "eval-harness-trajectory-factory",
        "evh-r23-embed-mismatch-e5a0": "eval-harness-trajectory-factory",
        "evh-r23-tenant-filter-f2c9": "eval-harness-trajectory-factory",
        "evh-r24-table-split-a8d3": "eval-harness-trajectory-factory",
        "evh-r24-mmr-drop-b7e1": "eval-harness-trajectory-factory",
        "evh-r25-stale-alias-c4b2": "eval-harness-trajectory-factory",
        "evh-r25-compress-numeral-d9aa": "eval-harness-trajectory-factory",
        "evh-r26-parent-cite-e1f6": "eval-harness-trajectory-factory",
        "evh-r26-hnsw-ef-f8c0": "eval-harness-trajectory-factory",
        "evh-r27-cohere-topn-a6b8": "eval-harness-trajectory-factory",
        "evh-r27-recency-bury-c2d4": "eval-harness-trajectory-factory",
        "evh-r28-lost-middle-g3a1": "eval-harness-trajectory-factory",
        "evh-r28-weaviate-cert-h4b2": "eval-harness-trajectory-factory",
        "evh-r29-history-embed-j5c3": "eval-harness-trajectory-factory",
        "evh-r29-pinecone-ns-k6d4": "eval-harness-trajectory-factory",
    },
}


def expected_factory_mix_ids() -> frozenset[str]:
    """Return all 30 record IDs frozen by the issue #43 census."""

    return frozenset(
        record_id
        for records in PUBLISHED_FACTORY_MIX.values()
        for record_id in records
    )


def audit_run(run_dir: Path | str) -> dict:
    """Return the shared census as an issue-focused quarantine report."""

    census = census_dir(run_dir)
    mix = census["mill_mix"]
    by_factory = {
        factory: {
            "records": records,
            "eligible": census["eligible_by_factory"][factory],
            "quarantined": records - census["eligible_by_factory"][factory],
        }
        for factory, records in census["by_factory"].items()
    }
    return {
        "run_dir": census["run_dir"],
        "files": census["files"],
        "records": census["records"],
        "parse_failures": census["parse_failures"],
        "decode_failures": census["decode_failures"],
        "unreadable_files": census["unreadable_files"],
        "eligible_records": census["eligible_records"],
        "quarantined": mix["records"],
        "reason_codes": mix["reason_codes"],
        "by_factory": by_factory,
        "quarantined_records": mix["quarantined_records"],
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only shared-detector leftover-mill audit."
    )
    parser.add_argument("run_dir", help="run directory holding factory JSONL")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 on a mill finding, invalid JSON, or invalid UTF-8",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        print(f"leftover_mill: not a directory: {run_dir}", file=sys.stderr)
        return 2
    try:
        report = audit_run(run_dir)
    except TransactionError as exc:
        print(f"leftover_mill failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    failed = (
        report["quarantined"]
        or report["parse_failures"]
        or report["decode_failures"]
    )
    return 1 if args.strict and failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
