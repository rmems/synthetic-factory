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


def _values():
    # vset_oracle_values imports the codec, which imports this module.
    if __package__:
        from . import vset_oracle_values as values
    else:
        import vset_oracle_values as values
    return values


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


def _tuple_subclass(value: object) -> bool:
    return isinstance(value, tuple) and value.__class__ is not tuple


def _name_tuple(fields: object) -> tuple[str, ...] | None:
    if not isinstance(fields, tuple) or not fields:
        return None
    names: list[str] = []
    for name in fields:
        if not isinstance(name, str):
            return None
        names.append(name)
    return tuple(names)


def _encoded_items(value: tuple[object, ...]) -> list[object] | None:
    encoded: list[object] = []
    for item in value:
        try:
            encoded.append(_codec().encode(item))
        except Exception:
            return None
    return encoded


def _namedtuple_record(value: object) -> dict[str, object] | None:
    if not _tuple_subclass(value):
        return None
    fields = _name_tuple(getattr(value, "_fields", None))
    if fields is None:
        return None
    items = _encoded_items(value)  # type: ignore[arg-type]
    if items is None:
        return None
    return {"namedtuple": type(value).__name__, "fields": list(fields), "items": items}


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


def _field(value: object, key: str) -> object:
    if key.startswith("_"):
        return None
    item = _public_attr(value, key)
    if item is _UNPLAIN:
        return None
    if callable(item):
        return None
    return _plain_field(item)


def _collect_fields(value: object) -> dict[str, object] | None:
    fields: dict[str, object] = {}
    for key in dir(value):
        encoded = _field(value, key)
        if encoded is _UNPLAIN:
            return None
        if encoded is None:
            continue
        fields[key] = encoded
    return fields


def _object_record(value: object) -> dict[str, object] | None:
    if live_collaborator(value):
        return None
    if callable(value):
        return None
    fields = _collect_fields(value)
    if not fields:
        return None
    return {"record": fields}


def receive(client: object, proc: object, ops: tuple[object, object, object, object]) -> object:
    """Read worker replies, relaying prints and logs before the final value."""

    read_reply, send, answer, relay = ops
    stdout = proc.stdout  # type: ignore[attr-defined]
    if stdout is None:
        raise EOFError("oracle worker exited")
    while True:
        reply = read_reply(stdout)  # type: ignore[operator]
        if not isinstance(reply, dict):
            return _values().interpret(client, reply)
        if relay(reply):  # type: ignore[operator]
            continue
        if reply.get("kind") == "callback":
            send(proc, answer(client, reply))  # type: ignore[operator]
            continue
        return _values().interpret(client, reply)


def data_record(value: object) -> dict[str, object] | None:
    """Field snapshot for a namedtuple or a simple data object."""

    recorded = _namedtuple_record(value)
    if recorded is not None:
        return recorded
    return _object_record(value)


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
