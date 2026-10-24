"""Encode candidate values for the parent-side oracle.

Primitives and containers cross as data. Exception classes become real
exception types. Other objects stay remote and forward the operations
unittest and ordinary assertions use.
"""

from __future__ import annotations

import base64
import builtins
import dataclasses
import sys
from collections import Counter, OrderedDict, defaultdict, namedtuple
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import PurePath

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_values")
    from .vset_oracle_codec import apply_slots as _apply_slots
    from .vset_oracle_shape import blank_instance as _blank_instance
    from .vset_oracle_shape import builtin_type as _builtin_type
    from .vset_oracle_shape import parent_types as _parent_types
    from .vset_oracle_shape import remote_hash as _remote_hash
    from .vset_oracle_shape import truth as _truth
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_values"
    )
    from vset_oracle_codec import apply_slots as _apply_slots
    from vset_oracle_shape import blank_instance as _blank_instance
    from vset_oracle_shape import builtin_type as _builtin_type
    from vset_oracle_shape import parent_types as _parent_types
    from vset_oracle_shape import remote_hash as _remote_hash
    from vset_oracle_shape import truth as _truth

_EXC_TYPES: dict[tuple[str, tuple[str, ...]], type[Exception]] = {}
_EXC_OID: dict[tuple[int, int], type[Exception]] = {}
_CLASSES: dict[tuple[int, int], type] = {}
_OBJECTS: dict[tuple[int, int], RemoteObject] = {}
_SLOTS: dict[int, object] = {}
_CALLBACKS: dict[int, object] = {}
_NAMED: dict[tuple[str, tuple[str, ...]], type] = {}
_DATACLASSES: dict[tuple[int, int], type] = {}
_FACTORIES = {
    "int": int,
    "list": list,
    "set": set,
    "dict": dict,
    "float": float,
    "str": str,
    "tuple": tuple,
}
_FORWARDED = (
    "__eq__ __ne__ __lt__ __le__ __gt__ __ge__ __len__ __iter__ __next__ "
    "__contains__ __getitem__ __setitem__ __delitem__ "
    "__add__ __radd__ __sub__ __rsub__ __mul__ __rmul__ "
    "__truediv__ __rtruediv__ __floordiv__ __rfloordiv__ __mod__ __rmod__ "
    "__pow__ __neg__ __pos__ __abs__ __int__ __float__ __index__ "
    "__repr__ __str__ __format__ __enter__ __exit__ __reversed__ "
    "__iadd__ __isub__ __imul__ __itruediv__ __ifloordiv__ __imod__ "
    "__matmul__ __rmatmul__ __imatmul__ __divmod__ __rdivmod__ "
    "__and__ __rand__ __iand__ __or__ __ror__ __ior__ "
    "__xor__ __rxor__ __ixor__ __invert__ "
    "__lshift__ __rlshift__ __ilshift__ __rshift__ __rrshift__ __irshift__"
).split()
_STRICT = {
    "__enter__",
    "__exit__",
    "__repr__",
    "__str__",
    "__format__",
    "__iter__",
    "__next__",
    "__len__",
    "__getitem__",
    "__setitem__",
    "__delitem__",
    "__int__",
    "__float__",
    "__index__",
    "__reversed__",
}


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


def _exc_bases(client: object, info: dict[str, object]) -> tuple[type[Exception], ...]:
    raw = info.get("bases")
    if not isinstance(raw, list) or not raw:
        return (Exception,)
    bases = [exc_from(client, item) for item in raw if isinstance(item, dict)]
    if not bases:
        return (Exception,)
    return tuple(bases)


def exc_from(client: object, info: dict[str, object]) -> type[Exception]:
    """One parent class per candidate exception class, keyed by child identity."""

    builtin_name = info.get("builtin")
    if isinstance(builtin_name, str):
        builtin = _builtin_exception(builtin_name)
        if builtin is not None:
            return builtin
        return Exception
    key = (id(client), int(info.get("oid") or -1))
    found = _EXC_OID.get(key)
    if found is not None:
        return found
    created = type(str(info.get("name") or "Error"), _exc_bases(client, info), {})
    _EXC_OID[key] = created
    return created


def raise_remote(
    cls: type[Exception],
    args: tuple[object, ...],
    attrs: dict[str, object],
) -> None:
    """Raise a candidate error without ever raising BaseException."""

    exc = cls(*args)
    for key, value in attrs.items():
        setattr(exc, key, value)
    raise exc


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

    def __delattr__(self, name: str) -> None:
        if name == "client":
            object.__delattr__(self, name)
            return
        if name == "oid":
            object.__delattr__(self, name)
            return
        self.client.delete_attr(self.oid, name)

    def __bool__(self) -> bool:
        return _truth(self)

    def __hash__(self) -> int:
        return _remote_hash(self)


