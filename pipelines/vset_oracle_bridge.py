"""Forward parent patches and callbacks into the candidate child.

Assertions stay in this process. ``unittest.mock.patch`` therefore mutates
modules here, while candidate code runs elsewhere. Module writes, stdlib
patches, and values that are not JSON cross the boundary; the child can call
those values back, and it still cannot report a pass.
"""

from __future__ import annotations

import importlib.machinery
import json
import logging
import sys
import types
import unittest.mock

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_bridge")
    from .vset_oracle_codec import encode as _encode
    from .vset_oracle_record import live_collaborator as _live_collaborator
    from . import vset_oracle_shape as shape
    from . import vset_oracle_values as values
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_bridge"
    )
    from vset_oracle_codec import encode as _encode
    from vset_oracle_record import live_collaborator as _live_collaborator
    import vset_oracle_shape as shape
    import vset_oracle_values as values

_REPLY_LIMIT = 1_000_000


class RemoteModule(types.ModuleType):
    """Candidate module whose attribute writes reach the child."""

    def __setattr__(self, name: str, value: object) -> None:
        if not self.__dict__.get("_vset_live"):
            super().__setattr__(name, value)
            return
        if name.startswith("_vset_"):
            super().__setattr__(name, value)
            return
        self._vset_client.set_attr(self._vset_oid, name, value)
        super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        live = self.__dict__.get("_vset_live")
        if live:
            if not name.startswith("_vset_"):
                self._vset_client.delete_attr(self._vset_oid, name)
        try:
            super().__delattr__(name)
        except AttributeError:
            if live:
                return
            raise


def remote_module(spec: importlib.machinery.ModuleSpec, client: object) -> RemoteModule:
    module = RemoteModule(spec.name)
    module._vset_client = client
    module._vset_remote = True
    module._vset_live = False
    module._vset_oid = 0
    return module


def _read_reply(stdout: object) -> object:
    line = stdout.readline(_REPLY_LIMIT)  # type: ignore[attr-defined]
    if not line:
        raise EOFError("oracle worker exited")
    if len(line) >= _REPLY_LIMIT:
        raise EOFError("oracle worker reply is too large")
    return json.loads(line)


def _send(proc: object, payload: dict[str, object]) -> None:
    if proc.poll() is not None:  # type: ignore[attr-defined]
        raise EOFError("oracle worker exited")
    stdin = proc.stdin  # type: ignore[attr-defined]
    if stdin is None:
        raise EOFError("oracle worker exited")
    stdin.write(json.dumps(payload) + "\n")
    stdin.flush()


def exchange(client: object, payload: dict[str, object]) -> object:
    """Send one request, answering any callbacks the child makes while it runs."""

    proc = client.proc  # type: ignore[attr-defined]
    _send(proc, payload)
    return _receive(client, proc)


def _relay(reply: dict[str, object]) -> bool:
    kind = reply.get("kind")
    if kind == "stdout":
        sys.stdout.write(str(reply.get("text", "")))
        return True
    if kind == "log":
        logging.getLogger(str(reply.get("name", ""))).log(
            int(reply.get("level", 0)),  # type: ignore[arg-type]
            str(reply.get("msg", "")),
        )
        return True
    return False


def _receive(client: object, proc: object) -> object:
    return shape.receive(client, proc, (_read_reply, _send, _answer, _relay))


def _answer(client: object, message: dict[str, object]) -> dict[str, object]:
    try:
        encoded = _encode(_invoke(client, message))
    except Exception as exc:
        return {
            "cb_result": True,
            "ok": False,
            "type": type(exc).__name__,
            "message": str(exc),
        }
    return {"cb_result": True, "ok": True, "value": encoded}


def _positional(client: object, message: dict[str, object]) -> list[object]:
    args = message.get("args")
    if not isinstance(args, list):
        return []
    return [values.interpret(client, item) for item in args]


def _named(client: object, message: dict[str, object]) -> dict[str, object]:
    kwargs = message.get("kwargs")
    if not isinstance(kwargs, dict):
        return {}
    return {str(key): values.interpret(client, item) for key, item in kwargs.items()}


def _closed_name(name: str) -> bool:
    return name.startswith("_")


def _read_collaborator(target: object, name: str) -> object:
    if not _live_collaborator(target):
        raise AttributeError(name)
    if _closed_name(name):
        raise AttributeError(name)
    return getattr(target, name)


def _write_collaborator(target: object, name: str, value: object) -> None:
    if not _live_collaborator(target):
        raise AttributeError(name)
    if _closed_name(name):
        raise AttributeError(name)
    setattr(target, name, value)


def _invoke(client: object, message: dict[str, object]) -> object:
    target = values.take_callback(int(message["cb"]))  # type: ignore[arg-type]
    op = message.get("op")
    if op == "get":
        return _read_collaborator(target, str(message.get("attr")))
    if op == "set":
        _write_collaborator(target, str(message.get("attr")), values.interpret(client, message.get("value")))
        return None
    if op != "call":
        raise TypeError("oracle callback is not readable")
    return target(*_positional(client, message), **_named(client, message))


def install_patches(client: object) -> tuple[object, object]:
    """Mirror stdlib ``mock.patch`` targets into the child for one test."""

    patch_cls = unittest.mock._patch
    saved = (patch_cls.__enter__, patch_cls.__exit__)

    def enter(self: object) -> object:
        entered = saved[0](self)
        try:
            _mirror(client, self, True)
        except Exception:
            saved[1](self, None, None, None)
            raise
        return entered

    def leave(self: object, exc_type: object, exc: object, tb: object) -> object:
        try:
            _mirror(client, self, False)
        except Exception:
            return saved[1](self, exc_type, exc, tb)
        return saved[1](self, exc_type, exc, tb)

    patch_cls.__enter__ = enter  # type: ignore[method-assign]
    patch_cls.__exit__ = leave  # type: ignore[method-assign]
    return saved, shape.install_dict_patches(client)


def restore_patches(saved: tuple[object, object]) -> None:
    attr, mapping = saved
    unittest.mock._patch.__enter__ = attr[0]  # type: ignore[index]
    unittest.mock._patch.__exit__ = attr[1]  # type: ignore[index]
    shape.restore_dict_patches(mapping)


def _mirror(client: object, patcher: object, install: bool) -> None:
    name = _module_name(patcher)
    if name is None:
        return
    # Prints already relay to the parent's current sys.stdout.
    if name == "sys":
        if patcher.attribute in {"stdout", "stderr"}:  # type: ignore[attr-defined]
            return
    if not install:
        client.unpatch_module()  # type: ignore[attr-defined]
        return
    # patch() leaves self.new as DEFAULT and stores the mock on the target.
    target = patcher.target  # type: ignore[attr-defined]
    current = getattr(target, patcher.attribute)  # type: ignore[attr-defined]
    client.patch_module(name, patcher.attribute, current)  # type: ignore[attr-defined]


def _module_name(patcher: object) -> str | None:
    target = getattr(patcher, "target", None)
    if getattr(target, "_vset_remote", False):
        return None
    if not isinstance(target, types.ModuleType):
        return None
    name = getattr(target, "__name__", None)
    if isinstance(name, str):
        if name != "":
            return name
    return None


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
