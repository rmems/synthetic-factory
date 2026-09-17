#!/usr/bin/env python3
"""Hashing, tree capture, and exact-JSON file I/O for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

Every read here binds bytes to a pathname identity: a file is captured once,
and the capture is refused if the path was replaced or rewritten while it was
being read. ``os`` is a module attribute on purpose -- tests patch
``curate_gate_digest.os.fstat`` to stage exactly that replacement race.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_digest")
    from . import curate_gate_contract as _contract
    from . import curate_rewards
    from .check_records import reject_json_constant
    from .exact_json import dumps_exact_json, parse_finite_json_float
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_digest"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_rewards
    from check_records import reject_json_constant
    from exact_json import dumps_exact_json, parse_finite_json_float

GOVERNANCE_DIRNAME = _contract.GOVERNANCE_DIRNAME
SHA256_HEX_RE = _contract.SHA256_HEX_RE
GateError = _contract.GateError


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stat_identity(info: os.stat_result) -> tuple[int, ...]:
    """The fields that must all agree before and after a capture."""
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _read_regular_file_snapshot(path: Path, label: str) -> tuple[bytes, str, int]:
    """Capture one regular file once and bind its bytes to its pathname identity."""
    path = Path(path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise GateError(f"cannot open {label} {path} without following links: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise GateError(f"{label} is not a regular file: {path}")
        if before.st_nlink != 1:
            raise GateError(f"{label} is multiply linked: {path}")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1 << 20):
            chunks.append(chunk)
        payload = b"".join(chunks)
        after_descriptor = os.fstat(descriptor)
        try:
            after_path = path.lstat()
        except OSError as exc:
            raise GateError(f"{label} changed while it was being read: {path}") from exc
        identity_before = _stat_identity(before)
        if (
            _stat_identity(after_descriptor) != identity_before
            or _stat_identity(after_path) != identity_before
            or len(payload) != before.st_size
        ):
            raise GateError(f"{label} changed while it was being read: {path}")
        return payload, sha256_hex(payload), len(payload)
    finally:
        os.close(descriptor)


def _tree_snapshot(root: Path) -> list[dict[str, Any]]:
    """Hash one staging tree and reject aliases or mid-read replacements."""
    root = Path(root)
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).parts):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise GateError(f"staging tree contains a symlink: {path}")
        before = path.lstat()
        if stat.S_ISDIR(before.st_mode):
            entries.append({"path": relative, "kind": "directory"})
            continue
        if not stat.S_ISREG(before.st_mode):
            raise GateError(f"staging tree contains a non-regular file: {path}")
        if before.st_nlink != 1:
            raise GateError(f"staging tree contains a multiply linked file: {path}")
        digest = file_sha256(path)
        after = path.lstat()
        if _stat_identity(after) != _stat_identity(before):
            raise GateError(f"staging file changed while it was being hashed: {path}")
        entries.append(
            {
                "path": relative,
                "kind": "file",
                "sha256": digest,
                "bytes": after.st_size,
            }
        )
    return entries


def _lf_lines(text: str) -> list[str]:
    """Split JSONL only at LF; U+2028/U+2029 are valid JSON string data."""
    return text.split("\n")


def _all_jsonl_paths(root: Path) -> list[Path]:
    return sorted(root.rglob("*.jsonl"), key=lambda path: path.relative_to(root).parts)


def jsonl_paths(root: Path) -> list[Path]:
    """Corpus ``*.jsonl`` files, excluding copied governance evidence."""
    return [
        path
        for path in _all_jsonl_paths(root)
        if path.relative_to(root).parts[0] != GOVERNANCE_DIRNAME
    ]


def count_records(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    return sum(1 for line in _lf_lines(text) if line.strip())


def corpus_digest(root: Path) -> str:
    """Digest of the JSONL corpus only, so sidecar reports do not disturb it."""
    digest = hashlib.sha256()
    for path in jsonl_paths(root):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return f"sha256:{digest.hexdigest()}"


def record_sha256(value: Any) -> str:
    try:
        blob = curate_rewards.canonical_bytes(value)
    except (TypeError, ValueError) as exc:
        raise GateError(f"record is not canonical JSON data: {exc}") from exc
    return sha256_hex(blob)


def _normalized_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise GateError(f"{label} must be a SHA-256")
    match = SHA256_HEX_RE.fullmatch(value)
    if match is None:
        raise GateError(f"{label} must be a SHA-256")
    return match.group(1)


def _write_json(path: Path, payload: Any) -> None:
    # Governance files are re-read with exact numeric hooks and re-hashed at
    # promotion time, so the writer must emit every ``ExactJSONFloat`` token
    # verbatim; ``json.dumps`` would silently round precision-sensitive
    # evidence (``25.000000000000001`` -> ``25.0``) and block promotion.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        dumps_exact_json(payload, ensure_ascii=True, sort_keys=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _load_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GateError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(
            text,
            parse_constant=reject_json_constant,
            parse_float=parse_finite_json_float,
        )
    # ``JSONDecodeError`` is a ``ValueError``, as is the refusal raised by the
    # exact-JSON float hook, so one clause covers both without widening it.
    except ValueError as exc:
        raise GateError(f"{path}: invalid JSON: {exc}") from exc


if __package__:
    _expose_package_sibling(__name__)
