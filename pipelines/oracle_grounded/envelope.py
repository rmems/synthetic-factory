"""Shared oracle-grounded record envelope: the domain-neutral foundation (#172).

Every oracle-grounded record in the factory (parent epic #76) is an envelope of
eight sections -- ``generator`` / ``scenario`` / ``intervention`` /
``candidate_prediction`` / ``oracle`` / ``result`` / ``provenance`` /
``validation`` -- under one governing rule: generators propose, oracles decide.
The first four sections are generator-authored; the rest are oracle- or
validator-authored, and a measurement-shaped key inside a generator section is
a contract violation, not a convenience.

This module carries only what every domain contract needs and none of them
disagrees on: the section names, the repository-wide ``provenance.kind``
vocabulary and its training-eligible subset, the bounded reserved-key walker
and the generator/oracle separation check built on it, the ``ContractError`` /
``OracleUnavailable`` exceptions, canonical JSON and the bare-hex
``record_digest`` dialect, the generator-subtree ``proposal_of`` /
``proposal_digest`` pair, the NaN/Infinity parse hooks, type-strict JSON
equality, and the section shape check ``check_sections``.

Deliberately excluded, because each is owned by one domain contract and the
contracts disagree: measurement units, meters and energy claims; parity
verdicts, reason codes and training views; oracle stages, availability and
``reproduce``; schema-version pins, record builders, and the result-status and
validation-status vocabularies (``unvalidated`` / ``stamp_validation``). Domain
contracts extend this module: they import these primitives, add their own
reserved-key sets, required-key tuples and per-block rules, and never redefine
a symbol carried here.

Digest dialect: ``canonical_json`` is ``json.dumps`` with sorted keys, compact
separators, ``ensure_ascii=False`` and ``allow_nan=False``; ``record_digest``
is the bare-hex SHA-256 of that text with ``validation`` and
``provenance.record_sha256`` removed. A contract that pins another dialect (a
``sha256:``-prefixed, float-rounded digest, say) passes its own callable to
``proposal_digest``.

Standard library only, like the rest of ``pipelines/``. Importable both as
``oracle_grounded.envelope`` (with ``pipelines/`` on ``sys.path``, the CLI
convention) and as ``pipelines.oracle_grounded.envelope`` from the repository
root.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from collections.abc import Callable, Container
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

if __name__.startswith("pipelines."):
    from .. import validate_run_provenance as _validate_run_provenance
else:
    # Direct-CLI convention: ``pipelines/`` is on sys.path, so the flat
    # sibling is importable by its bare name.
    import validate_run_provenance as _validate_run_provenance

# Sections a generator owns. Oracle-measured keys may never appear here.
# Identical in origin/agent/issue-77-oracle-grounded-datasets:pipelines/oracle_grounded/record.py:24
# and origin/agent/issue-78-distillation-datasets:pipelines/oracle_contract.py:82 (verbatim).
GENERATOR_SECTIONS = ("generator", "scenario", "intervention", "candidate_prediction")

# The eight sections of the epic contract, in envelope order; named at
# origin/agent/issue-78-distillation-datasets:pipelines/oracle_contract.py:10-12.
# Each domain contract keeps its own required-key tuple around these.
CONTRACT_SECTIONS = GENERATOR_SECTIONS + ("oracle", "result", "provenance", "validation")

# Sections a record may omit or set to null: the distillation builder writes
# them only when given (oracle_contract.py:834-838 on #138), the parity
# envelope accepts ``intervention: null`` (oracle_contract.py:466-467 on #135)
# and the neuromorphic envelope accepts ``candidate_prediction: null``
# (record.py:455-458 on #134).
_OPTIONAL_SECTIONS = frozenset({"intervention", "candidate_prediction"})

# ``provenance.kind`` is the repository-wide vocabulary that main's validator
# reads from the thalamic schema (pipelines/validate_run_provenance.py:18-22).
# It replaces the two PR copies at
# origin/agent/issue-79-fpga-nir-parity:pipelines/oracle_contract.py:64 and
# origin/agent/issue-77-oracle-grounded-datasets:pipelines/oracle_grounded/record.py:96.
PROVENANCE_KINDS = _validate_run_provenance.ALLOWED_PROVENANCE_KIND

# The training-eligible subset: ``unknown`` provenance is never a training
# candidate. From
# origin/agent/issue-77-oracle-grounded-datasets:pipelines/oracle_grounded/record.py:97.
TRAINING_PROVENANCE_KINDS = frozenset({"designed", "simulated", "hil"})

# From origin/agent/issue-78-distillation-datasets:pipelines/oracle_contract.py:216-220 (verbatim).
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

ISO_8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)

# One reserved key already rejects the record, so the scan stops collecting
# paths at this cap: a schema-open stored payload full of reserved keys must
# not be able to turn path collection into a multi-megabyte finding string.
# From origin/agent/issue-77-oracle-grounded-datasets:pipelines/oracle_grounded/record.py:104-107.
MAX_RESERVED_KEY_HITS = 25


# From origin/agent/issue-78-distillation-datasets:pipelines/oracle_contract.py:223-237 (verbatim).
class ContractError(ValueError):
    """Raised when a record cannot be built inside the contract."""


class OracleUnavailable(RuntimeError):
    """Raised when a named oracle cannot run in this environment.

    Callers must let this propagate or record an explicit abstention. It must
    never be swallowed into a synthesized result.
    """

    def __init__(self, oracle: str, detail: str) -> None:
        super().__init__(f"{oracle} unavailable: {detail}")
        self.oracle = oracle
        self.detail = detail


# From origin/agent/issue-78-distillation-datasets:pipelines/oracle_contract.py:240-276 (verbatim).
def canonical_json(value: Any) -> str:
    """Return the canonical JSON form used for digests and equality."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp with a trailing ``Z``."""

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def is_number(value: Any) -> bool:
    """True for a real, finite, non-boolean number."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


def is_enum_value(value: Any, allowed: Container[str]) -> bool:
    """Membership test for enum-like JSON fields that cannot raise.

    A JSON-valid record can put an array or object where a string enum
    belongs. Testing such an unhashable value against a set (or using it as a
    dict key) raises ``TypeError``, and ``validate_path`` does not catch that —
    one malformed line would abort validation of the entire run. A non-string
    is simply not a member.
    """

    return isinstance(value, str) and value in allowed


# From origin/agent/issue-78-distillation-datasets:pipelines/oracle_contract.py:279-291 (verbatim).
def record_digest(record: dict[str, Any]) -> str:
    """SHA-256 over the record with volatile/derived fields removed.

    ``validation`` and ``provenance.record_sha256`` are excluded so stamping a
    validation verdict does not change the identity of the measured record.
    """

    payload = copy.deepcopy(record)
    payload.pop("validation", None)
    provenance = payload.get("provenance")
    if isinstance(provenance, dict):
        provenance.pop("record_sha256", None)
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


# From origin/agent/issue-77-oracle-grounded-datasets:pipelines/oracle_grounded/record.py:145-147
# (verbatim).
def proposal_of(record: dict[str, Any]) -> dict[str, Any]:
    """Exactly the generator-authored subtree that ``proposal_hash`` covers."""
    return {section: record.get(section) for section in GENERATOR_SECTIONS}


def proposal_digest(
    record: dict[str, Any], digest: Callable[[Any], str] = record_digest
) -> str:
    """Digest of exactly the generator-authored subtree, computed by ``digest``.

    The digest is a parameter because the factory has two content-hash
    dialects: this module's bare-hex ``record_digest`` (the default) and the
    ``sha256:``-prefixed, float-rounded ``canon.digest`` that #134's golden
    fixtures pin as ``proposal_hash``. Either way the input is
    ``proposal_of(record)``, so a measurement back-written into a scenario
    after the oracle ran is detected by whichever dialect the contract uses.
    """
    return digest(proposal_of(record))


# From origin/agent/issue-79-fpga-nir-parity:pipelines/oracle_contract.py:165-188 (verbatim).
def reject_json_constant(value: str) -> None:
    """Reject Python's non-standard NaN/Infinity JSON extensions.

    Pass as ``json.loads(text, parse_constant=reject_json_constant)`` in both
    family readers so a record smuggling ``NaN``/``Infinity``/``-Infinity``
    is treated as a parse error rather than silently accepted with a value
    standards-compliant downstream JSON parsers cannot consume.
    """
    raise ValueError(f"non-standard JSON numeric constant {value}")


def reject_nonfinite_float(text: str) -> float:
    """Parse a JSON float token, rejecting overflow-to-infinity values.

    ``parse_constant`` never sees an ordinary numeric token like ``1e9999``,
    which ``float()`` silently turns into infinity — a value ``digest()``
    (``allow_nan=False``) can never re-derive. Pass as
    ``json.loads(text, parse_float=reject_nonfinite_float)`` alongside
    ``reject_json_constant`` so both smuggling routes fail at the parse.
    """
    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"non-finite JSON number {text}")
    return value


# From origin/agent/issue-79-fpga-nir-parity:pipelines/oracle_contract.py:219-243 (verbatim).
def _strict_mapping_equal(recorded: dict, expected: dict) -> bool:
    """Same keys, and every value strictly equal."""
    return recorded.keys() == expected.keys() and all(
        strict_json_equal(recorded[key], expected[key]) for key in expected
    )


def _strict_sequence_equal(recorded: list, expected: list) -> bool:
    """Same length, and every element strictly equal in order."""
    return len(recorded) == len(expected) and all(
        strict_json_equal(left, right) for left, right in zip(recorded, expected)
    )


def strict_json_equal(recorded: Any, expected: Any) -> bool:
    """Compare JSON-shaped evidence without Python's bool/number coercions."""
    if type(recorded) is not type(expected):
        return False
    if isinstance(expected, float):
        return math.isfinite(recorded) and math.isfinite(expected) and recorded == expected
    if isinstance(expected, dict):
        return _strict_mapping_equal(recorded, expected)
    if isinstance(expected, list):
        return _strict_sequence_equal(recorded, expected)
    return recorded == expected


