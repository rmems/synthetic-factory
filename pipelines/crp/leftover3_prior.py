#!/usr/bin/env python3
"""CRP leftover3-prior catalog: compact JSONL extract of ``crp-mill-leftover3``.

``catalog.plants_from_source`` is the extract seam. This module loads the
committed ``config/crp`` header plus ``plants-leftover3-prior.jsonl``. The mill script is
never vendored or executed; a live re-extract uses ``git show``.
"""

from __future__ import annotations

from ._contract import bind_import_twin
from . import wave_catalog

wave_catalog.install_wave(globals())
bind_import_twin(__name__)
