"""Record-level tag curation and provenance reuse."""

from __future__ import annotations

import copy
from collections import Counter
from typing import Any

from tag_constants import (
    REASON_PROVENANCE_CONFLICT,
    REASON_RECORD_NOT_OBJECT,
    REASON_TAGS_DEDUPLICATED,
    REASON_TAGS_MAPPED,
    REASON_TAGS_NOT_LIST,
    REASON_TAGS_PROVENANCE_REUSED,
    REASON_TAGS_PROVENANCE_WRITTEN,
    REASON_TAGS_UNMAPPED,
    RULE_TRANSFORM,
    TAG_PROVENANCE_FIELD,
    TAGS_KEY,
    TRANSFORM_NAME,
    TRANSFORM_VERSION,
)
from tag_jsonutil import (
    canonical_json,
    canonical_json_equal,
    count_tag,
    hash_value,
)
from tag_taxonomy import Taxonomy, load_taxonomy, map_tags


def json_pointer(tokens: list[str]) -> str:
    escaped = [token.replace("~", "~0").replace("/", "~1") for token in tokens]
    return "/" + "/".join(escaped)


def collect_tag_containers(node: Any) -> list[tuple[list[str], Any, Any]]:
    found: list[tuple[list[str], Any, Any]] = []
    _walk_for_tags(node, [], found)
    return found


def _walk_for_tags(
    node: Any, tokens: list[str], found: list[tuple[list[str], Any, Any]]
) -> None:
    if isinstance(node, dict):
        _walk_dict_for_tags(node, tokens, found)
        return
    if isinstance(node, list):
        _walk_list_for_tags(node, tokens, found)


def _walk_dict_for_tags(
    node: dict[str, Any], tokens: list[str], found: list[tuple[list[str], Any, Any]]
) -> None:
    for key, value in node.items():
        _consider_dict_key(node, tokens, found, (key, value))


def _consider_dict_key(
    node: dict[str, Any],
    tokens: list[str],
    found: list[tuple[list[str], Any, Any]],
    item: tuple[str, Any],
) -> None:
    key, value = item
    if _skip_provenance_field(tokens, key):
        return
    if key == TAGS_KEY:
        found.append((tokens + [key], node, key))
        return
    _walk_for_tags(value, tokens + [key], found)


def _skip_provenance_field(tokens: list[str], key: str) -> bool:
    if tokens:
        return False
    return key == TAG_PROVENANCE_FIELD


def _walk_list_for_tags(
    node: list[Any], tokens: list[str], found: list[tuple[list[str], Any, Any]]
) -> None:
    for index, item in enumerate(node):
        _walk_for_tags(item, tokens + [str(index)], found)


def existing_provenance(
    record: dict[str, Any], taxonomy: Taxonomy
) -> tuple[dict[str, dict[str, Any]], bool, bool]:
    """Return reusable provenance entries by pointer, a conflict flag, and presence.

    A record that already carries this transform's provenance is only reusable
    when the stored entries still describe the record exactly.  Recomputing over
    already-curated tags would make the curated vocabulary look like the source
    vocabulary, so a stale or malformed sidecar is a conflict, not an invitation
    to guess.
    """
    if TAG_PROVENANCE_FIELD not in record:
        return {}, False, False
    stored = record[TAG_PROVENANCE_FIELD]
    if not _stored_header_ok(stored, taxonomy):
        return {}, True, True
    reusable = _reusable_entries(stored.get("containers"), taxonomy)
    if reusable is None:
        return {}, True, True
    return reusable, False, True


def _stored_header_ok(stored: Any, taxonomy: Taxonomy) -> bool:
    if not isinstance(stored, dict):
        return False
    if stored.get("transform") != TRANSFORM_NAME:
        return False
    if stored.get("transform_version") != TRANSFORM_VERSION:
        return False
    if stored.get("taxonomy_version") != taxonomy.version:
        return False
    return _containers_header_ok(stored.get("containers"))


def _containers_header_ok(containers: Any) -> bool:
    if not isinstance(containers, list):
        return False
    return bool(containers)


def _reusable_entries(
    containers: Any, taxonomy: Taxonomy
) -> dict[str, dict[str, Any]] | None:
    reusable: dict[str, dict[str, Any]] = {}
    for entry in containers:
        pointer = _reusable_pointer(entry, reusable, taxonomy)
        if pointer is None:
            return None
        reusable[pointer] = entry
    return reusable


def _reusable_pointer(
    entry: Any, reusable: dict[str, dict[str, Any]], taxonomy: Taxonomy
) -> str | None:
    if not isinstance(entry, dict):
        return None
    pointer = entry.get("json_pointer")
    if not isinstance(pointer, str):
        return None
    if pointer in reusable:
        return None
    if not _entry_lists_ok(entry):
        return None
    if not _entry_matches_taxonomy(entry, taxonomy):
        return None
    return pointer


def _entry_lists_ok(entry: dict[str, Any]) -> bool:
    keys = ("source_tags", "canonical_tags", "mappings", "unmapped_tags")
    for key in keys:
        if not isinstance(entry.get(key), list):
            return False
    return True


