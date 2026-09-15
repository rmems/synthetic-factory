#!/usr/bin/env python3
"""The one place the contract-drift family reaches shared import-twin binding.

Both import forms are supported (``contract_drift.x`` with ``pipelines/`` on
``sys.path``, and ``pipelines.contract_drift.x`` from the repository root).
"""

from __future__ import annotations

if __name__.startswith("pipelines."):
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from oracle_grounded.import_twins import bind_import_twin

__all__ = ["bind_import_twin"]

bind_import_twin(__name__)
