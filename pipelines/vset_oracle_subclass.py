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
    from .vset_oracle_subclass_bind import candidate as _candidate
    from .vset_oracle_subclass_bind import extend as _extend
    from .vset_oracle_subclass_bind import members as _members
    from . import vset_oracle_subclass_call as _call
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_subclass"
    )
    from vset_oracle_codec import encode as _encode
    from vset_oracle_subclass_bind import candidate as _candidate
    from vset_oracle_subclass_bind import extend as _extend
    from vset_oracle_subclass_bind import members as _members
    import vset_oracle_subclass_call as _call


def _values():
    # vset_oracle_values imports this module. A top-level import would cycle.
    if __package__:  # pragma: no cover - package-child import path
        from . import vset_oracle_values as values
    else:
        import vset_oracle_values as values
    return values


def clear_live() -> None:
    """Drop parent subclass instances from the previous child."""

    _call.clear_live()


def mark_ready(obj: object) -> None:
    """Remember that the child constructor has already finished."""

    _call.mark_ready(obj)


def _encoded(values: tuple[object, ...] | object) -> list[object]:
    if isinstance(values, tuple):
        return [_encode(item) for item in values]
    return []


def _encoded_map(values: object) -> dict[str, object]:
    if not isinstance(values, dict):
        return {}
    return {str(key): _encode(item) for key, item in values.items()}


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
    callback = _values().remember_callback(_call.dispatcher(cls))
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
    _call.remember(client, remote.oid, inst)
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
    _call.remember(client, remote.oid, obj)


def initialize(obj: object, args: tuple[object, ...], kwargs: dict[str, object]) -> None:
    """Run the candidate ``__init__`` once for a parent subclass instance."""

    if _call._ready(obj):
        return
    found = _candidate(type(obj))
    if found is None:
        return
    client, base = found
    if not _call._bound(obj):
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
