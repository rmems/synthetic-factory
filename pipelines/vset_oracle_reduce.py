"""Rebuild standard-library values when they cross into the candidate child.

``assertEqual`` forwards to the child's ``__eq__``. A parent ``uuid.UUID``
must arrive as a real ``UUID``, not a field snapshot. ``__reduce_ex__`` is
used only when the callable lives in the standard library, every argument
encodes as data, and rebuilding it here reproduces the original value.
"""

from __future__ import annotations

import base64
import collections.abc
import importlib
import io
import sys
from unittest import mock as _mock

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_reduce")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_reduce"
    )


class _Skip(Exception):
    """This value stays on the ordinary encode path."""


def _stdlib_module(module_name: object) -> bool:
    if not isinstance(module_name, str) or not module_name:
        return False
    return module_name.split(".", 1)[0] in sys.stdlib_module_names


def _load(ref: object) -> object:
    if not isinstance(ref, dict):
        raise _Skip
    module_name = ref.get("m")
    qualname = ref.get("q")
    if not _stdlib_module(module_name) or not isinstance(qualname, str):
        raise _Skip
    found: object = importlib.import_module(str(module_name))
    for part in qualname.split("."):
        found = getattr(found, part, None)
        if found is None:
            raise _Skip
    return found


def _ref(func: object) -> dict[str, str]:
    module_name = getattr(func, "__module__", None)
    qualname = getattr(func, "__qualname__", None)
    if not _stdlib_module(module_name) or not isinstance(qualname, str):
        raise _Skip
    return {"m": str(module_name), "q": qualname}


def _plain_tree(encoded: object) -> bool:
    if encoded is None or type(encoded) in {bool, int, float, str}:
        return True
    if isinstance(encoded, list):
        return all(_plain_tree(item) for item in encoded)
    if isinstance(encoded, dict):
        if "cb" in encoded or "ref" in encoded:
            return False
        kept = [item for key, item in encoded.items() if key != "slot"]
        return all(_plain_tree(item) for item in kept)
    return False


def _drop_slots(encoded: object) -> object:
    if isinstance(encoded, list):
        return [_drop_slots(item) for item in encoded]
    if isinstance(encoded, dict):
        return {key: _drop_slots(item) for key, item in encoded.items() if key != "slot"}
    return encoded


def _arg(value: object, encode: object) -> object:
    if isinstance(value, type):
        if not _stdlib_module(value.__module__):
            raise _Skip
        return {"cls": {"m": value.__module__, "q": value.__qualname__}}
    encoded = encode(value)  # type: ignore[operator]
    if not _plain_tree(encoded):
        raise _Skip
    return _drop_slots(encoded)


def _parts(spec: object) -> tuple[object, tuple[object, ...], object]:
    if not isinstance(spec, tuple) or not 2 <= len(spec) <= 5:
        raise _Skip
    if len(spec) > 3 and spec[3] is not None:
        raise _Skip
    if len(spec) > 4 and spec[4] is not None:
        raise _Skip
    args = spec[1]
    if not isinstance(args, tuple):
        raise _Skip
    state = spec[2] if len(spec) > 2 else None
    return spec[0], args, state


def _decode(encoded: object) -> object:
    if not isinstance(encoded, dict):
        return encoded
    if "cls" in encoded:
        return _load(encoded["cls"])
    if "bytes" in encoded:
        return base64.b64decode(str(encoded["bytes"]))
    if "seq" in encoded:
        items = [_decode(item) for item in encoded["seq"]]  # type: ignore[union-attr]
        if encoded.get("tuple"):
            return tuple(items)
        return items
    if "reduce" in encoded:
        return _materialize(encoded)
    raise _Skip


def _apply_state(obj: object, payload: dict[str, object]) -> None:
    if "state" not in payload:
        return
    raw = payload["state"]
    if isinstance(raw, list):
        state: object = {_decode(pair[0]): _decode(pair[1]) for pair in raw}
    else:
        state = _decode(raw)
    setter = getattr(obj, "__setstate__", None)
    if setter is not None:
        setter(state)
        return
    if isinstance(state, dict):
        obj.__dict__.update(state)
        return
    raise _Skip


def _materialize(payload: dict[str, object]) -> object:
    func = _load(payload.get("reduce"))
    args = payload.get("args")
    if not isinstance(args, list):
        raise _Skip
    obj = func(*tuple(_decode(item) for item in args))  # type: ignore[operator]
    _apply_state(obj, payload)
    return obj


def _same(original: object, payload: dict[str, object]) -> bool:
    try:
        return bool(_materialize(payload) == original)
    except _Skip:
        return False


def _payload(func: object, args: tuple[object, ...], state: object, encode: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "reduce": _ref(func),
        "args": [_arg(item, encode) for item in args],
    }
    if isinstance(state, dict):
        payload["state"] = [[_arg(key, encode), _arg(item, encode)] for key, item in state.items()]
    elif state is not None:
        payload["state"] = _arg(state, encode)
    return payload


def _unsafe(value: object) -> bool:
    # reduce walks iterators and mocks, which consumes or fires them.
    if isinstance(value, collections.abc.Iterator):
        return True
    if isinstance(value, (_mock.Mock, io.IOBase)):
        return True
    return False


def reduce_payload(value: object, encode: object) -> dict[str, object] | None:
    """Return a child-rebuildable payload, or None when reduce is unsafe."""

    if _unsafe(value):
        return None
    if not _stdlib_module(getattr(type(value), "__module__", None)):
        return None
    reduce = getattr(value, "__reduce_ex__", None)
    if not callable(reduce):
        return None
    try:
        func, args, state = _parts(reduce(4))
        payload = _payload(func, args, state, encode)
    except _Skip:
        return None
    except Exception:
        return None
    if not _same(value, payload):
        return None
    return payload


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
