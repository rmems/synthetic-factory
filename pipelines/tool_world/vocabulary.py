#!/usr/bin/env python3
"""Vocabulary of the tool-world families: identities, limits, finding codes.

No logic beyond the coded refusal helpers. Surfaces, factories, record kinds,
and tool names are declared here so no shared pipeline needs a literal.
"""

from __future__ import annotations

from typing import TypeGuard

from ._contract import bind_import_twin, refusals, rng

FAMILY = "tool-world"
GENERATOR_NAME = "tool-world-scripted-policy"
GENERATOR_VERSION = "1.0.0"
GENERATOR_KIND = "programmatic"
GENERATOR_OWNERSHIP = "project_owned"
GENERATION_METHOD = "deterministic_execution"
CATALOG_FORMAT = "tool-world-catalog/1"
PACK_FORMAT = "tool-world-pack/1"
RUN_FORMAT = "tool-world-run/1"
RECORD_SCHEMA_VERSION = "tool-world-record-v1"
RECORD_ID_PREFIX = "twd"
ORACLE_KIND = "tool_world_replay"
ORACLE_CERTIFIER = "tool_world.replay"
CURATION_PIPELINE_VERSION = "tool-world-v1"
TASK_AUTHOR_MODEL = "tool-world-pack"

SURFACE_WORKSPACE = "workspace"
SURFACE_MCP = "mcp"
SURFACE_BROWSER = "browser"
SURFACE_DELEGATION = "delegation"
SURFACES = (SURFACE_WORKSPACE, SURFACE_MCP, SURFACE_BROWSER, SURFACE_DELEGATION)
CORE_SURFACE = "core"

FACTORY_BY_SURFACE = {
    SURFACE_WORKSPACE: "tool-world-workspace-factory",
    SURFACE_MCP: "tool-world-mcp-factory",
    SURFACE_BROWSER: "tool-world-browser-factory",
    SURFACE_DELEGATION: "tool-world-delegation-factory",
}
RECORD_KIND_BY_SURFACE = {
    SURFACE_WORKSPACE: "tool_episode_v1",
    SURFACE_MCP: "mcp_session_v1",
    SURFACE_BROWSER: "browser_task_v1",
    SURFACE_DELEGATION: "delegation_v1",
}

TOOL_REPORT = "report_result"
TOOL_CONFIRM = "confirm_action"
TOOL_MCP = "mcp"
TOOL_BROWSER = "browser"
TOOL_AGENT = "agent"

MAX_OBSERVATION_CHARS = 2000
MAX_DECISION_BASIS = 240
MAX_STEPS_CEILING = 60
MAX_SEED = rng.MAX_SEED
MAX_COUNT = 200
MAX_PACK_MEMBER_BYTES = 262_144

# The fault kind every surface may declare to mean "the call never reached the
# tool; retry it". The environment keeps a pending confirmation across such a
# fault, so the retry of an irreversible call still counts as confirmed.
FAULT_KIND_TRANSIENT = "transient_error"

DB_PLAN = "Plan"
DB_OBSERVATION = "Observation"
DB_REFLECTION = "Reflection"
DB_PREFIXES = (DB_PLAN, DB_OBSERVATION, DB_REFLECTION)

PERTURBATION_GIVE_UP = "give_up_on_fault"
PERTURBATION_SKIP_VERIFICATION = "skip_verification"
PERTURBATION_SKIP_CONFIRMATION = "skip_confirmation"
PERTURBATION_WRONG_ARG_TYPE = "wrong_arg_type"
PERTURBATIONS = (
    PERTURBATION_GIVE_UP,
    PERTURBATION_SKIP_VERIFICATION,
    PERTURBATION_SKIP_CONFIRMATION,
    PERTURBATION_WRONG_ARG_TYPE,
)
VARIANT_GOLD = "gold"

DECISION_ACCEPT = "accept"
DECISION_MEASURE = "measure"
OUTCOME_SUCCESS = "success"
OUTCOME_FAILURE = "failure"

