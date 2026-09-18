"""Compile the declared measurement modules from the bytes their digest names.

This binds the measurement sources, not the whole transitive Python runtime.
Current installed-source policy verification remains a separate eligibility gate.
"""

from __future__ import annotations

import hashlib
import importlib.abc
import importlib.util
import os
from pathlib import Path
import stat
import sys
from types import MappingProxyType
import weakref

from .import_twins import bind_import_twin

SOURCE_NAMES = (
    "canon.py",
    "families.py",
    "family_common.py",
    "family_credit.py",
    "family_credit_checks.py",
    "family_encoder.py",
    "family_memory.py",
    "family_memory_checks.py",
    "family_mesh.py",
    "family_neuron.py",
    "generator_common.py",
    "generator_credit.py",
    "generator_encoder.py",
    "generator_memory.py",
    "generator_mesh.py",
    "generator_neuron.py",
    "generators.py",
    "oracle_adapters.py",
    "oracle_binding.py",
    "oracle_core.py",
    "oracle_protocol.py",
    "oracles.py",
    "rng.py",
    "sim.py",
    "sim_common.py",
    "sim_credit.py",
    "sim_encoder.py",
    "sim_memory.py",
    "sim_mesh.py",
    "sim_neuron.py",
)
PACKAGE_NAMES = ("oracle_grounded", "pipelines.oracle_grounded")
MAX_SOURCE_BYTES = 4 * 1024 * 1024


def _identity(status):
    return (status.st_dev, status.st_ino, status.st_mode, status.st_size,
            status.st_mtime_ns, status.st_ctime_ns)


def _read_source(root_fd, name):
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    descriptor = os.open(name, flags, dir_fd=root_fd)
    with os.fdopen(descriptor, "rb") as source:
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_SOURCE_BYTES:
            raise ImportError(f"measurement source is not a bounded regular file: {name}")
        body = source.read(MAX_SOURCE_BYTES + 1)
        after = os.fstat(source.fileno())
    if len(body) > MAX_SOURCE_BYTES or _identity(before) != _identity(after):
        raise ImportError(f"measurement source changed during capture: {name}")
    return body, _identity(after)


def _capture(root):
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(descriptor)
        members = {name: _read_source(descriptor, name) for name in SOURCE_NAMES}
        for name, (_, identity) in members.items():
            if _identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False)) != identity:
                raise ImportError(f"measurement snapshot changed during capture: {name}")
        after = root.stat()
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise ImportError("measurement source directory was replaced during capture")
        return MappingProxyType({name: body for name, (body, _) in members.items()})
    finally:
        os.close(descriptor)


def _digest(sources):
    digest = hashlib.sha256()
    for name in SOURCE_NAMES:
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(sources[name]).hexdigest().encode("ascii") + b"\n")
    return "sha256:" + digest.hexdigest()


def _keep_finder(finder):
    owner = getattr(finder, "_oracle_snapshot_owner", None)
    # Import-test isolation may temporarily remove and then restore a live
    # package. Keep its loader until that owner object itself is released.
    return not isinstance(owner, weakref.ReferenceType) or owner() is not None


class _CapturedLoader(importlib.abc.SourceLoader):
    def __init__(self, finder, fullname, filename):
        self.finder = finder
        self.fullname = fullname
        self.filename = filename

    def get_filename(self, fullname):
        if fullname != self.fullname:
            raise ImportError("measurement loader requested a different module")
        return str(self.filename)

    def get_data(self, path):
        if path != str(self.filename):
            raise OSError("measurement loader has no data for that path")
        return self.finder.sources[self.filename.name]

    def get_code(self, fullname):
        filename = self.get_filename(fullname)
        # Never consult pyc, mtime caches, or the mutable source pathname.
        return compile(self.get_data(filename), filename, "exec", dont_inherit=True)

    def exec_module(self, module):
        super().exec_module(module)
        owner = self.finder._oracle_snapshot_owner()
        leaf = self.fullname.rsplit(".", 1)[1]
        for parent in PACKAGE_NAMES:
            if sys.modules.get(parent) is owner:
                sys.modules.setdefault(f"{parent}.{leaf}", module)


