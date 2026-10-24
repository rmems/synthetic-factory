"""Parent-side check for comparisons against candidate objects.

An affirmative ``__eq__`` or ordering result is a pass channel when the
other operand is a parent value: the child can answer True, then False.
Builtin and standard-library comparisons are real data comparisons. A
candidate class must also hold plain data that agrees with the answer.
"""

from __future__ import annotations

import operator
import sys

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_compare")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_compare"
    )


_CHECKED = frozenset({"__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__"})
_ORDER = {
    "__lt__": operator.lt,
    "__le__": operator.le,
    "__gt__": operator.gt,
    "__ge__": operator.ge,
}


def _affirms(result: object) -> bool:
    if result is NotImplemented:
        return False
    return bool(result)


def preview(obj: object, name: str) -> dict[str, object] | None:
    """Read plain fields before the candidate comparison can change them."""

    if name not in _CHECKED:
        return None
    try:
        found = obj.client.exchange({"op": "state", "oid": obj.oid})  # type: ignore[attr-defined]
    except Exception:
        return None
    if isinstance(found, dict):
        return found
    return None


def _same(left: object, right: object) -> bool:
    try:
        return bool(left == right)
    except Exception:
        return False


def _one_field(fields: dict[str, object], other: object) -> bool:
    for item in fields.values():
        if _same(item, other):
            return True
    return False


def _equal_data(fields: dict[str, object], other: object) -> bool:
    if _one_field(fields, other):
        return True
    values = tuple(fields.values())
    if not values:
        return False
    return _same(values, other)


def _comparable(op: object, item: object, other: object) -> bool:
    try:
        op(item, other)  # type: ignore[operator]
    except TypeError:
        return False
    return True


def _ordered(name: str, fields: dict[str, object], other: object) -> bool:
    op = _ORDER[name]
    comparable = [item for item in fields.values() if _comparable(op, item, other)]
    if not comparable:
        return False
    for item in comparable:
        if not op(item, other):
            return False
    return True


def _agrees(name: str, fields: dict[str, object], other: object) -> bool:
    if name == "__ne__":
        return not _equal_data(fields, other)
    if name == "__eq__":
        return _equal_data(fields, other)
    return _ordered(name, fields, other)


def _user_defined(info: dict[str, object], name: str) -> bool:
    user = info.get("user")
    if not isinstance(user, list):
        return False
    return name in user


def _agreed(name: str, info: dict[str, object], result: object, other: object) -> object:
    fields = info.get("fields")
    if not isinstance(fields, dict):
        return NotImplemented
    if _agrees(name, fields, other):
        return result
    return NotImplemented


def decide(name: str, result: object, info: dict[str, object] | None, other: object) -> object:
    """Keep a candidate comparison only when its data agrees."""

    if info is None:
        return result
    if not _affirms(result):
        return result
    if not _user_defined(info, name):
        return result
    return _agreed(name, info, result, other)


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
