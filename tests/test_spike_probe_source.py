import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import spike_probe  # noqa: E402
import spike_probe_source  # noqa: E402
from exact_json import MAX_JSON_NESTING_DEPTH  # noqa: E402


class ProbeSource(unittest.TestCase):
    def test_validation_only_exact_encoding_does_not_sort_discarded_output(self):
        with mock.patch.object(
            spike_probe_source,
            "dumps_exact_json",
            wraps=spike_probe_source.dumps_exact_json,
        ) as encode:
            record, reason = spike_probe_source._parse_record('{"z":1,"a":2}')

        self.assertEqual((record, reason), ({"z": 1, "a": 2}, None))
        encode.assert_called_once_with(record, ensure_ascii=False, sort_keys=False)

    def test_jsonl_probe_reports_encoder_depth_as_invalid_input(self):
        fixture = json.loads(
            (REPO / "tests" / "fixtures" / "bridge_gate_snn.jsonl").read_text(
                encoding="utf-8"
            )
        )
        fixture["gate_snn"]["populations"][0]["extension"] = "DEPTH_SENTINEL"
        nested = "[" * (MAX_JSON_NESTING_DEPTH + 1) + "0" + "]" * (
            MAX_JSON_NESTING_DEPTH + 1
        )
        payload = json.dumps(fixture).replace('"DEPTH_SENTINEL"', nested, 1)

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "nested.jsonl"
            path.write_text(payload + "\n", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = spike_probe.main(["--jsonl", str(path)])

        self.assertEqual(code, 1)
        self.assertEqual(stdout.getvalue(), "")
        problem = json.loads(stderr.getvalue())
        self.assertTrue(problem["unloadable"])
        self.assertEqual(problem["reason_codes"], ["BRIDGE_SOURCE_JSON_INVALID"])

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