# Adapted from
# origin/agent/issue-77-oracle-grounded-datasets:pipelines/oracle_grounded/record.py:110-142:
# the reserved-key set is a parameter (each contract keeps its own; a union
# would reject #134's golden ``scenario.outcome``), carried with the collected
# paths in one scan state so no helper grows past three arguments.
@dataclass
class _ReservedKeyScan:
    """Bounded collection state for one reserved-key walk."""

    reserved: Container[str]
    hits: list[str] = field(default_factory=list)

    def capped(self) -> bool:
        return len(self.hits) >= MAX_RESERVED_KEY_HITS


def _scan_mapping(value: dict, path: str, scan: _ReservedKeyScan) -> None:
    for key, item in value.items():
        if scan.capped():
            break
        here = f"{path}.{key}" if path else str(key)
        if key in scan.reserved:
            scan.hits.append(here)
        _scan_value(item, here, scan)


def _scan_value(value: Any, path: str, scan: _ReservedKeyScan) -> None:
    if isinstance(value, dict):
        _scan_mapping(value, path, scan)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            if scan.capped():
                break
            _scan_value(item, f"{path}[{index}]", scan)


def reserved_key_hits(record: dict[str, Any], reserved_keys: Container[str]) -> list[str]:
    """Paths of ``reserved_keys`` inside the generator sections, capped.

    Only ``proposal_of(record)`` is walked, so an oracle is free to use the
    same key names under ``result``. At most ``MAX_RESERVED_KEY_HITS`` paths
    are collected; one hit already rejects the record.
    """
    scan = _ReservedKeyScan(reserved_keys)
    _scan_value(proposal_of(record), "", scan)
    return scan.hits