def _forward(name: str):
    def method(self: RemoteObject, *args: object) -> object:
        try:
            func = self.client.get(self.oid, name)
        except AttributeError:
            if name in _STRICT:
                raise TypeError(name) from None
            return NotImplemented
        return func(*args)

    method.__name__ = name
    return method


for _name in _FORWARDED:
    setattr(RemoteObject, _name, _forward(_name))


def _namespace(client: object, oid: int) -> dict[str, object]:
    def new(cls: type, *args: object, **kwargs: object) -> object:
        return client.call(oid, args, kwargs)  # type: ignore[attr-defined]

    return {"__new__": new}


class _RemoteMeta(type):
    """Forwards class attributes to the candidate class."""

    def __getattr__(cls, name: str) -> object:
        client = cls.__dict__.get("_vset_client")
        if client is None:
            raise AttributeError(name)
        oid = cls.__dict__.get("_vset_oid")
        if oid is None:
            raise AttributeError(name)
        return client.get(oid, name)

    def __setattr__(cls, name: str, value: object) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
            return
        client = cls.__dict__.get("_vset_client")
        if client is None:
            super().__setattr__(name, value)
            return
        oid = cls.__dict__.get("_vset_oid")
        if oid is None:
            super().__setattr__(name, value)
            return
        client.set_attr(oid, name, value)
        super().__setattr__(name, value)

    def __delattr__(cls, name: str) -> None:
        if name.startswith("_"):
            super().__delattr__(name)
            return
        client = cls.__dict__.get("_vset_client")
        if client is None:
            super().__delattr__(name)
            return
        oid = cls.__dict__.get("_vset_oid")
        if oid is None:
            super().__delattr__(name)
            return
        client.delete_attr(oid, name)
        try:
            super().__delattr__(name)
        except AttributeError:
            return


def _class_from(client: object, info: dict[str, object]) -> type:
    builtin = _builtin_type(info)
    if builtin is not None:
        return builtin
    oid = int(info["oid"])
    key = (id(client), oid)
    found = _CLASSES.get(key)
    if found is not None:
        return found
    created = _RemoteMeta(
        str(info["name"]), tuple(_parent_types(client, info)), _namespace(client, oid)
    )
    _CLASSES[key] = created
    created._vset_client = client  # type: ignore[attr-defined]
    created._vset_oid = oid  # type: ignore[attr-defined]
    return created


def reset_identity() -> None:
    """Drop remote objects from the previous child."""

    _OBJECTS.clear()
    _CLASSES.clear()
    _SLOTS.clear()
    _CALLBACKS.clear()
    _NAMED.clear()
    _DATACLASSES.clear()
    _EXC_OID.clear()


def remember_callback(value: object) -> int:
    """Keep a parent object the child can call back into."""

    key = id(value)
    _CALLBACKS[key] = value
    return key


def take_callback(key: int) -> object:
    found = _CALLBACKS.get(key)
    if found is None:
        raise KeyError(key)
    return found


def _track(value: object) -> int:
    slot = id(value)
    _SLOTS[slot] = value
    return slot


def _wrap(client: object, payload: dict[str, object]) -> RemoteObject:
    oid = int(payload["oid"])
    key = (id(client), oid)
    found = _OBJECTS.get(key)
    if found is not None:
        return found
    cls = _class_from(client, payload["cls"])  # type: ignore[arg-type]
    obj = _blank_instance(cls)
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


def _synced(client: object, payload: dict[str, object]) -> object:
    _apply_slots(client, payload.get("states"))
    return interpret(client, payload["value"])


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


def _complex(_client: object, payload: dict[str, object]) -> complex:
    return complex(payload["real"], payload["imag"])  # type: ignore[arg-type]


def _range(_client: object, payload: dict[str, object]) -> range:
    return range(int(payload["start"]), int(payload["stop"]), int(payload["step"]))


def _slice(_client: object, payload: dict[str, object]) -> slice:
    start = payload.get("start")
    stop = payload.get("stop")
    step = payload.get("step")
    return slice(start, stop, step)  # type: ignore[arg-type]


def _timedelta(_client: object, payload: dict[str, object]) -> timedelta:
    return timedelta(int(payload["days"]), int(payload["seconds"]), int(payload["micro"]))


def _time(_client: object, payload: dict[str, object]) -> time:
    return time.fromisoformat(str(payload["data"]))


