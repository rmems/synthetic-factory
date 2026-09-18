#!/usr/bin/env python3
"""In-process git index and gitignore evidence for mill-script inventory."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_script_inventory_git")
    from . import mill_script_inventory_schema as _schema
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "mill_script_inventory_git"
    )
    import mill_script_inventory_schema as _schema

MillScriptInventoryError = _schema.MillScriptInventoryError
_GIT_REQUIRED = "git is required for inventory scope checks"
_INDEX_UNPARSEABLE = "git index is not parseable"
_INDEX_TRUNCATED = "git index is truncated"
_INDEX_UNSUPPORTED = "unsupported git index version"
GITIGNORE_NAME = ".gitignore"
REPO_ROOT = Path(__file__).resolve().parents[1]


def _resolve_gitdir_pointer(marker: Path, raw: str) -> Path:
    gitdir = Path(raw.strip())
    return gitdir if gitdir.is_absolute() else (marker.parent / gitdir).resolve()


def _gitdir_from_gitfile(marker: Path) -> Path | None:
    for line in marker.read_text(encoding="utf-8").splitlines():
        if line.startswith("gitdir:"):
            return _resolve_gitdir_pointer(marker, line.split(":", 1)[1])
    return None


def _git_dir(repo: Path) -> Path:
    marker = Path(repo).resolve() / ".git"
    if marker.is_file():
        found = _gitdir_from_gitfile(marker)
        if found is not None:
            return found
    if marker.is_dir():
        return marker
    raise MillScriptInventoryError(_GIT_REQUIRED)


def _git_available(repo: Path | None = None) -> bool:
    try:
        return (_git_dir(Path(repo or REPO_ROOT)) / "index").is_file()
    except MillScriptInventoryError:
        return False


def _require_git(repo: Path | None = None) -> None:
    if not _git_available(repo):
        raise MillScriptInventoryError(_GIT_REQUIRED)


def _class_skip(pattern: str, index: int, chars: str) -> int:
    return index + int(index < len(pattern) and pattern[index] in chars)


def _escape_width(pattern: str, index: int) -> int:
    if pattern.startswith("\\", index) and index + 1 < len(pattern):
        return 2
    return 1


def _class_close(pattern: str, start: int) -> int | None:
    index = _class_skip(pattern, _class_skip(pattern, start, "!^"), "]")
    while index < len(pattern):
        if pattern[index] == "]":
            return index
        index += _escape_width(pattern, index)
    return None


def _class_range(body: str, atom: str, index: int) -> tuple[str, int] | None:
    if index + 1 >= len(body) or body[index] != "-":
        return None
    end = body[index + 1]
    if len(atom) != 1 or len(end) != 1:
        return None
    return f"{re.escape(atom)}-{re.escape(end)}", index + 2


def _class_regex(body: str) -> str:
    parts: list[str] = []
    index = 0
    while index < len(body):
        if body.startswith("\\", index) and index + 1 < len(body):
            parts.append(re.escape(body[index + 1]))
            index += 2
            continue
        atom = body[index]
        index += 1
        ranged = _class_range(body, atom, index)
        if ranged is None:
            parts.append(re.escape(atom))
            continue
        token, index = ranged
        parts.append(token)
    return "".join(parts)


def _character_class(pattern: str, index: int) -> tuple[str, int]:
    close = _class_close(pattern, index + 1)
    inner = pattern[index + 1 : close] if close is not None else ""
    negated = inner[:1] in "!^"
    body = inner[1:] if negated else inner
    if close is None or not body:
        return re.escape("["), index + 1
    translated = _class_regex(body)
    if negated:
        return f"[^{translated}/]", close + 1
    return f"(?:(?!/)[{translated}])", close + 1


def _glob_star(pattern: str, index: int) -> tuple[str, int] | None:
    if pattern.startswith("**", index) and pattern[index + 2 : index + 3] in ("", "/"):
        skip = 3 if pattern.startswith("**/", index) else 2
        return ".*", index + skip
    if pattern[index] == "*":
        return "[^/]*", index + 1
    if pattern[index] == "?":
        return "[^/]", index + 1
    return None


def _wildcard_token(pattern: str, index: int) -> tuple[str, int]:
    starred = _glob_star(pattern, index)
    if starred is not None:
        return starred
    if pattern.startswith("\\", index) and index + 1 < len(pattern):
        return re.escape(pattern[index + 1]), index + 2
    if pattern[index] == "[":
        return _character_class(pattern, index)
    return re.escape(pattern[index]), index + 1


def _wildcard_regex(pattern: str) -> re.Pattern[str]:
    directory_only = pattern.endswith("/")
    pattern = pattern.removesuffix("/")
    anchored = pattern.startswith("/") or "/" in pattern
    pattern = pattern.removeprefix("/")
    chunks: list[str] = []
    index = 0
    while index < len(pattern):
        token, index = _wildcard_token(pattern, index)
        chunks.append(token)
    prefix = "^" if anchored else "(?:^|/)"
    suffix = "(?:/|$)" if directory_only else "$"
    return re.compile(prefix + "".join(chunks) + suffix)


def _collect_ignore_files(root: Path, paths: Iterable[str]) -> tuple[tuple[str, Path], ...]:
    files: dict[str, Path] = {"": Path(root) / GITIGNORE_NAME}
    for candidate in paths:
        relative = Path(candidate.replace("\\", "/")).parent
        while relative != Path("."):
            files[f"{relative.as_posix()}/"] = Path(root) / relative / GITIGNORE_NAME
            relative = relative.parent
    return tuple((scope, path) for scope, path in sorted(files.items()) if path.is_file())


def _parse_ignore_file(path: Path, source: str) -> tuple[tuple[str, str, str, re.Pattern[str]], ...]:
    rules: list[tuple[str, str, str, re.Pattern[str]]] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pattern = line[1:] if line.startswith("!") else line
        rules.append((source, str(number), line, _wildcard_regex(pattern)))
    return tuple(rules)


def _scope_relative(path: str, scope: str) -> str | None:
    if not scope:
        return path
    if path.startswith(scope):
        return path[len(scope):]
    return None


def _load_ignore_rules(
    root: Path, paths: Iterable[str]
) -> tuple[tuple[str, str, str, str, re.Pattern[str]], ...]:
    rules: list[tuple[str, str, str, str, re.Pattern[str]]] = []
    for scope, path in _collect_ignore_files(root, paths):
        parsed = _parse_ignore_file(path, f"{scope}{GITIGNORE_NAME}")
        rules.extend((scope, source, line, original, regex) for source, line, original, regex in parsed)
    return tuple(rules)


def _last_ignore_hit(
    path: str,
    rules: Sequence[tuple[str, str, str, str, re.Pattern[str]]],
) -> tuple[str, str, str] | None:
    last = None
    normalized = path.replace("\\", "/")
    for scope, source, line, original, regex in rules:
        relative = _scope_relative(normalized, scope)
        if relative is None:
            continue
        if regex.search(relative):
            last = (source, line, original)
    return last


def gitignore_matches(root: Path, paths: Iterable[str]) -> dict[str, tuple[str, str, str]]:
    """Use Git's effective ignore rules, including nested, negated, and ancestor rules."""

    candidates = tuple(paths)
    rules = _load_ignore_rules(root, candidates)
    matches: dict[str, tuple[str, str, str]] = {}
    for candidate in candidates:
        hit = _last_ignore_hit(candidate, rules)
        if hit is not None:
            matches[candidate] = hit
    return matches


