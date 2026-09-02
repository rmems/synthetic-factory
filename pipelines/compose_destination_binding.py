#!/usr/bin/env python3
"""Pinned directory identities shared by compose source and destination I/O.

Directory observation, no-replace renames, and exact-tree capture live in the
``compose_destination_directory``, ``compose_destination_rename``, and
``compose_destination_tree`` siblings; this module keeps the raw-relocation
guards and the ``PinnedDestination`` lifecycle, and re-exports every sibling
name so existing importers keep one binding surface.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_destination_binding")
    from . import compose_destination_directory as _directory_module
    from . import compose_destination_rename as _rename_module
    from . import compose_destination_tree as _tree_module
    from .compose_contract import ComposeError
    from .raw_tree_guard import contains_raw_segments, is_under_raw
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_destination_binding"
    )
    import compose_destination_directory as _directory_module
    import compose_destination_rename as _rename_module
    import compose_destination_tree as _tree_module
    from compose_contract import ComposeError
    from raw_tree_guard import contains_raw_segments, is_under_raw

DirectoryBinding = _directory_module.DirectoryBinding
_directory_identity = _directory_module._directory_identity
_directory_observations = _directory_module._directory_observations
_fresh_directory_names = _directory_module._fresh_directory_names
_require_empty_directory = _directory_module._require_empty_directory
_require_exact_directory = _directory_module._require_exact_directory
_require_safe_new_directory = _directory_module._require_safe_new_directory
_required_directory_observations = _directory_module._required_directory_observations
_verify_directory_binding = _directory_module._verify_directory_binding
directory_binding_matches = _directory_module.directory_binding_matches
_ATOMIC_RENAME_UNSUPPORTED = _rename_module._ATOMIC_RENAME_UNSUPPORTED
_OwnedEntryMove = _rename_module._OwnedEntryMove
_PRIVATE_NAME_ATTEMPTS = _rename_module._PRIVATE_NAME_ATTEMPTS
_RENAME_NOREPLACE = _rename_module._RENAME_NOREPLACE
_entry_identity = _rename_module._entry_identity
_move_owned_entry = _rename_module._move_owned_entry
_private_entry_name = _rename_module._private_entry_name
_quarantine_owned_entry = _rename_module._quarantine_owned_entry
_rename_noreplace = _rename_module._rename_noreplace
_stage_owned_entry = _rename_module._stage_owned_entry
_DestinationTreeSnapshot = _tree_module._DestinationTreeSnapshot
_TreeEntry = _tree_module._TreeEntry
_TreePath = _tree_module._TreePath

__all__ = (
    "DESTINATION_PARENT_LABEL",
    "DESTINATION_PIN_CLOSED",
    "DirectoryBinding",
    "PinnedDestination",
    "_ATOMIC_RENAME_UNSUPPORTED",
    "_DestinationTreeSnapshot",
    "_OwnedEntryMove",
    "_PRIVATE_NAME_ATTEMPTS",
    "_RENAME_NOREPLACE",
    "_TreeEntry",
    "_TreePath",
    "_assert_descriptor_contained",
    "_assert_descriptor_outside_raw",
    "_contains_raw_segments",
    "_descriptor_aliases_raw",
    "_descriptor_path",
    "_destination_descriptor",
    "_directory_identity",
    "_directory_observations",
    "_entry_identity",
    "_fresh_directory_names",
    "_is_under_raw",
    "_move_owned_entry",
    "_path_aliases_raw",
    "_private_entry_name",
    "_quarantine_owned_entry",
    "_rename_noreplace",
    "_require_empty_directory",
    "_require_exact_directory",
    "_require_safe_new_directory",
    "_required_directory_observations",
    "_stage_owned_entry",
    "_tree_snapshot",
    "_verify_destination_target",
    "_verify_directory_binding",
    "directory_binding_matches",
)

DESTINATION_PARENT_LABEL = "destination parent"
DESTINATION_PIN_CLOSED = "destination pin was already closed"

# Compatibility callers import this symbol through ``compose_destination``.
_contains_raw_segments = contains_raw_segments


def _is_under_raw(path: Path) -> bool:
    """Reject lexical raw aliases as well as symlink-resolved raw paths."""

    if _contains_raw_segments(path.parts):
        return True
    try:
        return _path_aliases_raw(path)
    except (OSError, RuntimeError) as exc:
        raise ComposeError(f"cannot resolve destination path safely: {path}") from exc


def _path_aliases_raw(path: Path) -> bool:
    return is_under_raw(path)


def _descriptor_path(descriptor: int, label: str) -> Path:
    try:
        current_path = os.readlink(f"/proc/self/fd/{descriptor}")
    except OSError as exc:
        raise ComposeError(
            f"{label}: cannot verify descriptor outside immutable raw evidence"
        ) from exc
    return Path(current_path)


def _descriptor_aliases_raw(descriptor_path: Path, label: str) -> bool:
    try:
        descriptor_path.resolve(strict=True)
        descriptor_path.stat()
        return _path_aliases_raw(descriptor_path)
    except (OSError, RuntimeError) as exc:
        raise ComposeError(
            f"{label}: cannot verify descriptor outside immutable raw evidence"
        ) from exc


def _assert_descriptor_outside_raw(descriptor: int, label: str) -> None:
    """Require the kernel's current descriptor path to remain outside raw."""

    descriptor_path = _descriptor_path(descriptor, label)
    if _contains_raw_segments(tuple(descriptor_path.parts)):
        raise ComposeError(f"{label}: destination was relocated into immutable raw evidence")
    if _descriptor_aliases_raw(descriptor_path, label):
        raise ComposeError(f"{label}: destination was relocated into immutable raw evidence")


