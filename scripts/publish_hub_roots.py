"""Hub mirror and factory source roots for ``scripts/publish_grok46_hub.py``.

The publisher reads published rounds from a factory source root and mirrors
them under a Hub root. ``main`` resolves each root once per run, taking the CLI
flag, then the environment, then the publisher's own defaults (``HF_ROOT``
and ``FACTORY_ROOT``, passed in at call time so a patched default still
applies). The result is a frozen :class:`PublisherRoots`. It is active only
inside :func:`active_roots`, a ``with`` block whose context variable is reset
on exit. The publisher's helpers read the active value through
:func:`active_hf_root` and :func:`active_factory_root`, which fall back to the
default they are given when no run is active. The module defaults themselves
are never reassigned.

A configured root must already be a real, non-symlinked directory; it is not
created. Whatever the source, the Hub root is refused when it names or aliases
``outputs/raw/`` (``pipelines/raw_tree_guard.py``) or overlaps the factory
source, so a Hub working tree cannot mutate immutable raw bytes. A refusal
names the flag or variable, never the configured value.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import stat
import sys
from collections.abc import Iterator, Mapping
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path

PIPELINES_ROOT = Path(__file__).resolve().parents[1] / "pipelines"
if str(PIPELINES_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINES_ROOT))

import raw_tree_guard  # noqa: E402


@dataclass(frozen=True)
class PublisherRoots:
    """The Hub mirror root and the read-only factory source root of one run."""

    hf: Path
    factory: Path


@dataclass(frozen=True)
class RootSetting:
    """How an operator overrides one root: a CLI flag, then an environment variable."""

    flag: str
    env: str
    dest: str
    label: str


HF_ROOT_SETTING = RootSetting(
    "--hf-root", "SYNTHETIC_FACTORY_HF_ROOT", "hf_root", "Hub mirror root"
)
FACTORY_ROOT_SETTING = RootSetting(
    "--factory-root", "SYNTHETIC_FACTORY_SOURCE_ROOT", "factory_root", "factory source root"
)
ROOT_SETTINGS = (HF_ROOT_SETTING, FACTORY_ROOT_SETTING)
# Options the schemas audit refuses: it reads no root and takes no --only.
SCHEMAS_REFUSED_OPTIONS = (("only", "--only"), *((s.dest, s.flag) for s in ROOT_SETTINGS))

_ACTIVE_ROOTS: ContextVar[PublisherRoots | None] = ContextVar(
    "publish_hub_roots_active", default=None
)


class PublisherRootError(ValueError):
    """A configured root was refused; the message names the setting, never its value."""


@contextlib.contextmanager
def active_roots(roots: PublisherRoots) -> Iterator[PublisherRoots]:
    """Make ``roots`` the run's roots for the duration of the ``with`` block.

    The variable is reset however the block exits, including an exception or
    the ``SystemExit`` a refused command raises.
    """
    token = _ACTIVE_ROOTS.set(roots)
    try:
        yield roots
    finally:
        _ACTIVE_ROOTS.reset(token)


def current_roots() -> PublisherRoots | None:
    """The roots of the active run, or ``None`` outside :func:`active_roots`."""
    return _ACTIVE_ROOTS.get()


def active_hf_root(default: Path) -> Path:
    """The active run's Hub root, or ``default`` when no run is active."""
    roots = _ACTIVE_ROOTS.get()
    return default if roots is None else roots.hf


def active_factory_root(default: Path) -> Path:
    """The active run's factory source root, or ``default`` when no run is active."""
    roots = _ACTIVE_ROOTS.get()
    return default if roots is None else roots.factory


def safe_factory_root(default: Path) -> Path:
    """The active factory source root, refused unless it is a real directory."""
    factory_root = active_factory_root(default)
    if factory_root.is_symlink() or not factory_root.is_dir():
        raise SystemExit(f"unsafe factory root: {factory_root}")
    return factory_root


def real_directory(directory: Path, *, parents: bool = False) -> None:
    """Create ``directory`` if absent, then require a real, non-symlinked directory.

    The Hub mirror is refreshed in place, so an existing real directory is
    accepted. There is no ``exists()`` pre-check to race: ``mkdir`` either
    creates the entry or reports one already there, and whatever is there,
    ours or a concurrent writer's, must then be a real directory.
    """
    with contextlib.suppress(FileExistsError):
        directory.mkdir(parents=parents)
    if directory.is_symlink() or not directory.is_dir():
        raise SystemExit(f"unsafe snapshot directory: {directory}")


