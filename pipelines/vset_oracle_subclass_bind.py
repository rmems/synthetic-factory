"""Which names on a parent subclass are forwarded into the child class.

Kept apart from construction so that file stays under the complexity gate.
"""

from __future__ import annotations

import sys
import types

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_subclass_bind")
    from .vset_oracle_codec import encode as _encode
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_subclass_bind"
    )
    from vset_oracle_codec import encode as _encode


def client_from(cls: type) -> object | None:
    for base in cls.__mro__:
        client = base.__dict__.get("_vset_client")
        if client is not None:
            return client
    return None


def candidate(cls: type) -> tuple[object, int] | None:
    for base in cls.__mro__[1:]:
        oid = base.__dict__.get("_vset_oid")
        client = base.__dict__.get("_vset_client")
        if isinstance(oid, int) and client is not None:
            return client, oid
    return None


def extend(cls: type) -> tuple[object, int] | None:
    for base in cls.__mro__[1:]:
        child = base.__dict__.get("_vset_child")
        if isinstance(child, int):
            client = client_from(base)
            if client is not None:
                return client, child
        oid = base.__dict__.get("_vset_oid")
        client = base.__dict__.get("_vset_client")
        if isinstance(oid, int) and client is not None:
            return client, oid
    return None


_SKIP = frozenset(
    {
        "__dict__",
        "__weakref__",
        "__module__",
        "__qualname__",
        "__doc__",
        "__init__",
        "__new__",
        "__init_subclass__",
    }
)


def _skipped(name: str) -> bool:
    if name in _SKIP:
        return True
    return name.startswith("_vset_")


def _kind(value: object) -> str:
    if isinstance(value, classmethod):
        return "class"
    if isinstance(value, staticmethod):
        return "static"
    if isinstance(value, property):
        return "prop"
    if isinstance(value, types.FunctionType):
        return "func"
    return ""


def members(cls: type) -> tuple[list[dict[str, str]], dict[str, object]]:
    methods: list[dict[str, str]] = []
    attrs: dict[str, object] = {}
    for name, value in cls.__dict__.items():
        if _skipped(name):
            continue
        kind = _kind(value)
        if kind:
            methods.append({"name": name, "kind": kind})
            continue
        if isinstance(value, type):
            continue
        attrs[name] = _encode(value)
    return methods, attrs


def args_of(args: object) -> tuple[object, ...]:
    if isinstance(args, tuple):
        return args
    return ()


def kwargs_of(kwargs: object) -> dict[str, object]:
    if isinstance(kwargs, dict):
        return kwargs
    return {}


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