def _assert_descriptor_contained(root_descriptor: int, descriptor: int, label: str) -> None:
    """Require a pinned component to remain below its destination root."""

    try:
        root_path = Path(os.readlink(f"/proc/self/fd/{root_descriptor}"))
        current_path = Path(os.readlink(f"/proc/self/fd/{descriptor}"))
    except OSError:
        return
    if current_path == root_path:
        return
    if root_path in current_path.parents:
        return
    raise ComposeError(f"{label}: component escaped its pinned destination root")


def _tree_snapshot(descriptor: int) -> tuple[frozenset[str], dict[str, str]]:
    return _DestinationTreeSnapshot(_assert_descriptor_outside_raw).capture(descriptor)


@dataclass
class PinnedDestination:
    """A new destination held by directory descriptors until commit or cleanup."""

    path: Path
    root: Path
    parent_descriptor: int
    destination_descriptor: int
    parent_identity: tuple[int, int, int]
    destination_identity: tuple[int, int, int]
    staged_name: str | None = None
    expected_directories: set[str] = field(default_factory=set, repr=False)
    expected_digests: dict[str, str] = field(default_factory=dict, repr=False)
    closed: bool = False

    def expect_directory(self, relative: str) -> None:
        """Record one directory that may appear in the committed topology."""

        self.expected_directories.add(relative)

    def expect_file(self, relative: str, digest: str) -> None:
        """Record one exact file digest and all of its parent directories."""

        path = PurePosixPath(relative)
        for parent in reversed(path.parents):
            if parent != PurePosixPath("."):
                self.expected_directories.add(parent.as_posix())
        self.expected_digests[relative] = digest

    def _authenticate_expected_tree(self) -> None:
        directories, digests = _tree_snapshot(self.destination_descriptor)
        if directories != frozenset(self.expected_directories):
            raise ComposeError("destination tree directory set changed before commit")
        if digests != self.expected_digests:
            raise ComposeError("destination tree bytes or member set changed before commit")

    def _verify_parent(self) -> None:
        _assert_descriptor_outside_raw(
            self.parent_descriptor,
            DESTINATION_PARENT_LABEL,
        )
        _verify_directory_binding(
            self.path.parent,
            self.parent_descriptor,
            DESTINATION_PARENT_LABEL,
            expected_identity=self.parent_identity,
        )

    def _verify_staged_entry(self) -> None:
        if self.staged_name is None:
            raise ComposeError("destination is not staged for commit")
        if (
            _entry_identity(
                self.parent_descriptor,
                self.staged_name,
            )
            != self.destination_identity
        ):
            raise ComposeError("destination changed while it was pinned")
        if _directory_identity(os.fstat(self.destination_descriptor)) != (
            self.destination_identity
        ):
            raise ComposeError("destination changed while it was pinned")

    def verify_binding(self) -> None:
        """Require both descriptors to retain their original path bindings."""

        if self.closed:
            raise ComposeError(DESTINATION_PIN_CLOSED)
        _assert_descriptor_outside_raw(self.destination_descriptor, "destination")
        self._verify_parent()
        if self.staged_name is not None:
            self._verify_staged_entry()
            return
        _verify_directory_binding(
            self.path,
            self.destination_descriptor,
            "destination",
            expected_identity=self.destination_identity,
        )

    def cleanup(self) -> None:
        """Detach only this transaction; never delete a public name."""

        if self.closed:
            return
        try:
            if self.staged_name is None:
                self.staged_name = _quarantine_owned_entry(
                    self.parent_descriptor,
                    self.path.name,
                    self.destination_identity,
                    "destination rollback",
                )
        finally:
            os.close(self.destination_descriptor)
            os.close(self.parent_descriptor)
            self.closed = True

    def begin_commit(self) -> None:
        """Atomically detach the destination before final authentication."""

        if self.closed:
            raise ComposeError(DESTINATION_PIN_CLOSED)
        if self.staged_name is not None:
            self.verify_binding()
            return
        self.verify_binding()
        self.staged_name = _stage_owned_entry(
            self.parent_descriptor,
            self.path.name,
            self.destination_identity,
            "destination commit",
        )
        self._verify_staged_entry()

    def _publish_staged(self) -> None:
        if self.staged_name is None:
            raise ComposeError("destination is not staged for commit")
        staged_name = self.staged_name
        try:
            _rename_noreplace(
                self.parent_descriptor,
                staged_name,
                self.path.name,
            )
        except OSError as exc:
            raise ComposeError(f"destination publication failed: {exc}") from exc
        self.staged_name = None
        if (
            _entry_identity(
                self.parent_descriptor,
                self.path.name,
            )
            != self.destination_identity
        ):
            _quarantine_owned_entry(
                self.parent_descriptor,
                self.path.name,
                self.destination_identity,
                "destination publication rollback",
            )
            raise ComposeError("published destination identity changed")

    def finish(self) -> None:
        """Verify lexical bindings survived, then release the descriptors."""

        if self.closed:
            raise ComposeError(DESTINATION_PIN_CLOSED)
        try:
            if self.staged_name is None:
                self.begin_commit()
            self.verify_binding()
            self._authenticate_expected_tree()
            self._publish_staged()
            self._authenticate_expected_tree()
            self.verify_binding()
        except BaseException:
            self.cleanup()
            raise
        os.close(self.destination_descriptor)
        os.close(self.parent_descriptor)
        self.closed = True


def _destination_descriptor(target: int | PinnedDestination) -> int:
    """Return the root descriptor carried by a raw or fully bound target."""

    if isinstance(target, PinnedDestination):
        return target.destination_descriptor
    return target


def _verify_destination_target(target: int | PinnedDestination) -> None:
    """Reject relocation when the caller retained the complete root binding."""

    if isinstance(target, PinnedDestination):
        _assert_descriptor_outside_raw(target.destination_descriptor, "destination")
        target.verify_binding()


if __package__:
    _expose_package_sibling(__name__)
