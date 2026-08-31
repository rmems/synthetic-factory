#!/usr/bin/env python3
"""Shared fixtures and helpers for the preference-curation test modules.

Split out of ``test_curate_preferences`` so each test module can state one
responsibility. Not named ``test_*`` so it is not itself collected.
"""

import contextlib
import copy
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import curate_preferences  # noqa: E402

PURITY_FIXTURES = REPO / "tests" / "fixtures" / "preference-purity"
PUBLISHED_AUDIT = REPO / "docs" / "ffpc-same-state-audit.json"
PUBLISHED_AUDIT_DOC = REPO / "docs" / "ffpc-same-state-audit.md"
PREFERENCE_ISOLATION_DOC = REPO / "docs" / "preference-isolation.md"
GENERATED_TABLE_START = "<!-- BEGIN GENERATED: curate_preferences audit --markdown -->"
GENERATED_TABLE_END = "<!-- END GENERATED -->"

# The Hub-side ``same_state`` audit of rmems/failure-as-fuel-preference-cascade
# reported 17/42 while the factory scan reports 19/42. Both are correct: a
# state-only check cannot see a pair that holds state constant and swaps the
# proposed action. These are the two pairs in that gap.
PROPOSAL_ONLY_IMPURE = (("batch-r05.jsonl", 2), ("batch-r05.jsonl", 3))

# Golden digests of the committed fixture corpus. Pinned as constants (not
# captured at runtime) so an in-place rewrite of the fixtures by the code
# under test — even an idempotent one performed before the immutability test
# takes its baseline — fails loudly instead of self-verifying.
GOLDEN_FIXTURE_SHA256 = {
    "batch-r02.jsonl": "9f85fd74e6974f91fbc9e6a59b4189e2cd93fdd4aaf12c081460132947aefdcc",
    "batch-r03.jsonl": "df8bc117a6e9347e9c8cf71ec3f408c7c36a49d708be1d9ea0d0d6ced5ecbd67",
    "batch-r04.jsonl": "60cf07294147cce075287ec468bbbec93a188b1508766bbdf2515686f90480fb",
    "batch-r05.jsonl": "6baf5f651c03da46fcbe4e9fd057d1f27eed97701d303847bcb2ccb2721818cc",
    "batch-r06.jsonl": "cb6cace4b68f20333809fe63ece0994c4744d3b92a926d689b819636203e3edf",
    "batch-r07.jsonl": "c63f8a1fb02fe88a394495c0b85635df43c0860fcc52f8a6724e598fcfff287e",
    "batch-r08.jsonl": "5741c3bdcc276972bdaefc6d2c1734beea579c5416782f47ea3e60ba6a8769d1",
    "batch-r09.jsonl": "9aa62ca8bd273869c994c4370839dfcbef115d53bad9637b4511a5c3cc02b6e5",
    "batch-r10.jsonl": "43e91b9967322aeeae3a06bb1fb9c6c806731f39c56ec389bb5fc28c0610570b",
    "preferences.jsonl": "12b0062d4a2d3f7494979bfda863401abf8faa26ab3ade426b6bfda94cdd0cff",
}

