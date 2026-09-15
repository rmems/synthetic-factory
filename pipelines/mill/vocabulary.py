#!/usr/bin/env python3
"""Vocabulary of the ``mill`` family (identity-bind episodes).

Identities, the plant catalog shape, step limits, banned keys, and the
coded refusal type on the shared :class:`refusals.CodedRefusal`. No logic
beyond the refusal helpers.
"""

from __future__ import annotations

from typing import Any

from ._contract import bind_import_twin, oc, refusals

FAMILY = "mill"
GENERATOR_NAME = "mill-identity-bind"
GENERATOR_VERSION = "1.0.0"
GENERATOR_KIND = "programmatic"
FACTORY_ID = "mill-identity-bind-factory"
RECORD_ID_PREFIX = "mill"
RECORD_KIND = "episode"
CATALOG_ID = "mill-identity-bind-v1"
CATALOG_FORMAT = "mill-catalog/1"
RUN_FORMAT = "mill-run/1"
PUBLICATION_FORMAT = "mill-publication/1"
PRODUCER = "pipelines/mill/records.py"

ROLE_TASK_AUTHOR = "task_author"
ROLE_SOLVER = "solver"
ACTOR_ROLES = (ROLE_TASK_AUTHOR, ROLE_SOLVER)

DB_PLAN = "Plan"
DB_OBSERVATION = "Observation"
DB_REFLECTION = "Reflection"
DB_PREFIXES = (f"{DB_PLAN}:", f"{DB_OBSERVATION}:", f"{DB_REFLECTION}:")
MAX_DECISION_BASIS = 240
SUCCESS_STEPS = 16
FAIL_STEPS = 17
PAIR_QUOTA = 2
MAX_SEED = oc.MAX_SEED
MAX_COUNT = 60

BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
BANNED_SUBSTRINGS = (
    "leftover leftover leftover",
    "grok-4.6",
    "hop_unreserved",
)
BANNED_SIM_OR_REAL = "real"

FINDING_CATALOG_FILE_MISSING = "CATALOG_FILE_MISSING"
FINDING_CATALOG_FIELD_MISSING = "CATALOG_FIELD_MISSING"
FINDING_CATALOG_FIELD_INVALID = "CATALOG_FIELD_INVALID"
FINDING_PLANTS_SHA_MISMATCH = "PLANTS_SHA_MISMATCH"
FINDING_PLANT_FIELD_MISSING = "PLANT_FIELD_MISSING"
FINDING_PLANT_FIELD_INVALID = "PLANT_FIELD_INVALID"
FINDING_PLANT_ID_DUPLICATE = "PLANT_ID_DUPLICATE"
FINDING_SEED_NOT_AN_INTEGER = "SEED_NOT_AN_INTEGER"
FINDING_SEED_OUT_OF_DOMAIN = "SEED_OUT_OF_DOMAIN"
FINDING_COUNT_OUT_OF_DOMAIN = "COUNT_OUT_OF_DOMAIN"
FINDING_PRODUCED_AT_NOT_A_TIMESTAMP = "PRODUCED_AT_NOT_A_TIMESTAMP"
FINDING_DESTINATION_EXISTS = "DESTINATION_EXISTS"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"
FINDING_RUN_FILE_MISSING = "RUN_FILE_MISSING"
FINDING_RECORD_MALFORMED = "RECORD_MALFORMED"
FINDING_RECORD_NOT_FOUND = "RECORD_NOT_FOUND"
FINDING_FACTORY_HOP_REFUSED = "FACTORY_HOP_REFUSED"
FINDING_FACTORY_MISMATCH = "FACTORY_MISMATCH"
FINDING_BANNED_KEY = "BANNED_KEY"
FINDING_BANNED_SUBSTRING = "BANNED_SUBSTRING"
FINDING_DECISION_BASIS_INVALID = "DECISION_BASIS_INVALID"
FINDING_STEP_COUNT_INVALID = "STEP_COUNT_INVALID"
FINDING_INPUT_NOT_AN_OBJECT = "INPUT_NOT_AN_OBJECT"
FINDING_CODES = (
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_ID_DUPLICATE,
    FINDING_SEED_NOT_AN_INTEGER,
    FINDING_SEED_OUT_OF_DOMAIN,
    FINDING_COUNT_OUT_OF_DOMAIN,
    FINDING_PRODUCED_AT_NOT_A_TIMESTAMP,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_RUN_FILE_MISSING,
    FINDING_RECORD_MALFORMED,
    FINDING_RECORD_NOT_FOUND,
    FINDING_FACTORY_HOP_REFUSED,
    FINDING_FACTORY_MISMATCH,
    FINDING_BANNED_KEY,
    FINDING_BANNED_SUBSTRING,
    FINDING_DECISION_BASIS_INVALID,
    FINDING_STEP_COUNT_INVALID,
    FINDING_INPUT_NOT_AN_OBJECT,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)
REASON_CODE_SET: frozenset[str] = frozenset()


class MillRefusal(refusals.CodedRefusal):
    """The family's coded refusal: a ``ContractError`` whose ``str`` is ``CODE: prose``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = refusals.helpers(MillRefusal)
shown = refusals.shown


def finding_code(text: Any) -> str | None:
    """The declared finding code before the first ``": "`` of a text, or None."""
    return refusals.code_of(text, FINDING_CODE_SET)


def record_id(round_n: int, stem: str) -> str:
    """Stable mill record id for one plant stem at ``round_n``."""
    return f"{RECORD_ID_PREFIX}-r{round_n:02d}-{stem}"


bind_import_twin(__name__)
