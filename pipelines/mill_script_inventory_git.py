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
    raise MillScriptInventoryError("git is required for inventory scope checks")


def _git_available(repo: Path | None = None) -> bool:
    try:
        return (_git_dir(Path(repo or REPO_ROOT)) / "index").is_file()
    except MillScriptInventoryError:
        return False


def _require_git(repo: Path | None = None) -> None:
    if not _git_available(repo):
        raise MillScriptInventoryError("git is required for inventory scope checks")


def _class_prefix(pattern: str, start: int) -> int:
    index = start
    if index < len(pattern) and pattern[index] in "!^":
        index += 1
    if index < len(pattern) and pattern[index] == "]":
        index += 1
    return index


def _class_close(pattern: str, start: int) -> int | None:
    index = _class_prefix(pattern, start)
    while index < len(pattern):
        if pattern[index] == "]":
            return index
        if pattern.startswith("\\", index) and index + 1 < len(pattern):
            index += 2
            continue
        index += 1
    return None


def _class_atom(body: str, index: int) -> tuple[str, int]:
    if body.startswith("\\", index) and index + 1 < len(body):
        return body[index + 1], index + 2
    return body[index], index + 1


def _class_range(body: str, atom: str, index: int) -> tuple[str, int] | None:
    if index + 1 >= len(body) or body[index] != "-":
        return None
    end, next_index = _class_atom(body, index + 1)
    if len(atom) != 1 or len(end) != 1:
        return None
    return f"{re.escape(atom)}-{re.escape(end)}", next_index


def _class_regex(body: str) -> str:
    parts: list[str] = []
    index = 0
    while index < len(body):
        atom, index = _class_atom(body, index)
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
    body = ""
    index = 0
    while index < len(pattern):
        token, index = _wildcard_token(pattern, index)
        body += token
    prefix = "^" if anchored else "(?:^|/)"
    suffix = "(?:/|$)" if directory_only else "$"
    return re.compile(prefix + body + suffix)


def _gitignore_rules(root: Path) -> tuple[tuple[str, str, str, bool, re.Pattern[str]], ...]:
    path = Path(root) / GITIGNORE_NAME
    if not path.is_file():
        return ()
    rules = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        negated = line.startswith("!")
        pattern = line[1:] if negated else line
        rules.append((GITIGNORE_NAME, str(number), line, negated, _wildcard_regex(pattern)))
    return tuple(rules)


def _git_index_header(payload: bytes) -> int:
    if payload[:4] != b"DIRC":
        raise MillScriptInventoryError("git index is not parseable")
    version = int.from_bytes(payload[4:8], "big")
    if version != 2:
        raise MillScriptInventoryError("unsupported git index version")
    return int.from_bytes(payload[8:12], "big")


def _nul_terminated(payload: bytes, offset: int) -> tuple[str, int]:
    end = payload.index(b"\0", offset)
    return payload[offset:end].decode(), end + 1


def _counted_path(payload: bytes, offset: int, path_len: int) -> tuple[str, int]:
    path = payload[offset : offset + path_len].decode()
    offset += path_len
    if offset < len(payload) and payload[offset] == 0:
        offset += 1
    return path, offset


def _skip_extended_flags(payload: bytes, offset: int, flags: int) -> int:
    if not flags & 0x4000:
        return offset
    if offset + 2 > len(payload):
        raise MillScriptInventoryError("git index is truncated")
    return offset + 2


def _git_index_entry(payload: bytes, offset: int) -> tuple[str, int]:
    if offset + 62 > len(payload):
        raise MillScriptInventoryError("git index is truncated")
    flags = int.from_bytes(payload[offset + 60 : offset + 62], "big")
    start = offset
    offset = _skip_extended_flags(payload, offset + 62, flags)
    if flags & 0xFFF == 0xFFF:
        path, offset = _nul_terminated(payload, offset)
    else:
        path, offset = _counted_path(payload, offset, flags & 0xFFF)
    pad = (8 - ((offset - start) % 8)) % 8
    return path.replace("\\", "/"), offset + pad


def _index_extensions(payload: bytes, offset: int) -> dict[bytes, bytes]:
    if offset + 20 > len(payload):
        raise MillScriptInventoryError("git index is truncated")
    body = payload[offset:-20]
    extensions: dict[bytes, bytes] = {}
    cursor = 0
    while cursor < len(body):
        if cursor + 8 > len(body):
            raise MillScriptInventoryError("git index is not parseable")
        signature = body[cursor : cursor + 4]
        size = int.from_bytes(body[cursor + 4 : cursor + 8], "big")
        cursor += 8
        if cursor + size > len(body):
            raise MillScriptInventoryError("git index is truncated")
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


def _ewah_run_bits(run_bit: int, running_len: int, start: int) -> tuple[tuple[int, ...], int]:
    bits = []
    index = start
    for _ in range(running_len):
        if run_bit:
            bits.extend(range(index, index + 64))
        index += 64
    return tuple(bits), index


def _ewah_literal_bits(word: int, start: int) -> tuple[int, ...]:
    return tuple(start + bit for bit in range(64) if word & (1 << bit))


