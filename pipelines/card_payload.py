#!/usr/bin/env python3
"""The payload summary a Hub card renders, and the keyword surfaces that build it.

``render_card`` in ``scripts/publish_grok46_hub.py`` accepts two call styles:
the current ``summary=PayloadSummary(...)`` and the legacy
``records=/bytes_=/first=/last=/payload_names=`` keywords still used by the
card leaf PRs stacked on the schema-infra branch. This module owns the frozen
summary itself and the fail-closed resolution between those surfaces, so both
styles keep rendering byte-identical cards until every leaf migrates.
"""

from __future__ import annotations

import dataclasses
from typing import cast

# The pre-PayloadSummary render_card keyword surface. Every card leaf PR
# stacked on the schema-infra branch still calls it; render_card keeps
# accepting it until those leaves migrate after merging.
LEGACY_SUMMARY_KEYS = ("records", "bytes_", "first", "last", "payload_names")


@dataclasses.dataclass(frozen=True)
class PayloadSummary:
    """Everything a card says about its published payload: counts, span, names."""

    records: int
    bytes_: int
    first: str | None
    last: str | None
    names: list[str] | None = None


def resolve_payload_summary(keywords: dict[str, object]) -> PayloadSummary:
    """Accept summary= or the legacy keyword surface, refusing mixtures.

    Both call styles must render byte-identical cards. Unknown keywords and
    mixing summary= with legacy keywords fail closed with TypeError, exactly
    as a plain wrong-signature call would.
    """

    unknown = sorted(set(keywords) - {"summary", *LEGACY_SUMMARY_KEYS})
    if unknown:
        raise TypeError(
            "render_card() got unexpected keyword arguments: " + ", ".join(unknown)
        )
    summary = keywords.get("summary")
    legacy = {key: value for key, value in keywords.items() if key != "summary"}
    if summary is not None:
        if legacy:
            raise TypeError(
                "render_card() takes summary= or the legacy payload keywords "
                "(records=, bytes_=, first=, last=, payload_names=), not both"
            )
        return cast(PayloadSummary, summary)
    missing = [
        key for key in ("records", "bytes_", "first", "last") if key not in legacy
    ]
    if missing:
        raise TypeError(
            "render_card() missing required keyword arguments: " + ", ".join(missing)
        )
    return PayloadSummary(
        records=cast(int, legacy["records"]),
        bytes_=cast(int, legacy["bytes_"]),
        first=cast("str | None", legacy["first"]),
        last=cast("str | None", legacy["last"]),
        names=cast("list[str] | None", legacy.get("payload_names")),
    )
