"""Pure syntax for procedural completion receipts; syntax grants no authority."""
from __future__ import annotations

import re

from ._contract import bind_import_twin

GATE = "code-repair-fresh-publication/1"
BINDING_FIELDS = frozenset({
    "factory", "round", "registry_sha256", "policy_sha256", "catalog_sha256",
    "programs_sha256", "source_license_evidence", "run_sha256", "candidates_sha256",
    "input_artifact", "input_sha256", "batch_sha256", "lineage_cap", "candidate_count",
    "positive_count", "selected", "harness_sha256",
})


def is_procedural_verification(verification) -> bool:
    if not isinstance(verification, dict):
        return False
    return verification.get("gate") == GATE or "procedural" in verification


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _fields(value, expected):
    _require(isinstance(value, dict), "receipt object must be a dictionary")
    _require(set(value) == set(expected), "invalid procedural receipt fields")


def _positive_integer(value):
    # Exact int rejects bool and subclasses in receipt counters.
    return type(value) is int and value > 0  # pylint: disable=unidiomatic-typecheck


def _verified_counts(counts):
    _fields(counts, {"total", "verified", "failed", "inconclusive"})
    # Exact ints keep all persisted replay counters canonical.
    _require(all(type(v) is int for v in counts.values()), "counts must be integers")  # pylint: disable=unidiomatic-typecheck
    _require(_positive_integer(counts["total"]), "completed batch must be nonempty")
    _require(counts == {"total": counts["total"], "verified": counts["total"],
                        "failed": 0, "inconclusive": 0}, "invalid fresh replay counts")


def _entries(entries, digest_field):
    for entry in entries:
        _fields(entry, {"id", digest_field})
        _require(isinstance(entry["id"], str), "invalid receipt record ID")
        digest = entry[digest_field]
        _require(isinstance(digest, str), "invalid receipt digest type")
        _require(re.fullmatch(r"[0-9a-f]{64}", digest) is not None, "invalid receipt digest")


def _membership(binding, replayed, total):
    for key in ("round", "lineage_cap", "candidate_count", "positive_count"):
        _require(_positive_integer(binding[key]), f"invalid procedural {key}")
    selected = binding["selected"]
    _require(isinstance(selected, list), "selected membership must be a list")
    _require(isinstance(replayed, list), "fresh replay membership must be a list")
    _require(len(selected) == total, "selected membership/count mismatch")
    _require(len(replayed) == binding["positive_count"], "fresh replay membership/count mismatch")
    _require(total <= binding["positive_count"] <= binding["candidate_count"], "invalid counts")
    _entries(selected, "source_sha256")
    _entries(replayed, "evidence_sha256")


def validate_summary(summary):
    """Validate the tagged representation; callers independently recompute every binding."""
    _fields(summary, {"gate", "strict", "semantics_version", "override", "counts",
                      "procedural", "fresh_replay"})
    _require(summary["gate"] == GATE, "invalid procedural gate")
    _require(summary["strict"] is True, "procedural gate must be strict")
    # Exact int rejects bool and subclasses in the receipt version.
    _require(type(summary["semantics_version"]) is int, "invalid semantics version type")  # pylint: disable=unidiomatic-typecheck
    _require(summary["semantics_version"] == 1, "invalid semantics version")
    _require(summary["override"] is None, "procedural gate cannot be waived")
    _verified_counts(summary["counts"])
    _fields(summary["procedural"], BINDING_FIELDS)
    _membership(summary["procedural"], summary["fresh_replay"], summary["counts"]["total"])
    return summary


bind_import_twin(__name__)
