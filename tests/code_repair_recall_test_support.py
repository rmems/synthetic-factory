"""Shared surface of the recall-probe tests: the smoke run, synthetic completions, the CLI.

Both import forms put ``pipelines/`` and ``tests/`` on ``sys.path`` before the
family modules load, so ``code_repair`` resolves to the package the other
``test_code_repair_*`` modules use.
"""

import contextlib
import io
import json
import shutil
import sys
import tempfile
import tokenize
from pathlib import Path

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS.parent / "pipelines"))

from code_repair import lineage, recall_probe
from code_repair_test_support import catalog, cli, smoke_run, views
from code_repair_test_support import vocabulary as cv

NO_EVIDENCE, DOCSTRING_ONLY = cv.RECALL_VARIANT_NO_EVIDENCE, cv.RECALL_VARIANT_DOCSTRING_ONLY
PLACEHOLDER_LINE = "    ...\n"
UNKNOWN_ID = "pfr-0-99999"


def smoke_records(positive):
    """The smoke run's records, in run order, that are (or are not) positive examples."""

    return [r for r in smoke_run()[1] if views.is_positive(r) == positive]


def positives():
    return smoke_records(True)


def rejected():
    return smoke_records(False)


def broken_of(record):
    return record["scenario"]["broken_program"]["files"][cv.PROGRAM_FILENAME]


def function_of(record):
    return record["scenario"]["source"]["upstream"]["function"]


def shown_code(prompt):
    """The first fenced Python block of a prompt."""

    return prompt.split("```python\n", 1)[1].split("```", 1)[0]


def _renamed_token(token, names):
    return token.type == tokenize.NAME and token.string in names


def rename_identifiers(text, names):
    """Every NAME token in ``names`` renamed consistently; strings and comments untouched."""

    lines = text.split("\n")
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    edits = [(t.start, t.end, f"renamed_{t.string}") for t in tokens if _renamed_token(t, names)]
    for (row, start), (_row, end), replacement in reversed(edits):
        lines[row - 1] = lines[row - 1][:start] + replacement + lines[row - 1][end:]
    return "\n".join(lines)


def renamed_repair(record):
    """The repaired module with its function and parameters renamed: same structure, new text."""

    repaired = views.completion_of(record)
    node = catalog.function_node(repaired, function_of(record))
    return rename_identifiers(repaired, {node.name, *(arg.arg for arg in node.args.args)})


def verdict(exact, structural, unparsable):
    """A ``score_completion`` verdict, spelled positionally."""

    return {"exact": exact, "structural": structural, "unparsable": unparsable}


def structure_of(text):
    return lineage.structure_digest(text)


def invoke(argv):
    """``cli.run(argv)`` with stdout and stderr captured: ``(code, stdout, stderr)``."""

    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


def write_lines(path, lines):
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    return path


def completion_lines(rows):
    """One JSONL line per ``(record, variant, completion)``."""

    return [json.dumps({"id": r["id"], "variant": v, "completion": c}) for r, v, c in rows]


class ProbeTree:
    """Mixin: a temporary root holding the emitted prompts of the smoke run.

    Use it as ``class Name(ProbeTree, unittest.TestCase)``. It is deliberately not a
    ``TestCase`` itself, so the loader never collects it as a test class with no tests,
    and its ``setUp`` runs before the ``TestCase`` one in the method resolution order.
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-recall-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        _summary, _records, self.run_dir = smoke_run()
        self.prompts = self.root / "probe" / recall_probe.PROMPTS_FILENAME
        recall_probe.emit(recall_probe.EmitRequest(self.run_dir, self.root / "probe"))

    def score(self, completions, prompts=None, out="report.json"):
        request = recall_probe.ScoreRequest(prompts or self.prompts, completions, self.run_dir,
                                            self.root / out)
        return recall_probe.score(request)

    def completions(self, rows, name="completions.jsonl"):
        return write_lines(self.root / name, completion_lines(rows))
