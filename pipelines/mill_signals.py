#!/usr/bin/env python3
"""The three observable mill signals a single record carries about itself.

One record, read in isolation: no corpus, no destination, no resolution. Every
function here answers "what does this payload say about the mill that wrote
it?" and nothing else -- which mill's id prefix its record id carries, which
factory its payload declares, and which content vocabulary its goal is written
from. Deciding whether those signals disagree with the directory the record
sits in is ``mill_evidence.py``'s job, not this module's.

Split out of ``mill_family.py`` verbatim: every name here is re-exported from
``mill_family`` so existing ``from mill_family import record_id`` call sites
resolve unchanged.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

# ``<mill>-r<round>[<suffix>]-<slug>``: the id shape every agentic factory
# emits. ``r4_29``-style round tokens occur in a handful of published rounds
# and are accepted. An id that does not carry a round token has no mill prefix
# we are willing to guess at, and contributes no id-prefix evidence.
MILL_ID_RE = re.compile(r"^(?P<prefix>[a-z][a-z0-9]{1,7})-r[0-9][0-9_]*[a-z]*(?:-|$)")
GOAL_TOKEN_RE = re.compile(r"[a-z][a-z0-9]{2,}")

# Vocabulary shared by every lane in this corpus: the leftover mechanic itself,
# the fix/verify arc, and episode scaffolding nouns. These words say nothing
# about which mill wrote a goal, so they are excluded from the goal family.
GOAL_STOPWORDS = frozenset(
    """
    add added adds after also and are was were been before but can case cases
    check checked checks correct correcting corrects dont drop dropped dropping
    drops during ensure ensuring error errors fail failed failing fails failure
    fix fixed fixes fixing for from full goal goals had has have here how into
    issue issues its keep keeping keeps key keys lattice leftover leftovers must
    name names new not old onto over partial pass passed passes path paths plant
    plants remove removed removes removing repair repaired repairs repairing
    reset resets run runs set sets should stale state states step steps than
    that the their then there these this those under until use used uses using
    valid validate value values verify verified verifies verifying was when
    while with without
    """.split()
)


def _mapping_field(container: Any, key: str) -> str | None:
    """Return one non-empty, stripped string field of a mapping, or ``None``.

    The read every signal below performs: anything that is not a mapping, is
    missing the key, is not a string, or is blank once stripped, carries no
    signal and reads as ``None``.
    """

    if not isinstance(container, Mapping):
        return None
    value = container.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _payload_sides(record: Mapping) -> tuple[Any, Any, Any]:
    """Return the wrapper and both preference sides, in declaration order."""

    return record, record.get("chosen"), record.get("rejected")


def record_id(record: Any) -> str | None:
    """Return the record's own id, falling back to ``meta.id``."""

    if not isinstance(record, Mapping):
        return None
    for container in (record, record.get("meta")):
        value = _mapping_field(container, "id")
        if value is not None:
            return value
    return None


def mill_prefix(record: Any) -> str | None:
    """Return the mill id prefix carried by a record id, or ``None``."""

    identifier = record_id(record)
    if identifier is None:
        return None
    match = MILL_ID_RE.match(identifier)
    return match.group("prefix") if match else None


def _container_declared_factory(container: Any) -> str | None:
    """Return the factory one mapping claims through its own ``meta``."""

    if not isinstance(container, Mapping):
        return None
    return _mapping_field(container.get("meta"), "factory")


def declared_factory_claims(record: Any) -> tuple[str, ...]:
    """Return every distinct factory this payload claims for itself.

    A legacy preference wrapper predates a wrapper-level ``meta.factory`` and
    attests the declaration on ``chosen``/``rejected`` instead -- the shape
    ``curate_identity._payload_factory`` explicitly accepts. Reading only the
    wrapper leaves a side-stamped foreign payload with no declaration at all,
    so a native destination-stamped prefix and a stopword-only goal would let
    it pass as owned. Claims are returned in wrapper-then-sides order with
    duplicates collapsed.
    """

    if not isinstance(record, Mapping):
        return ()
    claims: list[str] = []
    for container in _payload_sides(record):
        claim = _container_declared_factory(container)
        if claim is not None and claim not in claims:
            claims.append(claim)
    return tuple(claims)


def declared_factory(record: Any) -> str | None:
    """Return the factory the payload claims for itself, when unambiguous.

    Every present claim -- the wrapper and both preference sides -- must agree
    before the record is used as ownership evidence, so a wrapper claim that
    contradicts its sides can no longer define a prefix home or a destination
    identity. ``declared_factory_claims`` still exposes each claim, so a
    contradictory record is reported as foreign rather than silently dropped.
    """

    claims = declared_factory_claims(record)
    return claims[0] if len(claims) == 1 else None


def goal_text(record: Any) -> str | None:
    """Return the task goal, including the per-side goals of a preference pair."""

    if not isinstance(record, Mapping):
        return None
    parts = [
        goal
        for container in _payload_sides(record)
        if (goal := _mapping_field(container, "goal")) is not None
    ]
    return " ".join(parts) if parts else None


def goal_family(record: Any) -> frozenset[str]:
    """Return the mill-identifying content tokens of a record's goal."""

    text = goal_text(record)
    if text is None:
        return frozenset()
    return frozenset(
        token
        for token in GOAL_TOKEN_RE.findall(text.lower())
        if token not in GOAL_STOPWORDS
    )