def resolve_publisher_roots(
    flags: Mapping[str, str | None], environ: Mapping[str, str], defaults: PublisherRoots
) -> PublisherRoots:
    """Resolve both roots once: the CLI flag, then the environment, then the default.

    ``flags`` maps each setting's ``dest`` (``hf_root``, ``factory_root``) to
    the parsed flag value, ``None`` when the flag was not given.
    """
    roots = PublisherRoots(
        hf=_chosen_root(HF_ROOT_SETTING, flags, environ, defaults.hf),
        factory=_chosen_root(FACTORY_ROOT_SETTING, flags, environ, defaults.factory),
    )
    _require_separate_roots(roots)
    return roots


def publication_roots(
    args: argparse.Namespace, environ: Mapping[str, str], defaults: PublisherRoots
) -> PublisherRoots:
    """Resolve the run's roots right after parsing, or exit 2 naming the refused setting."""
    try:
        return resolve_publisher_roots(vars(args), environ, defaults)
    except PublisherRootError as exc:
        print(f"refusing publication root: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def add_root_arguments(parser: argparse.ArgumentParser, defaults: PublisherRoots) -> None:
    """Add ``--hf-root`` and ``--factory-root``, documenting each fallback."""
    for setting, default in zip(ROOT_SETTINGS, (defaults.hf, defaults.factory), strict=True):
        shown = str(default).replace("%", "%%")
        parser.add_argument(
            setting.flag,
            dest=setting.dest,
            metavar="DIR",
            help=f"existing {setting.label}; overrides ${setting.env} (default: {shown})",
        )


def refused_schemas_option(args: argparse.Namespace) -> str | None:
    """The first option given to ``schemas`` that it refuses, even with an empty value."""
    return next(
        (flag for dest, flag in SCHEMAS_REFUSED_OPTIONS if getattr(args, dest) is not None),
        None,
    )


def _chosen_root(
    setting: RootSetting,
    flags: Mapping[str, str | None],
    environ: Mapping[str, str],
    default: Path,
) -> Path:
    configured = _configured_value(setting, flags.get(setting.dest), environ)
    if configured is None:
        return default
    source, value = configured
    return _existing_root_directory(source, value)


def _configured_value(
    setting: RootSetting, flag_value: str | None, environ: Mapping[str, str]
) -> tuple[str, str] | None:
    """Return ``(source, value)`` for an explicit setting, the flag first."""
    if flag_value is not None:
        return setting.flag, flag_value
    if setting.env in environ:
        return setting.env, environ[setting.env]
    return None


def _existing_root_directory(source: str, value: str) -> Path:
    """Require a configured root to already be a real directory; a blank value is refused."""
    if not value.strip():
        raise PublisherRootError(f"{source} is set but empty")
    # Absolute but not resolved, like the defaults: the publisher's own guards
    # refuse a symlinked root lexically, which a pre-resolved path would make
    # vacuous. The overlap checks below resolve both sides themselves.
    path = Path(os.path.abspath(value))
    mode = _root_mode(source, path)
    if stat.S_ISLNK(mode):
        raise PublisherRootError(f"{source} names a symlink, not a real directory")
    if not stat.S_ISDIR(mode):
        raise PublisherRootError(f"{source} does not name a directory")
    return path


def _root_mode(source: str, path: Path) -> int:
    """``lstat`` one configured root without following it, failing closed."""
    try:
        return os.lstat(path).st_mode
    except FileNotFoundError as exc:
        raise PublisherRootError(
            f"{source} names a directory that does not exist; create it first"
        ) from exc
    except OSError as exc:
        raise PublisherRootError(f"{source} cannot be inspected") from exc


def _require_separate_roots(roots: PublisherRoots) -> None:
    """Refuse a Hub root that could write into raw bytes, by name, alias, or overlap."""
    if raw_tree_guard.is_under_raw(roots.hf):
        raise PublisherRootError("the Hub mirror root names or aliases outputs/raw/")
    # With the factory as its root, the raw guard is an alias-aware containment
    # test (resolved path, shared inode, bind mount), so it is stronger than
    # is_relative_to. Its outputs/raw segment branch was already refused above.
    if raw_tree_guard.is_under_raw(roots.hf, roots.factory):
        raise PublisherRootError("the Hub mirror root lies inside the factory source root")
    if roots.factory.resolve().is_relative_to(roots.hf.resolve()):
        raise PublisherRootError("the factory source root lies inside the Hub mirror root")
