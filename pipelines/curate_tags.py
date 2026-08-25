#!/usr/bin/env python3
"""Map free-form corpus tags onto the controlled taxonomy in tag-taxonomy-v1.

The 2026-08-17 raw corpus carries a free-form tag surface of roughly 2790
distinct strings, most of them used exactly once.  This transform replaces that
surface with the compact versioned vocabulary declared in
``schemas/tag-taxonomy-v1.json``.

The mapping is deterministic and conservative:

* a source tag becomes canonical only through an alias or an anchored pattern
  rule declared in the taxonomy file;
* alias and pattern lookup run on a purely lexical normal form, so case and
  separator variants fold together without inventing meaning;
* every canonical tag maps to itself, which makes the transform idempotent;
* a source tag with no declared mapping is never guessed at.  It is dropped
  from the curated tag list, reported explicitly, and preserved verbatim in the
  record's ``tag_provenance`` so the original vocabulary stays recoverable.

``curate_jsonl`` returns curated records, a reversible manifest, an explicit
unmapped-tag report, and vocabulary-entropy summary counts.  The optional CLI
writes only to new, non-raw files.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any


TRANSFORM_NAME = "tag_taxonomy"
TRANSFORM_VERSION = "1"

TAGS_KEY = "tags"
TAG_PROVENANCE_FIELD = "tag_provenance"
UNMAPPED_MARKER_TAG = "curation:unmapped_source_tags"

DEFAULT_TAXONOMY_PATH = (
    Path(__file__).resolve().parents[1] / "schemas" / "tag-taxonomy-v1.json"
)

RULE_CANONICAL = "canonical"
RULE_ALIAS = "alias"
RULE_PATTERN_PREFIX = "pattern:"
RULE_TRANSFORM = "transform"

REASON_TAG_CANONICAL = "tag_already_canonical"
REASON_TAG_ALIAS = "tag_mapped_alias"
REASON_TAG_PATTERN = "tag_mapped_pattern"
REASON_TAG_UNMAPPED = "tag_unmapped"
REASON_TAG_NOT_STRING = "tag_not_a_string"
REASON_TAG_EMPTY = "tag_empty_after_normalization"

REASON_TAGS_MAPPED = "tags_mapped"
REASON_TAGS_UNMAPPED = "tags_unmapped_present"
REASON_TAGS_DEDUPLICATED = "tags_deduplicated"
REASON_TAGS_PROVENANCE_REUSED = "tags_provenance_reused"

REASON_RECORD_NOT_OBJECT = "tag_record_not_object"
REASON_TAGS_NOT_LIST = "tag_container_not_list"
REASON_PROVENANCE_CONFLICT = "tag_provenance_conflict"
REASON_INVALID_JSON = "tag_invalid_json"
REASON_INVALID_UTF8 = "tag_invalid_utf8"

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


class TagTaxonomyError(ValueError):
    """Raised when a taxonomy document violates its own declared contract."""


def normalize_tag(tag: str) -> str:
    """Fold a source tag to its lexical normal form.

    The fold is lexical only: case and separator variants collapse, nothing
    else.  It never assigns meaning to a label.
    """
    return _NON_ALNUM_RE.sub("_", tag.strip().lower()).strip("_")


def canonical_json(value: Any) -> str:
    """Return the stable JSON representation used for output hashes."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _reject_json_constant(value: str) -> None:
    """Reject Python-only numeric constants accepted by ``json.loads``."""
    raise ValueError(f"non-standard JSON numeric constant: {value}")


