"""Encode candidate values for the parent-side oracle.

Primitives and containers cross as data. Exception classes become real
exception types. Other objects stay remote and forward the operations
unittest and ordinary assertions use.
"""

from __future__ import annotations

import base64
import sys
from collections import Counter, OrderedDict, defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import PurePath

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_values")
    from .vset_oracle_codec import apply_slots as _apply_slots
    from .vset_oracle_exc import clear_exception_oids as _clear_exception_oids
    from .vset_oracle_exc import exc_from as exc_from
    from .vset_oracle_exc import exception_type as exception_type
    from .vset_oracle_exc import raise_remote as raise_remote
    from .vset_oracle_rebuild import clear_named as _clear_named
    from .vset_oracle_rebuild import rebuild_namedtuple as _rebuild_namedtuple
    from .vset_oracle_shape import attach_dataclass_fields as _attach_dataclass_fields
    from .vset_oracle_shape import blank_instance as _blank_instance
    from .vset_oracle_shape import builtin_type as _builtin_type
    from .vset_oracle_shape import container_proxy as _container_proxy
    from .vset_oracle_shape import parent_types as _parent_types
    from .vset_oracle_shape import remote_hash as _remote_hash
    from .vset_oracle_shape import truth as _truth
    from . import vset_oracle_compare as _compare
    from . import vset_oracle_subclass as _subclass
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_values"
    )
    from vset_oracle_codec import apply_slots as _apply_slots
    from vset_oracle_exc import clear_exception_oids as _clear_exception_oids
    from vset_oracle_exc import exc_from as exc_from
    from vset_oracle_exc import exception_type as exception_type
    from vset_oracle_exc import raise_remote as raise_remote
    from vset_oracle_rebuild import clear_named as _clear_named
    from vset_oracle_rebuild import rebuild_namedtuple as _rebuild_namedtuple
    from vset_oracle_shape import attach_dataclass_fields as _attach_dataclass_fields
    from vset_oracle_shape import blank_instance as _blank_instance
    from vset_oracle_shape import builtin_type as _builtin_type
    from vset_oracle_shape import container_proxy as _container_proxy
    from vset_oracle_shape import parent_types as _parent_types
    from vset_oracle_shape import remote_hash as _remote_hash
    from vset_oracle_shape import truth as _truth
    import vset_oracle_compare as _compare
    import vset_oracle_subclass as _subclass

_CLASSES: dict[tuple[int, int], type] = {}
_OBJECTS: dict[tuple[int, int], RemoteObject] = {}
_SLOTS: dict[int, object] = {}
_CALLBACKS: dict[int, object] = {}
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
_HELD = frozenset({"client", "oid", "_vset_ready"})
_DIFFERENCE = frozenset({"__sub__", "__rsub__"})
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


class RemoteObject:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if "_vset_remote_new" in cls.__dict__:
            return
        _subclass.adopt(cls)

    def __init__(self, *args: object, **kwargs: object) -> None:
        _subclass.initialize(self, args, kwargs)

    def __call__(self, *args: object, **kwargs: object) -> object:
        return self.client.call(self.oid, args, kwargs)

    def __getattribute__(self, name: str) -> object:
        if name in _HELD or name.startswith("_"):
            return object.__getattribute__(self, name)
        cls = object.__getattribute__(self, "__class__")
        if _boxed_method(cls, name):
            client = object.__getattribute__(self, "client")
            oid = object.__getattribute__(self, "oid")
            return client.get(oid, name)
        return object.__getattribute__(self, name)

    def __getattr__(self, name: str) -> object:
        return self.client.get(self.oid, name)

    def __setattr__(self, name: str, value: object) -> None:
        if name in _HELD:
            object.__setattr__(self, name, value)
            return
        self.client.set_attr(self.oid, name, value)

    def __delattr__(self, name: str) -> None:
        if name in _HELD:
            object.__delattr__(self, name)
            return
        self.client.delete_attr(self.oid, name)

    def __bool__(self) -> bool:
        return _truth(self)

    def __hash__(self) -> int:
        return _remote_hash(self)


