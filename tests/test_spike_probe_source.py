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
