"""Parent-side check for comparisons against candidate objects.

An affirmative ``__eq__`` or ordering result is a pass channel when the
other operand is a parent value: the child can answer True for every
input. Builtin and standard-library comparisons are real data comparisons.
An affirmative answer is kept only when the same method returns false
for other operands: a marker string, an empty tuple, and a shifted
number. An unconditional ``True`` fails that check. A method that looks
at the real amount, ratio, or version does not.
"""

from __future__ import annotations

import sys

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_compare")
    from .vset_oracle_codec import encode as _encode
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_compare"
    )
    from vset_oracle_codec import encode as _encode


_CHECKED = frozenset({"__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__"})
_MARK = "\x00vset"


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


def _number(value: object) -> bool:
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, float))


def _lower(name: str) -> bool:
    if name == "__lt__":
        return True
    return name == "__le__"


def _higher(name: str) -> bool:
    if name == "__gt__":
        return True
    return name == "__ge__"


def _shift(name: str, other: object) -> object:
    if not _number(other):
        return 10**9
    if _lower(name):
        return -(10**18)
    if _higher(name):
        return 10**18
    if other == 0:
        return 1
    return 0


def _samples(name: str, other: object) -> list[object]:
    return [_MARK, (), _shift(name, other)]


def _user_defined(info: dict[str, object], name: str) -> bool:
    user = info.get("user")
    if not isinstance(user, list):
        return False
    return name in user


def _needs_data(result: object, info: dict[str, object], name: str) -> bool:
    if not _affirms(result):
        return False
    return _user_defined(info, name)


def _stable(obj: object, name: str, other: object) -> bool:
    """True when the same answer is false for operands the candidate cannot plant."""

    try:
        samples = [_encode(sample) for sample in _samples(name, other)]
        answer = obj.client.exchange(  # type: ignore[attr-defined]
            {"op": "probe", "oid": obj.oid, "name": name, "samples": samples}
        )
    except Exception:
        return False
    return answer is True


def decide(
    obj: object, name: str, result: object, info: dict[str, object] | None, other: object
) -> object:
    """Keep a candidate comparison only when probes of other operands do not affirm."""

    if info is None:
        return result
    if not _needs_data(result, info, name):
        return result
    if _stable(obj, name, other):
        return result
    return NotImplemented


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
