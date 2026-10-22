"""Encode parent objects for the candidate child.

Imported by ``vset_oracle_values`` after that module's types exist, so this
module loads ``vset_oracle_values`` lazily to avoid a cycle.
"""

from __future__ import annotations

import base64
import sys
from collections import deque
from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction

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
    if _plain(value):
        return value
    recorded = _data_record(value)
    if recorded is not None:
        return recorded
    return {"cb": _host().remember_callback(value)}


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