def _entry_matches_taxonomy(entry: dict[str, Any], taxonomy: Taxonomy) -> bool:
    expected = map_tags(entry["source_tags"], taxonomy)
    keys = (
        "canonical_tags",
        "mappings",
        "unmapped_tags",
        "duplicates_collapsed",
    )
    for key in keys:
        if not canonical_json_equal(entry.get(key), expected[key]):
            return False
    return True


def base_manifest(origin: tuple[str, int, str], taxonomy_version: str) -> dict[str, Any]:
    source_path, source_line, source_hash = origin
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


def record_id(record: Any) -> str | None:
    if not isinstance(record, dict):
        return None
    value = record.get("id")
    if _nonempty_id(value):
        return value.strip()
    return _meta_record_id(record.get("meta"))


def _nonempty_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return bool(value.strip())


def _meta_record_id(meta: Any) -> str | None:
    if not isinstance(meta, dict):
        return None
    value = meta.get("id")
    if not _nonempty_id(value):
        return None
    return value.strip()


def origin_fields(
    record: Any, origin: tuple[str, int, str | None] | None
) -> tuple[str, int, str]:
    if origin is None:
        return "<memory>", 1, hash_value(record)
    path, line, digest = origin
    if digest is None:
        digest = hash_value(record)
    return path, line, digest


