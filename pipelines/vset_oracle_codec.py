"""Encode parent objects for the candidate child.

Imported by ``vset_oracle_values`` after that module's types exist, so this
module loads ``vset_oracle_values`` lazily to avoid a cycle.
"""

from __future__ import annotations

import base64
import builtins
import sys
from collections import deque
from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_codec")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_codec"
    )


def _host():
    # vset_oracle_values imports this module. A top-level import would cycle.
    if __package__:
        from . import vset_oracle_values as values
    else:
        import vset_oracle_values as values
    return values


def _encode_list(value: list[object]) -> dict[str, object]:
    return {"seq": [encode(item) for item in value], "slot": _host()._track(value)}


def _encode_tuple(value: tuple[object, ...]) -> dict[str, object]:
    return {"seq": [encode(item) for item in value], "tuple": True}


def _encode_map(value: dict[object, object]) -> dict[str, object]:
    encoded = [[encode(key), encode(item)] for key, item in value.items()]
    return {"map": encoded, "slot": _host()._track(value)}


def _encode_set(value: set[object]) -> dict[str, object]:
    return {"set": [encode(item) for item in value], "slot": _host()._track(value)}


def _encode_frozen(value: frozenset[object]) -> dict[str, object]:
    return {"set": [encode(item) for item in value], "frozen": True}


def _encode_bytes(value: bytes | bytearray) -> dict[str, object]:
    payload: dict[str, object] = {"bytes": base64.b64encode(bytes(value)).decode("ascii")}
    if isinstance(value, bytearray):
        payload["slot"] = _host()._track(value)
    return payload


def _encode_decimal(value: Decimal) -> dict[str, str]:
    return {"decimal": str(value)}


def _encode_fraction(value: Fraction) -> dict[str, int]:
    return {"fraction": value.numerator, "d": value.denominator}


def _encode_datetime(value: datetime) -> dict[str, str]:
    return {"datetime": value.isoformat()}


def _encode_date(value: date) -> dict[str, str]:
    return {"date": value.isoformat()}


_ENCODE = {
    set: _encode_set,
    frozenset: _encode_frozen,
    bytes: _encode_bytes,
    bytearray: _encode_bytes,
    Decimal: _encode_decimal,
    Fraction: _encode_fraction,
    datetime: _encode_datetime,
    date: _encode_date,
}


def _encode_dict_or_list(value: object) -> object | None:
    if isinstance(value, dict):
        return _encode_map(value)  # type: ignore[arg-type]
    if isinstance(value, list):
        return _encode_list(value)  # type: ignore[arg-type]
    return None


def _encode_tuple_or_set(value: object) -> object | None:
    if isinstance(value, tuple):
        return _encode_tuple(tuple(value))
    if isinstance(value, set):
        return _encode_set(value)  # type: ignore[arg-type]
    if isinstance(value, deque):
        return _encode_list(list(value))
    return None


def _encode_known(value: object) -> object | None:
    encoded = _encode_dict_or_list(value)
    if encoded is not None:
        return encoded
    return _encode_tuple_or_set(value)


def builtin_type(info: dict[str, object]) -> type | None:
    """Real builtin when the child describes one, instead of a proxy class."""

    name = info.get("builtin")
    if not isinstance(name, str):
        return None
    found = getattr(builtins, name, None)
    if isinstance(found, type):
        return found
    return None


def _collect_parents(client: object, host: object, raw: list[object]) -> list[type]:
    parents: list[type] = []
    for base in raw:
        if not isinstance(base, dict):
            continue
        builtin = builtin_type(base)
        if builtin is not None:
            parents.append(builtin)
            continue
        parents.append(host._class_from(client, base))  # type: ignore[attr-defined]
    return parents


def _with_remote(host: object, parents: list[type]) -> list[type]:
    remote = host.RemoteObject  # type: ignore[attr-defined]
    for parent in parents:
        if issubclass(parent, remote):
            return parents
    return [remote, *parents]


def parent_types(client: object, info: dict[str, object]) -> list[type]:
    """Bases for a reconstructed candidate class, preserving builtin ancestry."""

    host = _host()
    raw = info.get("bases")
    if not isinstance(raw, list):
        return [host.RemoteObject]
    if not raw:
        return [host.RemoteObject]
    parents = _collect_parents(client, host, raw)
    if not parents:
        return [host.RemoteObject]
    return _with_remote(host, parents)


def _new_list(cls: type) -> object:
    return list.__new__(cls)


def _new_dict(cls: type) -> object:
    return dict.__new__(cls)


def _new_set(cls: type) -> object:
    return set.__new__(cls)


def _new_tuple(cls: type) -> object:
    return tuple.__new__(cls, ())


def _new_str(cls: type) -> object:
    return str.__new__(cls, "")


def _new_bytes(cls: type) -> object:
    return bytes.__new__(cls, b"")


def _new_bytearray(cls: type) -> object:
    return bytearray.__new__(cls)


def _new_int(cls: type) -> object:
    return int.__new__(cls, 0)


def _new_float(cls: type) -> object:
    return float.__new__(cls, 0.0)


_BLANK = (
    (list, _new_list),
    (dict, _new_dict),
    (set, _new_set),
    (tuple, _new_tuple),
    (str, _new_str),
    (bytes, _new_bytes),
    (bytearray, _new_bytearray),
    (int, _new_int),
    (float, _new_float),
)


def blank_instance(cls: type) -> object:
    """Empty instance whose real builtin bases ``isinstance`` still sees."""

    for base, maker in _BLANK:
        if cls is base:
            continue
        if issubclass(cls, base):
            return maker(cls)
    return object.__new__(cls)


def _replace(original: object, new: object) -> None:
    if isinstance(original, list):
        original.clear()
        original.extend(new)  # type: ignore[arg-type]
        return
    if isinstance(original, dict):
        original.clear()
        original.update(new)  # type: ignore[arg-type]
        return
    if isinstance(original, set):
        original.clear()
        original.update(new)  # type: ignore[arg-type]
        return
    if isinstance(original, bytearray):
        original.clear()
        original.extend(new)  # type: ignore[arg-type]


def apply_slots(client: object, states: object) -> None:
    """Copy child mutations of parent containers back onto the originals."""

    if not isinstance(states, list):
        return
    host = _host()
    for state in states:
        if not isinstance(state, dict):
            continue
        original = host._SLOTS.get(int(state["slot"]))
        if original is None:
            continue
        _replace(original, host.interpret(client, state["state"]))


def _plain(value: object) -> bool:
    if value is None:
        return True
    return type(value) in {bool, int, float, str}


def encode(value: object) -> object:
    if isinstance(value, _host().RemoteObject):
        return {"ref": value.oid}
    handler = _ENCODE.get(type(value))
    if handler is not None:
        return handler(value)
    encoded = _encode_known(value)
    if encoded is not None:
        return encoded
    if _plain(value):
        return value
    return {"cb": _host().remember_callback(value)}


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
