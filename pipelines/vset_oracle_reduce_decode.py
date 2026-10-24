"""Decode a standard-library reduce payload back into a parent value.

The module name has to be one this grader already named. A child-chosen
string is not passed to ``importlib``.
"""

from __future__ import annotations

import base64
import sys

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_reduce_decode")
    from .vset_oracle_exc_lookup import load_module as load_module
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_reduce_decode"
    )
    from vset_oracle_exc_lookup import load_module as load_module


class _Skip(Exception):
    """This value stays on the ordinary encode path."""


def _walk(found: object, qualname: str) -> object:
    for part in qualname.split("."):
        found = getattr(found, part, None)
        if found is None:
            raise _Skip
    return found


def load_qualified(module_name: object, qualname: object) -> object:
    if not isinstance(module_name, str):
        raise _Skip
    if not isinstance(qualname, str):
        raise _Skip
    found = load_module(module_name)
    if found is None:
        raise _Skip
    return _walk(found, qualname)


def _scalar(encoded: object) -> bool:
    if encoded is None:
        return True
    return type(encoded) in {bool, int, float, str}


def _plain_list(encoded: list[object]) -> bool:
    for item in encoded:
        if not plain_tree(item):
            return False
    return True


def _plain_dict(encoded: dict[object, object]) -> bool:
    if "cb" in encoded:
        return False
    if "ref" in encoded:
        return False
    for key, item in encoded.items():
        if key == "slot":
            continue
        if not plain_tree(item):
            return False
    return True


def plain_tree(encoded: object) -> bool:
    if _scalar(encoded):
        return True
    if isinstance(encoded, list):
        return _plain_list(encoded)
    if isinstance(encoded, dict):
        return _plain_dict(encoded)
    return False


def _drop_list(encoded: list[object]) -> list[object]:
    return [drop_slots(item) for item in encoded]


def _drop_item(key: object, item: object) -> tuple[object, object] | None:
    if key == "slot":
        return None
    return key, drop_slots(item)


def _drop_dict(encoded: dict[object, object]) -> dict[object, object]:
    kept: dict[object, object] = {}
    for key, item in encoded.items():
        pair = _drop_item(key, item)
        if pair is None:
            continue
        kept[pair[0]] = pair[1]
    return kept


def drop_slots(encoded: object) -> object:
    if isinstance(encoded, list):
        return _drop_list(encoded)
    if isinstance(encoded, dict):
        return _drop_dict(encoded)
    return encoded


def _decode_seq(encoded: dict[str, object]) -> object:
    raw = encoded.get("seq")
    items = raw if isinstance(raw, list) else []
    decoded = [decode(item) for item in items]
    if encoded.get("tuple"):
        return tuple(decoded)
    return decoded


def _class_ref(info: object) -> tuple[object, object]:
    if not isinstance(info, dict):
        return None, None
    return info.get("m"), info.get("q")


def _decode_class(encoded: dict[str, object]) -> object:
    module_name, qualname = _class_ref(encoded.get("cls"))
    return load_qualified(module_name, qualname)


def _decode_payload(encoded: dict[str, object]) -> object:
    if "bytes" in encoded:
        return base64.b64decode(str(encoded["bytes"]))
    if "seq" in encoded:
        return _decode_seq(encoded)
    if "reduce" in encoded:
        return materialize(encoded)
    raise _Skip


def decode(encoded: object) -> object:
    if not isinstance(encoded, dict):
        return encoded
    if "cls" in encoded:
        return _decode_class(encoded)
    return _decode_payload(encoded)


def _state_map(raw: object) -> object:
    if isinstance(raw, list):
        return {decode(pair[0]): decode(pair[1]) for pair in raw}
    return decode(raw)


def apply_state(obj: object, payload: dict[str, object]) -> None:
    if "state" not in payload:
        return
    state = _state_map(payload["state"])
    setter = getattr(obj, "__setstate__", None)
    if setter is not None:
        setter(state)
        return
    if isinstance(state, dict):
        obj.__dict__.update(state)
        return
    raise _Skip


def materialize(payload: dict[str, object]) -> object:
    func = load_qualified_reduce(payload.get("reduce"))
    args = payload.get("args")
    if not isinstance(args, list):
        raise _Skip
    obj = func(*tuple(decode(item) for item in args))  # type: ignore[operator]
    apply_state(obj, payload)
    return obj


def load_qualified_reduce(ref: object) -> object:
    if not isinstance(ref, dict):
        raise _Skip
    return load_qualified(ref.get("m"), ref.get("q"))


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
