"""JSONL batch curation for the tag taxonomy transform."""

from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path
from typing import Any

from tag_constants import (
    REASON_INVALID_JSON,
    REASON_INVALID_UTF8,
    REASON_RECORD_TOO_DEEP,
    RULE_TRANSFORM,
    TAG_PROVENANCE_FIELD,
    TagTaxonomyError,
)
from tag_jsonutil import (
    canonical_json,
    count_tag,
    display_source_path,
    load_strict_json,
    vocabulary_entropy,
)
from tag_record import base_manifest, curate_record
from tag_taxonomy import Taxonomy, load_taxonomy


def _excluded_line_manifest(
    origin: tuple[str, int, str], taxonomy_version: str, reason: str
) -> dict[str, Any]:
    source_path, source_line, source_hash = origin
    manifest = base_manifest(
        (source_path, source_line, source_hash), taxonomy_version
    )
    manifest["reason_codes"] = [reason]
    return manifest


def _raw_line_bytes(terminated_line: bytes) -> bytes:
    terminated = (
        terminated_line[:-1]
        if terminated_line.endswith(b"\n")
        else terminated_line
    )
    if terminated.endswith(b"\r"):
        return terminated[:-1]
    return terminated


def _parse_jsonl_payload(raw_line: bytes) -> tuple[Any, str | None]:
    try:
        text = raw_line.decode("utf-8")
    except UnicodeDecodeError:
        return None, REASON_INVALID_UTF8
    try:
        record = load_strict_json(text)
    except RecursionError:
        return None, REASON_RECORD_TOO_DEEP
    except ValueError:
        return None, REASON_INVALID_JSON
    return _reject_unencodable_record(record)


def _reject_unencodable_record(record: Any) -> tuple[Any, str | None]:
    try:
        canonical_json(record).encode("utf-8")
    except RecursionError:
        return None, REASON_RECORD_TOO_DEEP
    except (TypeError, ValueError, UnicodeEncodeError):
        return None, REASON_INVALID_JSON
    return record, None


def curate_jsonl(
    source_path: str | Path, taxonomy: Taxonomy | None = None
) -> dict[str, Any]:
    """Read a JSONL source without mutation and curate every nonblank line."""
    vocabulary = taxonomy if taxonomy is not None else load_taxonomy()
    source = Path(source_path)
    try:
        display_path = display_source_path(source)
    except UnicodeDecodeError as exc:
        raise TagTaxonomyError(f"source path is not valid UTF-8: {source}") from exc
    batch = _JsonlBatch(display_path, vocabulary)
    with source.open("rb") as handle:
        for line_number, terminated_line in enumerate(handle, 1):
            batch.consume_line(line_number, terminated_line)
    return batch.result()


