"""Cross-checks for the ``rights.json`` sidecar a public Hub release declares.

``release-status.json`` declares the sidecar through ``rights_record``.  A null
or absent ``rights_record`` keeps the release contract unchanged and nothing is
fetched.  ``"rights.json"`` makes the sidecar part of the contract: it must be
fetched, ``rights_document`` must accept it, it must name the repository, and
its ``intended_use`` / ``project_training_policy`` must equal any that
``release-status.json`` restates.  A procedural (schema 0.2.0) sidecar must also
declare the same release license as the shipped ``LICENSE``, the card front
matter and ``release-status.json``, and the same ``training_ready``.  Any other
``rights_record`` value fails closed.  Values in the messages are rendered as
JSON, the form the release files declare them in.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("verify_hf_release_rights")
    from . import rights_document as _rights_document
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "verify_hf_release_rights"
    )
    import rights_document as _rights_document


RIGHTS_SIDECAR_PATH = "rights.json"
DECISION_FIELDS = ("intended_use", "project_training_policy")
# release-status.json keys whose duplicates would hide a rights declaration.
RIGHTS_STATUS_FIELDS = ("rights_record", *DECISION_FIELDS)


class LicenseDeclarations(NamedTuple):
    """The release license the rest of the release declares, outside release-status.json."""

    # The license family the shipped LICENSE text was recognized as, if any.
    license_file: str | None
    # The card front matter's raw ``license`` value, if any.
    card: str | None


def declared_sidecar_bytes(
    status: Mapping[str, object], fetch: Callable[[str], bytes]
) -> bytes | None:
    """Fetch the sidecar through ``fetch(path)`` only when ``release-status.json`` declares it."""

    if status.get("rights_record") != RIGHTS_SIDECAR_PATH:
        return None
    return fetch(RIGHTS_SIDECAR_PATH)


def _normalized_license(value: object) -> str | None:
    return value.strip().casefold() if isinstance(value, str) else None


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _decision_errors(
    document: _rights_document.RightsDocument | _rights_document.ProceduralRightsDocument,
    status: Mapping[str, object],
) -> list[str]:
    errors: list[str] = []
    for field in DECISION_FIELDS:
        declared = getattr(document, field)
        if field in status and status[field] != declared:
            errors.append(
                f"{RIGHTS_SIDECAR_PATH} declares {field} {_json_text(declared)}, "
                f"but release-status.json declares {_json_text(status[field])}"
            )
    return errors


def _procedural_release_errors(
    document: _rights_document.ProceduralRightsDocument,
    status: Mapping[str, object],
    licenses: LicenseDeclarations,
) -> list[str]:
    declared = document.release_license
    shown = _json_text(declared)
    declarations = (
        ("LICENSE", licenses.license_file),
        ("the card front matter", _normalized_license(licenses.card)),
        ("release-status.json", _normalized_license(status.get("license"))),
    )
    errors = [
        f"{RIGHTS_SIDECAR_PATH} declares release_license {shown}, "
        f"but {source} declares {_json_text(other)}"
        for source, other in declarations
        if other != declared
    ]
    if status.get("training_ready") is not document.training_ready:
        errors.append(
            f"{RIGHTS_SIDECAR_PATH} declares training_ready "
            f"{_json_text(document.training_ready)}, but release-status.json does not"
        )
    return errors


def rights_sidecar_errors(
    repo: str,
    status: Mapping[str, object],
    rights_bytes: bytes | None,
    licenses: LicenseDeclarations,
) -> list[str]:
    """Verify the sidecar ``status`` declares; a release that declares none passes unchanged.

    ``rights_bytes`` is the fetched sidecar, or ``None`` when it was not fetched.
    """

    record = status.get("rights_record")
    if record is None:
        return []
    if record != RIGHTS_SIDECAR_PATH:
        return [
            f"release-status.json rights_record must be null or {_json_text(RIGHTS_SIDECAR_PATH)}"
        ]
    if rights_bytes is None:
        return [f"release-status.json declares {RIGHTS_SIDECAR_PATH}, but it was not fetched"]
    try:
        document = _rights_document.load_rights_document_bytes(
            rights_bytes, where=RIGHTS_SIDECAR_PATH
        )
    except _rights_document.RightsPolicyError as error:
        return [f"shipped rights sidecar is invalid: {error}"]
    errors: list[str] = []
    if document.dataset_id != repo:
        errors.append(f"{RIGHTS_SIDECAR_PATH} dataset_id must be {repo}")
    errors.extend(_decision_errors(document, status))
    if isinstance(document, _rights_document.ProceduralRightsDocument):
        errors.extend(_procedural_release_errors(document, status, licenses))
    return errors


if __package__:
    _expose_package_sibling(__name__)
