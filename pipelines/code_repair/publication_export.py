"""Bind admitted exports and pure audits to actual transactional completion bytes.

The completion receipt is evidence of a local transaction, not a signature or
permission to execute untrusted code. Every export freshly replays the captured
inputs against the independent reviewed catalog. Reads only validate bindings.
"""
from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from . import admission, publication, source_policy as sp, vocabulary as cv
from ._contract import bind_import_twin, load_strict_json, oc


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def trusted_export_catalog(supplied):
    """Reject substituted caller pins and return the independently loaded source authority."""
    trusted = admission.load_trusted_catalog()
    identity_fields = ("catalog_id", "programs_sha256", "license_sha256")
    same_identity = all(getattr(supplied, key) == getattr(trusted, key) for key in identity_fields)
    same_metadata = oc.canonical_json(supplied.meta) == oc.canonical_json(trusted.meta)
    cv.refuse_when(not same_identity or not same_metadata, cv.FINDING_EXPORT_INTEGRITY,
                   "admitted export catalog differs from sealed source authority")
    try:
        digest = _sha((supplied.directory / "CATALOG.json").read_bytes())
    except OSError as exc:
        raise cv.RepairRefusal(cv.FINDING_EXPORT_INTEGRITY, "catalog became unreadable") from exc
    cv.refuse_when(digest != sp.POLICY["catalog_sha256"], cv.FINDING_EXPORT_INTEGRITY,
                   "admitted catalog bytes differ from the reviewed pin")
    return trusted


def attribution_files() -> dict[str, bytes]:
    """Carry the pinned MIT notice with the locally admitted derivative corpus."""
    evidence = sp.POLICY["source_license_evidence"]
    license_bytes = (sp.ROOT / sp.POLICY["catalog_relative_path"] / "LICENSE.upstream").read_bytes()
    if _sha(license_bytes) != evidence["license_sha256"]:
        raise cv.RepairRefusal(cv.FINDING_EXPORT_INTEGRITY, "upstream license bytes changed")
    notice = (f"Derived from {evidence['repository']} at commit {evidence['commit']}.\n"
              "The upstream MIT copyright and permission notice is in LICENSE.upstream.\n"
              "Mutations, execution evidence and repair projections were generated locally "
              "by the project-owned deterministic python-repair-mutator.\n")
    return {"LICENSE.upstream": license_bytes, "NOTICE.txt": notice.encode("utf-8")}


def _completed_marker(marker: Path) -> dict:
    transaction = publication._transaction()
    match = transaction.COMPLETE_RE.fullmatch(marker.name)
    if marker.parent.name != sp.POLICY["path_id"] or match is None:
        publication._fail("an actual procedural ROUND-rNN.complete.json is required")
    if marker.parent.resolve().name != sp.POLICY["path_id"]:
        publication._fail("completion resolves to an unregistered factory path")
    if transaction.marker_mode_path(marker.parent) is None:
        publication._fail("completion must belong to a transactional marker store")
    manifests = transaction.completed_manifests(marker.parent)
    manifest = manifests.get(int(match.group(1)))
    if manifest is None:
        publication._fail("requested completed round does not exist")
    transaction.staging_dir(marker.parent.resolve(), manifest["round"], manifest.get("token"))
    return manifest


def completed_batch_matches(batch: Path, payload: bytes) -> bool:
    """Pure audit gate: exact snapshot bytes must be owned by a valid completed round."""
    transaction = publication._transaction()
    match = transaction.BATCH_RE.fullmatch(batch.name)
    if match is None:
        return False
    marker = transaction.marker_paths(batch.parent, int(match.group(1)))["complete"]
    try:
        manifest = _completed_marker(marker)
        summary = publication.validate_completed(batch, manifest)
        return summary["procedural"]["batch_sha256"] == _sha(payload)
    except (OSError, ValueError, transaction.TransactionError):
        return False


