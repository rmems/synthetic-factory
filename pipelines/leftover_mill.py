#!/usr/bin/env python3
"""Shared leftover-mill reporting and kind-mix quarantine.

PR #96 owns mill detection and ownership resolution in `mill_family.py`.
Issue #43 freezes its 30 published factory-mix IDs here and exposes a focused
CLI view of the shared `census.py` result.

`leftover` inside a record ID is a goal-naming convention, never grounds for
quarantine. Records are excluded only when the shared detector proves that
their payload-factory, mill-prefix, or goal-family evidence belongs elsewhere.

Issue #30 adds one complementary detector class: payload kind differing from
the destination's declared kind. `curate_agentic.classify_record` decides what
a record is; directory slugs and `*-leftover` suffixes are not evidence.
The 12 already-published episode records inside
`code-review-preference-factory` are acknowledged by immutable raw provenance
so curation and publication can name them while every new kind mix fails.

Raw JSONL is immutable evidence and is never rewritten.

Usage: python3 pipelines/leftover_mill.py [--strict] <run_dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from census import census_dir  # noqa: E402
from curate_agentic import classify_record  # noqa: E402
from round_txn import AGENTIC_FACTORY_KINDS, TransactionError  # noqa: E402

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


REASON_KIND_MIX = "LEFTOVER_MILL_KIND_MIX"

# Kinds that identify a concrete generation mill. ``unknown`` (unclassifiable)
# and ``legacy_preference`` (a pre-agentic preference shape) name no mill, so
# they are never reported as kind mix.
MILL_KINDS = frozenset(
    {
        "episode",
        "preference",
        "multi_agent",
        "safety_case",
        "bridge_pair",
        "thalamic",
    }
)

# Kind-mix records that are already published as raw evidence. They are
# excluded from preference curation and disclosed on the dataset card; the raw
# lines that carry them are never edited. Only records confirmed by a
# payload-first census belong here — this ledger acknowledges history, it does
# not grant a waiver for new mill mix.
KIND_MIX_QUARANTINE: dict[str, tuple[str, ...]] = {
    "code-review-preference-factory": (
        "dbc-r723-buildah-layers-vfs-id-leftover",
        "dbc-r723-buildah-vfs-graphroot-leftover",
        "dbc-r724-podman-sqlite-diff-leftover",
        "dbc-r724-podman-boltdb-compat-leftover",
        "dbc-r725-nerdctl-namespace-snapshot-leftover",
        "dbc-r725-nerdctl-cni-cache-leftover",
        "dbc-r726-containerd-content-lease-leftover",
        "dbc-r726-containerd-gc-label-leftover",
        "dbc-r727-crio-imagestore-pin-leftover",
        "dbc-r727-crio-overlay-mounts-leftover",
        "dbc-r728-buildx-builder-driver-opt-leftover",
        "dbc-r728-buildx-provenance-mode-leftover",
    ),
}


@dataclass(frozen=True)
class KindMixFinding:
    """One record whose payload kind disagrees with its destination."""

    source_name: str
    source_line: int
    record_id: str | None
    record_kind: str
    expected_kind: str
    acknowledged: bool

    def describe(self) -> str:
        return (
            f"{self.source_name}:{self.source_line} "
            f"{self.record_id or '<no-id>'} is {self.record_kind!r}, "
            f"destination requires {self.expected_kind!r}"
        )


def destination_kind(slug: str) -> str | None:
    """Return the record kind a factory slug is declared to publish."""
    return AGENTIC_FACTORY_KINDS.get(slug)


def is_preference_destination(slug: str) -> bool:
    """Whether a factory slug publishes preference pairs."""
    return destination_kind(slug) == "preference"


def quarantined_ids(slug: str) -> frozenset[str]:
    """Return the acknowledged kind-mix record ids for one factory slug."""
    return frozenset(KIND_MIX_QUARANTINE.get(slug, ()))


def record_id(record: Any) -> str | None:
    """Return a record's own id, falling back to ``meta.id``."""
    if not isinstance(record, dict):
        return None
    for container in (record, record.get("meta")):
        if not isinstance(container, dict):
            continue
        value = container.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def kind_mix_kind(record: Any, expected_kind: str | None) -> str | None:
    """Return the mill kind of a kind-mix record, or ``None`` when it fits.

    ``expected_kind`` of ``None`` means the destination declares no kind, so
    nothing can disagree with it.
    """
    if expected_kind is None:
        return None
    kind = classify_record(record)
    if kind == expected_kind or kind not in MILL_KINDS:
        return None
    return kind


def find_kind_mix(
    records: Iterable[tuple[int, Any]],
    expected_kind: str | None,
    *,
    slug: str,
    source_name: str,
) -> list[KindMixFinding]:
    """Report kind-mix findings for ``(line_number, record)`` pairs."""
    if expected_kind is None:
        return []
    acknowledged = quarantined_ids(slug)
    findings = []
    for line_number, record in records:
        kind = kind_mix_kind(record, expected_kind)
        if kind is None:
            continue
        identifier = record_id(record)
        findings.append(
            KindMixFinding(
                source_name=source_name,
                source_line=line_number,
                record_id=identifier,
                record_kind=kind,
                expected_kind=expected_kind,
                acknowledged=identifier is not None and identifier in acknowledged,
            )
        )
    return findings


def scan_jsonl_kind_mix(
    path: Path,
    expected_kind: str | None,
    *,
    slug: str,
    source_name: str | None = None,
) -> list[KindMixFinding]:
    """Scan one JSONL payload for kind mix without mutating it.

    A line that is not decodable JSON is reported as an unacknowledgeable
    ``unparseable`` finding: an undecodable record cannot be proven free of
    mill mix, so a gated destination must refuse it rather than assume it fits.
    """
    if expected_kind is None:
        return []
    name = source_name or path.name
    decoded: list[tuple[int, Any]] = []
    findings: list[KindMixFinding] = []
    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            if not raw_line.strip():
                continue
            try:
                decoded.append((line_number, json.loads(raw_line.decode("utf-8"))))
            except (UnicodeDecodeError, json.JSONDecodeError):
                findings.append(
                    KindMixFinding(
                        source_name=name,
                        source_line=line_number,
                        record_id=None,
                        record_kind="unparseable",
                        expected_kind=expected_kind,
                        acknowledged=False,
                    )
                )
    findings.extend(
        find_kind_mix(decoded, expected_kind, slug=slug, source_name=name)
    )
    findings.sort(key=lambda finding: (finding.source_name, finding.source_line))
    return findings


def unacknowledged(findings: Iterable[KindMixFinding]) -> list[KindMixFinding]:
    """Return the findings that no quarantine ledger entry covers."""
    return [finding for finding in findings if not finding.acknowledged]


if __name__ == "__main__":
    raise SystemExit(main())
