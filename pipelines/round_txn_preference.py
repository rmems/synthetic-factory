"""Preference-isolation helpers for pipelines/round_txn.py.

Split out of ``round_txn`` so that module keeps the general round
transaction and this one keeps the two-session preference path. Patchable
names are looked up on the host module through ``rt``, so tests that patch
``round_txn.<name>`` keep working across the split -- and so the CLI, which
runs ``round_txn.py`` as ``__main__``, still shares one set of globals.
"""

from __future__ import annotations
import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from round_txn_execution import rt


@dataclass(frozen=True)
class PreferenceMarkerReview:
    """One committed FFPC marker plus the artifact names it declares."""

    factory_dir: Path
    round_number: int
    path: Path
    payload: dict
    names: set[str]


@dataclass(frozen=True)
class PreferenceHandoffExpectation:
    """The identity a persisted pre-Session-B diagnosis receipt must carry."""

    factory_dir: Path
    round_number: int
    expected_records: int
    reservation_token: str
    expected_staging_dir: Path


@dataclass(frozen=True)
class CommittedPreferenceRound:
    """A committed FFPC round re-checked against its recorded arm evidence."""

    factory_dir: Path
    round_number: int
    manifest: dict
    batch: Path
    records: int
    manifest_version: int
    allow_unmigrated_preference_v1: bool


def _require_two_session_flag(preference_isolation):
    if preference_isolation != rt.PREFERENCE_TWO_SESSION:
        raise rt.TransactionError(
            f"{rt.PREFERENCE_ISOLATION_FACTORY} reservations require "
            f"--preference-isolation {rt.PREFERENCE_TWO_SESSION}"
        )


def require_preference_isolation(factory_name, preference_isolation):
    """The two-session flag is required for the preference factory, and only it."""

    if factory_name == rt.PREFERENCE_ISOLATION_FACTORY:
        _require_two_session_flag(preference_isolation)
        return
    if preference_isolation is not None:
        raise rt.TransactionError(
            f"--preference-isolation is only valid for {rt.PREFERENCE_ISOLATION_FACTORY}"
        )


def quota_is_locked(factory_name):
    """Factories whose round size is fixed by contract, not by --expected."""

    if factory_name in rt.AGENTIC_FACTORY_KINDS:
        return True
    return factory_name == rt.PREFERENCE_ISOLATION_FACTORY


def read_readonly_json(path: Path, *, label: str):
    """Read a regular transaction plan only after its write bits are sealed."""

    try:
        path_stat = path.lstat()
    except OSError as exc:
        raise rt.TransactionError(f"cannot inspect {label}: {path}: {exc}") from exc
    if stat.S_ISLNK(path_stat.st_mode) or not stat.S_ISREG(path_stat.st_mode):
        raise rt.TransactionError(f"unsafe {label}: {path}")
    if path_stat.st_mode & 0o222:
        raise rt.TransactionError(f"{label} is writable: {path}")
    return rt.read_json(path)


def _require_migrated_ledger_exists(path: Path, factory_dir: Path) -> None:
    """FFPC v1 markers stay invisible until the migration ledger is written."""

    if path.exists() or path.is_symlink():
        return
    raise rt.TransactionError(
        "historical FFPC v1 markers require `round_txn.py "
        f"migrate-preference-v1 {factory_dir}` before they become visible"
    )


