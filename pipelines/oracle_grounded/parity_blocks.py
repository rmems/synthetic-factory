"""Per-block rules of the parity record envelope.

Split out of ``parity_contract`` by responsibility; every name is re-exported
from there. Each check here reads one section of the envelope -- reason codes,
the generator block, the candidate prediction, the result, the provenance and
the validation stamp -- and returns findings in a fixed order, so the family
validators and the envelope check can concatenate them without re-sorting.
"""

from __future__ import annotations

from .envelope import PROVENANCE_KINDS, is_enum_value, strict_json_equal
from .parity_terms import (
    ORACLE_ONLY_KEYS,
    REASON_CODES,
    VERDICTS,
    _is_object,
    _nonempty_str,
)


def _reason_code_error(code, where, field):
    """The finding for one reason-code entry, or ``None`` when it is known."""
    if not isinstance(code, str):
        return f"{where}: {field} entries must be strings, got {code!r}"
    if code not in REASON_CODES:
        return f"{where}: {field} has unknown reason code {code!r}"
    return None


def check_reason_codes(codes, where, field):
    """Every reason code must come from the shared vocabulary."""
    if not isinstance(codes, list):
        return [f"{where}: {field} must be an array"]
    findings = (_reason_code_error(code, where, field) for code in codes)
    return [finding for finding in findings if finding is not None]


def _required_string_errors(block, keys, where, section):
    """One finding per required key of ``block`` that is not a non-empty string."""
    return [
        f"{where}.{section}.{key} must be a non-empty string"
        for key in keys
        if not _nonempty_str(block.get(key))
    ]


def _check_generator_produced(produced, where):
    """The generator may list what it authored, but never oracle output."""
    if not isinstance(produced, list) or not produced:
        return [f"{where}.generator.produced must list what the generator authored"]
    if any(item in ("result", "oracle", "measurement") for item in produced):
        return [
            f"{where}.generator.produced claims authorship of oracle output "
            f"[GENERATOR_SUBSTITUTED_FOR_ORACLE]"
        ]
    return []


def check_generator(generator, where):
    """The generator block, and the rule that it cannot certify itself."""
    if not _is_object(generator):
        return [f"{where}.generator must be an object"]
    errors = _required_string_errors(generator, ("name", "model", "role"), where, "generator")
    if generator.get("may_certify_oracle_result") is not False:
        errors.append(
            f"{where}.generator.may_certify_oracle_result must be exactly false "
            "[GENERATOR_SELF_CERTIFIED]"
        )
    errors += _check_generator_produced(generator.get("produced"), where)
    return errors


def _oracle_only_intruders(value):
    """Return oracle-only field names found at any depth of ``value``."""
    found = set()
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            found.update(ORACLE_ONLY_KEYS.intersection(current))
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    return found


def check_candidate_prediction(prediction, where):
    """A prediction is a guess. It may not wear an oracle's clothes."""
    if prediction is None:
        return []
    if not _is_object(prediction):
        return [f"{where}.candidate_prediction must be an object or null"]
    errors = []
    if prediction.get("source") != "generator":
        errors.append(f"{where}.candidate_prediction.source must be 'generator'")
    if prediction.get("authoritative") is not False:
        errors.append(
            f"{where}.candidate_prediction.authoritative must be exactly false "
            f"[GENERATOR_SUBSTITUTED_FOR_ORACLE]"
        )
    intruders = sorted(_oracle_only_intruders(prediction))
    if intruders:
        errors.append(
            f"{where}.candidate_prediction carries oracle-only fields {intruders} "
            f"[GENERATOR_SUBSTITUTED_FOR_ORACLE]"
        )
    return errors


def _absent_from(items, pool):
    """The entries of ``items`` that ``pool`` does not carry, in ``items`` order."""
    return [item for item in items if item not in pool]


def _derived_membership_errors(derived, where, oracle_digests):
    """Which digests are referenced without evidence, and which are omitted."""
    errors = []
    unknown = _absent_from(derived, oracle_digests)
    if unknown:
        errors.append(
            f"{where}.result.derived_from references digests absent from oracle "
            f"output: {unknown} [RESULT_DIGEST_UNLINKED]"
        )
    missing = _absent_from(oracle_digests, derived)
    if missing:
        errors.append(
            f"{where}.result.derived_from omits executed oracle digests {missing} "
            f"[RESULT_DIGEST_UNLINKED]"
        )
    return errors


def _check_derived_digests(derived, where, oracle_digests):
    """result.derived_from must reproduce the ordered oracle evidence exactly."""
    if not isinstance(derived, list) or not derived:
        return [
            f"{where}.result.derived_from must list oracle output digests "
            "[RESULT_DIGEST_UNLINKED]"
        ]
    if oracle_digests is None:
        return []
    errors = _derived_membership_errors(derived, where, oracle_digests)
    if not strict_json_equal(derived, oracle_digests):
        errors.append(
            f"{where}.result.derived_from must exactly match the ordered oracle "
            f"evidence, including duplicate occurrences; expected "
            f"{oracle_digests!r}, got {derived!r} [RESULT_DIGEST_UNLINKED]"
        )
    return errors


def check_result(result, where, oracle_digests):
    """A result must be oracle-backed and traceable to oracle output."""
    errors = []
    if not _is_object(result):
        return [f"{where}.result must be an object"]
    if result.get("oracle_backed") is not True:
        errors.append(
            f"{where}.result.oracle_backed must be exactly true [RESULT_NOT_ORACLE_BACKED]"
        )
    verdict = result.get("verdict")
    if verdict not in VERDICTS:
        errors.append(
            f"{where}.result.verdict must be one of {list(VERDICTS)} [VERDICT_UNKNOWN]"
        )
    errors += check_reason_codes(result.get("reason_codes", []), where, "result.reason_codes")
    errors += _check_derived_digests(result.get("derived_from"), where, oracle_digests)
    return errors


def _check_claimed_not_real(claimed, where):
    """A synthetic record may never claim a real-world origin."""
    if not isinstance(claimed, str):
        return []
    lowered = claimed.strip().lower()
    if lowered == "real" or lowered.startswith(("real_", "real-", "real ")):
        return [
            f"{where}.provenance.claimed asserts a real-world origin "
            f"[PROVENANCE_CLAIMS_REAL]"
        ]
    return []


def check_provenance(provenance, where):
    """Repository-wide provenance vocabulary; never a `real` claim."""
    if not _is_object(provenance):
        return [f"{where}.provenance must be an object"]
    errors = []
    kind = provenance.get("kind")
    if not is_enum_value(kind, PROVENANCE_KINDS):
        errors.append(
            f"{where}.provenance.kind must be one of {sorted(PROVENANCE_KINDS)} "
            f"[PROVENANCE_KIND_INVALID]"
        )
    errors += _check_claimed_not_real(provenance.get("claimed"), where)
    errors += _required_string_errors(provenance, ("tool", "tool_version"), where, "provenance")
    return errors


def check_validation_block(validation, where):
    """The validator's stamp: who validated, at which version, with which checks."""
    if not _is_object(validation):
        return [f"{where}.validation must be an object"]
    errors = _required_string_errors(
        validation, ("validator", "validator_version"), where, "validation"
    )
    checks = validation.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append(f"{where}.validation.checks must list the checks that were applied")
    return errors
