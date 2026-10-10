"""Solvers that propose actions to the environment; none of them authors an observation."""

from __future__ import annotations

from .._contract import bind_import_twin
from . import scripted

__all__ = ["scripted"]

bind_import_twin(__name__)
