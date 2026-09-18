#!/usr/bin/env python3
"""Operator-supplied paths, confined to the trees the operator runs in.

A CLI reads and writes only under the working directory, the home directory or
the temp directory (SonarCloud S8707): a path is resolved with ``realpath`` and
refused unless one of those roots is a prefix of it. Leaf symlinks, dangling
links, and special files are refused before any sink runs; destinations that
already exist are refused so a failed validation cannot replace them.

Confine at the CLI boundary, in the flow right after ``parse_args``, and never
as an argparse ``type=`` converter -- Sonar's taint engine does not model
converters, which is why #203 moved the calls out of the parser. Internal APIs
keep taking an unresolved ``Path``: several pipelines reject symlinked
components lexically, and handing them a pre-resolved path would make those
guards vacuous.

Refusals name the rejected argument and never include the typed path, the
resolved location, or the operator roots (home, temp, cwd), so environment
secrets in those strings cannot leak through argparse.
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("operator_paths")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "operator_paths"
    )

KIND_PATH = "path"
KIND_DESTINATION = "destination"
_OUTSIDE = "the path lies outside the working, home and temp trees"
_SPECIAL_MODES = (stat.S_ISFIFO, stat.S_ISCHR, stat.S_ISBLK, stat.S_ISSOCK)


def operator_roots() -> tuple[str, ...]:
    return tuple(
        os.path.realpath(root) for root in (os.getcwd(), Path.home(), tempfile.gettempdir())
    )


def _labeled(argument: str | None, reason: str) -> str:
    if argument:
        return f"{argument}: {reason}"
    return reason


def _refuse(argument: str | None, reason: str) -> NoReturn:
    raise argparse.ArgumentTypeError(_labeled(argument, reason))


def _text_of(value: str | os.PathLike[str], argument: str | None) -> str:
    try:
        text = os.fspath(value)
    except TypeError:
        _refuse(argument, "the path is empty")
    if not isinstance(text, str):
        text = os.fsdecode(text)
    if not text.strip():
        _refuse(argument, "the path is empty")
    return text


def _is_special_file(mode: int) -> bool:
    return any(check(mode) for check in _SPECIAL_MODES)


def _inspectable_leaf(text: str) -> Path:
    """The leaf ``realpath`` binds, without following a final symlink.

    Collapse terminal separators and dot components so an absent prefix
    cannot hide the effective leaf. For an ordinary named leaf, resolve
    its parent first: a symlink before an interior ``..`` changes which
    directory contains the leaf.
    """

    parent, name = os.path.split(_without_terminal_dots(text))
    return Path(os.path.join(os.path.realpath(parent), name))


def _without_terminal_dots(text: str) -> str:
    """Remove only the terminal syntax; interior symlink parents stay intact."""
    path = Path(text)
    parts = list(path.parts)
    pending = 0
    while parts:
        if not pending and parts[-1] != os.pardir:
            break
        component = parts.pop()
        if component == os.pardir:
            pending += 1
        elif component == path.anchor:
            parts.append(component)
            pending = 0
            break
        else:
            pending -= 1
    return str(Path(*parts, *([os.pardir] * pending)))


def _refuse_leaf(leaf: Path, argument: str | None) -> None:
    """Refuse a leaf that is a symlink or a special file, before following it."""

    try:
        mode = os.lstat(leaf).st_mode
    except FileNotFoundError:
        return
    except OSError:
        _refuse(argument, "the path cannot be inspected")
    if stat.S_ISLNK(mode):
        if os.path.exists(leaf):
            _refuse(argument, "the path is a symlink")
        _refuse(argument, "the path is a dangling symlink")
    if _is_special_file(mode):
        _refuse(argument, "the path is a special file")


def _under_root(resolved: str, root: str) -> bool:
    # Keep "/": rstrip(os.sep) would turn it into "" and commonpath would raise.
    stripped = root.rstrip(os.sep)
    if stripped:
        root = stripped
    try:
        return os.path.commonpath([resolved, root]) == root
    except ValueError:
        return False


def _inside_operator_trees(resolved: str) -> bool:
    return any(_under_root(resolved, root) for root in operator_roots())


def operator_path(
    value: str | os.PathLike[str],
    *,
    argument: str | None = None,
    kind: str = KIND_PATH,
) -> Path:
    """The resolved path, or an argparse error when the typed value is unsafe.

    ``kind="destination"`` also refuses a leaf that already exists, so a
    replacement cannot begin. ``--write-index`` and factory directories keep the
    default kind because they name existing trees, not new files.
    """

    if kind not in {KIND_PATH, KIND_DESTINATION}:
        _refuse(argument, "the path kind is not supported")
    text = _text_of(value, argument)
    leaf = _inspectable_leaf(text)
    _refuse_leaf(leaf, argument)
    resolved = os.path.realpath(text)
    if not _inside_operator_trees(resolved):
        _refuse(argument, _OUTSIDE)
    if kind == KIND_DESTINATION and os.path.lexists(leaf):
        _refuse(argument, "the destination already exists")
    return Path(resolved)


def confine(
    parser: argparse.ArgumentParser,
    value: str | os.PathLike[str] | None,
    *,
    argument: str,
    kind: str = KIND_PATH,
) -> Path | None:
    """Confine one parsed argument, or leave an absent optional as ``None``."""

    if value is None:
        return None
    try:
        return operator_path(value, argument=argument, kind=kind)
    except argparse.ArgumentTypeError as exc:
        return parser.error(str(exc))


def confine_named(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    arguments: dict[str, str],
    destinations: frozenset[str] = frozenset(),
) -> dict[str, Path | None]:
    """Confine each named field on ``args``; destination names refuse an existing leaf."""

    confined: dict[str, Path | None] = {}
    for name, argument in arguments.items():
        kind = KIND_DESTINATION if name in destinations else KIND_PATH
        confined[name] = confine(
            parser, getattr(args, name, None), argument=argument, kind=kind
        )
    return confined


if __package__:
    _expose_package_sibling(__name__)