def _ignored_paths(matches: Mapping[str, tuple[str, str, str]]) -> frozenset[str]:
    return frozenset(
        path for path, (_source, _line, rule) in matches.items() if not rule.startswith("!")
    )


def _need(payload: bytes, offset: int, size: int) -> None:
    if offset + size > len(payload):
        raise MillScriptInventoryError(_INDEX_TRUNCATED)


def _git_index_header(payload: bytes) -> int:
    if payload[:4] != b"DIRC":
        raise MillScriptInventoryError(_INDEX_UNPARSEABLE)
    version = int.from_bytes(payload[4:8], "big")
    if version not in (2, 3):
        raise MillScriptInventoryError(_INDEX_UNSUPPORTED)
    return int.from_bytes(payload[8:12], "big")


def _git_index_entry(payload: bytes, offset: int) -> tuple[str, int]:
    _need(payload, offset, 62)
    flags = int.from_bytes(payload[offset + 60 : offset + 62], "big")
    start = offset
    offset += 62
    if flags & 0x4000:
        _need(payload, offset, 2)
        offset += 2
    path_len = flags & 0xFFF
    if path_len == 0xFFF:
        end = payload.index(b"\0", offset)
        path, offset = payload[offset:end].decode(), end + 1
    else:
        path = payload[offset : offset + path_len].decode()
        offset += path_len
        if offset < len(payload) and payload[offset] == 0:
            offset += 1
    pad = (8 - ((offset - start) % 8)) % 8
    return path.replace("\\", "/"), offset + pad


def _index_extensions(payload: bytes, offset: int) -> dict[bytes, bytes]:
    _need(payload, offset, 20)
    body = payload[offset:-20]
    extensions: dict[bytes, bytes] = {}
    cursor = 0
    while cursor < len(body):
        _need(body, cursor, 8)
        signature = body[cursor : cursor + 4]
        size = int.from_bytes(body[cursor + 4 : cursor + 8], "big")
        cursor += 8
        _need(body, cursor, size)
        extensions[signature] = body[cursor : cursor + size]
        cursor += size
    return extensions


def _parse_git_index(payload: bytes) -> tuple[tuple[str, ...], dict[bytes, bytes]]:
    count = _git_index_header(payload)
    offset = 12
    paths: list[str] = []
    for _ in range(count):
        path, offset = _git_index_entry(payload, offset)
        paths.append(path)
    return tuple(paths), _index_extensions(payload, offset)


def _ewah_literal(words: Sequence[int], cursor: int, index: int, bits: list[int]) -> tuple[int, int]:
    if cursor >= len(words):
        raise MillScriptInventoryError(_INDEX_TRUNCATED)
    word = words[cursor]
    bits.extend(index + bit for bit in range(64) if word & (1 << bit))
    return cursor + 1, index + 64


