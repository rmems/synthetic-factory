"""Encode candidate values for the parent-side oracle.

Primitives and containers cross as data. Exception classes become real
exception types. Other objects stay remote and forward the operations
unittest and ordinary assertions use.
"""

from __future__ import annotations

import builtins
import sys

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_values")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_values"
    )

_EXC_TYPES: dict[tuple[str, str], type[Exception]] = {}
_CLASSES: dict[tuple[int, int], type] = {}
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


def _exception_base(name: str) -> type[Exception]:
    found = _builtin_exception(name)
    if found is None:
        return Exception
    return found


def exception_type(name: str, base_name: str) -> type[Exception]:
    """Return one real exception class for a candidate exception type."""

    key = (name, base_name)
    found = _EXC_TYPES.get(key)
    if found is not None:
        return found
    created = type(name, (_exception_base(base_name),), {})
    _EXC_TYPES[key] = created
    return created


def raise_remote(name: str, base_name: str, message: str) -> None:
    """Raise a candidate error without ever raising BaseException."""

    builtin = _builtin_exception(name)
    if builtin is not None:
        raise builtin(message)
    raise exception_type(name, base_name)(message)


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


def _class_for(client: object, oid: int, name: str) -> type:
    key = (id(client), oid)
    found = _CLASSES.get(key)
    if found is not None:
        return found

    def new(cls, *args, **kwargs):
        return client.call(oid, args, kwargs)  # type: ignore[attr-defined]

    created = type(name, (RemoteObject,), {"__new__": new})
    _CLASSES[key] = created
    return created


def _wrap(client: object, payload: dict[str, object]) -> RemoteObject:
    cls = _class_for(client, int(payload["cls"]), str(payload["name"]))
    obj = object.__new__(cls)
    object.__setattr__(obj, "client", client)
    object.__setattr__(obj, "oid", int(payload["oid"]))
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


def _class(client: object, payload: dict[str, object]) -> type:
    return _class_for(client, int(payload["oid"]), str(payload["name"]))


def _exc_type(_client: object, payload: dict[str, object]) -> type[Exception]:
    return exception_type(str(payload.get("name")), str(payload.get("base")))


def _base_name(payload: dict[str, object]) -> str:
    base = payload.get("base")
    if base:
        return str(base)
    return "Exception"


def _error(_client: object, payload: dict[str, object]) -> None:
    raise_remote(
        str(payload.get("type")),
        _base_name(payload),
        str(payload.get("message")),
    )


_KINDS = {
    "value": _value,
    "list": _list,
    "tuple": _tuple,
    "dict": _dict,
    "class": _class,
    "obj": _wrap,
    "exc_type": _exc_type,
    "error": _error,
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


def encode(value: object) -> object:
    if isinstance(value, RemoteObject):
        return {"ref": value.oid}
    if isinstance(value, list):
        return _encode_list(value)
    if isinstance(value, tuple):
        return _encode_tuple(value)
    if isinstance(value, dict):
        return _encode_map(value)
    return value


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
