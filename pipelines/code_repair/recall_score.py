"""Static scoring of recall-probe completions, and their per-variant and per-family tally.

A completion is compared to the record's verified repair exactly (SHA-256 of
the text against ``result.repaired_sha256``) and structurally (the canonical
AST digest of :mod:`.lineage`: identifiers renamed, docstrings dropped). It is
hashed and parsed, never imported, compiled or run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import catalog as cat
from . import lineage
from . import vocabulary as cv
from ._contract import bind_import_twin

__all__ = ["Tally", "Target", "score_completion", "tally"]


@dataclass(frozen=True)
class Target:
    """What one positive record is scored against; the repaired text itself is not kept."""

    repaired_sha256: str
    structure: str
    family: str


def _structure_digest(text: str) -> str | None:
    """The canonical AST digest, or None when the text is not a Python module (parse only).

    ``ast.parse`` reports text that is not a module as ``SyntaxError`` (indentation and tab
    errors included), ``ValueError`` (a NUL byte) or ``RecursionError`` (nesting too deep);
    anything else is a fault of the scorer, not of the completion, and propagates.
    """

    try:
        return lineage.structure_digest(text)
    except (SyntaxError, ValueError, RecursionError):
        return None


def score_completion(completion: str, repaired_sha256: str, structure: str) -> dict[str, bool]:
    """Exact (SHA-256 of the text) and structural (canonical AST) recall of the repair."""

    digest = _structure_digest(completion)
    return {
        "exact": cat.sha256_text(completion) == repaired_sha256,
        "structural": digest is not None and digest == structure,
        "unparsable": digest is None,
    }


@dataclass
class _Bucket:
    prompts: int = 0
    completions: int = 0
    exact: int = 0
    structural: int = 0
    unparsable: int = 0

    def add(self, verdict: dict[str, bool]) -> None:
        self.completions += 1
        self.exact += int(verdict["exact"])
        self.structural += int(verdict["structural"])
        self.unparsable += int(verdict["unparsable"])

    def rate(self, count: int) -> float | None:
        return None if self.completions == 0 else round(count / self.completions, 4)

    def as_json(self) -> dict[str, Any]:
        return {
            "prompts": self.prompts, "completions": self.completions,
            "missing": self.prompts - self.completions, "exact": self.exact,
            "structural": self.structural, "unparsable": self.unparsable,
            "exact_rate": self.rate(self.exact), "structural_rate": self.rate(self.structural),
        }


def _buckets_json(buckets: dict[str, _Bucket]) -> dict[str, Any]:
    return {variant: bucket.as_json() for variant, bucket in sorted(buckets.items())}


@dataclass
class Tally:
    """Counts per variant and per family/variant, and the ids exactly recalled under
    ``docstring_only``."""

    per_variant: dict[str, _Bucket] = field(default_factory=dict)
    per_family: dict[str, dict[str, _Bucket]] = field(default_factory=dict)
    recalled: list[str] = field(default_factory=list)

    def _buckets(self, family: str, variant: str) -> tuple[_Bucket, _Bucket]:
        by_variant = self.per_family.setdefault(family, {})
        return (self.per_variant.setdefault(variant, _Bucket()),
                by_variant.setdefault(variant, _Bucket()))

    def expect(self, family: str, variant: str) -> None:
        """One emitted prompt, answered or not."""

        for bucket in self._buckets(family, variant):
            bucket.prompts += 1

    def record(self, key: tuple[str, str], target: Target, completion: str) -> None:
        """One completion for ``(record id, variant)``, scored against the record's target."""

        record_id, variant = key
        verdict = score_completion(completion, target.repaired_sha256, target.structure)
        for bucket in self._buckets(target.family, variant):
            bucket.add(verdict)
        if verdict["exact"] and variant == cv.RECALL_VARIANT_DOCSTRING_ONLY:
            self.recalled.append(record_id)

    def as_json(self) -> dict[str, Any]:
        return {
            "per_variant": _buckets_json(self.per_variant),
            "per_family": {
                family: _buckets_json(buckets) for family, buckets in sorted(self.per_family.items())
            },
            "docstring_only_exact_recall_ids": sorted(self.recalled),
        }


def tally(
    prompts: dict[tuple[str, str], dict[str, Any]], completions: dict[tuple[str, str], str],
    targets: dict[str, Target],
) -> Tally:
    """Every emitted prompt counted, every completion scored; missing ones stay missing."""

    counted = Tally()
    for (_record_id, variant), row in prompts.items():
        counted.expect(row["family"], variant)
    for key, completion in sorted(completions.items()):
        counted.record(key, targets[key[0]], completion)
    return counted


bind_import_twin(__name__)
