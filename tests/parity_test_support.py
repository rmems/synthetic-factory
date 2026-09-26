#!/usr/bin/env python3
"""Assertions the hardware-parity and NIR-equivalence test suites share."""

import json
import tempfile
from pathlib import Path


def assert_catalog_rejected_after_clean_projection(case, views, retained, errors):
    # The projection itself is clean -- one view per retained record, none
    # of them flagged -- so the catalog check is the only thing that can
    # reject this batch.
    case.assertEqual(
        [view["id"] for view in views], [record["id"] for record in retained]
    )
    case.assertFalse([view["id"] for view in views if view["parity_failed"]])
    case.assertTrue(
        any(
            "does not cover the scenario catalog" in error
            and "TRAINING_VIEW_HIDES_FAILURE" in error
            for error in errors
        ),
        errors,
    )


def assert_absurd_nesting_is_a_line_error(case, read_jsonl):
    # A syntactically valid but absurdly nested line must be a line-level
    # parse error, not a decoder RecursionError that aborts the scan. The
    # depth at which the decoder gives up is a platform property (stack
    # budget), so probe for one it refuses rather than hard-coding it.
    depth = 100_000
    while depth <= 3_200_000:
        try:
            json.loads("[" * depth + "]" * depth)
        except RecursionError:
            break
        depth *= 2
    else:
        case.skipTest("this platform's decoder accepts 3.2M-deep nesting")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "batch.jsonl"
        path.write_text(
            "[" * depth + "]" * depth + '\n{"id": "after"}\n',
            encoding="utf-8",
        )
        records, errors = read_jsonl(path)
        case.assertEqual(records, [{"id": "after"}])
        case.assertEqual(len(errors), 1)
        case.assertIn("JSON parse error", errors[0])
