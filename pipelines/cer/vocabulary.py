#!/usr/bin/env python3
"""Vocabulary for the ``cer`` mill family (cascading-error-recovery lane).

The reviewed mill prefix ``cer`` maps to ``cascading-error-recovery-factory`` in
``mill_reviewed_vocabulary.REVIEWED_MILL_PREFIX_HOMES``. Slice ``A`` of the
mill-usage-burst plan covers the two preserved leftover-mill scripts
``cer_r1901`` and ``cer_r1958`` on ``legacy-mill-lane``.
"""

from __future__ import annotations

FAMILY_PREFIX = "cer"
FACTORY = "cascading-error-recovery-factory"
GENERATOR = "grok-4.6"
RECORD_ID_PREFIX = FAMILY_PREFIX
QUOTA_PER_ROUND = 2
PLAN_SCHEMA_ID = "mill-usage-burst-plan/v1"
PLAN_SLICE = "A"
DEFAULT_RUN_LABEL = "2026-08-19-agentic"
DEFAULT_PLAN_PATH = "config/mill-usage-burst-plan.cer-a.json"
