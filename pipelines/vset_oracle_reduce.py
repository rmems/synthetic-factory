"""Rebuild standard-library values when they cross into the candidate child.

``assertEqual`` forwards to the child's ``__eq__``. A parent ``uuid.UUID``
must arrive as a real ``UUID``, not a field snapshot. ``__reduce_ex__`` is
used only when the callable lives in the standard library, every argument
encodes as data, and rebuilding it here reproduces the original value.
"""

from __future__ import annotations

import collections.abc
import io
import sys
from unittest import mock as _mock

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_reduce")
    from .vset_oracle_exc_lookup import load_module as _load_module
    from .vset_oracle_reduce_decode import _Skip as _Skip
    from .vset_oracle_reduce_decode import drop_slots as _drop_slots
    from .vset_oracle_reduce_decode import materialize as _materialize
    from .vset_oracle_reduce_decode import plain_tree as _plain_tree
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_reduce"
    )
    from vset_oracle_exc_lookup import load_module as _load_module
    from vset_oracle_reduce_decode import _Skip as _Skip
    from vset_oracle_reduce_decode import drop_slots as _drop_slots
    from vset_oracle_reduce_decode import materialize as _materialize
    from vset_oracle_reduce_decode import plain_tree as _plain_tree


def _known_module(module_name: object) -> bool:
    if not isinstance(module_name, str):
        return False
    if not module_name:
        return False
    return _load_module(module_name) is not None


def _ref(func: object) -> dict[str, str]:
    module_name = getattr(func, "__module__", None)
    qualname = getattr(func, "__qualname__", None)
    if not _known_module(module_name):
        raise _Skip
    if not isinstance(qualname, str):
        raise _Skip
    return {"m": str(module_name), "q": qualname}


def _class_arg(value: type) -> dict[str, object]:
    if not _known_module(value.__module__):
        raise _Skip
    return {"cls": {"m": value.__module__, "q": value.__qualname__}}


def _arg(value: object, encode: object) -> object:
    if isinstance(value, type):
        return _class_arg(value)
    encoded = encode(value)  # type: ignore[operator]
    if not _plain_tree(encoded):
        raise _Skip
    return _drop_slots(encoded)


def _span(spec: object) -> tuple[object, ...] | None:
    if not isinstance(spec, tuple):
        return None
    if len(spec) < 2:
        return None
    if len(spec) > 5:
        return None
    return spec


def _tail_clear(spec: tuple[object, ...]) -> bool:
    for item in spec[3:]:
        if item is not None:
            return False
    return True


def _parts(spec: object) -> tuple[object, tuple[object, ...], object]:
    found = _span(spec)
    if found is None:
        raise _Skip
    if not _tail_clear(found):
        raise _Skip
    args = found[1]
    if not isinstance(args, tuple):
        raise _Skip
    state = found[2] if len(found) > 2 else None
    return found[0], args, state


def _same(original: object, payload: dict[str, object]) -> bool:
    try:
        return bool(_materialize(payload) == original)
    except _Skip:
        return False


def _state_payload(state: object, encode: object) -> object:
    if isinstance(state, dict):
        return [[_arg(key, encode), _arg(item, encode)] for key, item in state.items()]
    return _arg(state, encode)


def _payload(func: object, args: tuple[object, ...], state: object, encode: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "reduce": _ref(func),
        "args": [_arg(item, encode) for item in args],
    }
    if state is not None:
        payload["state"] = _state_payload(state, encode)
    return payload


def _unsafe(value: object) -> bool:
    # reduce walks iterators and mocks, which consumes or fires them.
    if isinstance(value, collections.abc.Iterator):
        return True
    if isinstance(value, (_mock.Mock, io.IOBase)):
        return True
    return False


def _reducer(value: object) -> object | None:
    if _unsafe(value):
        return None
    if not _known_module(getattr(type(value), "__module__", None)):
        return None
    reduce = getattr(value, "__reduce_ex__", None)
    if not callable(reduce):
        return None
    return reduce


def _built(value: object, encode: object) -> dict[str, object] | None:
    reduce = _reducer(value)
    if reduce is None:
        return None
    try:
        func, args, state = _parts(reduce(4))  # type: ignore[operator]
    except Exception:
        return None
    return _payload(func, args, state, encode)


def reduce_payload(value: object, encode: object) -> dict[str, object] | None:
    """Return a child-rebuildable payload, or None when reduce is unsafe."""

    try:
        payload = _built(value, encode)
    except _Skip:
        return None
    if payload is None:
        return None
    if not _same(value, payload):
        return None
    return payload


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
