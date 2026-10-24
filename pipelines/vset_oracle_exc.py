"""Parent-side exception classes for candidate errors.

``vset_oracle_values`` re-exports ``exception_type``, ``exc_from``, and
``raise_remote``. The caches live here so that module stays under the
file-complexity gate.
"""

from __future__ import annotations

import builtins
import sys

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_exc")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_exc"
    )

_EXC_TYPES: dict[tuple[str, tuple[str, ...]], type[Exception]] = {}
_EXC_OID: dict[tuple[int, int], type[Exception]] = {}


def _builtin_exception(name: str) -> type[Exception] | None:
    found = getattr(builtins, name, None)
    if not isinstance(found, type):
        return None
    if not issubclass(found, Exception):
        return None
    return found


def _exception_parent(chain: tuple[str, ...]) -> type[Exception]:
    if not chain:
        return Exception
    builtin = _builtin_exception(chain[0])
    if builtin is not None:
        return builtin
    return exception_type(chain[0], chain[1:])


def exception_type(name: str, chain: tuple[str, ...]) -> type[Exception]:
    """Return one real exception class, preserving the candidate MRO."""

    key = (name, chain)
    found = _EXC_TYPES.get(key)
    if found is not None:
        return found
    created = type(name, (_exception_parent(chain),), {})
    _EXC_TYPES[key] = created
    return created


def _exc_bases(client: object, info: dict[str, object]) -> tuple[type[Exception], ...]:
    raw = info.get("bases")
    if not isinstance(raw, list) or not raw:
        return (Exception,)
    bases = [exc_from(client, item) for item in raw if isinstance(item, dict)]
    if not bases:
        return (Exception,)
    return tuple(bases)


def exc_from(client: object, info: dict[str, object]) -> type[Exception]:
    """One parent class per candidate exception class, keyed by child identity."""

    builtin_name = info.get("builtin")
    if isinstance(builtin_name, str):
        builtin = _builtin_exception(builtin_name)
        if builtin is not None:
            return builtin
        return Exception
    key = (id(client), int(info.get("oid") or -1))
    found = _EXC_OID.get(key)
    if found is not None:
        return found
    created = type(str(info.get("name") or "Error"), _exc_bases(client, info), {})
    _EXC_OID[key] = created
    return created


def raise_remote(
    cls: type[Exception],
    args: tuple[object, ...],
    attrs: dict[str, object],
) -> None:
    """Raise a candidate error without ever raising BaseException."""

    exc = cls(*args)
    for key, value in attrs.items():
        setattr(exc, key, value)
    raise exc


def clear_exception_oids() -> None:
    """Drop oid-keyed exception classes from the previous child."""

    _EXC_OID.clear()


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