def _reserved_key_listing(hits: list[str]) -> str:
    """Human-readable path list, marking when the bounded scan stopped early."""
    listed = ", ".join(sorted(hits))
    if len(hits) >= MAX_RESERVED_KEY_HITS:
        listed += ", ... (scan capped)"
    return listed


# Adapted from origin/agent/issue-78-distillation-datasets:pipelines/oracle_contract.py:492-508:
# the uncapped ``_walk_keys`` is replaced by the bounded walker above and the
# reserved-key set is a parameter. The ``predicted_*`` naming rule that follows
# at 509-518 is a distillation rule and stays in that contract.
def check_generator_oracle_separation(
    record: dict[str, Any], reserved_keys: Container[str], where: str
) -> list[str]:
    """Reject oracle-owned keys hiding inside generator-owned sections.

    Stops at the separation check. Whether ``candidate_prediction`` keys must
    be namespaced, disclaim authority or declare a ``kind`` is a domain rule.
    """

    errors: list[str] = []
    for section in GENERATOR_SECTIONS:
        block = record.get(section)
        if block is not None and not isinstance(block, (dict, list)):
            errors.append(f"{where}.{section} must be an object")
    hits = reserved_key_hits(record, reserved_keys)
    if hits:
        errors.append(
            f"{where}: ORACLE_FIELD_IN_GENERATOR_NAMESPACE at "
            f"{_reserved_key_listing(hits)} (generator sections carry "
            "oracle-reserved keys that only an oracle may write)"
        )
    return errors


def _section_errors(record: dict[str, Any], section: str, where: str) -> list[str]:
    block = record.get(section)
    if section in _OPTIONAL_SECTIONS:
        if block is not None and not isinstance(block, dict):
            return [f"{where}.{section} must be an object or null"]
        return []
    if section not in record:
        return [f"{where}.{section} is required"]
    if not isinstance(block, dict):
        return [f"{where}.{section} must be an object"]
    return []


# Composed from the three envelope shape checks:
# origin/agent/issue-78-distillation-datasets:pipelines/oracle_contract.py:816-838,
# origin/agent/issue-79-fpga-nir-parity:pipelines/oracle_contract.py:459-468 and
# origin/agent/issue-77-oracle-grounded-datasets:pipelines/oracle_grounded/record.py:453-458.
def check_sections(record: Any, where: str) -> list[str]:
    """Check the shape of the eight contract sections; returns error strings.

    Only dict-ness is checked: the six sections every contract requires must
    be present objects, and ``intervention`` / ``candidate_prediction`` may be
    absent or null but must otherwise be objects. What goes inside a section,
    which extra top-level keys are required, and whether a section may be
    empty are domain rules. Named ``check_sections`` because each domain
    contract has its own, mutually incompatible ``check_envelope``.
    """

    if not isinstance(record, dict):
        return [f"{where}: record must be a JSON object"]
    errors: list[str] = []
    for section in CONTRACT_SECTIONS:
        errors.extend(_section_errors(record, section, where))
    return errors
