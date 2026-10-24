"""Encode parent objects for the candidate child.

Imported by ``vset_oracle_values`` after that module's types exist, so this
module loads ``vset_oracle_values`` lazily to avoid a cycle.
"""

from __future__ import annotations

import base64
import sys
from collections import Counter, OrderedDict, defaultdict, deque
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import PurePath

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_codec")
    from .vset_oracle_record import data_record as _data_record
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_codec"
    )
    from vset_oracle_record import data_record as _data_record


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


_FACTORIES = {
    "int": int,
    "list": list,
    "set": set,
    "dict": dict,
    "float": float,
    "str": str,
    "tuple": tuple,
}


def _pairs(value: dict[object, object]) -> list[list[object]]:
    return [[encode(key), encode(item)] for key, item in value.items()]


def _factory_name(factory: object) -> str | None:
    if factory is None:
        return ""
    name = getattr(factory, "__name__", "")
    if name in _FACTORIES:
        return str(name)
    return None


def _encode_complex(value: complex) -> dict[str, object]:
    return {"complex": [value.real, value.imag]}


def _encode_range(value: range) -> dict[str, object]:
    return {"range": [value.start, value.stop, value.step]}


def _encode_slice(value: slice) -> dict[str, object]:
    return {"slice": [value.start, value.stop, value.step]}


def _encode_timedelta(value: timedelta) -> dict[str, object]:
    return {"timedelta": [value.days, value.seconds, value.microseconds]}


def _encode_time(value: time) -> dict[str, str]:
    return {"time": value.isoformat()}


def _encode_path(value: PurePath) -> dict[str, str]:
    return {"path": str(value), "cls": type(value).__name__}


def _tracked(kind: str, value: dict[object, object]) -> dict[str, object]:
    return {kind: _pairs(value), "slot": _host()._track(value)}


def _encode_default(value: defaultdict[object, object]) -> dict[str, object] | None:
    name = _factory_name(value.default_factory)
    if name is None:
        return None
    encoded = _tracked("default", value)
    encoded["factory"] = name
    return encoded


def _encode_mapping(value: object) -> object | None:
    if isinstance(value, Counter):
        return _tracked("counter", value)  # type: ignore[arg-type]
    if isinstance(value, OrderedDict):
        return _tracked("ordered", value)  # type: ignore[arg-type]
    if isinstance(value, defaultdict):
        return _encode_default(value)
    return None


_EXACT = {
    complex: _encode_complex,
    range: _encode_range,
    slice: _encode_slice,
    timedelta: _encode_timedelta,
    time: _encode_time,
}


def _encode_stdlib(value: object) -> object | None:
    # type(), not __class__: a Mock(spec=complex) reports complex as its class.
    handler = _EXACT.get(type(value))
    if handler is not None:
        return handler(value)  # type: ignore[operator]
    if isinstance(value, PurePath):
        return _encode_path(value)
    mapped = _encode_mapping(value)
    if mapped is not None:
        return mapped
    return _encode_iterator(value)


def _iterator_types() -> tuple[type, ...]:
    # One-shot views of a finished container. Generators, map, filter, and zip
    # stay callbacks so the child pulls items and the parent iterator survives.
    return (
        type(iter(())),
        type(iter([])),
        type(iter(set())),
        type({}.keys()),
        type({}.values()),
        type({}.items()),
    )


def _encode_iterator(value: object) -> object | None:
    if type(value) not in _iterator_types():
        return None
    return {"seq": [encode(item) for item in value]}  # type: ignore[union-attr]


def _encode_dict_or_list(value: object) -> object | None:
    if isinstance(value, dict):
        return _encode_map(value)  # type: ignore[arg-type]
    if isinstance(value, list):
        return _encode_list(value)  # type: ignore[arg-type]
    return None


def _encode_tuple_or_set(value: object) -> object | None:
    if isinstance(value, tuple):
        if value.__class__ is tuple:
            return _encode_tuple(value)
    if isinstance(value, set):
        return _encode_set(value)  # type: ignore[arg-type]
    if isinstance(value, deque):
        return _encode_list(list(value))
    return None


def _encode_known(value: object) -> object | None:
    encoded = _encode_stdlib(value)
    if encoded is not None:
        return encoded
    encoded = _encode_dict_or_list(value)
    if encoded is not None:
        return encoded
    return _encode_tuple_or_set(value)


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
    return _encode_other(value)


def _encode_other(value: object) -> object:
    if _plain(value):
        return value
    recorded = _data_record(value)
    if recorded is not None:
        return recorded
    return {"cb": _host().remember_callback(value)}


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
