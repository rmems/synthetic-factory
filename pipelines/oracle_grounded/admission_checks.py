"""Source-route and generator checks for oracle admission."""

from typing import Any, Mapping

from . import generators, source_policy


def row_findings(row: Any) -> list[tuple[str, str]]:
    """Whether the resolved row is the one sealed oracle authority."""
    expected = source_policy.reviewed_row()
    expected["record_kinds"] = frozenset(expected["record_kinds"])
    expected["allowed_curation_lanes"] = tuple(expected["allowed_curation_lanes"])
    actual = {key: getattr(row, key, object()) for key in expected}
    authorized = getattr(row, "identity_authoritative", None) is True
    if not authorized or actual != expected:
        return [("ORACLE_ROUTE_UNAUTHORIZED", "row differs from sealed source authority")]
    try:
        source_policy.verify_source_bytes()
    except source_policy.SourcePolicyError as exc:
        return [("ORACLE_ROUTE_UNAUTHORIZED", str(exc))]
    return []


def factory_findings(record: Mapping[str, Any], row: Any) -> list[tuple[str, str]]:
    """Refuse a payload that contradicts its path-selected factory."""
    if row is None:
        return []
    meta = record.get("meta")
    if isinstance(meta, Mapping) and meta.get("factory") not in (None, row.payload_factory):
        return [
            (
                "ORACLE_FAMILY_MISMATCH",
                "payload meta.factory contradicts the source route",
            )
        ]
    return []


def generator_findings(record: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Authenticate the reviewed, explicitly non-authoritative generator."""
    generator = record.get("generator")
    if not isinstance(generator, Mapping):
        return [("ORACLE_GENERATOR_MISMATCH", "generator must be an object")]
    expected = {
        "authoritative": False,
        "name": generators.GENERATOR_NAME,
        "version": generators.GENERATOR_VERSION,
    }
    messages = {
        "authoritative": "generator must not be authoritative",
        "name": "generator is not the reviewed implementation",
        "version": "generator version is not the reviewed version",
    }
    for key, value in expected.items():
        if generator.get(key) != value:
            return [("ORACLE_GENERATOR_MISMATCH", messages[key])]
    return []
