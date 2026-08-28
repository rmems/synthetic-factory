import contextlib
import io
import json
import subprocess
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
from tag_test_support import (  # noqa: E402
    GROUPED_OPTIONAL_REGEX_PATTERNS,
    GROUPED_OPTIONAL_REPEATS,
    INVALID_REGEX_PATTERNS,
    PIPELINES,
    UNSAFE_LINEAR_REGEX_PATTERNS,
    _preflight_destinations,
    _write_destinations,
    minimal_taxonomy,
    record,
)


class CliTests(unittest.TestCase):
    def _source(self, root):
        source = root / "corpus.jsonl"
        source.write_text(
            json.dumps(record(["MODIFY", "tokamak"]), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return source

    def test_cli_writes_new_files_and_refuses_clobber(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            output = root / "new" / "tags.jsonl"
            manifest = root / "new" / "manifest.jsonl"
            unmapped = root / "new" / "unmapped.jsonl"
            command = [
                sys.executable,
                str(PIPELINES / "curate_tags.py"),
                str(source),
                "--output-jsonl",
                str(output),
                "--manifest-jsonl",
                str(manifest),
                "--unmapped-jsonl",
                str(unmapped),
            ]

            first = subprocess.run(command, capture_output=True, text=True, check=False)
            second = subprocess.run(command, capture_output=True, text=True, check=False)

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(len(output.read_text().splitlines()), 1)
            self.assertEqual(len(manifest.read_text().splitlines()), 1)
            self.assertEqual(
                json.loads(unmapped.read_text()), {"tag": "tokamak", "count": 1}
            )
            summary = json.loads(first.stdout)
            self.assertEqual(summary["unmapped_unique_tags"], 1)

    def test_cli_preflights_all_destinations_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            output = root / "new" / "tags.jsonl"
            manifest = root / "existing-manifest.jsonl"
            manifest.write_text("sentinel\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_tags.py"),
                    str(source),
                    "--output-jsonl",
                    str(output),
                    "--manifest-jsonl",
                    str(manifest),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            self.assertEqual(manifest.read_text(), "sentinel\n")

    def test_destination_race_preserves_competitor_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "output.jsonl"
            manifest = root / "manifest.jsonl"
            _preflight_destinations([output, manifest])
            manifest.write_text("competitor\n", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                _write_destinations([(output, [{"id": "x"}]), (manifest, [])])

            self.assertFalse(output.exists())
            self.assertEqual(manifest.read_text(encoding="utf-8"), "competitor\n")

    def test_cli_rejects_destinations_that_contain_one_another(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            output = root / "artifact"
            manifest = output / "manifest.jsonl"

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_tags.py"),
                    str(source),
                    "--output-jsonl",
                    str(output),
                    "--manifest-jsonl",
                    str(manifest),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())

    def test_cli_refuses_any_destination_under_outputs_raw(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            output = root / "outputs" / "raw" / "forbidden.jsonl"

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_tags.py"),
                    str(source),
                    "--output-jsonl",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())

    def test_cli_refuses_a_lexical_raw_path_through_a_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            external = root / "external-raw"
            external.mkdir()
            raw = root / "outputs" / "raw"
            raw.parent.mkdir()
            raw.symlink_to(external, target_is_directory=True)
            output = raw / "forbidden.jsonl"

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_tags.py"),
                    str(source),
                    "--output-jsonl",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((external / "forbidden.jsonl").exists())

    def test_cli_refuses_to_overwrite_its_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            before = source.read_text()

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_tags.py"),
                    str(source),
                    "--output-jsonl",
                    str(source),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(source.read_text(), before)

    def test_cli_rejects_an_invalid_taxonomy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            taxonomy = root / "broken.json"
            taxonomy.write_text("{", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_tags.py"),
                    str(source),
                    "--taxonomy",
                    str(taxonomy),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)

    def test_cli_reports_regex_compile_failures_without_tracebacks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)

            for exception_name, pattern in INVALID_REGEX_PATTERNS:
                documents = (
                    (
                        "canonical_tag_pattern",
                        minimal_taxonomy(canonical_tag_pattern=pattern),
                    ),
                    (
                        "pattern_rule",
                        minimal_taxonomy(
                            pattern_rules=[
                                {
                                    "id": "invalid_regex",
                                    "tag": "decision:accept",
                                    "pattern": pattern,
                                }
                            ]
                        ),
                    ),
                )
                for site, document in documents:
                    with self.subTest(exception=exception_name, site=site):
                        taxonomy = root / (
                            f"{exception_name.replace('.', '_')}-{site}.json"
                        )
                        taxonomy.write_text(json.dumps(document), encoding="utf-8")
                        result = subprocess.run(
                            [
                                sys.executable,
                                str(PIPELINES / "curate_tags.py"),
                                str(source),
                                "--taxonomy",
                                str(taxonomy),
                            ],
                            capture_output=True,
                            text=True,
                            check=False,
                        )

                        self.assertEqual(result.returncode, 2, result.stderr)
                        self.assertIn("not a valid regex", result.stderr)
                        self.assertNotIn("Traceback", result.stderr)

    def test_cli_rejects_unsafe_regexes_without_writing_or_tracebacks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            cases = []
            for unsafe_name, pattern in UNSAFE_LINEAR_REGEX_PATTERNS:
                cases.extend(
                    [
                        (
                            f"{unsafe_name}-canonical",
                            minimal_taxonomy(canonical_tag_pattern=pattern),
                        ),
                        (
                            f"{unsafe_name}-rule",
                            minimal_taxonomy(
                                pattern_rules=[
                                    {
                                        "id": "unsafe_regex",
                                        "tag": "decision:accept",
                                        "pattern": pattern,
                                    }
                                ]
                            ),
                        ),
                    ]
                )
            cases.append(
                (
                    "fast-then-pathological",
                    minimal_taxonomy(
                        pattern_rules=[
                            {
                                "id": "a_fast",
                                "tag": "decision:accept",
                                "pattern": "^a+x$",
                            },
                            {
                                "id": "z_pathological",
                                "tag": "decision:accept",
                                "pattern": "^(a+)+$",
                            },
                        ]
                    ),
                )
            )

            for index, (label, document) in enumerate(cases):
                with self.subTest(case=label):
                    taxonomy = root / f"unsafe-{index}.json"
                    output = root / f"unsafe-output-{index}.jsonl"
                    taxonomy.write_text(json.dumps(document), encoding="utf-8")
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(PIPELINES / "curate_tags.py"),
                            str(source),
                            "--taxonomy",
                            str(taxonomy),
                            "--output-jsonl",
                            str(output),
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn(
                        "supported linear-time regex subset", result.stderr
                    )
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertFalse(output.exists())

    def test_cli_rejects_grouped_optionals_before_matching_the_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "grouped-optionals-source.jsonl"
            source.write_text(
                json.dumps(record(["a" * GROUPED_OPTIONAL_REPEATS])) + "\n",
                encoding="utf-8",
            )

            for index, (group_kind, pattern) in enumerate(
                GROUPED_OPTIONAL_REGEX_PATTERNS
            ):
                with self.subTest(group=group_kind):
                    taxonomy = root / f"grouped-optionals-{index}.json"
                    output = root / f"grouped-optionals-{index}.jsonl"
                    taxonomy.write_text(
                        json.dumps(
                            minimal_taxonomy(
                                pattern_rules=[
                                    {
                                        "id": group_kind,
                                        "tag": "decision:accept",
                                        "pattern": pattern,
                                    }
                                ]
                            )
                        ),
                        encoding="utf-8",
                    )

                    result = subprocess.run(
                        [
                            sys.executable,
                            str(PIPELINES / "curate_tags.py"),
                            str(source),
                            "--taxonomy",
                            str(taxonomy),
                            "--output-jsonl",
                            str(output),
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=3,
                    )

                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertIn(
                        "supported linear-time regex subset", result.stderr
                    )
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertFalse(output.exists())


class TagCliInProcessTests(unittest.TestCase):
    def test_main_writes_outputs_and_rejects_unsafe_destinations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "in.jsonl"
            source.write_text(
                json.dumps(record(["MODIFY"])) + "\n", encoding="utf-8"
            )
            output = root / "out.jsonl"
            manifest = root / "man.jsonl"
            unmapped = root / "unm.jsonl"
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

            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ):
                curate_tags.main([str(source), "--output-jsonl", str(source)])
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ):
                curate_tags.main([str(source), "--output-jsonl", str(output)])
            nested = root / "nested"
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ):
                curate_tags.main(
                    [
                        str(source),
                        "--output-jsonl",
                        str(nested / "a.jsonl"),
                        "--manifest-jsonl",
                        str(nested),
                    ]
                )
            raw = root / "outputs" / "raw" / "x.jsonl"
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ):
                curate_tags.main([str(source), "--output-jsonl", str(raw)])
            missing_taxonomy = root / "missing-taxonomy.json"
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ):
                curate_tags.main(
                    [
                        str(source),
                        "--taxonomy",
                        str(missing_taxonomy),
                        "--output-jsonl",
                        str(root / "fresh.jsonl"),
                    ]
                )
            missing_source = root / "nope.jsonl"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                curate_tags.main([str(missing_source)])
            self.assertNotIn("Traceback", stderr.getvalue())
            curate_tags._unlink_created_file(root / "absent.jsonl", (0, 0))
            with self.assertRaisesRegex(ValueError, "distinct"):
                curate_tags._preflight_destinations([output, output])

    def test_cli_reports_write_parent_not_a_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "in.jsonl"
            source.write_text(json.dumps(record(["MODIFY"])) + "\n", encoding="utf-8")
            blocker = root / "notdir"
            blocker.write_text("file", encoding="utf-8")
            dest = blocker / "out.jsonl"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                curate_tags.main([str(source), "--output-jsonl", str(dest)])
            self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
