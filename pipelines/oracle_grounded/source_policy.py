"""Independently sealed oracle source authority; no hosted policy vocabulary.

The deterministic scenario generator is project-owned: no hosted provider or
channel certifies its output, so the hosted rights route (research_only /
blocked for every authorized assignment) can never carry it to training.
Like the code-repair procedural route, this module seals the single reviewed
oracle row: the policy JSON bytes pinned by POLICY_SHA256 below, refreshed
only with a reviewed generator/policy change. Catalog rebuilds update the
reviewed JSON pins and POLICY_SHA256 in the same review. Caller-supplied JSON
cannot authorize a new source or generator. The snapshot loaded at import
remains immutable for the process lifetime.

Pin semantics (recompute on any reviewed change):
- catalog_sha256: SHA-256 over every pipelines/oracle_grounded/*.py except this
  module, the base oracle-grounded-v1.schema.json, and every family schema under
  schemas/oracle-grounded/. Members are sorted by repository-relative path.
  Each member is framed by its path and byte length before its bytes, so a byte
  redistribution across two adjacent modules cannot preserve the digest while
  the module boundary moves. This module is the trust anchor that seals the
  policy carrying the digest, so including it would make the value a
  self-referential cycle with no stable fixpoint; it is the seal, not part of
  what is sealed.
- programs_sha256: SHA-256 over pipelines/oracle_generate.py followed by
  pipelines/oracle_validate.py (the pipeline entry points), framed the same way.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

from .import_twins import bind_import_twin

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "schemas/procedural-oracle-policy-v1.json"
# Independent trust anchor: update only with the reviewed generator/policy change.
POLICY_SHA256 = "4e6e8c247e6252a52773512c10df954ced2bddae20ee2284ef364b7a5d3a0a4b"
PROCEDURAL_FIELDS = frozenset({
    "source_type", "generator_ownership", "generation_method", "source_license_evidence",
    "procedural_policy_sha256", "catalog_id", "catalog_sha256", "programs_sha256",
})


class SourcePolicyError(ValueError):
    """An oracle authority differs from the reviewed source policy."""


def framed_digest(members: Iterable[tuple[str, bytes]]) -> str:
    """SHA-256 over ``(name, bytes)`` members with unambiguous framing.

    Each member contributes its UTF-8 name, a NUL separator, its byte length in
    decimal, another NUL, then its exact bytes. Concatenating raw bytes alone
    lets a byte move across a member boundary without changing the digest, so
    the module partition the pin is supposed to authenticate would be
    forgeable (CWE-354). Length framing makes the boundary part of the hashed
    content. Callers pass members already in their reviewed order.
    """
    digest = hashlib.sha256()
    for name, payload in members:
        digest.update(name.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(str(len(payload)).encode("ascii"))
        digest.update(b"\x00")
        digest.update(payload)
    return digest.hexdigest()


def catalog_digest(package: Path) -> str:
    """Seal implementation and executable schema bytes from one source tree."""
    root = package.parent.parent
    domain = [path for path in package.glob("*.py") if path.name != Path(__file__).name]
    domain.append(root / "schemas/oracle-grounded-v1.schema.json")
    domain.extend((root / "schemas/oracle-grounded").glob("*.schema.json"))
    members = sorted(domain, key=lambda path: path.relative_to(root).as_posix())
    return framed_digest(
        (path.relative_to(root).as_posix(), path.read_bytes()) for path in members
    )


def programs_digest(pipelines: Path, names: Sequence[str]) -> str:
    """The reviewed ``programs_sha256`` for the pipeline entry points."""
    return framed_digest((name, (pipelines / name).read_bytes()) for name in names)


# The pinned entry points, in the reviewed order the digest was taken.
PROGRAM_NAMES = ("oracle_generate.py", "oracle_validate.py")


def verify_source_bytes() -> None:
    """Recompute both sealed digest domains from the installed files.

    ``validate_registry_row`` only proves the registry repeats the strings in
    the sealed policy. Without this check a dirty or mispackaged checkout can
    differ from the reviewed generation semantics while the registry still
    grants identity authority, because the recomputation otherwise lives only
    in tests. Every admission request rechecks the bytes.
    """
    try:
        catalog = catalog_digest(ROOT / POLICY["catalog_relative_path"])
        programs = programs_digest(ROOT / "pipelines", PROGRAM_NAMES)
    except OSError as exc:
        raise SourcePolicyError(f"oracle source package unreadable: {exc}") from exc
    if catalog != POLICY["catalog_sha256"]:
        raise SourcePolicyError(
            "oracle source package differs from the reviewed catalog digest"
        )
    if programs != POLICY["programs_sha256"]:
        raise SourcePolicyError(
            "oracle pipeline entry points differ from the reviewed digest"
        )


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object key: {key!r}")
        result[key] = value
    return result


def load_policy(path: Path = POLICY_PATH) -> Mapping[str, Any]:
    """Read exact trusted bytes; alternate paths have no independent authority."""
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_object_keys)
    except (OSError, ValueError) as exc:
        raise SourcePolicyError(f"oracle policy unreadable or invalid: {exc}") from exc
    if hashlib.sha256(raw).hexdigest() != POLICY_SHA256:
        raise SourcePolicyError("oracle policy differs from independently reviewed bytes")
    return _freeze(value)


POLICY = load_policy()


def reviewed_row() -> dict[str, Any]:
    """Fresh registry representation of the sealed, single approved route."""
    result = {key: POLICY[key] for key in (
        "path_id", "generator", "generator_version", "generator_ownership", "generation_method",
        "catalog_id", "catalog_sha256", "programs_sha256", "intended_use",
        "project_training_policy", "publication_target",
    )}
    result.update(
        source_type="procedural", payload_factory=POLICY["path_id"],
        source_license_evidence=dict(POLICY["source_license_evidence"]),
        procedural_policy_sha256=POLICY_SHA256, record_kinds=["oracle"],
        identity_authoritative=True, training_ready_policy="compose_eligible",
        allowed_curation_lanes=["curate_identity"],
        provenance_contract_by_kind={"oracle": "synthetic_shape_implies_designed"},
    )
    return result


def validate_registry_row(raw: Any) -> None:
    """Only the exact reviewed discriminated row grants oracle authority."""
    if not isinstance(raw, Mapping):
        raise SourcePolicyError("oracle registry row must be an object")
    if raw.get("identity_authoritative") is not True:
        raise SourcePolicyError("oracle registry row must be identity-authoritative")
    if dict(raw) != reviewed_row():
        raise SourcePolicyError("oracle registry row drifts from independently sealed policy")


def claims_oracle_route(raw: Any) -> bool:
    """Identify this authority's single row without touching hosted rows."""
    if not isinstance(raw, Mapping):
        return False
    route = (raw.get("source_type"), raw.get("path_id"), raw.get("payload_factory"))
    return route == ("procedural", "oracle-grounded", "oracle-grounded")


bind_import_twin(__name__)
