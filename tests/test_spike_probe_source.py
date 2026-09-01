import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import spike_probe  # noqa: E402


class ProbeSource(unittest.TestCase):
    def test_invalid_utf8_is_reported_per_physical_line(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "mixed.jsonl"
            path.write_bytes(b'{"id":"first"}\n\xff\n{"id":"third"}\n')

            records = list(spike_probe.iter_records([path]))

        self.assertEqual([where.rsplit(":", 1)[1] for where, _, _ in records], ["1", "2", "3"])
        self.assertEqual(records[0][1], {"id": "first"})
        self.assertEqual(records[1][2], "BRIDGE_SOURCE_UTF8_INVALID")
        self.assertEqual(records[2][1], {"id": "third"})

    def test_symlink_loop_is_an_unreadable_input_not_a_crash(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "loop.jsonl"
            path.symlink_to(path.name)

            records = list(spike_probe.iter_records(spike_probe.jsonl_paths([path])))

        self.assertEqual(records, [(f"{path}:0", None, "BRIDGE_SOURCE_UNREADABLE")])

    def test_resolution_failure_falls_back_to_a_lexical_input_identity(self):
        path = Path("input.jsonl")
        with mock.patch.object(Path, "resolve", side_effect=RuntimeError("symlink loop")):
            paths = spike_probe.jsonl_paths([path])

        self.assertEqual(paths, [path])

    def test_strict_probe_reports_parser_recursion_as_invalid_input(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "nested.jsonl"
            path.write_text('{"id":"deep"}\n', encoding="utf-8")
            stdout = io.StringIO()
            with (
                mock.patch(
                    "spike_probe_source.json.loads",
                    side_effect=RecursionError("decoder nesting limit"),
                ),
                redirect_stdout(stdout),
            ):
                code = spike_probe.main(["--strict", str(path)])

        report = json.loads(stdout.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual((report["loaded"], report["input_errors"]), (0, 1))
        self.assertEqual(
            report["problems"][0]["reason_codes"],
            ["BRIDGE_SOURCE_JSON_INVALID"],
        )


if __name__ == "__main__":
    unittest.main()