def hash_value(value: Any) -> str:
    """Hash a parsed value deterministically."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def vocabulary_entropy(counts: Counter | dict[str, int]) -> float:
    """Return the Shannon entropy, in bits, of a tag-use distribution."""
    total = sum(count for count in counts.values() if count > 0)
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        share = count / total
        entropy -= share * math.log2(share)
    return round(entropy, 6)


class Taxonomy:
    """A loaded, validated controlled tag vocabulary."""

    def __init__(self, document: dict[str, Any], *, source: str) -> None:
        self.source = source
        self.version = _require_str(document, "version", source)
        canonical_pattern = _require_str(document, "canonical_tag_pattern", source)
        try:
            self._canonical_re = re.compile(canonical_pattern)
        except re.error as exc:  # pragma: no cover - guarded by tests
            raise TagTaxonomyError(
                f"{source}: canonical_tag_pattern is not a valid regex: {exc}"
            ) from exc

        facets = document.get("facets")
        if not isinstance(facets, list) or not facets:
            raise TagTaxonomyError(f"{source}: facets must be a nonempty array")

        self.facet_of: dict[str, str] = {}
        self.definition_of: dict[str, str] = {}
        self.alias_index: dict[str, str] = {}
        alias_owner: dict[str, str] = {}

        for facet in facets:
            if not isinstance(facet, dict):
                raise TagTaxonomyError(f"{source}: every facet must be an object")
            facet_id = _require_str(facet, "id", source)
            terms = facet.get("terms")
            if not isinstance(terms, list) or not terms:
                raise TagTaxonomyError(
                    f"{source}: facet {facet_id} must declare a nonempty terms array"
                )
            for term in terms:
                if not isinstance(term, dict):
                    raise TagTaxonomyError(
                        f"{source}: every term in facet {facet_id} must be an object"
                    )
                tag = _require_str(term, "tag", source)
                if not self._canonical_re.match(tag):
                    raise TagTaxonomyError(
                        f"{source}: canonical tag {tag!r} does not match "
                        f"canonical_tag_pattern"
                    )
                if not tag.startswith(f"{facet_id}:"):
                    raise TagTaxonomyError(
                        f"{source}: canonical tag {tag!r} is not in facet {facet_id}"
                    )
                if tag in self.facet_of:
                    raise TagTaxonomyError(
                        f"{source}: canonical tag {tag!r} is declared twice"
                    )
                self.facet_of[tag] = facet_id
                self.definition_of[tag] = _require_str(term, "definition", source)

                aliases = term.get("aliases", [])
                if not isinstance(aliases, list):
                    raise TagTaxonomyError(
                        f"{source}: aliases for {tag!r} must be an array"
                    )
                for alias in [tag, *aliases]:
                    if not isinstance(alias, str) or not alias.strip():
                        raise TagTaxonomyError(
                            f"{source}: alias for {tag!r} must be a nonempty string"
                        )
                    key = normalize_tag(alias)
                    if not key:
                        raise TagTaxonomyError(
                            f"{source}: alias {alias!r} for {tag!r} normalizes to nothing"
                        )
                    owner = alias_owner.get(key)
                    if owner is not None and owner != tag:
                        raise TagTaxonomyError(
                            f"{source}: alias {alias!r} maps to both {owner!r} and {tag!r}"
                        )
                    alias_owner[key] = tag
                    self.alias_index[key] = tag

        rules = document.get("pattern_rules", [])
        if not isinstance(rules, list):
            raise TagTaxonomyError(f"{source}: pattern_rules must be an array")
        self.pattern_rules: list[tuple[str, str, re.Pattern[str]]] = []
        seen_rule_ids: set[str] = set()
        for rule in rules:
            if not isinstance(rule, dict):
                raise TagTaxonomyError(f"{source}: every pattern rule must be an object")
            rule_id = _require_str(rule, "id", source)
            if rule_id in seen_rule_ids:
                raise TagTaxonomyError(
                    f"{source}: pattern rule id {rule_id!r} is declared twice"
                )
            seen_rule_ids.add(rule_id)
            tag = _require_str(rule, "tag", source)
            if tag not in self.facet_of:
                raise TagTaxonomyError(
                    f"{source}: pattern rule {rule_id!r} targets undeclared tag {tag!r}"
                )
            pattern = _require_str(rule, "pattern", source)
            if not pattern.startswith("^") or not pattern.endswith("$"):
                raise TagTaxonomyError(
                    f"{source}: pattern rule {rule_id!r} must be anchored with ^ and $"
                )
            try:
                compiled = re.compile(pattern)
            except re.error as exc:
                raise TagTaxonomyError(
                    f"{source}: pattern rule {rule_id!r} is not a valid regex: {exc}"
                ) from exc
            self.pattern_rules.append((rule_id, tag, compiled))

        emitted = document.get("transform_emitted_tags", [])
        if not isinstance(emitted, list):
            raise TagTaxonomyError(
                f"{source}: transform_emitted_tags must be an array"
            )
        for tag in emitted:
            if tag not in self.facet_of:
                raise TagTaxonomyError(
                    f"{source}: transform_emitted_tags names undeclared tag {tag!r}"
                )
        self.transform_emitted_tags = tuple(emitted)
        if UNMAPPED_MARKER_TAG not in self.facet_of:
            raise TagTaxonomyError(
                f"{source}: taxonomy must declare {UNMAPPED_MARKER_TAG!r}"
            )

    @property
    def canonical_tags(self) -> frozenset[str]:
        """Every canonical tag the taxonomy declares."""
        return frozenset(self.facet_of)

    def is_canonical(self, tag: Any) -> bool:
        """Return whether a value is a declared canonical tag."""
        return isinstance(tag, str) and tag in self.facet_of

    def map_tag(self, tag: Any) -> dict[str, Any]:
        """Map one source tag and explain the decision."""
        if not isinstance(tag, str):
            return {
                "source": tag,
                "normalized": None,
                "canonical": None,
                "rule": None,
                "reason": REASON_TAG_NOT_STRING,
            }
        normalized = normalize_tag(tag)
        if not normalized:
            return {
                "source": tag,
                "normalized": normalized,
                "canonical": None,
                "rule": None,
                "reason": REASON_TAG_EMPTY,
            }
        canonical = self.alias_index.get(normalized)
        if canonical is not None:
            reason = (
                REASON_TAG_CANONICAL if tag == canonical else REASON_TAG_ALIAS
            )
            rule = RULE_CANONICAL if tag == canonical else RULE_ALIAS
            return {
                "source": tag,
                "normalized": normalized,
                "canonical": canonical,
                "rule": rule,
                "reason": reason,
            }
        for rule_id, mapped, compiled in self.pattern_rules:
            if compiled.match(normalized):
                return {
                    "source": tag,
                    "normalized": normalized,
                    "canonical": mapped,
                    "rule": f"{RULE_PATTERN_PREFIX}{rule_id}",
                    "reason": REASON_TAG_PATTERN,
                }
        return {
            "source": tag,
            "normalized": normalized,
            "canonical": None,
            "rule": None,
            "reason": REASON_TAG_UNMAPPED,
        }


def _require_str(container: dict[str, Any], key: str, source: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TagTaxonomyError(f"{source}: {key} must be a nonempty string")
    return value


def load_taxonomy(path: str | Path | None = None) -> Taxonomy:
    """Load and validate a taxonomy document."""
    resolved = Path(path) if path is not None else DEFAULT_TAXONOMY_PATH
    try:
        document = json.loads(
            resolved.read_text(encoding="utf-8"),
            parse_constant=_reject_json_constant,
        )
    except ValueError as exc:
        raise TagTaxonomyError(f"{resolved}: invalid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise TagTaxonomyError(f"{resolved}: taxonomy document must be an object")
    return Taxonomy(document, source=str(resolved))


def _pointer(tokens: list[str]) -> str:
    escaped = [token.replace("~", "~0").replace("/", "~1") for token in tokens]
    return "/" + "/".join(escaped)


def _collect_tag_containers(
    node: Any, tokens: list[str], found: list[tuple[list[str], Any, Any]]
) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if not tokens and key == TAG_PROVENANCE_FIELD:
                continue
            if key == TAGS_KEY:
                found.append((tokens + [key], node, key))
                continue
            _collect_tag_containers(value, tokens + [key], found)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _collect_tag_containers(item, tokens + [str(index)], found)


def map_tags(tags: list[Any], taxonomy: Taxonomy) -> dict[str, Any]:
    """Map one tag list and return its reversible provenance entry."""
    mappings = [taxonomy.map_tag(tag) for tag in tags]
    canonical: list[str] = []
    seen: set[str] = set()
    duplicates = 0
    for mapping in mappings:
        tag = mapping["canonical"]
        if tag is None:
            continue
        if tag in seen:
            duplicates += 1
            continue
        seen.add(tag)
        canonical.append(tag)

    unmapped = [
        mapping["source"] for mapping in mappings if mapping["canonical"] is None
    ]
    if unmapped and UNMAPPED_MARKER_TAG not in seen:
        seen.add(UNMAPPED_MARKER_TAG)
        canonical.append(UNMAPPED_MARKER_TAG)
        mappings.append(
            {
                "source": None,
                "normalized": None,
                "canonical": UNMAPPED_MARKER_TAG,
                "rule": RULE_TRANSFORM,
                "reason": REASON_TAGS_UNMAPPED,
            }
        )

    return {
        "source_tags": copy.deepcopy(tags),
        "canonical_tags": sorted(canonical),
        "mappings": mappings,
        "unmapped_tags": unmapped,
        "duplicates_collapsed": duplicates,
    }


def _existing_provenance(
    record: dict[str, Any], taxonomy: Taxonomy
) -> tuple[dict[str, dict[str, Any]], bool, bool]:
    """Return reusable provenance entries by pointer, a conflict flag, and presence.

    A record that already carries this transform's provenance is only reusable
    when the stored entries still describe the record exactly.  Recomputing over
    already-curated tags would make the curated vocabulary look like the source
    vocabulary, so a stale or malformed sidecar is a conflict, not an invitation
    to guess.
    """
    stored = record.get(TAG_PROVENANCE_FIELD)
    if stored is None:
        return {}, False, False
    if not isinstance(stored, dict):
        return {}, True, True
    if stored.get("taxonomy_version") != taxonomy.version:
        return {}, True, True
    containers = stored.get("containers")
    if not isinstance(containers, list):
        return {}, True, True
    reusable: dict[str, dict[str, Any]] = {}
    for entry in containers:
        if not isinstance(entry, dict):
            return {}, True, True
        pointer = entry.get("json_pointer")
        if not isinstance(pointer, str) or pointer in reusable:
            return {}, True, True
        for key in ("source_tags", "canonical_tags", "mappings", "unmapped_tags"):
            if not isinstance(entry.get(key), list):
                return {}, True, True
        expected = map_tags(entry["source_tags"], taxonomy)
        for key in (
            "canonical_tags",
            "mappings",
            "unmapped_tags",
            "duplicates_collapsed",
        ):
            if entry.get(key) != expected[key]:
                return {}, True, True
        reusable[pointer] = entry
    return reusable, False, True


def _base_manifest(
    *,
    source_path: str,
    source_line: int,
    source_hash: str,
    taxonomy_version: str,
) -> dict[str, Any]:
    return {
        "source_path": source_path,
        "source_line": source_line,
        "source_hash": source_hash,
        "transform": TRANSFORM_NAME,
        "transform_version": TRANSFORM_VERSION,
        "taxonomy_version": taxonomy_version,
        "action": "excluded",
        "reason_codes": [],
        "output_id": None,
        "output_hash": None,
        "tag_counts": {
            "containers": 0,
            "source_uses": 0,
            "source_unique": 0,
            "canonical_uses": 0,
            "canonical_unique": 0,
            "mapped_uses": 0,
            "unmapped_uses": 0,
        },
        "unmapped_tags": [],
        "containers": [],
    }


def _record_id(record: Any) -> str | None:
    if not isinstance(record, dict):
        return None
    value = record.get("id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    meta = record.get("meta")
    if isinstance(meta, dict):
        value = meta.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def curate_record(
    record: Any,
    *,
    taxonomy: Taxonomy | None = None,
    source_path: str = "<memory>",
    source_line: int = 1,
    source_hash: str | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Curate one record's tags and emit a deterministic manifest entry."""
    vocabulary = taxonomy if taxonomy is not None else load_taxonomy()
    digest = source_hash or hash_value(record)
    manifest = _base_manifest(
        source_path=source_path,
        source_line=source_line,
        source_hash=digest,
        taxonomy_version=vocabulary.version,
    )
    if not isinstance(record, dict):
        manifest["reason_codes"] = [REASON_RECORD_NOT_OBJECT]
        return None, manifest

    reusable, conflict, has_provenance = _existing_provenance(record, vocabulary)
    if conflict:
        manifest["reason_codes"] = [REASON_PROVENANCE_CONFLICT]
        return None, manifest

    curated = copy.deepcopy(record)
    found: list[tuple[list[str], Any, Any]] = []
    _collect_tag_containers(curated, [], found)
    found.sort(key=lambda item: _pointer(item[0]))

    if has_provenance and set(reusable) != {_pointer(tokens) for tokens, _, _ in found}:
        manifest["reason_codes"] = [REASON_PROVENANCE_CONFLICT]
        return None, manifest

    entries: list[dict[str, Any]] = []
    container_manifests: list[dict[str, Any]] = []
    source_uses = Counter()
    canonical_uses = Counter()
    unmapped_uses = Counter()
    unmapped_total = 0
    mapped_total = 0
    duplicates_total = 0
    reused_any = False

    for tokens, parent, key in found:
        pointer = _pointer(tokens)
        tags = parent[key]
        if not isinstance(tags, list):
            manifest["reason_codes"] = [REASON_TAGS_NOT_LIST]
            return None, manifest

        prior = reusable.get(pointer)
        if prior is not None:
            if prior["canonical_tags"] != tags:
                # The stored sidecar no longer describes this container, so the
                # original tags are not recoverable from the record.
                manifest["reason_codes"] = [REASON_PROVENANCE_CONFLICT]
                return None, manifest
            entry = copy.deepcopy(prior)
            reused_any = True
        else:
            entry = map_tags(tags, vocabulary)

        entry["json_pointer"] = pointer
        parent[key] = list(entry["canonical_tags"])
        entries.append(entry)

        for tag in entry["source_tags"]:
            if isinstance(tag, str):
                source_uses[tag] += 1
        for tag in entry["canonical_tags"]:
            canonical_uses[tag] += 1
        for tag in entry["unmapped_tags"]:
            unmapped_total += 1
            if isinstance(tag, str):
                unmapped_uses[tag] += 1
        mapped_total += sum(
            1
            for mapping in entry["mappings"]
            if mapping.get("canonical") is not None
            and mapping.get("rule") != RULE_TRANSFORM
        )
        duplicates_total += int(entry.get("duplicates_collapsed") or 0)

        container_manifests.append(
            {
                "json_pointer": pointer,
                "source_tag_count": len(entry["source_tags"]),
                "canonical_tag_count": len(entry["canonical_tags"]),
                "unmapped_tag_count": len(entry["unmapped_tags"]),
                "unmapped_tags": list(entry["unmapped_tags"]),
            }
        )

    if entries:
        curated[TAG_PROVENANCE_FIELD] = {
            "taxonomy_version": vocabulary.version,
            "transform": TRANSFORM_NAME,
            "transform_version": TRANSFORM_VERSION,
            "containers": entries,
        }
    elif TAG_PROVENANCE_FIELD in curated:
        del curated[TAG_PROVENANCE_FIELD]

    reasons: list[str] = []
    if mapped_total:
        reasons.append(REASON_TAGS_MAPPED)
    if unmapped_total:
        reasons.append(REASON_TAGS_UNMAPPED)
    if duplicates_total:
        reasons.append(REASON_TAGS_DEDUPLICATED)
    if reused_any:
        reasons.append(REASON_TAGS_PROVENANCE_REUSED)

    manifest["tag_counts"] = {
        "containers": len(entries),
        "source_uses": sum(source_uses.values()),
        "source_unique": len(source_uses),
        "canonical_uses": sum(canonical_uses.values()),
        "canonical_unique": len(canonical_uses),
        "mapped_uses": mapped_total,
        "unmapped_uses": unmapped_total,
    }
    manifest["unmapped_tags"] = sorted(unmapped_uses)
    manifest["containers"] = container_manifests
    manifest["reason_codes"] = reasons
    manifest["action"] = "modified" if curated != record else "unchanged"
    manifest["output_id"] = _record_id(curated)
    manifest["output_hash"] = hash_value(curated)

    leftover = [
        tag
        for entry in entries
        for tag in entry["canonical_tags"]
        if not vocabulary.is_canonical(tag)
    ]
    if leftover:
        raise AssertionError(f"tag curation emitted noncanonical tags: {leftover!r}")
    return curated, manifest