def _require_sealed_ledger_file(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise rt.TransactionError(f"unsafe FFPC v1 migration ledger: {path}")
    if path.stat().st_mode & 0o222:
        raise rt.TransactionError(f"FFPC v1 migration ledger is writable: {path}")


def _require_ledger_identity(payload: dict, factory_dir: Path, path: Path) -> None:
    if type(payload.get("version")) is not int or payload["version"] != 1:
        raise rt.TransactionError(f"unsupported FFPC v1 migration ledger version: {path}")
    if payload.get("factory") != factory_dir.name:
        raise rt.TransactionError(f"FFPC v1 migration ledger identity mismatch: {path}")


def _validated_ledger_mode_digest(payload: dict, path: Path) -> str:
    mode_digest = payload.get("marker_mode_sha256")
    if not isinstance(mode_digest, str) or rt.SHA256_RE.fullmatch(mode_digest) is None:
        raise rt.TransactionError(f"FFPC v1 migration ledger has invalid marker-mode hash: {path}")
    return mode_digest


#: The marker-mode fields a migration freezes: the declaration that decides
#: how the historical markers are read. The execution-cutover keys are
#: publish-time bookkeeping that ``remember_execution_gate_cutover`` rewrites
#: on the lane's first v2 round, so a digest over the whole file invalidated
#: itself and stranded the lane it had just upgraded.
_LEDGER_MARKER_MODE_FIELDS = ("version", "commit_point", "legacy_baseline")


def _ledger_marker_mode_digest(mode_path: Path) -> str:
    """Digest the marker-mode fields the migration froze, not the whole file."""

    mode = rt.read_json(mode_path)
    frozen = {name: mode[name] for name in _LEDGER_MARKER_MODE_FIELDS if name in mode}
    payload = json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _require_ledger_marker_mode(payload: dict, factory_dir: Path, path: Path) -> None:
    """The ledger is only trustworthy while the marker mode it froze is intact."""

    mode_path = rt.marker_mode_path(factory_dir)
    if mode_path is None:
        raise rt.TransactionError(f"FFPC v1 migration ledger has no marker mode: {path}")
    mode_digest = _validated_ledger_mode_digest(payload, path)
    if _ledger_marker_mode_digest(mode_path) != mode_digest:
        raise rt.TransactionError(f"FFPC v1 migration ledger marker-mode hash mismatch: {path}")


def _ledger_round_is_new(round_number, markers: dict[int, str]) -> bool:
    if type(round_number) is not int:
        return False
    if round_number < 1:
        return False
    return round_number not in markers


def _ledger_digest_is_valid(digest) -> bool:
    if not isinstance(digest, str):
        return False
    return rt.SHA256_RE.fullmatch(digest) is not None


def _ledger_entry_is_valid(entry, markers: dict[int, str]) -> bool:
    if not isinstance(entry, dict):
        return False
    if not _ledger_round_is_new(entry.get("round"), markers):
        return False
    return _ledger_digest_is_valid(entry.get("sha256"))


def _ledger_markers(payload: dict, path: Path) -> dict[int, str]:
    entries = payload.get("markers")
    if not isinstance(entries, list):
        raise rt.TransactionError(f"FFPC v1 migration ledger markers must be an array: {path}")
    markers: dict[int, str] = {}
    for entry in entries:
        if not _ledger_entry_is_valid(entry, markers):
            raise rt.TransactionError(f"FFPC v1 migration ledger has an invalid entry: {path}")
        markers[entry["round"]] = entry["sha256"]
    return markers


def validated_preference_v1_ledger(factory_dir: Path) -> tuple[dict, dict[int, str]]:
    """Return the read-only digest ledger for explicitly migrated FFPC v1 markers."""

    path = factory_dir / rt.PREFERENCE_V1_LEDGER_FILE
    _require_migrated_ledger_exists(path, factory_dir)
    _require_sealed_ledger_file(path)
    payload = rt.read_json(path)
    _require_ledger_identity(payload, factory_dir, path)
    _require_ledger_marker_mode(payload, factory_dir, path)
    return payload, _ledger_markers(payload, path)


def _expected_diagnosis_names(round_number: int) -> set[str]:
    from preference_arms import diagnosis_filenames, diagnosis_receipt_filename

    return {
        *diagnosis_filenames(
            round_number,
            rt.FACTORY_QUOTAS[rt.PREFERENCE_ISOLATION_FACTORY],
        ),
        diagnosis_receipt_filename(round_number),
    }


def _declared_diagnosis_names(names: set[str], round_number: int) -> set[str]:
    round_suffix = f"-r{round_number:02d}."
    return {
        name for name in names if name.startswith("diagnosis-") and round_suffix in name
    }


def _require_declared_diagnosis_names(marker: PreferenceMarkerReview) -> None:
    expected_handoff_names = _expected_diagnosis_names(marker.round_number)
    declared_handoff_names = _declared_diagnosis_names(marker.names, marker.round_number)
    if declared_handoff_names == expected_handoff_names:
        return
    raise rt.TransactionError(
        f"completion marker diagnosis artifact set does not match r{marker.round_number:02d}: "
        f"{marker.path}"
    )


def _completed_preference_marker_is_sealed(marker: PreferenceMarkerReview) -> None:
    """Refuse an FFPC completion marker that is writable or under-declared."""

    if marker.factory_dir.name != rt.PREFERENCE_ISOLATION_FACTORY:
        return
    if marker.payload.get("version") != rt.EXECUTION_VERIFIED_COMPLETION_MARKER_VERSION:
        return
    if marker.path.stat().st_mode & 0o222:
        raise rt.TransactionError(f"FFPC v2 completion marker is writable: {marker.path}")
    _require_declared_diagnosis_names(marker)


def _require_preference_factory_dir(factory_dir: Path) -> None:
    if factory_dir.name != rt.PREFERENCE_ISOLATION_FACTORY:
        raise rt.TransactionError(
            f"v1 preference migration is only valid for {rt.PREFERENCE_ISOLATION_FACTORY}"
        )
    if not factory_dir.is_dir():
        raise rt.TransactionError(f"not a factory directory: {factory_dir}")


def _migration_rounds_at_version(manifests: dict[int, dict], version: int) -> list[int]:
    return sorted(
        round_number
        for round_number, manifest in manifests.items()
        if manifest.get("version") == version
    )


def _require_contiguous_v1_prefix(
    manifests: dict[int, dict], v1_rounds: list[int], mode: dict
) -> None:
    """Only one unbroken historical prefix, never interleaved with v2, may freeze."""

    expected_prefix = list(range(mode["legacy_baseline"] + 1, v1_rounds[-1] + 1))
    if v1_rounds != expected_prefix:
        raise rt.TransactionError(
            "FFPC v1 migration requires one contiguous historical marker prefix"
        )
    v2_rounds = _migration_rounds_at_version(manifests, 2)
    if v2_rounds and min(v2_rounds) < v1_rounds[-1]:
        raise rt.TransactionError("FFPC v1 markers cannot follow a v2 completion marker")


def _migratable_v1_rounds(factory_dir: Path, mode: dict) -> list[int]:
    manifests = rt.completed_manifests(
        factory_dir,
        _allow_unmigrated_preference_v1=True,
    )
    v1_rounds = _migration_rounds_at_version(manifests, 1)
    if v1_rounds:
        _require_contiguous_v1_prefix(manifests, v1_rounds, mode)
    return v1_rounds


def _preference_v1_ledger_payload(
    factory_dir: Path, mode_path: Path, v1_rounds: list[int]
) -> dict:
    return {
        "version": 1,
        "factory": factory_dir.name,
        "created_at": rt.utc_now(),
        "marker_mode_sha256": _ledger_marker_mode_digest(mode_path),
        "markers": [
            {
                "round": round_number,
                "sha256": rt.file_sha256(factory_dir / f"ROUND-r{round_number:02d}.complete.json"),
            }
            for round_number in v1_rounds
        ],
    }


def _write_preference_v1_ledger(factory_dir: Path, ledger_path: Path, payload: dict) -> dict:
    try:
        rt.write_exclusive_json(ledger_path, payload, mode=0o400)
    except FileExistsError:
        existing, _ = validated_preference_v1_ledger(factory_dir)
        return existing
    return payload


def _migrate_preference_v1_under_lock(factory_dir: Path) -> dict:
    mode_path = rt.marker_mode_path(factory_dir)
    if mode_path is None:
        raise rt.TransactionError(f"marker mode is not enabled for {factory_dir}")
    mode = rt.validated_marker_mode(factory_dir, mode_path)
    ledger_path = factory_dir / rt.PREFERENCE_V1_LEDGER_FILE
    if ledger_path.exists() or ledger_path.is_symlink():
        payload, _ = validated_preference_v1_ledger(factory_dir)
        return payload
    v1_rounds = _migratable_v1_rounds(factory_dir, mode)
    payload = _preference_v1_ledger_payload(factory_dir, mode_path, v1_rounds)
    return _write_preference_v1_ledger(factory_dir, ledger_path, payload)


def migrate_preference_v1_markers(factory_dir: Path) -> dict:
    """Freeze the already-visible FFPC v1 prefix into a one-shot digest ledger."""

    factory_dir = Path(factory_dir).resolve()
    _require_preference_factory_dir(factory_dir)
    with rt.run_publish_lock(factory_dir):
        return _migrate_preference_v1_under_lock(factory_dir)


def validate_preference_diagnosis_handoff(
    artifact_dir: Path,
    expectation: PreferenceHandoffExpectation,
) -> dict:
    """Bind FFPC publication to its persisted pre-Session-B receipt."""

    from preference_arms import (
        PreferenceArmsError,
        ReceiptExpectation,
        validate_diagnosis_handoff_receipt,
    )

    try:
        return validate_diagnosis_handoff_receipt(
            artifact_dir,
            ReceiptExpectation(
                factory=expectation.factory_dir.name,
                round_number=expectation.round_number,
                staging_dir=expectation.expected_staging_dir,
                reservation_token=expectation.reservation_token,
                expected_count=expectation.expected_records,
            ),
        )
    except (OSError, PreferenceArmsError, ValueError) as exc:
        raise rt.TransactionError(f"diagnosis handoff receipt validation failed: {exc}") from exc


def _stable_preference_gate_evidence(summary: dict) -> dict:
    """Return gate evidence whose identity survives a code-only version bump.

    Historical markers retain their exact implementation version for audit,
    while semantic fields are re-evaluated by the current implementation.
    Changing only ``GATE_VERSION`` must not hide committed data or wedge a
    publish that crossed the immutable-plan point.
    """

    evidence = dict(summary)
    gate = evidence.get("gate")
    if isinstance(gate, dict):
        gate = dict(gate)
        gate.pop("version", None)
        evidence["gate"] = gate
    return evidence


def _same_file_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _readonly_open_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _require_opened_inode(
    path: Path, expected_stat: os.stat_result, opened_stat: os.stat_result, label: str
) -> None:
    if not stat.S_ISREG(opened_stat.st_mode):
        raise rt.TransactionError(f"{label} changed while it was opened: {path}")
    if not _same_file_identity(expected_stat, opened_stat):
        raise rt.TransactionError(f"{label} changed while it was opened: {path}")


def _require_opened_readonly(require_readonly: bool, mode: int, label: str, path: Path) -> None:
    if require_readonly and mode & 0o222:
        raise rt.TransactionError(f"{label} is writable: {path}")


def _require_json_object(value, label: str, path: Path) -> dict:
    if not isinstance(value, dict):
        raise rt.TransactionError(f"{label} must contain an object: {path}")
    return value


def _read_json_from_expected_inode(
    path: Path,
    *,
    label: str,
    expected_stat: os.stat_result,
    require_readonly: bool,
) -> dict:
    """Read JSON through a descriptor bound to one already-verified inode."""

    fd = -1
    try:
        fd = os.open(path, _readonly_open_flags())
        opened_stat = os.fstat(fd)
        _require_opened_inode(path, expected_stat, opened_stat, label)
        _require_opened_readonly(require_readonly, opened_stat.st_mode, label, path)
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            fd = -1
            value = json.load(handle)
    except rt.TransactionError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise rt.TransactionError(f"cannot read {label} {path}: {exc}") from exc
    finally:
        if fd >= 0:
            os.close(fd)
    return _require_json_object(value, label, path)


def _path_still_identifies(current_stat: os.stat_result, expected_stat: os.stat_result) -> bool:
    if stat.S_ISLNK(current_stat.st_mode):
        return False
    if not stat.S_ISREG(current_stat.st_mode):
        return False
    return _same_file_identity(expected_stat, current_stat)


def _require_expected_path_identity(
    path: Path,
    expected_stat: os.stat_result,
    *,
    label: str,
) -> None:
    try:
        current_stat = path.lstat()
    except OSError as exc:
        raise rt.TransactionError(f"cannot inspect {label}: {path}") from exc
    if not _path_still_identifies(current_stat, expected_stat):
        raise rt.TransactionError(f"{label} changed during commit: {path}")


def _linkable_publishing_plan(publishing: Path, require_readonly: bool) -> os.stat_result:
    """Stat the plan that commit will link, refusing anything but a sealed file."""

    try:
        expected_stat = publishing.lstat()
    except OSError as exc:
        raise rt.TransactionError(
            f"cannot inspect publishing plan before commit: {publishing}"
        ) from exc
    if stat.S_ISLNK(expected_stat.st_mode) or not stat.S_ISREG(expected_stat.st_mode):
        raise rt.TransactionError(f"unsafe publishing plan before commit: {publishing}")
    _require_opened_readonly(
        require_readonly, expected_stat.st_mode, "publishing plan", publishing
    )
    return expected_stat


def _linked_marker_is_the_plan(
    expected_stat: os.stat_result,
    publishing_stat: os.stat_result,
    complete_stat: os.stat_result,
) -> bool:
    if not _same_file_identity(expected_stat, publishing_stat):
        return False
    if not _same_file_identity(expected_stat, complete_stat):
        return False
    if stat.S_ISLNK(complete_stat.st_mode):
        return False
    return stat.S_ISREG(complete_stat.st_mode)


def _require_linked_marker_identity(
    publishing: Path, complete: Path, expected_stat: os.stat_result
) -> None:
    publishing_stat = publishing.lstat()
    complete_stat = complete.lstat()
    if _linked_marker_is_the_plan(expected_stat, publishing_stat, complete_stat):
        return
    raise rt.TransactionError(
        f"publishing plan changed while linking the completion marker: {publishing}"
    )


def _require_committed_marker_bytes(
    complete: Path, manifest: dict, expected_stat: os.stat_result, require_readonly: bool
) -> None:
    # Through the host module: a test patches
    # ``round_txn._read_json_from_expected_inode`` to replace the marker
    # between the read and the commit.
    committed = rt._read_json_from_expected_inode(
        complete,
        label="completion marker",
        expected_stat=expected_stat,
        require_readonly=require_readonly,
    )
    if committed != manifest:
        raise rt.TransactionError(
            f"completion marker bytes differ from the validated publishing plan: {complete}"
        )


def _require_both_names_identify_plan(
    publishing: Path, complete: Path, expected_stat: os.stat_result
) -> None:
    # Re-check both pathnames after the descriptor read. The completion
    # marker is the visibility point, so recovery state is retained unless
    # both names still identify the exact plan inode at helper return.
    _require_expected_path_identity(
        publishing,
        expected_stat,
        label="publishing plan",
    )
    _require_expected_path_identity(
        complete,
        expected_stat,
        label="completion marker",
    )


def link_verified_completion_marker(
    publishing: Path,
    complete: Path,
    manifest: dict,
    *,
    require_readonly: bool,
) -> None:
    """Link exactly the plan inode and bytes that publication validated."""

    expected_stat = _linkable_publishing_plan(publishing, require_readonly)
    linked = False
    try:
        os.link(publishing, complete, follow_symlinks=False)
        linked = True
        _require_linked_marker_identity(publishing, complete, expected_stat)
        _require_committed_marker_bytes(complete, manifest, expected_stat, require_readonly)
        _require_both_names_identify_plan(publishing, complete, expected_stat)
        # These are final accidental-concurrency checks, not an owner-level
        # immutable-file claim. A same-UID process can always mutate the parent
        # directory after the final check; the documented protocol treats that
        # as hostile operator action outside its orchestration attestation.
    except FileExistsError as exc:
        raise rt.TransactionError(f"completion marker already exists: {complete}") from exc
    except (OSError, rt.TransactionError):
        if linked:
            try:
                complete.unlink()
            except FileNotFoundError:
                pass
        raise


def _is_unmigrated_v1_round(committed: CommittedPreferenceRound) -> bool:
    if committed.manifest_version != 1:
        return False
    return not committed.allow_unmigrated_preference_v1


def _require_frozen_v1_marker(committed: CommittedPreferenceRound) -> None:
    _, migrated_markers = validated_preference_v1_ledger(committed.factory_dir)
    marker = committed.factory_dir / f"ROUND-r{committed.round_number:02d}.complete.json"
    if migrated_markers.get(committed.round_number) != rt.file_sha256(marker):
        raise rt.TransactionError(
            f"FFPC v1 completion marker is not in the frozen migration ledger: {marker}"
        )


def _require_preference_quota(committed: CommittedPreferenceRound) -> None:
    quota = rt.FACTORY_QUOTAS[rt.PREFERENCE_ISOLATION_FACTORY]
    if committed.records != quota:
        raise rt.TransactionError(
            f"committed batch has {committed.records} records; "
            f"{rt.PREFERENCE_ISOLATION_FACTORY} "
            f"requires exactly {quota}: {committed.batch}"
        )


def _validated_trusted_isolation(committed: CommittedPreferenceRound) -> str:
    trusted_isolation = committed.manifest.get("preference_isolation")
    if trusted_isolation != rt.PREFERENCE_TWO_SESSION:
        raise rt.TransactionError(
            f"completion marker lacks trusted two-session isolation: {committed.batch}"
        )
    return trusted_isolation


def _require_recorded_arm_gate(committed: CommittedPreferenceRound, trusted_isolation: str) -> None:
    recorded_gate = committed.manifest.get("preference_arm_gate")
    if not isinstance(recorded_gate, dict):
        raise rt.TransactionError(
            f"completion marker lacks the preference arm gate result: {committed.batch}"
        )
    current_gate = rt.validate_preference_arm_gate(
        committed.batch, committed.records, trusted_isolation
    )
    if _stable_preference_gate_evidence(recorded_gate) != _stable_preference_gate_evidence(
        current_gate
    ):
        raise rt.TransactionError(
            f"completion marker preference arm gate does not match batch: {committed.batch}"
        )


def _validated_reservation_token(committed: CommittedPreferenceRound) -> str:
    token = committed.manifest.get("token")
    if not isinstance(token, str) or rt.TOKEN_RE.fullmatch(token) is None:
        raise rt.TransactionError(
            f"completion marker has an invalid reservation token: {committed.batch}"
        )
    return token


def _require_recorded_diagnosis_handoff(committed: CommittedPreferenceRound) -> None:
    token = _validated_reservation_token(committed)
    current_handoff = validate_preference_diagnosis_handoff(
        committed.factory_dir,
        PreferenceHandoffExpectation(
            factory_dir=committed.factory_dir,
            round_number=committed.round_number,
            expected_records=committed.records,
            reservation_token=token,
            expected_staging_dir=rt.staging_dir(
                committed.factory_dir, committed.round_number, token
            ),
        ),
    )
    if committed.manifest.get("preference_diagnosis_handoff") != current_handoff:
        raise rt.TransactionError(
            "completion marker diagnosis handoff does not match committed evidence: "
            f"{committed.batch}"
        )


def _completed_preference_isolation_matches(committed: CommittedPreferenceRound) -> None:
    """Re-check the committed FFPC round against its recorded arm evidence."""

    if committed.factory_dir.name != rt.PREFERENCE_ISOLATION_FACTORY:
        return
    if _is_unmigrated_v1_round(committed):
        _require_frozen_v1_marker(committed)
    if committed.manifest_version != rt.EXECUTION_VERIFIED_COMPLETION_MARKER_VERSION:
        return
    _require_preference_quota(committed)
    _require_recorded_arm_gate(committed, _validated_trusted_isolation(committed))
    _require_recorded_diagnosis_handoff(committed)


def reservation_matches_completed_round(reservation, factory_name, round_number, token):
    """The reservation on disk is the one that produced this completed round."""

    if not _supported_reservation_version(reservation):
        return False
    if reservation.get("factory") != factory_name:
        return False
    if reservation.get("round") != round_number:
        return False
    return reservation.get("token") == token


def _supported_reservation_version(reservation: dict) -> bool:
    """Accept only the integer v1 marker; JSON booleans/floats are not v1."""

    version = reservation.get("version")
    return type(version) is int and version == 1
