"""Plain snapshots of namedtuples and simple parent objects.

``vset_oracle_codec`` imports this module. Codec helpers are loaded lazily
so the two files do not import each other at module scope.
"""

from __future__ import annotations

import sys
import unittest

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_record")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_record"
    )


def _codec():
    # vset_oracle_codec imports this module. A top-level import would cycle.
    if __package__:
        from . import vset_oracle_codec as codec
    else:
        import vset_oracle_codec as codec
    return codec


class _Unplain:
    pass


_UNPLAIN = _Unplain()


def _plain_field(value: object) -> object:
    codec = _codec()
    if codec._plain(value):
        return value
    if isinstance(value, tuple):
        if value.__class__ is tuple:
            return codec._encode_tuple(value)
    return _UNPLAIN


def _namedtuple_record(value: object) -> dict[str, object] | None:
    asdict = getattr(value, "_asdict", None)
    if not callable(asdict):
        return None
    try:
        raw = asdict()
    except Exception:
        return None
    if not isinstance(raw, dict):
        return None
    fields: dict[str, object] = {}
    for key, item in raw.items():
        encoded = _plain_field(item)
        if encoded is _UNPLAIN:
            return None
        fields[str(key)] = encoded
    return {"record": fields}


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


def _public_attr(value: object, key: str) -> object:
    try:
        return getattr(value, key)
    except Exception:
        return _UNPLAIN


def _object_record(value: object) -> dict[str, object] | None:
    if live_collaborator(value):
        return None
    if callable(value):
        return None
    fields: dict[str, object] = {}
    for key in dir(value):
        if key.startswith("_"):
            continue
        item = _public_attr(value, key)
        if item is _UNPLAIN:
            continue
        if callable(item):
            continue
        encoded = _plain_field(item)
        if encoded is _UNPLAIN:
            return None
        fields[key] = encoded
    if not fields:
        return None
    return {"record": fields}


def data_record(value: object) -> dict[str, object] | None:
    """Field snapshot for a namedtuple or a simple data object."""

    recorded = _namedtuple_record(value)
    if recorded is not None:
        return recorded
    return _object_record(value)


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
