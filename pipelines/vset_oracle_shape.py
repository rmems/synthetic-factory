"""Candidate class bases and blank builtin instances.

Imported by ``vset_oracle_values``. That module is loaded lazily from here
so the two files do not import each other at module scope.
"""

from __future__ import annotations

import builtins
import sys

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_shape")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_shape"
    )


def _values():
    # vset_oracle_values imports this module. A top-level import would cycle.
    if __package__:
        from . import vset_oracle_values as values
    else:
        import vset_oracle_values as values
    return values


def builtin_type(info: dict[str, object]) -> type | None:
    """Real builtin when the child describes one, instead of a proxy class."""

    name = info.get("builtin")
    if not isinstance(name, str):
        return None
    found = getattr(builtins, name, None)
    if isinstance(found, type):
        return found
    return None


def _collect_parents(client: object, host: object, raw: list[object]) -> list[type]:
    parents: list[type] = []
    for base in raw:
        if not isinstance(base, dict):
            continue
        builtin = builtin_type(base)
        if builtin is not None:
            parents.append(builtin)
            continue
        parents.append(host._class_from(client, base))  # type: ignore[attr-defined]
    return parents


def _with_remote(host: object, parents: list[type]) -> list[type]:
    remote = host.RemoteObject  # type: ignore[attr-defined]
    for parent in parents:
        if issubclass(parent, remote):
            return parents
    return [remote, *parents]


def parent_types(client: object, info: dict[str, object]) -> list[type]:
    """Bases for a reconstructed candidate class, preserving builtin ancestry."""

    host = _values()
    raw = info.get("bases")
    if not isinstance(raw, list):
        return [host.RemoteObject]
    if not raw:
        return [host.RemoteObject]
    parents = _collect_parents(client, host, raw)
    if not parents:
        return [host.RemoteObject]
    return _with_remote(host, parents)


def _new_list(cls: type) -> object:
    return list.__new__(cls)


def _new_dict(cls: type) -> object:
    return dict.__new__(cls)


def _new_set(cls: type) -> object:
    return set.__new__(cls)


def _new_tuple(cls: type) -> object:
    return tuple.__new__(cls, ())


def _new_str(cls: type) -> object:
    return str.__new__(cls, "")


def _new_bytes(cls: type) -> object:
    return bytes.__new__(cls, b"")


def _new_bytearray(cls: type) -> object:
    return bytearray.__new__(cls)


def _new_int(cls: type) -> object:
    return int.__new__(cls, 0)


def _new_float(cls: type) -> object:
    return float.__new__(cls, 0.0)


_BLANK = (
    (list, _new_list),
    (dict, _new_dict),
    (set, _new_set),
    (tuple, _new_tuple),
    (str, _new_str),
    (bytes, _new_bytes),
    (bytearray, _new_bytearray),
    (int, _new_int),
    (float, _new_float),
)


def blank_instance(cls: type) -> object:
    """Empty instance whose real builtin bases ``isinstance`` still sees."""

    for base, maker in _BLANK:
        if cls is base:
            continue
        if issubclass(cls, base):
            return maker(cls)
    return object.__new__(cls)


def remote_hash(obj: object) -> int:
    try:
        func = obj.client.get(obj.oid, "__hash__")  # type: ignore[attr-defined]
    except AttributeError:
        return object.__hash__(obj)
    if func is None:
        raise TypeError("unhashable type")
    return func()


def truth(obj: object) -> bool:
    try:
        func = obj.client.get(obj.oid, "__bool__")  # type: ignore[attr-defined]
    except AttributeError:
        func = None
    if func is not None:
        return bool(func())
    try:
        func = obj.client.get(obj.oid, "__len__")  # type: ignore[attr-defined]
    except AttributeError:
        return True
    return bool(func())


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
