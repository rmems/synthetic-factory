"""Direct coverage for oracle helper branches the suite runs do not hit."""

from __future__ import annotations

import os
import sys
import tempfile
import types
import unittest
from collections import defaultdict
from datetime import time, timedelta
from pathlib import Path, PurePath

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import child_timeout, vset  # noqa: E402
import vset_oracle_bridge as bridge  # noqa: E402
import vset_oracle_codec as codec  # noqa: E402
import vset_oracle_collect as collect  # noqa: E402
import vset_oracle_exec as oracle_exec  # noqa: E402
import vset_oracle_grade as grade  # noqa: E402
import vset_oracle_layout as layout  # noqa: E402
import vset_oracle_record as record  # noqa: E402
import vset_oracle_remote as remote  # noqa: E402
import vset_oracle_shape as shape  # noqa: E402
import vset_oracle_values as values  # noqa: E402


class _Client:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def get(self, oid: int, name: str) -> object:
        self.calls.append(("get", oid, name))
        if name == "__hash__":
            return lambda: 7
        if name == "__bool__":
            raise AttributeError(name)
        if name == "__len__":
            return lambda: 0
        if name == "__eq__":
            raise AttributeError(name)
        raise AttributeError(name)

    def set_attr(self, oid: int, name: str, value: object) -> None:
        self.calls.append(("set", oid, name, value))

    def delete_attr(self, oid: int, name: str) -> None:
        self.calls.append(("del", oid, name))

    def shift_environ(self, changed: dict[str, str], dropped: list[str]) -> None:
        self.calls.append(("env", changed, dropped))

    def call(self, oid: int, args: tuple[object, ...], kwargs: dict[str, object]) -> object:
        return (oid, args, kwargs)


class _Proc:
    def __init__(self) -> None:
        self.pid = os.getpid()
        self.killed = False
        self.stdin = None
        self.stdout = None
        self.waits = 0

    def poll(self) -> int:
        return 0

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: float = 0) -> int:
        self.waits += 1
        if self.waits == 1:
            raise child_timeout(timeout)
        return 0


class _Boom:
    def close(self) -> None:
        raise OSError("closed")


class _Lines:
    def __init__(self, rows: list[str]) -> None:
        self.rows = rows

    def readline(self, limit: int = -1) -> str:
        if not self.rows:
            return ""
        return self.rows.pop(0)


class _Pipe:
    def __init__(self, rows: list[str]) -> None:
        self.stdout = _Lines(rows)


