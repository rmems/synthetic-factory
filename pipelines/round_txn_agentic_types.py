#!/usr/bin/env python3
"""Shared types and tiny predicates for the agentic envelope rule table.

``round_txn_agentic`` and its factory-rule siblings read the same policy,
batch contract, tally and per-record context. Keeping those shapes here
avoids a cycle: the rule modules import this file, not each other.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("round_txn_agentic_types")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "round_txn_agentic_types"
    )


@dataclass(frozen=True)
class AgenticPolicy:
    """Facade-owned seams the envelope reads through ``round_txn``'s namespace."""

    factory_kinds: Mapping[str, str]
    factory_quotas: Mapping[str, int]
    scenario_terms: Mapping[str, tuple]
    reviewed_hosted_generator: Callable[[Path], str]
    jsonl_records: Callable[[Path], tuple[list, list[str]]]


@dataclass(frozen=True)
class BatchContract:
    """The fixed identity every record of one staged agentic batch must carry."""

    factory_name: str
    kind: str
    round_number: int
    expected_generator: str
    #: The restart-lane scenario phases, or ``None`` when the lane has none.
    scenario_terms: tuple | None


@dataclass
class EnvelopeTally:
    """Per-batch totals the batch rules judge after every record was checked."""

    safety_case_types: list = field(default_factory=list)
    cascade_fault_kinds: list = field(default_factory=list)
    cascade_recovery_values: list = field(default_factory=list)
    long_horizon_success_values: list = field(default_factory=list)
    long_horizon_scenario_signatures: list = field(default_factory=list)
    tool_use_lesson_signatures: list = field(default_factory=list)


@dataclass(frozen=True)
class EnvelopeContext:
    """One staged record under the batch contract, plus the shared tally."""

    batch: BatchContract
    where: str
    record: object
    tally: EnvelopeTally

    @property
    def factory_name(self) -> str:
        return self.batch.factory_name

    def get(self, key: str):
        """``record.get(key)`` when the record is an object, else ``None``."""
        return self.record.get(key) if isinstance(self.record, dict) else None


RecordRule = Callable[[EnvelopeContext], list[str]]
BatchRule = Callable[[EnvelopeTally, int], list[str]]


def _is_plain_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _nonempty_str(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _outcome_text(outcome) -> str:
    return outcome.casefold() if isinstance(outcome, str) else ""


if __package__:
    _expose_package_sibling(__name__)
