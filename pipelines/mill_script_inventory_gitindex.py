"""Read tracked paths from a git index (v2/v3), merging a split index's shared base."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_script_inventory_gitindex")
    from . import mill_script_inventory_gitdir as _gitdir
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "mill_script_inventory_gitindex"
    )
    import mill_script_inventory_gitdir as _gitdir

MillScriptInventoryError = _gitdir.MillScriptInventoryError
_git_dir = _gitdir._git_dir
_INDEX_UNPARSEABLE = "git index is not parseable"
_INDEX_TRUNCATED = "git index is truncated"
_INDEX_UNSUPPORTED = "unsupported git index version"
_INDEX_SPARSE = "sparse git index directories are not expanded"


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
    mode = int.from_bytes(payload[offset + 24 : offset + 28], "big")
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
    if mode & 0o170000 == 0o040000:
        raise MillScriptInventoryError(_INDEX_SPARSE)
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


if __package__:
    _expose_package_sibling(__name__)
