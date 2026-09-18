#!/usr/bin/env python3
"""Cleaned db-migration-repair mill package (AST-extracted, r845+)."""

from __future__ import annotations

from pathlib import Path

from .import_twins import bind_import_twin

__all__ = ["FACTORY_DIR", "PLANTS", "build_episode", "build_pair", "self_check"]


def FACTORY_DIR(repo_root: Path | None = None) -> Path:
    """Raw factory directory; never created or written on import."""
    root = repo_root if repo_root is not None else Path(__file__).resolve().parents[2]
    return root / "outputs" / "raw" / "2026-08-19-agentic" / "db-migration-repair-factory"


def __getattr__(name: str):  # lazy re-exports; keeps import side-effect-free
    if name == "PLANTS":
        from .plants import PLANTS as _p

        return _p
    if name == "build_episode":
        from .episode import build_episode as _b

        return _b
    if name == "build_pair":
        from .notes import build_pair as _bp

        return _bp
    if name == "self_check":
        from .check import self_check as _s

        return _s
    raise AttributeError(name)


bind_import_twin(__name__)