# The nineteen impure pairs, keyed by (file, line), mirroring the read-only
# scan of the real raw corpus (outputs/raw/2026-08-17/
# failure-as-fuel-preference-cascade, 2026-08-19): action, classification,
# and reason codes are identical to the raw decisions line-for-line.
REPAIRED_IDENTITY = (
    "repaired",
    "attested_identity_annotation_only",
    (
        "EXACT_CONTEXT_COPIED_FROM_ATTESTED_REFERENCE",
        "BRANCH_ONLY_IDENTITY_NOTE_REMOVED",
    ),
)
EXPECTED_IMPURE_DECISIONS = {
    ("batch-r02.jsonl", 1): (
        "excluded",
        "unsupported_context_divergence",
        ("BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE",),
    ),
    ("batch-r02.jsonl", 2): (
        "excluded",
        "unsupported_context_divergence",
        ("BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE",),
    ),
    ("batch-r02.jsonl", 3): (
        "excluded",
        "unsupported_context_divergence",
        ("BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE",),
    ),
    ("batch-r03.jsonl", 4): REPAIRED_IDENTITY,
    ("batch-r03.jsonl", 5): REPAIRED_IDENTITY,
    ("batch-r03.jsonl", 6): REPAIRED_IDENTITY,
    ("batch-r04.jsonl", 4): REPAIRED_IDENTITY,
    ("batch-r04.jsonl", 5): REPAIRED_IDENTITY,
    ("batch-r04.jsonl", 6): REPAIRED_IDENTITY,
    ("batch-r05.jsonl", 2): (
        "excluded",
        "unsupported_context_divergence",
        ("PROPOSED_ACTION_CONTEXT_DIVERGES",),
    ),
    ("batch-r05.jsonl", 3): (
        "repaired",
        "attested_proposal_annotation_only",
        (
            "EXACT_PROPOSAL_COPIED_FROM_ATTESTED_REFERENCE",
            "BRANCH_ONLY_PROPOSAL_ANNOTATION_REMOVED",
        ),
    ),
    ("batch-r06.jsonl", 2): (
        "excluded",
        "unsupported_context_divergence",
        ("POLICY_MEMORY_CONTEXT_DIVERGES",),
    ),
    ("batch-r07.jsonl", 2): (
        "excluded",
        "unsupported_context_divergence",
        ("POLICY_MEMORY_CONTEXT_DIVERGES",),
    ),
    **{
        ("preferences.jsonl", line): (
            "excluded",
            "unsupported_context_divergence",
            ("STATE_CONTEXT_DIVERGES", "PROPOSED_ACTION_CONTEXT_DIVERGES"),
        )
        for line in range(1, 7)
    },
}


def trajectory(record_id, state=None, proposal=None, decision="ACCEPT"):
    return {
        "id": record_id,
        "state": state or {"sim_or_real": "designed", "domain": "preference-curation-test"},
        "proposed_action": proposal or {"action": "bounded-noop", "decision_basis": "fixture"},
        "safety_decision": {"decision": decision, "rationale": "fixture rationale"},
        "executed_action": {"action": "bounded-noop"},
        "future_outcome": {"success": decision != "REJECT"},
        "reward_components": {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        "meta": {"tags": ["preference", "fixture"]},
    }


def pair(record_id="pair-1", chosen_state=None, rejected_state=None, proposal=None):
    shared_state = {"sim_or_real": "designed", "domain": "same-problem"}
    shared_proposal = proposal or {"action": "inspect", "decision_basis": "fixture"}
    return {
        "id": record_id,
        "chosen": trajectory(
            f"{record_id}-chosen",
            state=copy.deepcopy(chosen_state or shared_state),
            proposal=copy.deepcopy(shared_proposal),
            decision="MODIFY",
        ),
        "rejected": trajectory(
            f"{record_id}-rejected",
            state=copy.deepcopy(rejected_state or shared_state),
            proposal=copy.deepcopy(shared_proposal),
            decision="ACCEPT",
        ),
        "critique": "fixture preference",
        "reward_delta": {"task_progress": 0.0, "safety": 0.0, "total": 0.0},
    }


def write_jsonl(path, records):
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def leftover_mill_episode(record_id):
    """An agentic episode of the kind that leaked into a preference tree."""
    return {
        "id": record_id,
        "goal": "remove the leftover buildah vfs image id",
        "plan": "inspect, repair, verify",
        "steps": [
            {
                "n": index,
                "decision_basis": "Observation: inspect the leftover object",
                "tool_call": {"name": "bash", "args": {"command": f"echo {index}"}},
                "observation": f"inspected step {index}",
            }
            for index in range(1, 5)
        ],
        "outcome": "leftover object removed",
        "reward": {"success": True},
        "meta": {"factory": "code-review-preference-factory", "round": 723},
    }


RAW_FFPC = REPO / "outputs" / "raw" / "2026-08-17" / "failure-as-fuel-preference-cascade"


def run_cli(*argv):
    """Run the module CLI, returning ``(status, stdout, stderr)``."""

    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        status = curate_preferences.main(list(argv))
    return status, out.getvalue(), err.getvalue()


def audit_decision_map(audit):
    """Key one audit document by source location, dropping corpus-copy fields.

    ``source_sha256`` and ``record_id`` identify a particular copy of the
    corpus; the decision itself must be reproducible from any faithful copy.
    """

    return {
        (pair["source_path"], pair["source_line"]): (
            pair["action"],
            pair["classification"],
            tuple(pair["reason_codes"]),
            pair["same_state"],
            pair["same_proposed_action"],
            tuple(pair["divergent_context_fields"]),
        )
        for pair in audit["impure_pairs"]
    }