FINDING_CATALOG_FILE_MISSING = "CATALOG_FILE_MISSING"
FINDING_CATALOG_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_PACK_SHA_MISMATCH = "PACK_SHA_MISMATCH"
FINDING_PACK_FILE_MISSING = "PACK_FILE_MISSING"
FINDING_PACK_FIELD_INVALID = "PACK_FIELD_INVALID"
FINDING_PACK_MEMBER_INVALID = "PACK_MEMBER_INVALID"
FINDING_TASK_FIELD_INVALID = "TASK_FIELD_INVALID"
FINDING_TASK_NOT_FOUND = "TASK_NOT_FOUND"
FINDING_SEED_INVALID = "SEED_INVALID"
FINDING_COUNT_OUT_OF_DOMAIN = "COUNT_OUT_OF_DOMAIN"
FINDING_PRODUCED_AT_NOT_A_TIMESTAMP = "PRODUCED_AT_NOT_A_TIMESTAMP"
FINDING_DESTINATION_EXISTS = "DESTINATION_EXISTS"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"
FINDING_RUN_FILE_MISSING = "RUN_FILE_MISSING"
FINDING_RUN_FILE_INVALID = "RUN_FILE_INVALID"
FINDING_RUN_SHA_MISMATCH = "RUN_SHA_MISMATCH"
FINDING_RECORD_MALFORMED = "RECORD_MALFORMED"
FINDING_RECORD_NOT_FOUND = "RECORD_NOT_FOUND"
FINDING_TOOL_UNKNOWN = "TOOL_UNKNOWN"
FINDING_TOOL_CALL_MALFORMED = "TOOL_CALL_MALFORMED"
FINDING_SURFACE_UNKNOWN = "SURFACE_UNKNOWN"
FINDING_PREDICATE_UNKNOWN = "PREDICATE_UNKNOWN"
FINDING_FAULT_UNKNOWN = "FAULT_UNKNOWN"
FINDING_BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
FINDING_DECISION_BASIS_INVALID = "DECISION_BASIS_INVALID"
FINDING_CAPTURE_FAILED = "CAPTURE_FAILED"
FINDING_TRAINING_VIEW_INVALID = "TRAINING_VIEW_INVALID"
FINDING_REPLAY_MISMATCH = "REPLAY_MISMATCH"
FINDING_INPUT_NOT_AN_OBJECT = "INPUT_NOT_AN_OBJECT"
FINDING_CODES = frozenset(
    {
        FINDING_CATALOG_FILE_MISSING,
        FINDING_CATALOG_FIELD_INVALID,
        FINDING_PACK_SHA_MISMATCH,
        FINDING_PACK_FILE_MISSING,
        FINDING_PACK_FIELD_INVALID,
        FINDING_PACK_MEMBER_INVALID,
        FINDING_TASK_FIELD_INVALID,
        FINDING_TASK_NOT_FOUND,
        FINDING_SEED_INVALID,
        FINDING_COUNT_OUT_OF_DOMAIN,
        FINDING_PRODUCED_AT_NOT_A_TIMESTAMP,
        FINDING_DESTINATION_EXISTS,
        FINDING_DESTINATION_UNDER_RAW,
        FINDING_RUN_FILE_MISSING,
        FINDING_RUN_FILE_INVALID,
        FINDING_RUN_SHA_MISMATCH,
        FINDING_RECORD_MALFORMED,
        FINDING_RECORD_NOT_FOUND,
        FINDING_TOOL_UNKNOWN,
        FINDING_TOOL_CALL_MALFORMED,
        FINDING_SURFACE_UNKNOWN,
        FINDING_PREDICATE_UNKNOWN,
        FINDING_FAULT_UNKNOWN,
        FINDING_BUDGET_EXHAUSTED,
        FINDING_DECISION_BASIS_INVALID,
        FINDING_CAPTURE_FAILED,
        FINDING_TRAINING_VIEW_INVALID,
        FINDING_REPLAY_MISMATCH,
        FINDING_INPUT_NOT_AN_OBJECT,
    }
)


class ToolWorldRefusal(refusals.CodedRefusal):
    """A coded tool-world refusal; ``str(exc)`` is ``"CODE: prose"``."""

    CODES = FINDING_CODES


refuse, refuse_when, refuse_first = refusals.helpers(ToolWorldRefusal)
shown = refusals.shown


def is_genuine_int(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def check_seed(seed: object) -> None:
    if not is_genuine_int(seed):
        raise ToolWorldRefusal(FINDING_SEED_INVALID, f"seed must be an integer, got {shown(seed)}")
    refuse_when(
        not 0 <= seed <= MAX_SEED,
        FINDING_SEED_INVALID,
        f"seed must lie in [0, {MAX_SEED}], got {shown(seed)}",
    )


bind_import_twin(__name__)
