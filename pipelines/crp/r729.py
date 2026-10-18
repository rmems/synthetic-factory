#!/usr/bin/env python3
"""CRP r729 catalog: compact JSONL extract of ``crp-mill-r729``.

``catalog.plants_from_source`` is the extract seam. This module loads the
committed ``config/crp`` header plus ``plants-r729.jsonl``. The mill script is
never vendored or executed; a live re-extract uses ``git show``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._contract import bind_import_twin
from . import wave_catalog

if TYPE_CHECKING:
    from . import WaveCatalogCheck

    catalog_check: WaveCatalogCheck

wave_catalog.install_wave(globals())
bind_import_twin(__name__)
