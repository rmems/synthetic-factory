"""Temp catalog trees and refusal checks for the mill public-branch suites.

The azr, cei, dbc, lef and obs suites drive each package's public loaders and
extractors against mutated copies of the committed catalogs. Every copy lives
in a temporary directory that the test case removes on cleanup, so nothing is
written under the repository and no committed catalog is edited.
"""

from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import json
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
DELETE = object()
DEEP_DEPTH = 600


def scratch_dir(case) -> Path:
    """A fresh temporary directory removed when ``case`` cleans up."""

    tmp = tempfile.TemporaryDirectory(prefix="mill-public-")
    case.addCleanup(tmp.cleanup)
    return Path(tmp.name)


def compact(row) -> str:
    """One compact JSON object line, keys sorted, no trailing newline."""

    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def jsonl_bytes(rows) -> bytes:
    """LF-framed compact JSONL bytes for ``rows``."""

    return "".join(compact(row) + "\n" for row in rows).encode("utf-8")


def read_jsonl(path: Path) -> list:
    """Every JSON object line of a committed JSONL file."""

    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def edited(document, path, value):
    """A deep copy of ``document`` with ``path`` set to ``value`` (removed for ``DELETE``)."""

    result = copy.deepcopy(document)
    *parents, leaf = path
    target = result
    for key in parents:
        target = target[key]
    if value is DELETE:
        del target[leaf]
    else:
        target[leaf] = value
    return result


def setter(*path_and_value):
    """A document edit that sets (or ``DELETE``s) the value at one key path."""

    *path, value = path_and_value
    return lambda document: edited(document, tuple(path), value)


def recounted_mills(pins, rows) -> list:
    """The committed mill ``pins`` for the mills ``rows`` name, with recounted plant counts."""

    by_id = {mill["mill_id"]: mill for mill in pins}
    counts: dict[str, int] = {}
    for mill_id in (row.get("mill_id") for row in rows if isinstance(row, dict)):
        if mill_id in by_id:
            counts[mill_id] = counts.get(mill_id, 0) + 1
    return [dict(by_id[mill_id], plant_count=count) for mill_id, count in counts.items()]


def write_tree(case, files) -> Path:
    """A temp directory holding ``files`` ({name: bytes or text})."""

    directory = scratch_dir(case)
    for name, content in files.items():
        data = content.encode("utf-8") if isinstance(content, str) else content
        (directory / name).write_bytes(data)
    return directory


@contextlib.contextmanager
def refusal(case, error_type, fragment, code=None):
    """Assert one ``error_type`` whose text holds ``fragment`` (and whose ``code`` matches)."""

    with case.assertRaises(error_type) as caught:
        yield caught
    if code is not None:
        case.assertEqual(caught.exception.code, code)
    case.assertIn(fragment, str(caught.exception))


def assert_each_refused(case, error_type, call, cases) -> None:
    """``call(argument)`` refuses for every ``(argument, fragment[, code])`` case."""

    for argument, fragment, *code in cases:
        with case.subTest(fragment=fragment), refusal(case, error_type, fragment, *code):
            call(argument)


def parse_expr(text: str) -> ast.expr:
    return ast.parse(text, mode="eval").body


def deep_negation() -> str:
    """``--…-1`` nested ``DEEP_DEPTH`` unary operators deep; main evaluates it to 1."""

    return "-" * DEEP_DEPTH + "1"


def deep_concatenation() -> str:
    """``'a' + 'a' + …`` nested ``DEEP_DEPTH`` binary operators deep."""

    return " + ".join(["'a'"] * (DEEP_DEPTH + 1))


class SharedExtractSurfaceCases:
    """The public ``catalog_ast`` / ``catalog_extract`` surface azr, dbc and lef share.

    A subclass mixes this into ``unittest.TestCase`` and sets ``ast_module`` and
    ``extract_module``. The depth-600 chains pin main's results.
    """

    ast_module = None
    extract_module = None

    def literal(self, text: str, env=None):
        return self.ast_module.literal_value(parse_expr(text), env)

    def test_assignment_names_read_annotated_chained_and_other_statements(self):
        cases = (("X: int = 1", ("X",)), ("a = b = 1", ("a", "b")), ("x += 1", ()))
        for text, expected in cases:
            node = ast.parse(text).body[0]
            with self.subTest(text=text):
                self.assertEqual(self.ast_module.assignment_names(node), expected)

    def test_constant_f_strings_resolve_and_other_f_strings_stay_unset(self):
        env = {"NAME": "a", "COUNT": 3, "RATIO": 1.5}
        self.assertEqual(self.literal('f"{NAME}-y"', env), "a-y")
        self.assertEqual(self.literal('f"{COUNT}"', env), "3")
        for text in ('f"{MISSING}"', 'f"{RATIO}"'):
            with self.subTest(text=text):
                self.assertIs(self.literal(text, env), self.ast_module.UNSET)

    def test_depth_600_negation_chain_evaluates(self):
        self.assertEqual(self.literal(deep_negation(), {}), 1)

    def test_depth_600_concatenation_chain_evaluates(self):
        self.assertEqual(self.literal(deep_concatenation(), {}), "a" * (DEEP_DEPTH + 1))

    def test_write_catalog_document_writes_the_dumped_document(self):
        document = self.extract_module.catalog_document([])
        destination = scratch_dir(self) / "CATALOG.json"
        written = self.extract_module.write_catalog_document(document, destination)
        self.assertEqual(written, destination)
        dumped = self.extract_module.dumps_catalog(document)
        self.assertEqual(destination.read_text(encoding="utf-8"), dumped)
