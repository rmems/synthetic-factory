#!/usr/bin/env python3
"""The eval denylist: program ids the gate must never turn into training tasks.

The denylist is a REQUIRED input (#494 supplies the vendored list; its wiring follows #504).
The primary form is ``eval-exclusion-list-v1`` JSON (``program_ids``); a legacy UTF-8,
LF-framed text file with one program id per line is still accepted. A missing, unreadable,
empty ``program_ids`` (including reviewed lists whose ``repos`` are populated), or
malformed payload refuses the run -- an absent denylist must never read as "nothing is denied".
"""

from __future__ import annotations

import hashlib
import os
import stat
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from . import vocabulary as cv
from ._contract import StrictJsonlError, bind_import_twin, load_strict_json, strict_lf_jsonl_lines
from .checks import is_identifier

__all__ = ["Denylist", "load_denylist"]


@dataclass(frozen=True)
class Denylist:
    """The denied program ids and the digest of the bytes they came from."""

    program_ids: frozenset[str]
    sha256: str

    @classmethod
    def of(cls, program_ids: Iterable[str]) -> Denylist:
        """An in-memory denylist (tests, callers that already hold the ids)."""

        if isinstance(program_ids, (str, bytes)):
            raise cv.GateRefusal(cv.REFUSE_DENYLIST_MALFORMED, "denylist must be a collection of ids")
        ids = list(program_ids)
        cv.refuse_when(not ids, cv.REFUSE_DENYLIST_MALFORMED, "denylist has no entries")
        for item in ids:
            cv.refuse_when(
                not is_identifier(item), cv.REFUSE_DENYLIST_MALFORMED,
                f"denylist entry is not a program id: {item!r}",
            )
        cv.refuse_when(len(set(ids)) != len(ids), cv.REFUSE_DENYLIST_MALFORMED, "denylist repeats an id")
        digest = hashlib.sha256("".join(f"{item}\n" for item in sorted(ids)).encode("utf-8"))
        return cls(frozenset(ids), digest.hexdigest())

    def __contains__(self, program_id: object) -> bool:
        return program_id in self.program_ids

    def __len__(self) -> int:
        return len(self.program_ids)


def _program_ids_from_json(data: bytes, location: str) -> list[str]:
    """The ``program_ids`` array from one eval-exclusion JSON document."""

    try:
        document = load_strict_json(data.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise cv.GateRefusal(cv.REFUSE_DENYLIST_MALFORMED, f"{location} is not UTF-8") from exc
    except (ValueError, RecursionError) as exc:
        raise cv.GateRefusal(cv.REFUSE_DENYLIST_MALFORMED, f"{location} is not strict JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise cv.GateRefusal(cv.REFUSE_DENYLIST_MALFORMED, f"{location} must be a JSON object")
    if "program_ids" not in document:
        raise cv.GateRefusal(cv.REFUSE_DENYLIST_MALFORMED, f"{location} has no program_ids")
    program_ids = document["program_ids"]
    repos = document.get("repos")
    if not isinstance(program_ids, list):
        raise cv.GateRefusal(cv.REFUSE_DENYLIST_MALFORMED, f"{location}.program_ids must be a list")
    if not program_ids:
        if isinstance(repos, list) and repos:
            raise cv.GateRefusal(
                cv.REFUSE_DENYLIST_MALFORMED,
                f"{location}: program_ids is empty while repos names {len(repos)} entries",
            )
        raise cv.GateRefusal(cv.REFUSE_DENYLIST_MALFORMED, "denylist has no entries")
    ids: list[str] = []
    for index, item in enumerate(program_ids):
        cv.refuse_when(
            not is_identifier(item), cv.REFUSE_DENYLIST_MALFORMED,
            f"{location}.program_ids[{index}] is not a program id: {item!r}",
        )
        ids.append(item)
    cv.refuse_when(
        len(set(ids)) != len(ids), cv.REFUSE_DENYLIST_MALFORMED,
        f"{location}.program_ids repeats an id",
    )
    return ids


def _read(path: Path) -> bytes:
    cv.refuse_when(
        not path.exists(), cv.REFUSE_DENYLIST_MISSING, f"denylist {path} does not exist",
    )
    try:
        mode = os.stat(path).st_mode
        cv.refuse_when(
            not stat.S_ISREG(mode), cv.REFUSE_DENYLIST_MALFORMED, f"denylist {path} is not a regular file",
        )
        with path.open("rb") as handle:
            data = handle.read(cv.MAX_DENYLIST_BYTES + 1)
    except OSError as exc:
        raise cv.GateRefusal(cv.REFUSE_DENYLIST_MISSING, f"denylist {path} is unreadable: {exc}") from exc
    cv.refuse_when(
        len(data) > cv.MAX_DENYLIST_BYTES, cv.REFUSE_DENYLIST_MALFORMED, f"denylist {path} is too large",
    )
    return data


def load_denylist(path: Path | str | None) -> Denylist:
    """Load the denylist file or refuse; ``None`` is a refusal, never an empty list."""

    cv.refuse_when(path is None, cv.REFUSE_DENYLIST_MISSING, "a denylist is required")
    location = Path(str(path))
    data = _read(location)
    digest = hashlib.sha256(data).hexdigest()
    if data.lstrip().startswith(b"{"):
        ids = _program_ids_from_json(data, str(location))
        return Denylist(frozenset(ids), digest)
    try:
        lines = strict_lf_jsonl_lines(data, str(location))
    except StrictJsonlError as exc:
        raise cv.GateRefusal(cv.REFUSE_DENYLIST_MALFORMED, str(exc)) from exc
    listed = Denylist.of(lines)
    return Denylist(listed.program_ids, digest)


bind_import_twin(__name__)
