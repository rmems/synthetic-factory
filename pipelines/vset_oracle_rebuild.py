"""Namedtuple rebuild and small oracle helpers kept out of the hot modules.

``vset_oracle_values`` imports this module. Value interpretation is loaded
lazily so the two files do not import each other at module scope.
"""

from __future__ import annotations

import sys
import unittest.mock
from collections import namedtuple

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_rebuild")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_rebuild"
    )


def _values():
    # vset_oracle_values imports this module. A top-level import would cycle.
    if __package__:
        from . import vset_oracle_values as values
    else:
        import vset_oracle_values as values
    return values


_NAMED: dict[tuple[str, tuple[str, ...]], type] = {}


def clear_named() -> None:
    """Drop namedtuple classes rebuilt for the previous child."""

    _NAMED.clear()


def _named_fields(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, list):
        return ()
    return tuple(str(item) for item in raw)


def _named_items(client: object, payload: dict[str, object]) -> list[object]:
    raw = payload.get("items")
    if not isinstance(raw, list):
        return []
    host = _values()
    return [host.interpret(client, item) for item in raw]


def rebuild_namedtuple(client: object, payload: dict[str, object]) -> tuple[object, ...]:
    """Rebuild one child namedtuple from field names and encoded items."""

    fields = _named_fields(payload.get("fields"))
    name = str(payload.get("name") or "Record")
    key = (name, fields)
    cls = _NAMED.get(key)
    if cls is None:
        cls = namedtuple(name, fields)  # type: ignore[misc]
        _NAMED[key] = cls
    return cls(*_named_items(client, payload))


def live_collaborator(value: object) -> bool:
    """Mocks and test-defined fakes stay live. ``TestCase`` does not."""

    if isinstance(value, unittest.mock.Mock):
        return True
    if isinstance(value, unittest.TestCase):
        return False
    module = getattr(type(value), "__module__", "")
    if not isinstance(module, str):
        return False
    return module.startswith("vset_oracle_")


def exception_chain(exc: Exception) -> list[str]:
    """Builtin bases of an exception, nearest first, stopping at BaseException."""

    names: list[str] = []
    for base in type(exc).__mro__[1:]:
        if base is BaseException or base is object:
            break
        names.append(base.__name__)
    return names


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