def _excluded_line_manifest(
    *,
    source_path: str,
    source_line: int,
    source_hash: str,
    taxonomy_version: str,
    reason: str,
) -> dict[str, Any]:
    manifest = _base_manifest(
        source_path=source_path,
        source_line=source_line,
        source_hash=source_hash,
        taxonomy_version=taxonomy_version,
    )
    manifest["reason_codes"] = [reason]
    return manifest


def curate_jsonl(
    source_path: str | Path, taxonomy: Taxonomy | None = None
) -> dict[str, Any]:
    """Read a JSONL source without mutation and curate every nonblank line."""
    vocabulary = taxonomy if taxonomy is not None else load_taxonomy()
    source = Path(source_path)
    records: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    source_uses = Counter()
    canonical_uses = Counter()
    unmapped_uses = Counter()
    rule_uses = Counter()
    nonstring_uses = 0

    with source.open("rb") as handle:
        for line_number, terminated_line in enumerate(handle, 1):
            raw_line = terminated_line.rstrip(b"\r\n")
            if not raw_line.strip():
                continue
            line_hash = hashlib.sha256(raw_line).hexdigest()
            try:
                text = raw_line.decode("utf-8")
            except UnicodeDecodeError:
                manifests.append(
                    _excluded_line_manifest(
                        source_path=str(source),
                        source_line=line_number,
                        source_hash=line_hash,
                        taxonomy_version=vocabulary.version,
                        reason=REASON_INVALID_UTF8,
                    )
                )
                continue
            try:
                record = json.loads(text, parse_constant=_reject_json_constant)
            except ValueError:
                manifests.append(
                    _excluded_line_manifest(
                        source_path=str(source),
                        source_line=line_number,
                        source_hash=line_hash,
                        taxonomy_version=vocabulary.version,
                        reason=REASON_INVALID_JSON,
                    )
                )
                continue

            curated, manifest = curate_record(
                record,
                taxonomy=vocabulary,
                source_path=str(source),
                source_line=line_number,
                source_hash=line_hash,
            )
            manifests.append(manifest)
            if curated is None:
                continue
            records.append(curated)
            provenance = curated.get(TAG_PROVENANCE_FIELD)
            containers = provenance.get("containers", []) if provenance else []
            for entry in containers:
                for tag in entry["source_tags"]:
                    if isinstance(tag, str):
                        source_uses[tag] += 1
                for tag in entry["canonical_tags"]:
                    canonical_uses[tag] += 1
                for tag in entry["unmapped_tags"]:
                    if isinstance(tag, str):
                        unmapped_uses[tag] += 1
                    else:
                        nonstring_uses += 1
                for mapping in entry["mappings"]:
                    rule = mapping.get("rule")
                    if rule:
                        rule_uses[rule] += 1

    source_entropy = vocabulary_entropy(source_uses)
    canonical_entropy = vocabulary_entropy(canonical_uses)
    unmapped_report = [
        {"tag": tag, "count": count}
        for tag, count in sorted(unmapped_uses.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    summary = {
        "source_path": str(source),
        "taxonomy_version": vocabulary.version,
        "taxonomy_size": len(vocabulary.canonical_tags),
        "input_records": len(manifests),
        "output_records": len(records),
        "excluded_records": sum(item["action"] == "excluded" for item in manifests),
        "tag_containers": sum(
            item["tag_counts"]["containers"] for item in manifests
        ),
        "source_tag_uses": sum(source_uses.values()),
        "source_unique_tags": len(source_uses),
        "canonical_tag_uses": sum(canonical_uses.values()),
        "canonical_unique_tags": len(canonical_uses),
        "mapped_tag_uses": sum(
            count for rule, count in rule_uses.items() if rule != RULE_TRANSFORM
        ),
        "unmapped_tag_uses": sum(unmapped_uses.values()),
        "unmapped_unique_tags": len(unmapped_uses),
        "nonstring_tag_uses": nonstring_uses,
        "entropy_bits": {
            "source": source_entropy,
            "canonical": canonical_entropy,
            "reduction": round(source_entropy - canonical_entropy, 6),
        },
        "rule_uses": dict(sorted(rule_uses.items())),
        "canonical_tag_counts": dict(sorted(canonical_uses.items())),
        "unmapped_tags": unmapped_report,
    }
    return {
        "records": records,
        "manifest": manifests,
        "unmapped": unmapped_report,
        "summary": summary,
    }


def _is_under_raw(path: Path) -> bool:
    parts = path.resolve(strict=False).parts
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def _unlink_created_file(path: Path, identity: tuple[int, int]) -> None:
    """Remove ``path`` only when it still names the file this run created."""
    try:
        current = path.lstat()
    except FileNotFoundError:
        return
    if (current.st_dev, current.st_ino) == identity:
        path.unlink()


def _write_new_jsonl(
    path: Path, values: list[dict[str, Any]]
) -> tuple[int, int]:
    """Write one JSONL file without replacing any pre-existing path."""
    if _is_under_raw(path):
        raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    # O_EXCL is the atomic no-clobber gate; preflight is only an early diagnostic.
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise FileExistsError(
            f"refusing to replace existing destination: {path}"
        ) from exc
    state = os.fstat(descriptor)
    identity = (state.st_dev, state.st_ino)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            for value in values:
                handle.write(canonical_json(value))
                handle.write("\n")
    except BaseException:
        _unlink_created_file(path, identity)
        raise
    return identity


def _preflight_destinations(paths: list[Path]) -> None:
    resolved = [path.resolve(strict=False) for path in paths]
    if len(set(resolved)) != len(resolved):
        raise ValueError("output destinations must be distinct")
    for index, path in enumerate(resolved):
        for other in resolved[index + 1 :]:
            if path in other.parents or other in path.parents:
                raise ValueError("output destinations must not contain one another")
    for path in paths:
        if _is_under_raw(path):
            raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
        if path.exists():
            raise FileExistsError(f"refusing to replace existing destination: {path}")


def _write_destinations(
    destinations: list[tuple[Path, list[dict[str, Any]]]],
) -> None:
    """Publish a destination set, rolling back this run's files on failure."""
    for path, _values in destinations:
        path.parent.mkdir(parents=True, exist_ok=True)

    created: list[tuple[Path, tuple[int, int]]] = []
    try:
        for path, values in destinations:
            identity = _write_new_jsonl(path, values)
            created.append((path, identity))
    except BaseException:
        for path, identity in reversed(created):
            _unlink_created_file(path, identity)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="JSONL corpus to inspect")
    parser.add_argument("--taxonomy", type=Path, default=None)
    parser.add_argument("--output-jsonl", type=Path)
    parser.add_argument("--manifest-jsonl", type=Path)
    parser.add_argument("--unmapped-jsonl", type=Path)
    args = parser.parse_args(argv)

    if (
        args.output_jsonl is not None
        and args.output_jsonl.resolve(strict=False) == args.source.resolve()
    ):
        parser.error("output must not replace the source")
    destinations = [
        path
        for path in (args.output_jsonl, args.manifest_jsonl, args.unmapped_jsonl)
        if path is not None
    ]
    try:
        _preflight_destinations(destinations)
    except (FileExistsError, ValueError) as exc:
        parser.error(str(exc))

    try:
        taxonomy = load_taxonomy(args.taxonomy)
    except TagTaxonomyError as exc:
        parser.error(str(exc))

    result = curate_jsonl(args.source, taxonomy)
    _write_destinations(
        [
            (path, values)
            for path, values in (
                (args.output_jsonl, result["records"]),
                (args.manifest_jsonl, result["manifest"]),
                (args.unmapped_jsonl, result["unmapped"]),
            )
            if path is not None
        ]
    )
    print(
        json.dumps(
            result["summary"],
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
