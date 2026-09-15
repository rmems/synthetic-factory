"""Hopper: deterministic Q=2 episode replay for 2026-08-19-agentic factories.

Public API later families (qbp, wsr, ewr, cei, kcl) import:

- ``emit_stage`` / ``factory_dir``
- ``START`` / ``PAIRS`` keyed by factory (plus ``start_by_factory`` /
  ``pairs_by_factory`` when a wave, including **g46c**, must be selected)
- ``_p``
- ``build_success`` / ``build_fail``
- ``dumps_episode`` / ``notes_md``

Deterministic, no LLM. Replays 76 research_only/blocked rounds (152 plants
across g46/g46b/g46c/g46d). Reward metrics are constants. Plant content is
grok-4.6-authored. Writes never target ``outputs/raw`` unless ``publish
--raw-root`` is given.
"""

from ._contract import bind_import_twin
from .episode import (
    GENERATOR,
    assert_clean,
    build_fail,
    build_pair,
    build_success,
    dumps_episode,
    emit_stage,
    factory_dir,
    validate_pair,
)
from .notes import notes_md
from .plants import CYCLE, PAIRS, PREFIX, START, _p, all_pairs, pairs_by_factory, start_by_factory

__all__ = [
    "CYCLE",
    "GENERATOR",
    "PAIRS",
    "PREFIX",
    "START",
    "_p",
    "all_pairs",
    "assert_clean",
    "build_fail",
    "build_pair",
    "build_success",
    "dumps_episode",
    "emit_stage",
    "factory_dir",
    "notes_md",
    "pairs_by_factory",
    "start_by_factory",
    "validate_pair",
]

bind_import_twin(__name__)
