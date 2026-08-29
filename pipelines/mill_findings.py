#!/usr/bin/env python3
"""What a resolved mill disagreement is reported as.

The result vocabulary shared by every caller: the three reason codes an
axis can fire, the per-record finding they are attached to, and the JSON-safe
roll-up census and curation both publish. Nothing here decides anything --
resolution happens in ``mill_evidence.py`` and ``mill_ownership.py``; this
module only names and shapes the answer.

Split out of ``mill_family.py`` verbatim; every name is re-exported from
``mill_family`` so existing ``from mill_family import MillFinding`` and
``from mill_family import summarize`` call sites resolve unchanged.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Hashable, Iterable
from dataclasses import dataclass
from typing import Any

REASON_FOREIGN_PAYLOAD_FACTORY = "FOREIGN_PAYLOAD_FACTORY"
REASON_FOREIGN_MILL_ID_PREFIX = "FOREIGN_MILL_ID_PREFIX"
REASON_FOREIGN_MILL_GOAL_FAMILY = "FOREIGN_MILL_GOAL_FAMILY"

REASON_CODES = (
    REASON_FOREIGN_PAYLOAD_FACTORY,
    REASON_FOREIGN_MILL_ID_PREFIX,
    REASON_FOREIGN_MILL_GOAL_FAMILY,
)


@dataclass(frozen=True)
class MillFinding:
    """One record whose mill signals disagree with the directory it sits in."""

    factory: str
    ref: Hashable
    record_id: str | None
    reason_codes: tuple[str, ...]
    mill_prefix: str | None = None
    declared_factory: str | None = None
    expected_factory: str | None = None
    home_factories: tuple[str, ...] = ()
    goal_family_home: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "factory": self.factory,
            "record_id": self.record_id,
            "reason_codes": list(self.reason_codes),
        }
        if self.mill_prefix is not None:
            payload["mill_prefix"] = self.mill_prefix
        if self.declared_factory is not None:
            payload["declared_factory"] = self.declared_factory
        if self.expected_factory is not None:
            payload["expected_factory"] = self.expected_factory
        if self.home_factories:
            payload["home_factories"] = list(self.home_factories)
        if self.goal_family_home is not None:
            payload["goal_family_home"] = self.goal_family_home
        return payload


def summarize(findings: Iterable[MillFinding], id_limit: int = 200) -> dict[str, Any]:
    """Build the JSON-safe mill-mix block shared by census and curation."""

    findings = tuple(findings)
    reason_counts: Counter[str] = Counter()
    by_factory: dict[str, dict[str, Any]] = {}
    for finding in findings:
        reason_counts.update(finding.reason_codes)
        bucket = by_factory.setdefault(
            finding.factory, {"records": 0, "foreign_prefixes": Counter()}
        )
        bucket["records"] += 1
        if REASON_FOREIGN_MILL_ID_PREFIX in finding.reason_codes:
            bucket["foreign_prefixes"][finding.mill_prefix] += 1

    identifiers = sorted(
        finding.record_id for finding in findings if finding.record_id is not None
    )
    return {
        "records": len(findings),
        "reason_codes": dict(sorted(reason_counts.items())),
        "by_factory": {
            factory: {
                "records": bucket["records"],
                "foreign_prefixes": dict(sorted(bucket["foreign_prefixes"].items())),
            }
            for factory, bucket in sorted(by_factory.items())
        },
        "record_ids": identifiers[:id_limit],
        "record_ids_truncated": len(identifiers) > id_limit,
    }
