"""Parent subclasses of candidate classes.

Collection imports nothing under ``src/``. Grading does. A test class such
as ``class Square(shapes.Base)`` therefore has to be created here, while
``Base.__init__`` and any method the candidate calls on ``self`` still run
against the child object. ``super()`` from a parent method does not see
candidate methods: ``super()`` reads the parent MRO, not the child class.
"""

from __future__ import annotations

import sys
import types

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_subclass")
    from .vset_oracle_codec import encode as _encode
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_subclass"
    )
    from vset_oracle_codec import encode as _encode


def _values():
    # vset_oracle_values imports this module. A top-level import would cycle.
    if __package__:  # pragma: no cover - package-child import path
        from . import vset_oracle_values as values
    else:
        import vset_oracle_values as values
    return values


_LIVE: dict[tuple[int, int], object] = {}


def clear_live() -> None:
    """Drop parent subclass instances from the previous child."""

    _LIVE.clear()


def _state(obj: object) -> dict[str, object] | None:
    try:
        found = object.__getattribute__(obj, "__dict__")
    except AttributeError:
        return None
    if isinstance(found, dict):
        return found
    return None  # pragma: no cover - instances expose a real dict or raise


def mark_ready(obj: object) -> None:
    """Remember that the child constructor has already finished."""

    try:
        object.__setattr__(obj, "_vset_ready", True)
    except (AttributeError, TypeError):
        return


def _ready(obj: object) -> bool:
    state = _state(obj)
    if state is None:
        return True
    return "_vset_ready" in state


def _bound(obj: object) -> bool:
    state = _state(obj)
    if state is None:
        return False
    return "oid" in state


def _client_from(cls: type) -> object | None:
    for base in cls.__mro__:
        client = base.__dict__.get("_vset_client")
        if client is not None:
            return client
    return None


def _candidate(cls: type) -> tuple[object, int] | None:
    for base in cls.__mro__[1:]:
        oid = base.__dict__.get("_vset_oid")
        client = base.__dict__.get("_vset_client")
        if isinstance(oid, int) and client is not None:
            return client, oid
    return None


def _extend(cls: type) -> tuple[object, int] | None:
    for base in cls.__mro__[1:]:
        child = base.__dict__.get("_vset_child")
        if isinstance(child, int):
            client = _client_from(base)
            if client is not None:
                return client, child
        oid = base.__dict__.get("_vset_oid")
        client = base.__dict__.get("_vset_client")
        if isinstance(oid, int) and client is not None:
            return client, oid
    return None


def _own_methods(cls: type) -> list[str]:
    names: list[str] = []
    for name, value in cls.__dict__.items():
        if name.startswith("_"):
            continue
        if isinstance(value, types.FunctionType):
            names.append(name)
    return names


def _encoded(values: tuple[object, ...] | object) -> list[object]:
    if isinstance(values, tuple):
        return [_encode(item) for item in values]
    return []


def _encoded_map(values: object) -> dict[str, object]:
    if not isinstance(values, dict):
        return {}
    return {str(key): _encode(item) for key, item in values.items()}


def _view(cls: type, child: object) -> object:
    state = _state(child)
    if state is None:
        return child
    inst = object.__new__(cls)
    object.__setattr__(inst, "client", state.get("client"))
    object.__setattr__(inst, "oid", state.get("oid"))
    mark_ready(inst)
    return inst


def _resolve(cls: type, child: object) -> object:
    state = _state(child)
    if state is None:
        return child
    client = state.get("client")
    oid = state.get("oid")
    if not isinstance(oid, int):
        return _view(cls, child)
    found = _LIVE.get((id(client), oid))
    if isinstance(found, cls):
        return found
    return _view(cls, child)


def _dispatcher(cls: type):
    def dispatch(name: object, child: object, args: object, kwargs: object) -> object:
        inst = _resolve(cls, child)
        func = cls.__dict__[str(name)]
        positional = args if isinstance(args, tuple) else ()
        named = kwargs if isinstance(kwargs, dict) else {}
        return func(inst, *positional, **named)

    return dispatch


def adopt(cls: type) -> None:
    """Build the child-side subclass that callbacks into ``cls``."""

    if "_vset_child" in cls.__dict__ or "_vset_adopting" in cls.__dict__:
        return
    found = _extend(cls)
    if found is None:
        return
    cls._vset_adopting = True  # type: ignore[attr-defined]
    client, base_oid = found
    callback = _values().remember_callback(_dispatcher(cls))
    created = client.exchange(  # type: ignore[attr-defined]
        {
            "op": "subclass",
            "base": base_oid,
            "name": cls.__name__,
            "methods": _own_methods(cls),
            "cb": callback,
        }
    )
    cls._vset_child = created._vset_oid  # type: ignore[attr-defined]


def _bare(cls: type, args: tuple[object, ...], kwargs: dict[str, object]) -> object:
    try:
        return object.__new__(cls)
    except TypeError:
        found = _candidate(cls)
        if found is None:
            raise
        client, oid = found
        return client.call(oid, args, kwargs)  # type: ignore[attr-defined]


def spawn(cls: type, args: tuple[object, ...], kwargs: dict[str, object]) -> object:
    """Allocate a child instance and return it as ``cls``."""

    child = cls.__dict__.get("_vset_child")
    found = _candidate(cls)
    if not isinstance(child, int) or found is None:
        return _bare(cls, args, kwargs)
    client, _base = found
    remote = client.exchange(  # type: ignore[attr-defined]
        {
            "op": "alloc",
            "oid": child,
            "args": _encoded(args),
            "kwargs": _encoded_map(kwargs),
        }
    )
    inst = object.__new__(cls)
    object.__setattr__(inst, "client", client)
    object.__setattr__(inst, "oid", remote.oid)
    _LIVE[(id(client), remote.oid)] = inst
    return inst


def _construct(obj: object, client: object, base: int, args: object, kwargs: object) -> None:
    remote = client.call(base, args, kwargs)  # type: ignore[attr-defined]
    object.__setattr__(obj, "client", client)
    object.__setattr__(obj, "oid", remote.oid)
    mark_ready(obj)
    _LIVE[(id(client), remote.oid)] = obj


def initialize(obj: object, args: tuple[object, ...], kwargs: dict[str, object]) -> None:
    """Run the candidate ``__init__`` once for a parent subclass instance."""

    if _ready(obj):
        return
    found = _candidate(type(obj))
    if found is None:
        return
    client, base = found
    if not _bound(obj):
        _construct(obj, client, base, args, kwargs)
        return
    client.exchange(  # type: ignore[attr-defined]
        {
            "op": "init",
            "oid": obj.oid,  # type: ignore[attr-defined]
            "base": base,
            "args": _encoded(args),
            "kwargs": _encoded_map(kwargs),
        }
    )
    mark_ready(obj)


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