_BOXES = frozenset({list, dict, set, frozenset, tuple, bytearray})


def _parent_difference(name: str, args: tuple[object, ...]) -> bool:
    # assertAlmostEqual subtracts in the parent. A candidate __sub__ must not
    # supply that distance when the other operand is a parent value.
    if name not in _DIFFERENCE:
        return False
    if not args:
        return True
    return not isinstance(args[0], RemoteObject)


def _boxed_method(cls: type, name: str) -> bool:
    if name in cls.__dict__ or name in RemoteObject.__dict__:
        return False
    for base in cls.__mro__:
        if base in _BOXES and name in base.__dict__:
            return True
    return False


def _parent_operand(args: tuple[object, ...]) -> object | None:
    if not args:
        return None
    other = args[0]
    if isinstance(other, RemoteObject):
        return None
    return other


def _missing(name: str) -> object:
    if name in _STRICT:
        raise TypeError(name)
    return NotImplemented


def _forward(name: str):
    def method(self: RemoteObject, *args: object) -> object:
        if _parent_difference(name, args):
            return NotImplemented
        try:
            func = self.client.get(self.oid, name)
        except AttributeError:
            return _missing(name)
        other = _parent_operand(args)
        info = None
        if other is not None:
            info = _compare.preview(self, name)
        return _compare.decide(name, func(*args), info, args[0] if args else None)

    method.__name__ = name
    return method


for _name in _FORWARDED:
    setattr(RemoteObject, _name, _forward(_name))


def _namespace(client: object, oid: int) -> dict[str, object]:
    def new(cls: type, *args: object, **kwargs: object) -> object:
        if cls.__dict__.get("_vset_oid") == oid:
            return client.call(oid, args, kwargs)  # type: ignore[attr-defined]
        return _subclass.spawn(cls, args, kwargs)

    return {"__new__": new, "_vset_remote_new": True}


def _class_bookkeeping(name: str) -> bool:
    if name.startswith("_vset_"):
        return True
    return name.startswith("__") and name.endswith("__")


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
        if _class_bookkeeping(name):
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
        if _class_bookkeeping(name):
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
        proxy = _container_proxy(builtin)
        if proxy is not None:
            return proxy
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
    _attach_dataclass_fields(created, info)
    return created


def reset_identity() -> None:
    """Drop remote objects from the previous child."""

    _OBJECTS.clear()
    _CLASSES.clear()
    _SLOTS.clear()
    _CALLBACKS.clear()
    _subclass.clear_live()
    _clear_named()
    _clear_exception_oids()


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
    _subclass.mark_ready(obj)
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


def _path_type(name: str) -> type[PurePath]:
    found = getattr(sys.modules["pathlib"], name, None)
    if isinstance(found, type) and issubclass(found, PurePath):
        return found
    return PurePath


def _path(_client: object, payload: dict[str, object]) -> PurePath:
    return _path_type(str(payload.get("cls") or ""))(str(payload.get("data")))


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
    if "module" in payload:
        return exc_from(client, payload)
    if "builtin" in payload:
        return exc_from(client, payload)
    if "oid" in payload:
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


def _compare_state(client: object, payload: dict[str, object]) -> dict[str, object]:
    raw = payload.get("fields")
    fields: dict[str, object] = {}
    if isinstance(raw, dict):
        for key, value in raw.items():
            fields[str(key)] = interpret(client, value)
    user = payload.get("user")
    names = [str(item) for item in user] if isinstance(user, list) else []
    return {"fields": fields, "user": names}


def _alias(_client: object, payload: dict[str, object]) -> object:
    found = _SLOTS.get(int(payload["slot"]))
    if found is None:
        raise EOFError("bad worker reply")
    return found


def _error(client: object, payload: dict[str, object]) -> None:
    _apply_slots(client, payload.get("states"))
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
    "default": _default, "namedtuple": _rebuild_namedtuple,
    "state": _compare_state, "alias": _alias,
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
