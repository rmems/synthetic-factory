"""Check stored outcome semantics without executing candidate source."""
from __future__ import annotations

import ast
import doctest
import math

from . import catalog, executor, vocabulary as cv
from ._contract import bind_import_twin


def _hidden_agrees(got: str, want: str) -> bool:
    if got == want:
        return True
    if any(text.removeprefix("-").isdigit() for text in (got, want)):
        return False
    try:
        left, right = float(got), float(want)
    except ValueError:
        return False
    return (math.isfinite(left) and math.isfinite(right)
            and math.isclose(left, right, rel_tol=executor.FLOAT_REL_TOL,
                             abs_tol=executor.FLOAT_ABS_TOL))


def _hidden_matches(row, case) -> bool:
    status, want = row["status"], case["want"]
    if want is None:
        return status in (cv.ROW_OBSERVED, cv.ROW_ERROR) and "got" in row
    if status in (cv.ROW_ERROR, cv.ROW_FAIL):
        return "got" not in row
    if status != cv.ROW_SUCCESS or "got" not in row:
        return False
    if row["truncated"]:
        # A clipped passing repr must still bind the complete pinned output.
        return (want.startswith(row["got"])
                and catalog.sha256_text(want) == row["got_sha256"])
    return _hidden_agrees(row["got"], want)


def _public_examples(text, function):
    node = catalog.function_node(text, function)
    if node is None:
        return []
    docstring = ast.get_docstring(node, clean=True) or ""
    return [example for example in doctest.DocTestParser().get_examples(docstring)
            if not example.options.get(doctest.SKIP)]


def _clipped_public_matches(row, want, flags) -> bool:
    # Directives may admit many complete outputs for the retained prefix.
    # Those observations remain indeterminate until mandatory fresh replay.
    variable_output = flags & (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE
                               | doctest.IGNORE_EXCEPTION_DETAIL)
    if row["status"] == cv.ROW_FAIL or variable_output:
        return True
    return want.startswith(row["got"]) and catalog.sha256_text(want) == row["got_sha256"]


def _public_want(got, example) -> str:
    if example.exc_msg is not None and not got.endswith("\n"):
        return example.exc_msg.strip().splitlines()[-1]
    return example.want


def _public_matches(row, example) -> bool:
    status = row["status"]
    if status == cv.ROW_ERROR:
        return True  # Exception text alone cannot authenticate execution.
    if status not in (cv.ROW_SUCCESS, cv.ROW_FAIL):
        return False
    flags = sum(flag for flag, enabled in example.options.items() if enabled)
    if example.exc_msg is not None and flags & doctest.IGNORE_EXCEPTION_DETAIL:
        # The harness retains only the final exception line, which may be a
        # multiline message continuation without its type. Replay must decide.
        return True
    got = row["got"]
    want = _public_want(got, example)
    if row["truncated"]:
        return _clipped_public_matches(row, want, flags)
    matched = doctest.OutputChecker().check_output(want, got, flags)
    return matched == (status == cv.ROW_SUCCESS)


def _suite_matches(rows, cases, matches) -> bool:
    for row in rows:
        index = int(row["id"].split(":")[1])
        if index >= len(cases) or not matches(row, cases[index]):
            return False
    return True


def outcomes_match(record) -> bool:
    """Require public and hidden rows to obey the pinned harness output contract."""
    scenario = record["scenario"]
    function = scenario["source"]["upstream"]["function"]
    original = _public_examples(scenario["broken_program"]["files"][cv.PROGRAM_FILENAME], function)
    repaired = _public_examples(
        record["candidate_prediction"]["predicted_repair"]["files"][cv.PROGRAM_FILENAME],
        function)
    cases = record["oracle"]["configuration"]["hidden_check"]["cases"]
    for name, phase in record["result"]["phases"].items():
        if phase is None:
            continue
        examples = repaired if name == cv.PHASE_REPAIRED else original
        if not _suite_matches(phase["public"], examples, _public_matches):
            return False
        if not _suite_matches(phase["hidden"], cases, _hidden_matches):
            return False
    return True


bind_import_twin(__name__)
