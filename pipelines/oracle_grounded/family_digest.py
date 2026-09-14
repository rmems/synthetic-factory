#!/usr/bin/env python3
"""The source digest a split generator stamps as its ``generator_version``.

Both parity generators were one module each and are now families of siblings.
A digest over a single file would have kept attesting a facade while the code
that actually builds records moved out from under it -- and because each
validator re-derives through the same function, that would have stayed green
rather than failing. So the digest covers the whole family.

The family is declared by its caller rather than discovered, so adding a
sibling is a deliberate act; the declaration is then cross-checked against the
directory every time the digest is computed, so a sibling can never be added
and silently left out of it.
"""

from __future__ import annotations

from .import_twins import bind_import_twin

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parents[1]
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from neuro_oracle import digest  # noqa: E402


def family_sources(root, glob, family, validator):
    """The family's source texts by path, or raise if the directory disagrees."""

    found = tuple(sorted(path.name for path in root.glob(glob)))
    declared = tuple(sorted(family))
    if found != declared:
        raise RuntimeError(
            f"{validator}: the {glob} family on disk is {found}, but the module "
            f"declares {declared}. generator_version must cover every file that "
            "generates, so reconcile the two before running."
        )
    return [
        {"path": f"pipelines/{name}", "text": (root / name).read_text(encoding="utf-8")}
        for name in declared
    ]


def module_source_digest(root, glob, family, validator):
    """Immutable digest of the whole family, used as the in-repo generator_version."""

    return digest({"paths": family_sources(root, glob, family, validator)})


bind_import_twin(__name__)
