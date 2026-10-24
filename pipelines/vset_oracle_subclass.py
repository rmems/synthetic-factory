"""Parent subclasses of candidate classes.

Collection imports nothing under ``src/``. Grading does. A test class such
as ``class Square(shapes.Base)`` therefore has to be created here, while
``Base.__init__`` and any method the candidate calls on ``self`` still run
against the child object. ``super()`` from a parent method does not see
candidate methods: ``super()`` reads the parent MRO, not the child class.
"""

from __future__ import annotations

import sys

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_subclass")
    from .vset_oracle_codec import encode as _encode
    from .vset_oracle_subclass_bind import args_of as _args
    from .vset_oracle_subclass_bind import candidate as _candidate
    from .vset_oracle_subclass_bind import extend as _extend
    from .vset_oracle_subclass_bind import kwargs_of as _kwargs
    from .vset_oracle_subclass_bind import members as _members
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_subclass"
    )
    from vset_oracle_codec import encode as _encode
    from vset_oracle_subclass_bind import args_of as _args
    from vset_oracle_subclass_bind import candidate as _candidate
    from vset_oracle_subclass_bind import extend as _extend
    from vset_oracle_subclass_bind import kwargs_of as _kwargs
    from vset_oracle_subclass_bind import members as _members


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


def _invoke(cls: type, func: object, call: tuple[object, tuple[object, ...], dict[str, object]]) -> object:
    child, positional, named = call
    if child is None:
        if isinstance(func, classmethod):
            return func.__func__(cls, *positional, **named)
        bare = getattr(func, "__func__", func)
        return bare(*positional, **named)
    inst = _resolve(cls, child)
    if isinstance(func, property):
        return func.fget(inst)  # type: ignore[misc]
    return func(inst, *positional, **named)  # type: ignore[operator]


def _dispatcher(cls: type):
    def dispatch(name: object, child: object, args: object, kwargs: object) -> object:
        func = cls.__dict__[str(name)]
        return _invoke(cls, func, (child, _args(args), _kwargs(kwargs)))

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
    methods, attrs = _members(cls)
    callback = _values().remember_callback(_dispatcher(cls))
    created = client.exchange(  # type: ignore[attr-defined]
        {
            "op": "subclass",
            "base": base_oid,
            "name": cls.__name__,
            "methods": methods,
            "attrs": attrs,
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


def _construct(
    obj: object,
    target: tuple[object, int],
    incoming: tuple[tuple[object, ...], dict[str, object]],
) -> None:
    client, base = target
    args, kwargs = incoming
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
        _construct(obj, (client, base), (args, kwargs))
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
