"""Encode candidate values for the parent-side oracle.

Primitives and containers cross as data. Exception classes become real
exception types. Other objects stay remote and forward the operations
unittest and ordinary assertions use.
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

    _assert_direct_sibling("vset_oracle_values")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_values"
    )

_EXC_TYPES: dict[tuple[str, str], type[Exception]] = {}
_CLASSES: dict[tuple[int, int], type] = {}
_OBJECTS: dict[tuple[int, int], RemoteObject] = {}
_FORWARDED = (
    "__eq__ __ne__ __lt__ __le__ __gt__ __ge__ __len__ __iter__ __next__ "
    "__contains__ __getitem__ __add__ __radd__ __sub__ __rsub__ __mul__ __rmul__"
).split()


def _builtin_exception(name: str) -> type[Exception] | None:
    found = getattr(builtins, name, None)
    if not isinstance(found, type):
        return None
    if not issubclass(found, Exception):
        return None
    return found


def _exception_parent(chain: tuple[str, ...]) -> type[Exception]:
    if not chain:
        return Exception
    builtin = _builtin_exception(chain[0])
    if builtin is not None:
        return builtin
    return exception_type(chain[0], chain[1:])


def exception_type(name: str, chain: tuple[str, ...]) -> type[Exception]:
    """Return one real exception class, preserving the candidate MRO."""

    key = (name, chain)
    found = _EXC_TYPES.get(key)
    if found is not None:
        return found
    created = type(name, (_exception_parent(chain),), {})
    _EXC_TYPES[key] = created
    return created


def raise_remote(name: str, chain: tuple[str, ...], message: str) -> None:
    """Raise a candidate error without ever raising BaseException."""

    builtin = _builtin_exception(name)
    if builtin is not None:
        raise builtin(message)
    raise exception_type(name, chain)(message)


class RemoteObject:
    def __init__(self, *args: object, **kwargs: object) -> None:
        return None

    def __call__(self, *args: object, **kwargs: object) -> object:
        return self.client.call(self.oid, args, kwargs)

    def __getattr__(self, name: str) -> object:
        return self.client.get(self.oid, name)

    def __setattr__(self, name: str, value: object) -> None:
        if name == "client":
            object.__setattr__(self, name, value)
            return
        if name == "oid":
            object.__setattr__(self, name, value)
            return
        self.client.set_attr(self.oid, name, value)

    def __bool__(self) -> bool:
        return _truth(self)

    def __hash__(self) -> int:
        return _remote_hash(self)


def _forward(name: str):
    def method(self: RemoteObject, *args: object) -> object:
        try:
            func = self.client.get(self.oid, name)
        except AttributeError:
            return NotImplemented
        return func(*args)

    method.__name__ = name
    return method


for _name in _FORWARDED:
    setattr(RemoteObject, _name, _forward(_name))


def _remote_hash(obj: RemoteObject) -> int:
    try:
        func = obj.client.get(obj.oid, "__hash__")
    except AttributeError:
        return object.__hash__(obj)
    if func is None:
        raise TypeError("unhashable type")
    return int(func())


def _truth(obj: RemoteObject) -> bool:
    try:
        func = obj.client.get(obj.oid, "__bool__")
    except AttributeError:
        func = None
    if func is not None:
        return bool(func())
    try:
        func = obj.client.get(obj.oid, "__len__")
    except AttributeError:
        return True
    return bool(func())


def _class_from(client: object, info: dict[str, object]) -> type:
    oid = int(info["oid"])
    key = (id(client), oid)
    found = _CLASSES.get(key)
    if found is not None:
        return found
    raw_bases = info.get("bases")
    if raw_bases is None:
        raw_bases = []
    parents = [_class_from(client, base) for base in raw_bases]  # type: ignore[union-attr]
    if not parents:
        parents = [RemoteObject]

    def new(cls, *args, **kwargs):
        return client.call(oid, args, kwargs)  # type: ignore[attr-defined]

    created = type(str(info["name"]), tuple(parents), {"__new__": new})
    _CLASSES[key] = created
    return created


def reset_identity() -> None:
    """Drop remote objects from the previous child."""

    _OBJECTS.clear()
    _CLASSES.clear()


def _wrap(client: object, payload: dict[str, object]) -> RemoteObject:
    oid = int(payload["oid"])
    key = (id(client), oid)
    found = _OBJECTS.get(key)
    if found is not None:
        return found
    cls = _class_from(client, payload["cls"])  # type: ignore[arg-type]
    obj = object.__new__(cls)
    object.__setattr__(obj, "client", client)
    object.__setattr__(obj, "oid", oid)
    _OBJECTS[key] = obj
    return obj


def _list(client: object, payload: dict[str, object]) -> list[object]:
    return [interpret(client, item) for item in payload["items"]]  # type: ignore[misc]


def _tuple(client: object, payload: dict[str, object]) -> tuple[object, ...]:
    return tuple(interpret(client, item) for item in payload["items"])  # type: ignore[misc]


def _dict(client: object, payload: dict[str, object]) -> dict[object, object]:
    pairs = payload["items"]
    return {
        interpret(client, pair[0]): interpret(client, pair[1])  # type: ignore[index]
        for pair in pairs  # type: ignore[union-attr]
    }


def _value(_client: object, payload: dict[str, object]) -> object:
    return payload.get("value")


def _notimplemented(_client: object, _payload: dict[str, object]) -> object:
    return NotImplemented


def _set(client: object, payload: dict[str, object]) -> set[object]:
    return {interpret(client, item) for item in payload["items"]}  # type: ignore[misc]


def _frozenset(client: object, payload: dict[str, object]) -> frozenset[object]:
    return frozenset(interpret(client, item) for item in payload["items"])  # type: ignore[misc]


def _bytes(_client: object, payload: dict[str, object]) -> bytes:
    return base64.b64decode(str(payload["data"]))


def _decimal(_client: object, payload: dict[str, object]) -> Decimal:
    return Decimal(str(payload["data"]))


def _fraction(_client: object, payload: dict[str, object]) -> Fraction:
    return Fraction(int(payload["n"]), int(payload["d"]))


def _datetime(_client: object, payload: dict[str, object]) -> datetime:
    return datetime.fromisoformat(str(payload["data"]))


def _date(_client: object, payload: dict[str, object]) -> date:
    return date.fromisoformat(str(payload["data"]))


def _class(client: object, payload: dict[str, object]) -> type:
    return _class_from(client, payload)


def _chain(payload: dict[str, object]) -> tuple[str, ...]:
    raw = payload.get("chain")
    if not raw:
        return ("Exception",)
    return tuple(str(item) for item in raw)  # type: ignore[union-attr]


def _exc_type(_client: object, payload: dict[str, object]) -> type[Exception]:
    return exception_type(str(payload.get("name")), _chain(payload))


def _error(_client: object, payload: dict[str, object]) -> None:
    raise_remote(str(payload.get("type")), _chain(payload), str(payload.get("message")))


_KINDS = {
    "value": _value,
    "notimplemented": _notimplemented,
    "list": _list,
    "tuple": _tuple,
    "dict": _dict,
    "class": _class,
    "obj": _wrap,
    "exc_type": _exc_type,
    "error": _error,
    "set": _set,
    "frozenset": _frozenset,
    "bytes": _bytes,
    "decimal": _decimal,
    "fraction": _fraction,
    "datetime": _datetime,
    "date": _date,
}


def interpret(client: object, payload: object) -> object:
    if not isinstance(payload, dict):
        raise EOFError("bad worker reply")
    handler = _KINDS.get(str(payload.get("kind")))
    if handler is None:
        raise EOFError("bad worker reply")
    return handler(client, payload)


def _encode_list(value: list[object]) -> dict[str, object]:
    return {"seq": [encode(item) for item in value]}


def _encode_tuple(value: tuple[object, ...]) -> dict[str, object]:
    return {"seq": [encode(item) for item in value], "tuple": True}


def _encode_map(value: dict[object, object]) -> dict[str, object]:
    return {"map": [[encode(key), encode(item)] for key, item in value.items()]}


def _encode_set(value: set[object]) -> dict[str, object]:
    return {"set": [encode(item) for item in value]}


def _encode_frozen(value: frozenset[object]) -> dict[str, object]:
    return {"set": [encode(item) for item in value], "frozen": True}


def _encode_bytes(value: bytes | bytearray) -> dict[str, str]:
    return {"bytes": base64.b64encode(bytes(value)).decode("ascii")}


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


def _encode_fallback(value: object) -> object:
    if isinstance(value, dict):
        return _encode_map(dict(value))
    if isinstance(value, tuple):
        return _encode_tuple(tuple(value))
    if isinstance(value, list):
        return _encode_list(list(value))
    if isinstance(value, deque):
        return _encode_list(list(value))
    return value


def encode(value: object) -> object:
    if isinstance(value, RemoteObject):
        return {"ref": value.oid}
    handler = _ENCODE.get(type(value))
    if handler is None:
        return _encode_fallback(value)
    return handler(value)


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
