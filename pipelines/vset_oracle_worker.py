"""Candidate worker program text.

A fresh interpreter runs this with ``python -c``. It lives outside the grader
module so that file stays small, and nothing under the worktree can replace it.
"""

from __future__ import annotations

import sys
import textwrap

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_worker")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_worker"
    )

WORKER_SOURCE = textwrap.dedent(
    """\
    import base64
    import builtins
    import dataclasses
    import importlib
    import json
    import logging
    import os
    import sys
    import types
    from datetime import date, datetime
    from decimal import Decimal
    from fractions import Fraction
    from pathlib import Path

    real_out = sys.stdout
    sys.stdout = sys.stderr
    os.chdir(sys.argv[1])
    sys.path.insert(0, str(Path(sys.argv[1]) / "src"))
    objs = {}
    ids = {}
    slots = {}
    nxt = 0


    def remember(value):
        global nxt
        key = id(value)
        if key in ids:
            return ids[key]
        oid = nxt
        nxt += 1
        ids[key] = oid
        objs[oid] = value
        return oid


    def is_exception(value):
        if not isinstance(value, type):
            return False
        try:
            return issubclass(value, Exception)
        except TypeError:
            return False


    def exc_chain(value):
        names = []
        for base in value.__mro__[1:]:
            if base is BaseException or base is object:
                break
            names.append(base.__name__)
        return names


    def describe_class(cls):
        if cls.__module__ == "builtins":
            found = getattr(builtins, cls.__name__, None)
            if isinstance(found, type):
                return {"builtin": cls.__name__}
        bases = []
        for base in cls.__bases__:
            if base is object:
                continue
            bases.append(describe_class(base))
        return {"oid": remember(cls), "name": cls.__name__, "bases": bases}


    def put(value):
        if value is None:
            return {"kind": "value", "value": None}
        if isinstance(value, ParentProxy):
            return {"kind": "cb", "cb": value._cb}
        if value is NotImplemented:
            return {"kind": "notimplemented"}
        if isinstance(value, (bool, int, float, str)):
            return {"kind": "value", "value": value}
        if type(value) is bytes or type(value) is bytearray:
            raw = bytes(value)
            return {"kind": "bytes", "data": base64.b64encode(raw).decode("ascii")}
        if isinstance(value, Decimal):
            return {"kind": "decimal", "data": str(value)}
        if isinstance(value, Fraction):
            return {"kind": "fraction", "n": value.numerator, "d": value.denominator}
        if isinstance(value, datetime):
            return {"kind": "datetime", "data": value.isoformat()}
        if isinstance(value, date):
            return {"kind": "date", "data": value.isoformat()}
        if type(value) is list:
            return {"kind": "list", "items": [put(item) for item in value]}
        if type(value) is tuple:
            return {"kind": "tuple", "items": [put(item) for item in value]}
        if type(value) is dict:
            pairs = [[put(key), put(item)] for key, item in value.items()]
            return {"kind": "dict", "items": pairs}
        if type(value) is set:
            return {"kind": "set", "items": [put(item) for item in value]}
        if type(value) is frozenset:
            return {"kind": "frozenset", "items": [put(item) for item in value]}
        if is_exception(value):
            return {"kind": "exc_type", "name": value.__name__, "chain": exc_chain(value)}
        if isinstance(value, type):
            info = describe_class(value)
            info["kind"] = "class"
            return info
        if dataclasses.is_dataclass(value):
            fields = {}
            for field in dataclasses.fields(value):
                fields[field.name] = put(getattr(value, field.name))
            return {"kind": "dataclass", "name": type(value).__name__, "fields": fields}
        return {"kind": "obj", "oid": remember(value), "cls": describe_class(type(value))}


    def decode(value):
        if not isinstance(value, dict):
            return value
        if "record" in value:
            fields = {key: decode(item) for key, item in value["record"].items()}
            return types.SimpleNamespace(**fields)
        if "cb" in value:
            return ParentProxy(value["cb"])
        if "ref" in value:
            return objs[value["ref"]]
        if "seq" in value:
            items = [decode(item) for item in value["seq"]]
            if value.get("tuple"):
                return tuple(items)
            if value.get("slot") is not None:
                slots[value["slot"]] = items
            return items
        if "map" in value:
            decoded = {decode(pair[0]): decode(pair[1]) for pair in value["map"]}
            if value.get("slot") is not None:
                slots[value["slot"]] = decoded
            return decoded
        if "set" in value:
            items = [decode(item) for item in value["set"]]
            if value.get("frozen"):
                return frozenset(items)
            decoded = set(items)
            if value.get("slot") is not None:
                slots[value["slot"]] = decoded
            return decoded
        if "bytes" in value:
            raw = base64.b64decode(value["bytes"])
            if value.get("slot") is None:
                return raw
            buf = bytearray(raw)
            slots[value["slot"]] = buf
            return buf
        if "decimal" in value:
            return Decimal(value["decimal"])
        if "fraction" in value:
            return Fraction(value["fraction"], value["d"])
        if "datetime" in value:
            return datetime.fromisoformat(value["datetime"])
        if "date" in value:
            return date.fromisoformat(value["date"])
        return value


    def snapshot(value):
        if value is None or isinstance(value, (bool, int, float, str)):
            return {"kind": "value", "value": value}
        if type(value) is list:
            return {"kind": "list", "items": [snapshot(item) for item in value]}
        if type(value) is dict:
            pairs = [[snapshot(key), snapshot(item)] for key, item in value.items()]
            return {"kind": "dict", "items": pairs}
        if type(value) is set:
            return {"kind": "set", "items": [snapshot(item) for item in value]}
        if type(value) is bytearray:
            data = base64.b64encode(bytes(value)).decode("ascii")
            return {"kind": "bytes", "data": data}
        return put(value)


    def reply(payload):
        real_out.write(json.dumps(payload) + "\\n")
        real_out.flush()


    _MISSING = object()
    _PATCHES = []


    class ParentProxy:
        def __init__(self, cb):
            self._cb = cb

        def __setattr__(self, name, value):
            if name == "_cb":
                object.__setattr__(self, name, value)
                return
            ask({
                "kind": "callback",
                "op": "set",
                "cb": self._cb,
                "attr": name,
                "value": put(value),
            })

        def __call__(self, *args, **kwargs):
            return ask({
                "kind": "callback",
                "op": "call",
                "cb": self._cb,
                "args": [put(arg) for arg in args],
                "kwargs": {key: put(val) for key, val in kwargs.items()},
            })

        def __getattr__(self, name):
            return ask({
                "kind": "callback",
                "op": "get",
                "cb": self._cb,
                "attr": name,
            })


    def ask(payload):
        reply(payload)
        while True:
            line = sys.stdin.readline()
            if not line:
                raise EOFError("oracle worker exited")
            req = json.loads(line)
            if "cb_result" not in req:
                handle(req)
                continue
            if req.get("ok"):
                return decode(req.get("value"))
            raise RuntimeError(str(req.get("message")))


    def handle(req):
        try:
            out = run_op(req)
        except Exception as exc:
            attrs = {}
            for key, val in getattr(exc, "__dict__", {}).items():
                attrs[key] = put(val)
            out = {
                "kind": "error",
                "type": type(exc).__name__,
                "chain": exc_chain(type(exc)),
                "args": [put(arg) for arg in exc.args],
                "attrs": attrs,
            }
        reply(out)


    def run_op(req):
        op = req["op"]
        if op == "import":
            return put(importlib.import_module(req["name"]))
        if op == "get":
            return put(getattr(objs[req["oid"]], req["attr"]))
        if op == "set":
            setattr(objs[req["oid"]], req["attr"], decode(req["value"]))
            return {"kind": "value", "value": None}
        if op == "del":
            delattr(objs[req["oid"]], req["attr"])
            return {"kind": "value", "value": None}
        if op == "patch":
            mod = importlib.import_module(req["name"])
            attr = req["attr"]
            old = _MISSING
            if hasattr(mod, attr):
                old = getattr(mod, attr)
            _PATCHES.append((mod, attr, old))
            setattr(mod, attr, decode(req["value"]))
            return {"kind": "value", "value": None}
        if op == "unpatch":
            mod, attr, old = _PATCHES.pop()
            if old is _MISSING:
                delattr(mod, attr)
            else:
                setattr(mod, attr, old)
            return {"kind": "value", "value": None}
        if op == "environ":
            for key in req["drop"]:
                os.environ.pop(key, None)
            os.environ.update(req["set"])
            return {"kind": "value", "value": None}
        if op == "call":
            args = [decode(arg) for arg in req["args"]]
            kwargs = {key: decode(val) for key, val in req["kwargs"].items()}
            result = objs[req["oid"]](*args, **kwargs)
            states = []
            for slot, obj in slots.items():
                states.append({"slot": slot, "state": snapshot(obj)})
            slots.clear()
            return {"kind": "synced", "value": put(result), "states": states}
        return {
            "kind": "error",
            "type": "RuntimeError",
            "chain": ["Exception"],
            "message": "bad op",
        }


    class _Out:
        def write(self, text):
            if text:
                reply({"kind": "stdout", "text": text})
            return len(text or "")

        def flush(self):
            return None


    class _Log(logging.Handler):
        def emit(self, record):
            reply({
                "kind": "log",
                "name": record.name,
                "level": record.levelno,
                "msg": record.getMessage(),
            })


    sys.stdout = _Out()
    logging.getLogger().addHandler(_Log())

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        if not line.strip():
            continue
        handle(json.loads(line))
    """
)


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
