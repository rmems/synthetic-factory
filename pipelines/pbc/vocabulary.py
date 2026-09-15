#!/usr/bin/env python3
"""Vocabulary for the ``pbc`` mill family (proto-breaking-change lane).

The reviewed mill prefix ``pbc`` maps to ``proto-breaking-change-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. Slice ``A`` of the
mill-usage-burst plan covers the eight deterministic catalogs extracted from
``legacy-mill-lane`` (r701, r731, r751, r787, r803, r966, r988, r2535).
The leftover cartesian generator r1335 is extracted but not in this slice.
"""

from __future__ import annotations

FAMILY_PREFIX = "pbc"
FACTORY = "proto-breaking-change-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
PLAN_SCHEMA_ID = "mill-usage-burst-plan/v1"
PLAN_SLICE = "A"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
DEFAULT_PLAN_PATH = "config/mill-usage-burst-plan.pbc-a.json"
