"""Payment-idempotency (pay) lane: slice A builders and Archive B catalog.

Slice A (merged #249) is the r330 leftover-leftover-leftover extract in
:mod:`pipelines.pay.pairs` / :mod:`pipelines.pay.episodes`. Archive B is the
``mill_plants.py`` pair catalog (rounds 98+) in :mod:`pipelines.pay.archive_b_catalog`.
Mill scripts are never executed on this branch.
"""

from __future__ import annotations

from .archive_b_catalog import ArchiveBCatalog, ArchiveBPair, load_archive_b_catalog
from .episodes import db, fail_ep, success_ep
from .notes import notes
from .pairs import FAC, GEN, PAIRS, PREFIX

__all__ = [
    "ArchiveBCatalog",
    "ArchiveBPair",
    "FAC",
    "GEN",
    "PAIRS",
    "PREFIX",
    "db",
    "fail_ep",
    "load_archive_b_catalog",
    "notes",
    "success_ep",
]