def _ewah_repeat(rlw: int, index: int, bits: list[int]) -> int:
    running_len = (rlw >> 1) & 0xFFFFFFFF
    if rlw & 1:
        bits.extend(range(index, index + running_len * 64))
    return index + running_len * 64


def _ewah_literals(
    words: Sequence[int], rlw: int, pos: tuple[int, int], bits: list[int]
) -> tuple[int, int]:
    cursor, index = pos
    for _ in range(rlw >> 33):
        cursor, index = _ewah_literal(words, cursor, index, bits)
    return cursor, index


def _ewah_decode(words: Sequence[int], bit_size: int) -> frozenset[int]:
    if bit_size == 0:
        return frozenset()
    bits: list[int] = []
    index = 0
    cursor = 0
    while cursor < len(words):
        rlw = words[cursor]
        cursor += 1
        index = _ewah_repeat(rlw, index, bits)
        cursor, index = _ewah_literals(words, rlw, (cursor, index), bits)
    return frozenset(bit for bit in bits if bit < bit_size)


def _ewah_bits(payload: bytes, offset: int) -> tuple[frozenset[int], int]:
    _need(payload, offset, 8)
    bit_size = int.from_bytes(payload[offset : offset + 4], "big")
    word_count = int.from_bytes(payload[offset + 4 : offset + 8], "big")
    offset += 8
    words: list[int] = []
    for _ in range(word_count):
        _need(payload, offset, 8)
        words.append(int.from_bytes(payload[offset : offset + 8], "big"))
        offset += 8
    _need(payload, offset, 4)
    return _ewah_decode(words, bit_size), offset + 4


def _link_bitmaps(link: bytes) -> tuple[str, frozenset[int], frozenset[int]]:
    _need(link, 0, 20)
    deleted, offset = _ewah_bits(link, 20)
    replaced, offset = _ewah_bits(link, offset)
    if offset != len(link):
        raise MillScriptInventoryError(_INDEX_UNPARSEABLE)
    return link[:20].hex(), deleted, replaced


def _next_replacement(split: Sequence[str], cursor: int, inherited: str) -> tuple[str, int]:
    if cursor >= len(split):
        raise MillScriptInventoryError(_INDEX_TRUNCATED)
    return split[cursor] or inherited, cursor + 1


def _remaining_split(split: Sequence[str], cursor: int) -> tuple[str, ...]:
    return tuple(path for path in split[cursor:] if path)


def _merge_split_paths(
    shared: Sequence[str],
    split: Sequence[str],
    deleted: frozenset[int],
    replaced: frozenset[int],
) -> tuple[str, ...]:
    merged: list[str] = []
    cursor = 0
    for index, path in enumerate(shared):
        if index in deleted:
            continue
        if index in replaced:
            path, cursor = _next_replacement(split, cursor, path)
        if path:
            merged.append(path)
    return tuple(merged) + _remaining_split(split, cursor)


def _read_git_index(repo: Path) -> tuple[str, ...]:
    gitdir = _git_dir(repo)
    paths, extensions = _parse_git_index((gitdir / "index").read_bytes())
    link = extensions.get(b"link")
    if link is None:
        return tuple(path for path in paths if path)
    oid, deleted, replaced = _link_bitmaps(link)
    shared_path = gitdir / f"sharedindex.{oid}"
    if not shared_path.is_file():
        raise MillScriptInventoryError(_INDEX_UNPARSEABLE)
    shared_paths, shared_ext = _parse_git_index(shared_path.read_bytes())
    if b"link" in shared_ext:
        raise MillScriptInventoryError(_INDEX_UNSUPPORTED)
    return _merge_split_paths(shared_paths, paths, deleted, replaced)


def _ls_files_output(repo: Path) -> bytes:
    return "\0".join(tracked_paths(repo)).encode() + b"\0"


def _check_ignore_output(repo: Path, payload: bytes | None) -> bytes:
    paths = tuple(filter(None, (payload or b"").decode().split("\0")))
    matches = gitignore_matches(repo, paths)
    chunks: list[str] = []
    for path in paths:
        hit = matches.get(path)
        if hit is None:
            continue
        chunks.extend((*hit, path))
    if not chunks:
        return b""
    return ("\0".join(chunks) + "\0").encode()


def _git_output(repo: Path, arguments: Sequence[str], payload: bytes | None = None) -> bytes:
    command = tuple(arguments)
    if command == ("ls-files", "-z"):
        return _ls_files_output(repo)
    if command == ("check-ignore", "--no-index", "-z", "-v", "--stdin"):
        return _check_ignore_output(repo, payload)
    raise MillScriptInventoryError("inventory git helper accepts only ls-files or check-ignore")


def tracked_paths(root: Path | None = None) -> tuple[str, ...]:
    """Return git-tracked paths for inventory completeness."""

    repo = root or REPO_ROOT
    _require_git(repo)
    return _read_git_index(repo)


if __package__:
    _expose_package_sibling(__name__)