class _SnapshotFinder(importlib.abc.MetaPathFinder):
    def __init__(self, owner, root, sources):
        self._oracle_snapshot_owner = weakref.ref(owner)
        self.root = root
        self.sources = sources
        self.digest = _digest(sources)

    def _owns_scope(self, fullname):
        parent, _, leaf = fullname.rpartition(".")
        if parent not in PACKAGE_NAMES or f"{leaf}.py" not in self.sources:
            return False
        owner = self._oracle_snapshot_owner()
        return owner is not None and sys.modules.get(parent) is owner

    def find_spec(self, fullname, path=None, target=None):
        if not self._owns_scope(fullname):
            return None
        if tuple(Path(item).resolve() for item in (path or ())) != (self.root,):
            raise ImportError("measurement package path no longer matches its captured owner")
        leaf = fullname.rsplit(".", 1)[1]
        filename = self.root / f"{leaf}.py"
        loader = _CapturedLoader(self, fullname, filename)
        return importlib.util.spec_from_file_location(fullname, filename, loader=loader)


def _package_children(parent):
    for name in SOURCE_NAMES:
        child = sys.modules.get(f"{parent}.{name[:-3]}")
        if child is not None:
            yield child


def _owned_children(owner):
    for parent in PACKAGE_NAMES:
        if sys.modules.get(parent) is owner:
            yield from _package_children(parent)


def _require_children(owner, finder):
    for child in _owned_children(owner):
        loader = getattr(child, "__loader__", None)
        if not isinstance(loader, _CapturedLoader) or loader.finder is not finder:
            raise ImportError("measurement package contains an unauthenticated child module")


def _require_fresh_owner(owner):
    if any(_owned_children(owner)):
        raise ImportError("fresh measurement package inherited child modules")


def _existing_snapshot(owner, root):
    finder = getattr(owner, "_measurement_source_snapshot", None)
    if finder is None:
        _require_fresh_owner(owner)
        return None
    if not isinstance(finder, _SnapshotFinder) or finder._oracle_snapshot_owner() is not owner:
        raise ImportError("measurement snapshot belongs to a different package")
    if finder.root != root:
        raise ImportError("measurement package was reloaded from a different path")
    _require_children(owner, finder)
    return finder


def install(package_name):
    """Capture before the package imports any of its measurement modules."""
    if package_name not in PACKAGE_NAMES:
        raise ImportError("unsupported measurement package name")
    owner = sys.modules[package_name]
    root = Path(owner.__file__).resolve().parent
    existing = _existing_snapshot(owner, root)
    if existing is not None:
        if existing not in sys.meta_path:
            sys.meta_path.insert(0, existing)
        return
    try:
        sources = _capture(root)
    except OSError as exc:
        raise ImportError(f"cannot capture measurement source: {type(exc).__name__}") from exc
    finder = _SnapshotFinder(owner, root, sources)
    sys.meta_path[:] = [existing for existing in sys.meta_path if _keep_finder(existing)]
    sys.meta_path.insert(0, finder)
    owner._measurement_source_snapshot = finder


def loaded_snapshot(package_name):
    """Bind a module to its package's capture while that module is executing."""
    owner = sys.modules[package_name]
    finder = owner._measurement_source_snapshot
    snapshot_digest(finder)
    return finder


def snapshot_digest(finder):
    """Attest this loaded snapshot only while its imported children remain owned."""
    owner = finder._oracle_snapshot_owner()
    if owner is None or not any(sys.modules.get(name) is owner for name in PACKAGE_NAMES):
        raise ImportError("measurement snapshot package is no longer active")
    _require_children(owner, finder)
    return finder.digest


bind_import_twin(__name__)