class _JsonlBatch:
    def __init__(self, display_path: str, vocabulary: Taxonomy) -> None:
        self.display_path = display_path
        self.vocabulary = vocabulary
        self.records: list[dict[str, Any]] = []
        self.manifests: list[dict[str, Any]] = []
        self.source_uses: Counter = Counter()
        self.source_total = 0
        self.canonical_uses: Counter = Counter()
        self.unmapped_uses: Counter = Counter()
        self.unmapped_originals: dict[tuple[str, str], Any] = {}
        self.rule_uses: Counter = Counter()
        self.nonstring_uses = 0

    def consume_line(self, line_number: int, terminated_line: bytes) -> None:
        raw_line = _raw_line_bytes(terminated_line)
        if not raw_line.strip():
            return
        origin = (
            self.display_path,
            line_number,
            hashlib.sha256(raw_line).hexdigest(),
        )
        record, reason = _parse_jsonl_payload(raw_line)
        if reason is not None:
            self.manifests.append(
                _excluded_line_manifest(origin, self.vocabulary.version, reason)
            )
            return
        self._curate_parsed(record, origin)

    def _curate_parsed(
        self, record: Any, origin: tuple[str, int, str]
    ) -> None:
        try:
            curated, manifest = curate_record(
                record, taxonomy=self.vocabulary, origin=origin
            )
        except RecursionError:
            self.manifests.append(
                _excluded_line_manifest(
                    origin, self.vocabulary.version, REASON_RECORD_TOO_DEEP
                )
            )
            return
        self.manifests.append(manifest)
        if curated is None:
            return
        self.records.append(curated)
        self._count_curated(curated)

    def _count_curated(self, curated: dict[str, Any]) -> None:
        provenance = curated.get(TAG_PROVENANCE_FIELD)
        containers = provenance.get("containers", []) if provenance else []
        for entry in containers:
            self._count_entry(entry)

    def _count_entry(self, entry: dict[str, Any]) -> None:
        self.source_total += len(entry["source_tags"])
        for tag in entry["source_tags"]:
            count_tag(self.source_uses, tag)
        for tag in entry["canonical_tags"]:
            self.canonical_uses[tag] += 1
        self._count_unmapped(entry["unmapped_tags"])
        self._count_rules(entry["mappings"])

    def _count_unmapped(self, tags: list[Any]) -> None:
        for tag in tags:
            if not isinstance(tag, str):
                self.nonstring_uses += 1
            count_tag(self.unmapped_uses, tag, self.unmapped_originals)

    def _count_rules(self, mappings: list[dict[str, Any]]) -> None:
        for mapping in mappings:
            rule = mapping.get("rule")
            if rule:
                self.rule_uses[rule] += 1

    def result(self) -> dict[str, Any]:
        unmapped_report = _unmapped_report(
            self.unmapped_uses, self.unmapped_originals
        )
        return {
            "records": self.records,
            "manifest": self.manifests,
            "unmapped": unmapped_report,
            "summary": self._summary(unmapped_report),
        }

    def _summary(self, unmapped_report: list[dict[str, Any]]) -> dict[str, Any]:
        source_entropy = vocabulary_entropy(self.source_uses)
        canonical_entropy = vocabulary_entropy(self.canonical_uses)
        return {
            "source_path": self.display_path,
            "taxonomy_version": self.vocabulary.version,
            "taxonomy_size": len(self.vocabulary.canonical_tags),
            "input_records": len(self.manifests),
            "output_records": len(self.records),
            "excluded_records": sum(
                item["action"] == "excluded" for item in self.manifests
            ),
            "tag_containers": sum(
                item["tag_counts"]["containers"] for item in self.manifests
            ),
            "source_tag_uses": self.source_total,
            "source_unique_tags": len(self.source_uses),
            "canonical_tag_uses": sum(self.canonical_uses.values()),
            "canonical_unique_tags": len(self.canonical_uses),
            "mapped_tag_uses": sum(
                count
                for rule, count in self.rule_uses.items()
                if rule != RULE_TRANSFORM
            ),
            "unmapped_tag_uses": sum(self.unmapped_uses.values()),
            "unmapped_unique_tags": len(self.unmapped_uses),
            "nonstring_tag_uses": self.nonstring_uses,
            "entropy_bits": {
                "source": source_entropy,
                "canonical": canonical_entropy,
                "reduction": round(source_entropy - canonical_entropy, 6),
            },
            "rule_uses": dict(sorted(self.rule_uses.items())),
            "canonical_tag_counts": dict(sorted(self.canonical_uses.items())),
            "unmapped_tags": unmapped_report,
        }


def _unmapped_report(
    unmapped_uses: Counter, unmapped_originals: dict[tuple[str, str], Any]
) -> list[dict[str, Any]]:
    return [
        {"tag": unmapped_originals[ident], "count": count}
        for ident, count in sorted(
            unmapped_uses.items(),
            key=lambda kv: _unmapped_sort_item(kv, unmapped_originals),
        )
    ]


def _unmapped_sort_item(
    kv: tuple[tuple[str, str], int],
    unmapped_originals: dict[tuple[str, str], Any],
) -> tuple[int, tuple[int, Any]]:
    ident, count = kv
    original = unmapped_originals[ident]
    if isinstance(original, str):
        return -count, (0, original)
    return -count, (1, ident[1])
