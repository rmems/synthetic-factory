"""Dispatch a candidate call back onto the parent subclass.

Kept apart from construction so each file stays under the complexity gate.
"""

from __future__ import annotations

import sys

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_subclass_call")
    from .vset_oracle_subclass_bind import args_of as _args
    from .vset_oracle_subclass_bind import kwargs_of as _kwargs
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_subclass_call"
    )
    from vset_oracle_subclass_bind import args_of as _args
    from vset_oracle_subclass_bind import kwargs_of as _kwargs


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


def remember(client: object, oid: object, inst: object) -> None:
    """Keep the parent instance that owns this child object id."""

    if isinstance(oid, int):
        _LIVE[(id(client), oid)] = inst


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


def _invoke(
    cls: type,
    func: object,
    call: tuple[object, tuple[object, ...], dict[str, object]],
) -> object:
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


def dispatcher(cls: type):
    """Callback the child uses to run one parent override."""

    def dispatch(name: object, child: object, args: object, kwargs: object) -> object:
        func = cls.__dict__[str(name)]
        return _invoke(cls, func, (child, _args(args), _kwargs(kwargs)))

    return dispatch


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