class EdgeTests(unittest.TestCase):
    def test_blank_instances_keep_builtin_bases(self) -> None:
        class Bag(list):
            pass

        class Map(dict):
            pass

        class Group(set):
            pass

        class Pair(tuple):
            pass

        class Word(str):
            pass

        class Blob(bytes):
            pass

        class Buf(bytearray):
            pass

        class Count(int):
            pass

        class Measure(float):
            pass

        self.assertIsInstance(shape.blank_instance(Bag), list)
        self.assertIsInstance(shape.blank_instance(Map), dict)
        self.assertIsInstance(shape.blank_instance(Group), set)
        self.assertIsInstance(shape.blank_instance(Pair), tuple)
        self.assertIsInstance(shape.blank_instance(Word), str)
        self.assertIsInstance(shape.blank_instance(Blob), bytes)
        self.assertIsInstance(shape.blank_instance(Buf), bytearray)
        self.assertEqual(shape.blank_instance(Count), 0)
        self.assertEqual(shape.blank_instance(Measure), 0.0)
        self.assertIsNone(shape.builtin_type({}))
        self.assertIsNone(shape.builtin_type({"builtin": "NotARealBuiltin"}))
        self.assertIs(shape.builtin_type({"builtin": "int"}), int)
        self.assertEqual(shape.parent_types(object(), {}), [values.RemoteObject])
        self.assertEqual(shape.parent_types(object(), {"bases": []}), [values.RemoteObject])
        self.assertEqual(shape.parent_types(object(), {"bases": ["nope"]}), [values.RemoteObject])
        parents = shape.parent_types(object(), {"bases": [{"builtin": "int"}]})
        self.assertIn(int, parents)

    def test_remote_object_forwarding_and_truth(self) -> None:
        client = _Client()
        obj = values.RemoteObject.__new__(values.RemoteObject)
        obj.client = client
        obj.oid = 4
        self.assertEqual(hash(obj), 7)
        self.assertFalse(bool(obj))
        with self.assertRaises(AttributeError):
            getattr(obj, "missing")
        obj.label = "x"
        del obj.label
        self.assertIn(("set", 4, "label", "x"), client.calls)
        self.assertIn(("del", 4, "label"), client.calls)
        def refuse(oid: int, name: str) -> object:
            if name == "__hash__":
                return None
            raise AttributeError(name)

        client.get = refuse  # type: ignore[method-assign]
        with self.assertRaises(TypeError):
            len(obj)
        with self.assertRaises(TypeError):
            hash(obj)

    def test_environ_mirror_and_codec_edges(self) -> None:
        client = _Client()

        class StringTarget:
            in_dict = "os.environ"

        entered = shape._enter_environ((lambda patcher: "in", lambda *_args: "out"), client, StringTarget())
        self.assertEqual(entered, "in")

        class LiveTarget:
            in_dict = os.environ

        shape._enter_environ((lambda patcher: "in", lambda *_args: "out"), client, LiveTarget())

        class Boom:
            in_dict = os.environ

            def shift_environ(self, changed: dict[str, str], dropped: list[str]) -> None:
                raise RuntimeError("shift")

        left = shape._leave_environ(
            (lambda patcher: "in", lambda *_args: "out"),
            Boom(),
            LiveTarget(),
            (None, None, None),
        )
        self.assertEqual(left, "out")
        self.assertEqual(codec._factory_name(None), "")
        self.assertIsNone(codec._factory_name(lambda: None))
        self.assertEqual(codec.encode(1 + 2j)["complex"], [1.0, 2.0])
        self.assertEqual(codec.encode(range(1, 4, 2))["range"], [1, 4, 2])
        self.assertEqual(codec.encode(slice(1, 3))["slice"], [1, 3, None])
        self.assertEqual(codec.encode(timedelta(seconds=5))["timedelta"][1], 5)
        self.assertEqual(codec.encode(time(1, 2, 3))["time"], "01:02:03")
        self.assertEqual(codec.encode(PurePath("x/y"))["path"], "x/y")
        self.assertEqual(codec.encode(defaultdict(int))["factory"], "int")
        self.assertIn("seq", codec.encode(iter([1, 2])))
        self.assertIn("cb", codec.encode(k for k in [1]))
        self.assertIn("cb", codec.encode(map(int, ["1"])))
        self.assertIn("cb", codec.encode(unittest.mock.Mock(spec=complex)))
        self.assertIn("map", codec.encode(defaultdict(lambda: 0, {1: 2})))
        values.reset_identity()

    def test_exception_identity_helpers(self) -> None:
        self.assertIsNone(values._builtin_exception("missing-name"))
        self.assertIsNone(values._builtin_exception("SystemExit"))
        kind = values.exception_type("Mine", ("ValueError", "Exception"))
        self.assertIs(values.exception_type("Mine", ("ValueError", "Exception")), kind)
        self.assertTrue(issubclass(kind, ValueError))
        other = values.exception_type("Other", ())
        self.assertTrue(issubclass(other, Exception))
        nested = values.exception_type("Child", ("Parent",))
        self.assertTrue(issubclass(nested, values.exception_type("Parent", ())))
        client = object()
        self.assertIs(values.exc_from(client, {"builtin": "ValueError"}), ValueError)
        self.assertIs(values.exc_from(client, {"builtin": "SystemExit"}), Exception)
        base = values.exc_from(client, {"oid": 1, "name": "BaseError", "bases": []})
        specific = values.exc_from(
            client,
            {"oid": 2, "name": "Specific", "bases": [{"oid": 1, "name": "BaseError", "bases": []}]},
        )
        self.assertIs(values.exc_from(client, {"oid": 2}), specific)
        self.assertTrue(issubclass(specific, base))
        empty = values.exc_from(client, {"oid": 3, "name": "Empty", "bases": ["nope"]})
        self.assertTrue(issubclass(empty, Exception))
        with self.assertRaises(Exception) as caught:
            values.interpret(
                client,
                {
                    "kind": "error",
                    "type": "ValueError",
                    "chain": ["Exception"],
                    "args": [{"kind": "value", "value": "x"}],
                    "attrs": {},
                },
            )
        self.assertEqual(type(caught.exception).__name__, "ValueError")
        with self.assertRaises(EOFError):
            values.interpret(client, [])
        with self.assertRaises(EOFError):
            values.interpret(client, {"kind": "missing"})
        self.assertIsNone(values.interpret(client, {"kind": "value"}))
        self.assertIs(values.interpret(client, {"kind": "notimplemented"}), NotImplemented)
        values.reset_identity()

    def test_grade_and_collect_refusals(self) -> None:
        self.assertFalse(grade._suite_ok([], []))
        self.assertFalse(grade._suite_ok([{"id": "a", "status": "ok"}], ["b"]))
        report = grade._suite_report(
            [{"id": "a", "status": "FAIL"}],
            ["a"],
            "trace\n",
        )
        self.assertIn("trace", report["captured_output"])
        with self.assertRaises(vset.VSetValidationError):
            grade._spec_for("missing", [{"module": "other"}])
        with self.assertRaises(vset.VSetValidationError):
            grade._class_and_method("mod", "mod")
        with self.assertRaises(vset.VSetValidationError):
            grade._class_and_method("mod.", "mod")
        with self.assertRaises(vset.VSetValidationError):
            grade._class_and_method("mod.class.", "mod")
        with self.assertRaises(vset.VSetValidationError):
            grade._class_and_method("mod..method", "mod")
        spec = {
            "module": "vset_oracle_tests_edge",
            "relative": "tests/edge.py",
            "source": "import unittest\nclass T(unittest.TestCase):\n    def test_a(self):\n        pass\n",
        }
        with self.assertRaises(vset.VSetValidationError):
            collect.require_match(spec, ["vset_oracle_tests_edge.T.test_missing"], {"edge.py": spec["source"]})

    def test_loader_and_layout_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            pack = work / "pack"
            (pack / "tests").mkdir(parents=True)
            (pack / "tests" / "edge.py").write_text(
                "import unittest\nclass T(unittest.TestCase):\n    def test_a(self):\n        self.assertTrue(True)\n",
                encoding="utf-8",
            )
            work = work / "stage"
            work.mkdir()
            suite = oracle_exec.load_tests(work, pack, "tests/edge.py")
            self.assertEqual(suite.countTestCases(), 1)
            with self.assertRaises(vset.VSetValidationError):
                oracle_exec.load_tests(work, pack, "tests/missing.py")
            with self.assertRaises(vset.VSetValidationError):
                oracle_exec._resolve_under_work(pack, "../escape.py", code="vset.oracle_execution_mismatch")
            copy = work / "copy"
            (copy / "tests").mkdir(parents=True)
            (copy / "tests" / "__pycache__").mkdir()
            (copy / "tests" / "extra.py").write_text("x = 1\n", encoding="utf-8")
            layout.restore_suite_dir(pack, copy, "tests/edge.py")
            self.assertTrue((copy / "tests" / "edge.py").is_file())
            self.assertFalse((copy / "tests" / "extra.py").exists())
            layout.restore_suite_dir(pack, copy, "missing/file.py")
            (work / "src" / "pkg").mkdir(parents=True)
            (work / "src" / "pkg" / "__init__.py").write_text("", encoding="utf-8")
            (work / "src" / "kept.py").write_text("x = 1\n", encoding="utf-8")
            (work / "src" / "nodata").mkdir()
            layout._drop_added_packages(work / "src", frozenset({"pkg"}))
            self.assertIn("pkg", layout.src_names(work))
            layout.drop_added_src(work, frozenset({"pkg", "kept"}))
            layout.freeze_pack(work)
            self.assertIn("edge.py", layout.frozen_folder("tests"))
            self.assertEqual(layout.frozen_folder(""), {})
            layout.clear_pack()
            with self.assertRaises(KeyError):
                layout.frozen_text("tests/edge.py")

    def test_kill_group_falls_back_when_the_group_is_gone(self) -> None:
        proc = _Proc()
        with unittest.mock.patch("os.killpg", side_effect=OSError("no group")):
            remote._kill_group(proc)  # type: ignore[arg-type]
        self.assertTrue(proc.killed)

    def test_stop_closes_streams_and_pops_paths(self) -> None:
        proc = _Proc()
        remote._close(None)
        remote._close(_Boom())
        remote._stop(proc)  # type: ignore[arg-type]
        remote._push_path("folder")
        remote._pop_path("folder")
        remote._pop_path("other")
        sys.path.insert(0, "")
        remote._pop_path("folder")
        del sys.path[0]
        self.assertEqual(proc.waits, 2)

    def test_status_labels(self) -> None:
        result = unittest.TestResult()
        self.assertEqual(remote._status(result), "ERROR")
        result.testsRun = 1
        self.assertEqual(remote._status(result), "ok")
        result.skipped.append((None, "skip"))  # type: ignore[arg-type]
        self.assertEqual(remote._status(result), "SKIP")
        result.skipped.clear()
        result.expectedFailures.append((None, "x"))  # type: ignore[arg-type]
        self.assertEqual(remote._status(result), "expectedFailure")
        result.expectedFailures.clear()
        result.failures.append((None, "x"))  # type: ignore[arg-type]
        self.assertEqual(remote._status(result), "FAIL")
        result.failures.clear()
        result.unexpectedSuccesses.append(None)  # type: ignore[arg-type]
        self.assertEqual(remote._status(result), "unexpectedSuccess")

    def test_receive_relays_stdout_before_the_value(self) -> None:
        sent: list[object] = []

        def send(proc_obj: object, payload: object) -> None:
            sent.append(payload)

        def answer(client: object, message: object) -> dict[str, object]:
            return {"ok": True}

        def relay(reply: dict[str, object]) -> bool:
            return reply.get("kind") == "stdout"

        ops = (bridge._read_reply, send, answer, relay)
        rows = ['{"kind": "stdout", "text": "hi"}\n', '{"kind": "value", "value": 3}\n']
        self.assertEqual(record.receive(object(), _Pipe(rows), ops), 3)
        with self.assertRaises(EOFError):
            record.receive(object(), _Pipe([]), ops)
        missing = type("P", (), {"stdout": None})()
        with self.assertRaises(EOFError):
            record.receive(object(), missing, (None, None, None, None))

    def test_data_record_skips_callables_and_failures(self) -> None:
        class Plain:
            def __init__(self) -> None:
                self.pair = (1, 2)

        self.assertIn("pair", record.data_record(Plain())["record"])  # type: ignore[index]

        class Raising:
            @property
            def n(self) -> int:
                raise RuntimeError("no")

        self.assertIsNone(record.data_record(Raising()))
        case = unittest.TestCase(methodName="run")
        self.assertFalse(record.live_collaborator(case))
        self.assertTrue(record.live_collaborator(unittest.mock.Mock()))

    def test_remote_module_deletes_and_callback_closure(self) -> None:
        client = _Client()
        spec = types.SimpleNamespace(name="candidate")
        module = bridge.remote_module(spec, client)  # type: ignore[arg-type]
        module._vset_live = True
        module._vset_oid = 9
        module.label = "a"
        module._vset_note = "local"
        del module.label
        del module._vset_note
        del module.missing
        module._vset_live = False
        with self.assertRaises(AttributeError):
            del module.missing
        self.assertTrue(bridge._closed_name("__dict__"))
        self.assertFalse(bridge._closed_name("__iter__"))
        self.assertTrue(bridge._closed_name("assert_called"))
        self.assertTrue(bridge._closed_name("side_effect"))
        with self.assertRaises(AttributeError):
            bridge._read_collaborator(unittest.mock.Mock(), "side_effect")
        with self.assertRaises(AttributeError):
            bridge._write_collaborator(object(), "label", 1)
        chain = bridge._exception_chain(ValueError("x"))
        self.assertEqual(chain[0], "Exception")

    def test_remote_class_and_payload_edges(self) -> None:
        client = _Client()
        obj = values.RemoteObject.__new__(values.RemoteObject)
        obj.client = client
        obj.oid = 1
        del obj.oid
        obj.oid = 1
        del obj.client
        obj.client = client

        def missing(oid: int, name: str) -> object:
            raise AttributeError(name)

        client.get = missing  # type: ignore[method-assign]
        with self.assertRaises(TypeError):
            obj + 1  # type: ignore[operator]
        meta = values._RemoteMeta("Kid", (values.RemoteObject,), values._namespace(client, 3))
        with self.assertRaises(AttributeError):
            getattr(meta, "color")
        meta._vset_client = client
        with self.assertRaises(AttributeError):
            getattr(meta, "color")
        meta._vset_oid = 3
        client.get = lambda oid, name: "attr"  # type: ignore[method-assign]
        self.assertEqual(meta.color, "attr")
        self.assertEqual(meta(), (3, (), {}))
        meta._hidden = 1
        meta.label = "z"
        del meta._hidden
        del meta.label
        bare = values._RemoteMeta("Bare", (values.RemoteObject,), {})
        bare.label = "local"
        del bare.label
        self.assertEqual(values._mapped(client, {}), {})
        self.assertEqual(
            values.interpret(client, {"kind": "path", "data": "a", "cls": "Nope"}),
            PurePath("a"),
        )
        self.assertEqual(
            values.interpret(client, {"kind": "list", "items": [{"kind": "value", "value": 1}]}),
            [1],
        )
        self.assertEqual(values.interpret(client, {"kind": "tuple", "items": []}), ())
        self.assertEqual(values.interpret(client, {"kind": "set", "items": []}), set())
        self.assertEqual(values.interpret(client, {"kind": "frozenset", "items": []}), frozenset())
        self.assertEqual(values.interpret(client, {"kind": "bytes", "data": "YWI="}), b"ab")
        key = values.remember_callback(len)
        self.assertIs(values.interpret(client, {"kind": "cb", "cb": key}), len)
        self.assertEqual(values._chain({}), ("Exception",))
        kind = values.interpret(client, {"kind": "exc_type", "name": "Mine", "chain": []})
        self.assertTrue(issubclass(kind, Exception))
        values.reset_identity()