def _ewah_decode(words: Sequence[int], bit_size: int) -> frozenset[int]:
    if bit_size == 0:
        return frozenset()
    bits: list[int] = []
    index = 0
    cursor = 0
    while cursor < len(words):
        rlw = words[cursor]
        cursor += 1
        run_bits, index = _ewah_run_bits(rlw & 1, (rlw >> 1) & 0xFFFFFFFF, index)
        bits.extend(run_bits)
        for _ in range(rlw >> 33):
            if cursor >= len(words):
                raise MillScriptInventoryError("git index is truncated")
            bits.extend(_ewah_literal_bits(words[cursor], index))
            cursor += 1
            index += 64
    return frozenset(bit for bit in bits if bit < bit_size)


def _u32(payload: bytes, offset: int) -> tuple[int, int]:
    if offset + 4 > len(payload):
        raise MillScriptInventoryError("git index is truncated")
    return int.from_bytes(payload[offset : offset + 4], "big"), offset + 4


def _ewah_bits(payload: bytes, offset: int) -> tuple[frozenset[int], int]:
    bit_size, offset = _u32(payload, offset)
    word_count, offset = _u32(payload, offset)
    words: list[int] = []
    for _ in range(word_count):
        if offset + 8 > len(payload):
            raise MillScriptInventoryError("git index is truncated")
        words.append(int.from_bytes(payload[offset : offset + 8], "big"))
        offset += 8
    _rlw_pos, offset = _u32(payload, offset)
    return _ewah_decode(words, bit_size), offset


def _link_bitmaps(link: bytes) -> tuple[str, frozenset[int], frozenset[int]]:
    if len(link) < 20:
        raise MillScriptInventoryError("git index is truncated")
    deleted, offset = _ewah_bits(link, 20)
    replaced, offset = _ewah_bits(link, offset)
    if offset != len(link):
        raise MillScriptInventoryError("git index is not parseable")
    return link[:20].hex(), deleted, replaced


def _next_replacement(split: Sequence[str], cursor: int, inherited: str) -> tuple[str, int]:
    if cursor >= len(split):
        raise MillScriptInventoryError("git index is truncated")
    return split[cursor] or inherited, cursor + 1


def _apply_split_slot(
    index: int,
    path: str,
    split: Sequence[str],
    cursor: int,
    deleted: frozenset[int],
    replaced: frozenset[int],
) -> tuple[str | None, int]:
    if index in deleted:
        return None, cursor
    if index not in replaced:
        return path, cursor
    return _next_replacement(split, cursor, path)


def _merge_split_paths(
    shared: Sequence[str],
    split: Sequence[str],
    deleted: frozenset[int],
    replaced: frozenset[int],
) -> tuple[str, ...]:
    merged: list[str] = []
    cursor = 0
    for index, path in enumerate(shared):
        kept, cursor = _apply_split_slot(index, path, split, cursor, deleted, replaced)
        if kept:
            merged.append(kept)
    merged.extend(path for path in split[cursor:] if path)
    return tuple(merged)


def _paths_from_split_index(gitdir: Path, split_paths: Sequence[str], link: bytes) -> tuple[str, ...]:
    oid, deleted, replaced = _link_bitmaps(link)
    shared_path = gitdir / f"sharedindex.{oid}"
    if not shared_path.is_file():
        raise MillScriptInventoryError("git index is not parseable")
    shared_paths, shared_ext = _parse_git_index(shared_path.read_bytes())
    if b"link" in shared_ext:
        raise MillScriptInventoryError("unsupported git index version")
    return _merge_split_paths(shared_paths, split_paths, deleted, replaced)


def _read_git_index(repo: Path) -> tuple[str, ...]:
    gitdir = _git_dir(repo)
    paths, extensions = _parse_git_index((gitdir / "index").read_bytes())
    link = extensions.get(b"link")
    if link is None:
        return tuple(path for path in paths if path)
    return _paths_from_split_index(gitdir, paths, link)


def _git_output(repo: Path, arguments: Sequence[str], payload: bytes | None = None) -> bytes:
    if tuple(arguments) == ("ls-files", "-z"):
        return "\0".join(tracked_paths(repo)).encode() + b"\0"
    if tuple(arguments) == ("check-ignore", "--no-index", "-z", "-v", "--stdin"):
        paths = tuple(filter(None, (payload or b"").decode().split("\0")))
        matches = gitignore_matches(repo, paths)
        chunks = [
            part
            for path in paths
            if path in matches
            for part in (*matches[path], path)
        ]
        return ("\0".join(chunks) + "\0").encode() if chunks else b""
    raise MillScriptInventoryError("inventory git helper accepts only ls-files or check-ignore")


def tracked_paths(root: Path | None = None) -> tuple[str, ...]:
    """Return git-tracked paths for inventory completeness."""

    repo = root or REPO_ROOT
    _require_git(repo)
    return _read_git_index(repo)


def gitignore_matches(root: Path, paths: Iterable[str]) -> dict[str, tuple[str, str, str]]:
    """Use Git's effective ignore rules, including negation and ancestor rules."""

    rules = _gitignore_rules(root)
    matches: dict[str, tuple[str, str, str]] = {}
    for path in paths:
        last: tuple[str, str, str] | None = None
        for source, line, original, _negated, regex in rules:
            if regex.search(path.replace("\\", "/")):
                last = (source, line, original)
        if last is not None:
            matches[path] = last
    return matches


def _ignored_paths(matches: Mapping[str, tuple[str, str, str]]) -> frozenset[str]:
    return frozenset(
        path for path, (_source, _line, rule) in matches.items() if not rule.startswith("!")
    )


if __package__:
    _expose_package_sibling(__name__)