def curate_record(
    record: Any,
    *,
    taxonomy: Taxonomy | None = None,
    origin: tuple[str, int, str | None] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Curate one record's tags and emit a deterministic manifest entry."""
    vocabulary = taxonomy if taxonomy is not None else load_taxonomy()
    path, line, digest = origin_fields(record, origin)
    manifest = base_manifest((path, line, digest), vocabulary.version)
    if not isinstance(record, dict):
        manifest["reason_codes"] = [REASON_RECORD_NOT_OBJECT]
        return None, manifest
    return _curate_object_record(record, vocabulary, manifest)


def _curate_object_record(
    record: dict[str, Any], vocabulary: Taxonomy, manifest: dict[str, Any]
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    reusable, conflict, has_provenance = existing_provenance(record, vocabulary)
    if conflict:
        manifest["reason_codes"] = [REASON_PROVENANCE_CONFLICT]
        return None, manifest
    curated = copy.deepcopy(record)
    found = collect_tag_containers(curated)
    found.sort(key=lambda item: json_pointer(item[0]))
    if _provenance_pointer_mismatch(has_provenance, reusable, found):
        manifest["reason_codes"] = [REASON_PROVENANCE_CONFLICT]
        return None, manifest
    applied, reason = _apply_containers(found, reusable, vocabulary)
    if applied is None:
        manifest["reason_codes"] = [reason or REASON_TAGS_NOT_LIST]
        return None, manifest
    return _finish_curated_record(record, curated, (applied, vocabulary, manifest))


def _provenance_pointer_mismatch(
    has_provenance: bool,
    reusable: dict[str, dict[str, Any]],
    found: list[tuple[list[str], Any, Any]],
) -> bool:
    if not has_provenance:
        return False
    return set(reusable) != {json_pointer(tokens) for tokens, _, _ in found}


def _apply_containers(
    found: list[tuple[list[str], Any, Any]],
    reusable: dict[str, dict[str, Any]],
    vocabulary: Taxonomy,
) -> tuple[_RecordStats | None, str | None]:
    stats = _RecordStats()
    for tokens, parent, key in found:
        work = (json_pointer(tokens), reusable, vocabulary)
        reason = stats.consume(parent, key, work)
        if reason is not None:
            return None, reason
    return stats, None


class _RecordStats:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []
        self.container_manifests: list[dict[str, Any]] = []
        self.source_uses: Counter = Counter()
        self.source_total = 0
        self.canonical_uses: Counter = Counter()
        self.unmapped_uses: Counter = Counter()
        self.unmapped_originals: dict[tuple[str, str], Any] = {}
        self.unmapped_total = 0
        self.mapped_total = 0
        self.duplicates_total = 0
        self.reused_any = False

    def consume(
        self,
        parent: Any,
        key: Any,
        work: tuple[str, dict[str, dict[str, Any]], Taxonomy],
    ) -> str | None:
        pointer, reusable, vocabulary = work
        tags = parent[key]
        if not isinstance(tags, list):
            return REASON_TAGS_NOT_LIST
        entry, reason = self._entry_for_container(
            tags, pointer, reusable, vocabulary
        )
        if reason is not None:
            return reason
        entry["json_pointer"] = pointer
        parent[key] = list(entry["canonical_tags"])
        self.entries.append(entry)
        self._count_entry(entry)
        self._note_container(pointer, entry)
        return None

    def _entry_for_container(
        self,
        tags: list[Any],
        pointer: str,
        reusable: dict[str, dict[str, Any]],
        vocabulary: Taxonomy,
    ) -> tuple[dict[str, Any], str | None]:
        prior = reusable.get(pointer)
        if prior is None:
            return map_tags(tags, vocabulary), None
        if not canonical_json_equal(prior["canonical_tags"], tags):
            # The stored sidecar no longer describes this container, so the
            # original tags are not recoverable from the record.
            return {}, REASON_PROVENANCE_CONFLICT
        self.reused_any = True
        return copy.deepcopy(prior), None

    def _count_entry(self, entry: dict[str, Any]) -> None:
        self.source_total += len(entry["source_tags"])
        for tag in entry["source_tags"]:
            count_tag(self.source_uses, tag)
        for tag in entry["canonical_tags"]:
            self.canonical_uses[tag] += 1
        self._count_unmapped(entry["unmapped_tags"])
        self.mapped_total += _mapped_use_count(entry["mappings"])
        self.duplicates_total += int(entry.get("duplicates_collapsed") or 0)

    def _count_unmapped(self, tags: list[Any]) -> None:
        for tag in tags:
            self.unmapped_total += 1
            count_tag(self.unmapped_uses, tag, self.unmapped_originals)

    def _note_container(self, pointer: str, entry: dict[str, Any]) -> None:
        self.container_manifests.append(
            {
                "json_pointer": pointer,
                "source_tag_count": len(entry["source_tags"]),
                "canonical_tag_count": len(entry["canonical_tags"]),
                "unmapped_tag_count": len(entry["unmapped_tags"]),
                "unmapped_tags": list(entry["unmapped_tags"]),
            }
        )

    def reason_codes(self) -> list[str]:
        reasons: list[str] = []
        if self.mapped_total:
            reasons.append(REASON_TAGS_MAPPED)
        if self.unmapped_total:
            reasons.append(REASON_TAGS_UNMAPPED)
        if self.duplicates_total:
            reasons.append(REASON_TAGS_DEDUPLICATED)
        if self.reused_any:
            reasons.append(REASON_TAGS_PROVENANCE_REUSED)
        return reasons

    def tag_counts(self) -> dict[str, int]:
        return {
            "containers": len(self.entries),
            "source_uses": self.source_total,
            "source_unique": len(self.source_uses),
            "canonical_uses": sum(self.canonical_uses.values()),
            "canonical_unique": len(self.canonical_uses),
            "mapped_uses": self.mapped_total,
            "unmapped_uses": self.unmapped_total,
        }

    def sorted_unmapped(self) -> list[Any]:
        return sorted(
            (self.unmapped_originals[ident] for ident in self.unmapped_uses),
            key=_unmapped_sort_key,
        )


def _unmapped_sort_key(item: Any) -> tuple[int, Any]:
    if isinstance(item, str):
        return 0, item
    return 1, canonical_json(item)


def _mapped_use_count(mappings: list[dict[str, Any]]) -> int:
    total = 0
    for mapping in mappings:
        total += int(_is_mapped_use(mapping))
    return total


def _is_mapped_use(mapping: dict[str, Any]) -> bool:
    if mapping.get("canonical") is None:
        return False
    return mapping.get("rule") != RULE_TRANSFORM


def _finish_curated_record(
    record: dict[str, Any],
    curated: dict[str, Any],
    payload: tuple[_RecordStats, Taxonomy, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    stats, vocabulary, manifest = payload
    _write_or_clear_provenance(curated, stats, vocabulary)
    reasons = stats.reason_codes()
    manifest["tag_counts"] = stats.tag_counts()
    manifest["unmapped_tags"] = stats.sorted_unmapped()
    manifest["containers"] = stats.container_manifests
    manifest["action"] = "modified" if curated != record else "unchanged"
    if _needs_provenance_written_reason(manifest["action"], reasons):
        reasons.append(REASON_TAGS_PROVENANCE_WRITTEN)
    manifest["reason_codes"] = reasons
    manifest["output_id"] = record_id(curated)
    manifest["output_hash"] = hash_value(curated)
    _assert_canonical_output(stats.entries, vocabulary)
    return curated, manifest


def _write_or_clear_provenance(
    curated: dict[str, Any], stats: _RecordStats, vocabulary: Taxonomy
) -> None:
    if stats.entries:
        curated[TAG_PROVENANCE_FIELD] = {
            "taxonomy_version": vocabulary.version,
            "transform": TRANSFORM_NAME,
            "transform_version": TRANSFORM_VERSION,
            "containers": stats.entries,
        }
        return
    if TAG_PROVENANCE_FIELD in curated:
        del curated[TAG_PROVENANCE_FIELD]


def _needs_provenance_written_reason(action: str, reasons: list[str]) -> bool:
    if action != "modified":
        return False
    return not reasons


def _assert_canonical_output(
    entries: list[dict[str, Any]], vocabulary: Taxonomy
) -> None:
    leftover = [
        tag
        for entry in entries
        for tag in entry["canonical_tags"]
        if not vocabulary.is_canonical(tag)
    ]
    if leftover:
        raise AssertionError(f"tag curation emitted noncanonical tags: {leftover!r}")
