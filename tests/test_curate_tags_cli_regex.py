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

from tag_test_support import (  # noqa: E402
    GROUPED_OPTIONAL_REGEX_PATTERNS,
    GROUPED_OPTIONAL_REPEATS,
    INVALID_REGEX_PATTERNS,
    UNSAFE_LINEAR_REGEX_PATTERNS,
    minimal_taxonomy,
    record,
    run_tag_cli,
    write_tag_source,
)


def _pattern_rule(rule_id, pattern):
    return {"id": rule_id, "tag": "decision:accept", "pattern": pattern}


def _unsafe_taxonomy_cases():
    cases = []
    for unsafe_name, pattern in UNSAFE_LINEAR_REGEX_PATTERNS:
        cases.append(
            (f"{unsafe_name}-canonical", minimal_taxonomy(canonical_tag_pattern=pattern))
        )
        cases.append(
            (
                f"{unsafe_name}-rule",
                minimal_taxonomy(pattern_rules=[_pattern_rule("unsafe_regex", pattern)]),
            )
        )
    cases.append(
        (
            "fast-then-pathological",
            minimal_taxonomy(
                pattern_rules=[
                    _pattern_rule("a_fast", "^a+x$"),
                    _pattern_rule("z_pathological", "^(a+)+$"),
                ]
            ),
        )
    )
    return cases


class CliRegexTests(unittest.TestCase):
    def _write_taxonomy(self, root, name, document):
        path = root / name
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def _assert_regex_rejected(self, source, taxonomy, output=None):
        extra = ["--taxonomy", str(taxonomy)]
        if output is not None:
            extra.extend(["--output-jsonl", str(output)])
        result = run_tag_cli(source, extra, timeout=3)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        if output is not None:
            self.assertFalse(output.exists())
        return result

    def test_cli_reports_regex_compile_failures_without_tracebacks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_tag_source(root)
            for exception_name, pattern in INVALID_REGEX_PATTERNS:
                documents = (
                    (
                        "canonical_tag_pattern",
                        minimal_taxonomy(canonical_tag_pattern=pattern),
                    ),
                    (
                        "pattern_rule",
                        minimal_taxonomy(
                            pattern_rules=[_pattern_rule("invalid_regex", pattern)]
                        ),
                    ),
                )
                for site, document in documents:
                    with self.subTest(exception=exception_name, site=site):
                        taxonomy = self._write_taxonomy(
                            root,
                            f"{exception_name.replace('.', '_')}-{site}.json",
                            document,
                        )
                        result = self._assert_regex_rejected(source, taxonomy)
                        self.assertIn("not a valid regex", result.stderr)

    def test_cli_rejects_unsafe_regexes_without_writing_or_tracebacks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_tag_source(root)
            for index, (label, document) in enumerate(_unsafe_taxonomy_cases()):
                with self.subTest(case=label):
                    taxonomy = self._write_taxonomy(root, f"unsafe-{index}.json", document)
                    output = root / f"unsafe-output-{index}.jsonl"
                    result = self._assert_regex_rejected(source, taxonomy, output)
                    self.assertIn("supported linear-time regex subset", result.stderr)

    def test_cli_rejects_grouped_optionals_before_matching_the_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "grouped-optionals-source.jsonl"
            source.write_text(
                json.dumps(record(["a" * GROUPED_OPTIONAL_REPEATS])) + "\n",
                encoding="utf-8",
            )
            for index, (group_kind, pattern) in enumerate(GROUPED_OPTIONAL_REGEX_PATTERNS):
                with self.subTest(group=group_kind):
                    taxonomy = self._write_taxonomy(
                        root,
                        f"grouped-optionals-{index}.json",
                        minimal_taxonomy(
                            pattern_rules=[_pattern_rule(group_kind, pattern)]
                        ),
                    )
                    output = root / f"grouped-optionals-{index}.jsonl"
                    result = self._assert_regex_rejected(source, taxonomy, output)
                    self.assertEqual(result.stdout, "")
                    self.assertIn("supported linear-time regex subset", result.stderr)


if __name__ == "__main__":
    unittest.main()
