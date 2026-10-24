"""Parent-side check for comparisons against candidate objects.

An affirmative ``__eq__`` or ordering result is a pass channel when the
other operand is a parent value: the child can answer True for every
input. Builtin and standard-library comparisons are real data comparisons.
A candidate comparison is kept when every plain field of the operand's
kind agrees with that value, or when the tuple of fields is the operand.
Fields of another kind, such as a currency string beside an amount, are
not part of that check. One matching number among many numbers is not
agreement: the candidate can plant every expected answer.
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


_CHECKED = frozenset({"__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__", "__contains__"})
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


def _closed(name: str) -> dict[str, object]:
    return {"fields": {}, "user": [name]}


def _state(obj: object, name: str) -> dict[str, object]:
    try:
        found = obj.client.exchange({"op": "state", "oid": obj.oid})  # type: ignore[attr-defined]
    except Exception:
        return _closed(name)
    if isinstance(found, dict):
        return found
    return _closed(name)


def preview(obj: object, name: str) -> dict[str, object] | None:
    """Read plain fields before the candidate comparison can change them."""

    if name not in _CHECKED:
        return None
    return _state(obj, name)


def _same(left: object, right: object) -> bool:
    try:
        return bool(left == right)
    except Exception:
        return False


def _matches_all(items: list[object], other: object) -> bool:
    for item in items:
        if not _same(item, other):
            return False
    return True


def _number(value: object) -> bool:
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, float))


def _same_kind(item: object, other: object) -> bool:
    if _number(item):
        return _number(other)
    return item.__class__ == other.__class__


def _related(fields: dict[str, object], other: object) -> list[object]:
    return [item for item in fields.values() if _same_kind(item, other)]


def _equal_data(fields: dict[str, object], other: object) -> bool:
    if not fields:
        return False
    related = _related(fields, other)
    if related:
        return _matches_all(related, other)
    return _same(tuple(fields.values()), other)


def _comparable(op: object, item: object, other: object) -> bool:
    try:
        op(item, other)  # type: ignore[operator]
    except TypeError:
        return False
    return True


def _ordered_item(op: object, item: object, other: object) -> bool | None:
    if not _comparable(op, item, other):
        return None
    return bool(op(item, other))  # type: ignore[operator]


def _ordered(name: str, fields: dict[str, object], other: object) -> bool:
    if not fields:
        return False
    op = _ORDER[name]
    seen = False
    for item in fields.values():
        answer = _ordered_item(op, item, other)
        if answer is None:
            continue
        if not answer:
            return False
        seen = True
    return seen


def _relation(name: str, fields: dict[str, object], other: object) -> bool:
    if name == "__ne__":
        return not _equal_data(fields, other)
    if name == "__eq__":
        return _equal_data(fields, other)
    return _ordered(name, fields, other)


def _agrees(name: str, fields: dict[str, object], other: object) -> bool:
    if not fields:
        return False
    return _relation(name, fields, other)


def _user_defined(info: dict[str, object], name: str) -> bool:
    user = info.get("user")
    if not isinstance(user, list):
        return False
    return name in user


def _agreed(name: str, info: dict[str, object], other: object) -> bool:
    fields = info.get("fields")
    if not isinstance(fields, dict):
        return False
    return _agrees(name, fields, other)


def _answer(result: object) -> object:
    if result is NotImplemented:
        return NotImplemented
    return _affirms(result)


def _release(verdict: object, info: dict[str, object] | None) -> bool:
    if verdict is NotImplemented:
        return True
    if info is None:
        return True
    return verdict is False


def _deny(name: str, info: dict[str, object], other: object) -> bool:
    if not _user_defined(info, name):
        return False
    if name == "__contains__":
        return True
    return not _agreed(name, info, other)


def _kept(name: str, info: dict[str, object] | None, other: object, verdict: object) -> object:
    if _release(verdict, info):
        return verdict
    if _deny(name, info, other):  # type: ignore[arg-type]
        return NotImplemented
    return verdict


def decide(name: str, result: object, info: dict[str, object] | None, other: object) -> object:
    """Return one parent bool. A later read must not see a different answer."""

    if name not in _CHECKED:
        return result
    return _kept(name, info, other, _answer(result))


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
