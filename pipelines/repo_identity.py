#!/usr/bin/env python3
"""Canonical ``owner/name`` spelling for public source repositories (#494).

This module only fixes the *spelling* of a repository name: GitHub owner and
repository syntax, compared case-insensitively, so the canonical form is the
lowercased ``owner/name``. Renames and transfers are a separate question that
``eval_exclusion_aliases`` answers offline from the committed alias cache; no
function here touches the network.

Matching is on whole values only. ``rmems/thalamic-relay`` and
``rmems/thalamic-relay-trajectories`` are different repositories, and no
helper here ever compares by prefix or substring.
"""

from __future__ import annotations

import re
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("repo_identity")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "repo_identity"
    )

# The one spelling rule, shared verbatim with the ``canonicalRepo`` definition
# in schemas/actor-provenance-v1.schema.json (the other schemas ``$ref`` it, and
# a drift test pins the equality). GitHub owners: 1-39 alphanumerics or single
# hyphens, no leading, trailing, or consecutive hyphen. Repository names: 1-100
# of alphanumerics, ``.``, ``_`` or ``-``, never the path segments ``.`` or
# ``..``. Both are compared lowercased. The syntax is common to ECMA-262 (JSON
# Schema) and Python ``re``; Python callers use ``fullmatch``, so ``$`` cannot
# accept a trailing newline.
CANONICAL_REPO_PATTERN = (
    r"^(?![^/]*--)[a-z0-9](?:[a-z0-9-]{0,37}[a-z0-9])?/(?!\.{1,2}$)[a-z0-9._-]{1,100}$"
)
CANONICAL_REPO_RE = re.compile(CANONICAL_REPO_PATTERN, re.ASCII)


class RepoNameError(ValueError):
    """A repository name is not a well-formed GitHub ``owner/name``."""


def canonical_repo(value: object) -> str:
    """Return the lowercased ``owner/name`` spelling, or raise ``RepoNameError``.

    Surrounding whitespace, URLs, ``.git`` suffixes, and extra path segments
    are refused rather than repaired: a record names its source exactly.
    """

    if not isinstance(value, str):
        raise RepoNameError("repository name must be a string")
    lowered = value.lower()
    if CANONICAL_REPO_RE.fullmatch(lowered) is None:
        raise RepoNameError(f"not a GitHub owner/name: {value!r}")
    return lowered


def is_canonical_repo(value: object) -> bool:
    """Whether ``value`` is already in canonical (lowercased, well-formed) form."""

    try:
        return canonical_repo(value) == value
    except RepoNameError:
        return False


if __package__:
    _expose_package_sibling(__name__)