def _path(_client: object, payload: dict[str, object]) -> PurePath:
    name = str(payload.get("cls") or "")
    cls = getattr(sys.modules["pathlib"], name, None)
    if not isinstance(cls, type):
        return PurePath(str(payload.get("data")))
    return cls(str(payload.get("data")))


def _mapped(client: object, payload: dict[str, object]) -> dict[object, object]:
    pairs = payload.get("items")
    if not isinstance(pairs, list):
        return {}
    return {interpret(client, pair[0]): interpret(client, pair[1]) for pair in pairs}


def _counter(client: object, payload: dict[str, object]) -> Counter[object]:
    return Counter(_mapped(client, payload))


def _ordered(client: object, payload: dict[str, object]) -> OrderedDict[object, object]:
    return OrderedDict(_mapped(client, payload))


def _default(client: object, payload: dict[str, object]) -> defaultdict[object, object]:
    factory = _FACTORIES.get(str(payload.get("factory") or ""))
    return defaultdict(factory, _mapped(client, payload))


def _namedtuple(client: object, payload: dict[str, object]) -> tuple[object, ...]:
    raw_fields = payload.get("fields")
    fields = tuple(str(item) for item in raw_fields) if isinstance(raw_fields, list) else ()
    name = str(payload.get("name") or "Record")
    key = (name, fields)
    cls = _NAMED.get(key)
    if cls is None:
        cls = namedtuple(name, fields)  # type: ignore[misc]
        _NAMED[key] = cls
    raw_items = payload.get("items")
    items = raw_items if isinstance(raw_items, list) else []
    return cls(*(interpret(client, item) for item in items))


def _dataclass(client: object, payload: dict[str, object]) -> object:
    raw = payload.get("fields")
    fields = raw if isinstance(raw, dict) else {}
    key = (id(client), int(payload.get("oid") or 0))
    cls = _DATACLASSES.get(key)
    if cls is None:
        cls = dataclasses.make_dataclass(
            str(payload.get("name") or "Record"),
            [(str(name), object) for name in fields],
        )
        _DATACLASSES[key] = cls
    values = {str(name): interpret(client, item) for name, item in fields.items()}
    return cls(**values)


def _callback(_client: object, payload: dict[str, object]) -> object:
    return take_callback(int(payload["cb"]))


def _class(client: object, payload: dict[str, object]) -> type:
    return _class_from(client, payload)


def _chain(payload: dict[str, object]) -> tuple[str, ...]:
    raw = payload.get("chain")
    if not raw:
        return ("Exception",)
    return tuple(str(item) for item in raw)  # type: ignore[union-attr]


def _exc_type(client: object, payload: dict[str, object]) -> type[Exception]:
    if "builtin" in payload or "oid" in payload:
        return exc_from(client, payload)
    return exception_type(str(payload.get("name")), _chain(payload))


def _items(client: object, payload: dict[str, object], key: str) -> tuple[object, ...]:
    raw = payload.get(key)
    if not raw:
        return ()
    return tuple(interpret(client, item) for item in raw)  # type: ignore[union-attr]


def _attrs(client: object, payload: dict[str, object]) -> dict[str, object]:
    raw = payload.get("attrs")
    if not isinstance(raw, dict):
        return {}
    return {str(key): interpret(client, value) for key, value in raw.items()}


def _error_class(client: object, payload: dict[str, object]) -> type[Exception]:
    info = payload.get("exc")
    if isinstance(info, dict):
        return exc_from(client, info)
    return exception_type(str(payload.get("type")), _chain(payload))


def _error(client: object, payload: dict[str, object]) -> None:
    raise_remote(
        _error_class(client, payload),
        _items(client, payload, "args"),
        _attrs(client, payload),
    )


_KINDS = {
    "value": _value, "synced": _synced, "notimplemented": _notimplemented,
    "list": _list, "tuple": _tuple, "dict": _dict, "set": _set,
    "frozenset": _frozenset, "bytes": _bytes, "class": _class, "obj": _wrap,
    "exc_type": _exc_type, "error": _error, "decimal": _decimal,
    "fraction": _fraction, "datetime": _datetime, "date": _date, "cb": _callback,
    "complex": _complex, "range": _range, "slice": _slice, "timedelta": _timedelta,
    "time": _time, "path": _path, "counter": _counter, "ordered": _ordered,
    "default": _default, "namedtuple": _namedtuple, "dataclass": _dataclass,
}


def interpret(client: object, payload: object) -> object:
    if not isinstance(payload, dict):
        raise EOFError("bad worker reply")
    handler = _KINDS.get(str(payload.get("kind")))
    if handler is None:
        raise EOFError("bad worker reply")
    return handler(client, payload)


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