def _capture_completion(marker: Path, destination: Path) -> tuple[dict, bytes, bytes]:
    """Capture and revalidate all manifest members before fresh execution."""
    transaction = publication._transaction()
    original = _completed_marker(marker)
    destination.mkdir()
    transaction.capture_regular_file(marker, destination / marker.name)
    marker_bytes = (destination / marker.name).read_bytes()
    manifest = load_strict_json(marker_bytes)
    if oc.canonical_json(manifest) != oc.canonical_json(original):
        publication._fail("completion marker changed during capture")
    for entry in manifest["files"]:
        name = entry["name"]
        size, digest = transaction.capture_regular_file(marker.parent / name, destination / name)
        if digest != entry["sha256"] or size != entry["bytes"]:
            publication._fail("completion artifact changed during capture")
    # A captured marker needs the same reviewed transaction cutover as its store.
    mode = marker.parent / transaction.MODE_FILE
    transaction.capture_regular_file(mode, destination / mode.name)
    mode_bytes = (destination / mode.name).read_bytes()
    transaction.completed_manifests(destination)
    if transaction.file_sha256(marker) != _sha(marker_bytes):
        publication._fail("completion marker changed during validation")
    return manifest, marker_bytes, mode_bytes


def _fresh_completion(factory, manifest):
    batch = factory / f"batch-r{manifest['round']:02d}.jsonl"
    fresh = publication.fresh_gate(factory, batch, manifest["round"])
    if oc.canonical_json(fresh) != oc.canonical_json(manifest["execution_verification"]):
        publication._fail("fresh replay differs from completed evidence")
    return fresh


def _unchanged_completion(marker, manifest, marker_bytes, mode_bytes):
    transaction = publication._transaction()
    for entry in manifest["files"]:
        transaction.completion_manifest_file_matches(marker.parent / entry["name"], manifest)
    if transaction.file_sha256(marker) != _sha(marker_bytes):
        publication._fail("completion changed during fresh replay")
    if transaction.file_sha256(marker.parent / transaction.MODE_FILE) != _sha(mode_bytes):
        publication._fail("marker mode changed during fresh replay")


def authorize_export(request, *, run_bytes: bytes, candidates: bytes, selected_ids: list[str]) -> dict:
    """Authorize only the exact run and selection, freshly replaying captured completed inputs."""
    transaction = publication._transaction()
    try:
        if request.round_marker is None:
            publication._fail("admitted export requires --round-marker")
        marker = Path(request.round_marker).absolute()
        with tempfile.TemporaryDirectory(prefix="code-repair-admitted-") as directory:
            factory = Path(directory) / sp.POLICY["path_id"]
            manifest, marker_bytes, mode_bytes = _capture_completion(marker, factory)
            summary = manifest["execution_verification"]
            binding = summary["procedural"]
            expected = (_sha(run_bytes), _sha(candidates), request.lineage_cap, sorted(selected_ids))
            actual = (binding["run_sha256"], binding["candidates_sha256"], binding["lineage_cap"],
                      [r["id"] for r in binding["selected"]])
            if expected != actual:
                publication._fail("export run and selected membership must exactly match completion")
            fresh = _fresh_completion(factory, manifest)
            # Even after capture, report an identity only while its original store is unchanged.
            _unchanged_completion(marker, manifest, marker_bytes, mode_bytes)
            return {
                "path": str(marker), "sha256": _sha(marker_bytes),
                "factory": manifest["factory"], "round": manifest["round"],
                "verification": fresh,
                "passed_gates": ["reviewed_registry", "procedural_source_policy",
                                 "trusted_catalog", "complete_run_validation",
                                 "actual_round_completion", "exact_selected_membership",
                                 "fresh_replay"],
            }
    except (OSError, ValueError, transaction.TransactionError) as exc:
        raise cv.RepairRefusal(cv.FINDING_EXPORT_INTEGRITY, str(exc)) from exc


bind_import_twin(__name__)
