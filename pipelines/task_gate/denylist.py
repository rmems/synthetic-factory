#!/usr/bin/env python3
"""The eval denylist: program ids the gate must never turn into training tasks.

The denylist is a REQUIRED input (#494 supplies the vendored list; its wiring follows #504).
JSON input is an ``eval-exclusion-list-v1`` document, loaded by the same strict loader
compose uses (``eval_exclusion_lists.load_list`` for the ``eval_denylist`` slot). A legacy
UTF-8, LF-framed text file with one program id per line is still accepted. A missing,
unreadable, empty ``program_ids`` (including a reviewed list whose ``repos`` are populated),
or malformed payload refuses the run -- an absent denylist must never read as "nothing is denied".
"""

from __future__ import annotations

import hashlib
import os
import stat
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from . import vocabulary as cv
from ._contract import StrictJsonlError, bind_import_twin, strict_lf_jsonl_lines
from .checks import is_identifier

if __name__.startswith("pipelines."):
    from .. import eval_exclusion_lists as _exclusion_lists
else:
    import eval_exclusion_lists as _exclusion_lists

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


_JSON_START = (b"{", b"[")


def _refuse_empty_program_ids(program_ids: frozenset[str], repos: frozenset[str], location: str) -> None:
    """Empty ``program_ids`` is always a refusal; populated ``repos`` names the gap."""

    if program_ids:
        return
    if repos:
        raise cv.GateRefusal(
            cv.REFUSE_DENYLIST_MALFORMED,
            f"{location}: program_ids is empty while repos names {len(repos)} entries",
        )
    raise cv.GateRefusal(cv.REFUSE_DENYLIST_MALFORMED, f"{location}: denylist has no entries")


def _json_program_ids(location: Path, digest: str) -> frozenset[str]:
    """Program ids from one strict ``eval_denylist`` document, or a coded refusal.

    Compose and the gate share ``eval_exclusion_lists.load_list``. A do-not-train
    document, a placeholder that carries entries, unsorted ids, or non-canonical
    bytes are the same refusal here as they are there. An empty ``program_ids``
    array is still a refusal even when ``repos`` is populated: the gate's input
    is the program-id denylist, not the repository list.
    """

    try:
        loaded = _exclusion_lists.load_list(location, _exclusion_lists.LIST_EVAL_DENYLIST)
    except _exclusion_lists.ExclusionPolicyError as exc:
        raise cv.GateRefusal(cv.REFUSE_DENYLIST_MALFORMED, str(exc)) from exc
    cv.refuse_when(
        loaded.sha256 != digest, cv.REFUSE_DENYLIST_MALFORMED,
        f"{location} changed while it was being read",
    )
    _refuse_empty_program_ids(loaded.program_ids, loaded.repos, str(location))
    return loaded.program_ids


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
    if data.lstrip()[:1] in _JSON_START:
        return Denylist(_json_program_ids(location, digest), digest)
    try:
        lines = strict_lf_jsonl_lines(data, str(location))
    except StrictJsonlError as exc:
        raise cv.GateRefusal(cv.REFUSE_DENYLIST_MALFORMED, str(exc)) from exc
    listed = Denylist.of(lines)
    return Denylist(listed.program_ids, digest)


bind_import_twin(__name__)
