"""Shared constants for the payload-kind audit test suite (issue #74).

Split out of test_payload_kind_audit.py so the published-fixture and
raw-corpus-fidelity test classes can each live in their own file without
duplicating these paths and tables.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

AUDIT_JSON = REPO / "docs" / "agentic-coding-payload-kind.json"
AUDIT_DOC = REPO / "docs" / "agentic-coding-payload-kind.md"
RAW_AGENTIC_CODING = REPO / "outputs" / "raw" / "2026-08-17" / "agentic-coding-trajectory-factory"

# The keys build_audit derives from a corpus. The published document adds
# context around them (Hub cross-reference, card text) that no corpus scan can
# produce; only the derived keys are re-derivable.
DERIVED_KEYS = ("schema_version", "source", "summary", "files", "records")

# Every thalamic record id issue #74 lists, in published order.
ISSUE_74_THALAMIC_IDS = (
    "act-r02-001",
    "act-r02-002",
    "act-r03-001",
    "act-r03-002",
    "act-r04-001",
    "act-r04-002",
    "act-r05-001",
    "act-r05-002",
    "act-r06-001",
    "act-r06-002",
    "act-r07-001",
    "act-r07-002",
    "act-r08-001",
    "act-r08-002",
    "act-r09-001",
    "act-r09-002",
)
