import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
_PIPELINES = _TESTS.parent / "pipelines"
for _path in (_TESTS, _PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import curate_tags  # noqa: E402
import tag_write  # noqa: E402
from tag_test_support import (  # noqa: E402
    record,
    run_tag_cli,
    write_tag_source,
)


class _AsciiStdout(io.StringIO):
    encoding = "ascii"

    def write(self, text):
        text.encode(self.encoding)
        return super().write(text)


class CliWriteTests(unittest.TestCase):
    def test_cli_writes_new_files_and_refuses_clobber(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_tag_source(root)
            output = root / "lane" / "tags.jsonl"
            manifest = root / "lane" / "manifest.jsonl"
            unmapped = root / "reports" / "unmapped.jsonl"
            command = [
                "--output-jsonl",
                str(output),
                "--manifest-jsonl",
                str(manifest),
                "--unmapped-jsonl",
                str(unmapped),
            ]

            first = run_tag_cli(source, command)
            second = run_tag_cli(source, command)

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(len(output.read_text().splitlines()), 1)
            self.assertEqual(len(manifest.read_text().splitlines()), 1)
            self.assertEqual(
                json.loads(unmapped.read_text()), {"tag": "tokamak", "count": 1}
            )
            self.assertEqual(json.loads(first.stdout)["unmapped_unique_tags"], 1)

    def test_cli_rejects_unmapped_report_in_curated_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_tag_source(root)
            output = root / "lane" / "tags.jsonl"
            unmapped = root / "lane" / "unmapped.jsonl"
            result = run_tag_cli(
                source,
                ["--output-jsonl", str(output), "--unmapped-jsonl", str(unmapped)],
            )

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("curated JSONL tree", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(unmapped.exists())

            nested = run_tag_cli(
                source,
                [
                    "--output-jsonl",
                    str(root / "lane" / "factory" / "tags.jsonl"),
                    "--unmapped-jsonl",
                    str(root / "lane" / "unmapped.jsonl"),
                ],
            )
            self.assertEqual(nested.returncode, 2, nested.stderr)

    def test_rollback_follows_created_file_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_parent = root / "real"
            alias = root / "alias"
            other = root / "other"
            real_parent.mkdir()
            other.mkdir()
            alias.symlink_to(real_parent)
            destination = alias / "out.jsonl"
            created, identity = tag_write._write_new_jsonl(destination, [{"id": "a"}])
            self.assertTrue((real_parent / "out.jsonl").exists())
            alias.unlink()
            alias.symlink_to(other)
            tag_write._unlink_created_file(created, identity)
            self.assertFalse((real_parent / "out.jsonl").exists())


class TagCliInProcessTests(unittest.TestCase):
    def _source(self, root, tags=None):
        source = root / "in.jsonl"
        source.write_text(
            json.dumps(record(tags or ["MODIFY"])) + "\n", encoding="utf-8"
        )
        return source

    def _stderr_exit(self, args):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            curate_tags.main(args)
        return stderr.getvalue()

    def test_main_writes_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            output = root / "lane" / "out.jsonl"
            manifest = root / "lane" / "man.jsonl"
            unmapped = root / "reports" / "unm.jsonl"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = curate_tags.main(
                    [
                        str(source),
                        "--output-jsonl",
                        str(output),
                        "--manifest-jsonl",
                        str(manifest),
                        "--unmapped-jsonl",
                        str(unmapped),
                    ]
                )
            self.assertEqual(code, 0)
            self.assertTrue(output.is_file())
            self.assertTrue(manifest.is_file())
            self.assertTrue(unmapped.is_file())
            self.assertIn("input_records", json.loads(stdout.getvalue()))

    def test_main_prints_ascii_safe_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root, ["café"])
            stdout = _AsciiStdout()
            with contextlib.redirect_stdout(stdout):
                code = curate_tags.main([str(source)])
            self.assertEqual(code, 0)
            summary = json.loads(stdout.getvalue())
            self.assertEqual(summary["unmapped_tags"][0]["tag"], "café")

    def test_main_rejects_missing_source_without_traceback(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "nope.jsonl"
            stderr = self._stderr_exit([str(missing)])
            self.assertNotIn("Traceback", stderr)

    def test_cli_reports_write_parent_not_a_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            blocker = root / "notdir"
            blocker.write_text("file", encoding="utf-8")
            stderr = self._stderr_exit(
                [str(source), "--output-jsonl", str(blocker / "out.jsonl")]
            )
            self.assertNotIn("Traceback", stderr)

    def test_preflight_requires_distinct_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "out.jsonl"
            output.write_text("x\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "distinct"):
                curate_tags._preflight_destinations([output, output])

    def test_unlink_missing_is_noop(self):
        with tempfile.TemporaryDirectory() as temporary:
            curate_tags._unlink_created_file(Path(temporary) / "absent.jsonl", (0, 0))


if __name__ == "__main__":
    unittest.main()
