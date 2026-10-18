"""Pin the one-shot NELB plants builder (``scripts/build_nelb_plants_jsonl.py``).

The builder reads recovered mill sources through ``git``; here its source
listing, source picker, extractor and committed-catalog reader are replaced by
in-memory fakes built from the committed plants, and its output directory is a
temporary one, so the merge rules and the bytes it writes are checked offline.
"""

from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_nelb_plants_jsonl.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_nelb_plants_jsonl_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILDER = _load_builder()
COMMITTED = BUILDER.cat._read_plants_jsonl(BUILDER.NELB_DIR / BUILDER.PLANTS_FILENAME)


def _round(number: int) -> tuple:
    return tuple(plant for plant in COMMITTED if plant.source_round == number)


def _refusal(*_args):
    raise BUILDER.NelbRefusal(BUILDER.cat.FINDING_FIELD_INVALID, "fake source does not extract")


class _Sources:
    """Fake ``_pick_source``/``_extract_path``: a round maps to plants, ``None`` or a refusal."""

    def __init__(self, rounds: dict[int, object]) -> None:
        self.rounds = rounds
        self.extracted: list[tuple[str, int]] = []

    def pick(self, want: int, _by_round) -> str | None:
        return None if self.rounds[want] is None else f"r{want}.py"

    def extract(self, path: str, want: int):
        self.extracted.append((path, want))
        plants = self.rounds[want]
        if plants == "refuse":
            _refusal()
        return plants


def _run(sources: _Sources, existing):
    with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
        out = Path(tmp) / "nelb"
        for name, value in (
            ("NELB_DIR", out),
            ("_paths_by_round", lambda: {want: [f"r{want}.py"] for want in sources.rounds}),
            ("_load_existing", lambda: existing),
            ("_pick_source", sources.pick),
            ("_extract_path", sources.extract),
        ):
            stack.enter_context(mock.patch.object(BUILDER, name, value))
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            status = BUILDER.main()
        plants_text = (out / BUILDER.PLANTS_FILENAME).read_text(encoding="utf-8")
        header = json.loads((out / BUILDER.CATALOG_FILENAME).read_text(encoding="utf-8"))
    return status, plants_text, header, printed.getvalue()


def _payload(plants) -> str:
    return "".join(
        BUILDER.dumps_exact_json(plant.as_mapping(), ensure_ascii=False, sort_keys=True) + "\n"
        for plant in plants
    )


class FirstExtractTests(unittest.TestCase):
    def test_rounds_that_extract_are_written_and_the_rest_of_the_wave_is_deferred(self) -> None:
        first = _round(1)
        duplicate = dataclasses.replace(first[0], goal="a later round repeats this id")
        sources = _Sources({3: _round(3), 1: first, 2: None, 6: "refuse", 13: (duplicate,)})
        status, plants_text, header, printed = _run(sources, None)

        expected = sorted(first + _round(3), key=lambda plant: (plant.source_round, plant.index))
        self.assertEqual(status, 0)
        self.assertEqual(
            sources.extracted, [("r1.py", 1), ("r3.py", 3), ("r6.py", 6), ("r13.py", 13)]
        )
        self.assertEqual(plants_text, _payload(expected))
        digest = hashlib.sha256(plants_text.encode()).hexdigest()
        self.assertEqual(header["plants_sha256"], digest)
        self.assertEqual(header["rounds"], [1, 3])
        self.assertEqual(header["plant_count"], len(expected))
        self.assertEqual(header["triples"], len(expected) // BUILDER.QUOTA_PER_ROUND)
        deferred = [number for number in range(1, BUILDER.WAVE_MAX + 1) if number not in {1, 3}]
        self.assertEqual(header["extract"]["deferred_rounds"], deferred)
        self.assertEqual(header["extract"]["n_rounds_committed"], 2)
        self.assertEqual(
            printed,
            f"plants={len(expected)} rounds=2 landed_slice=2 "
            f"deferred={len(deferred)} sha256={digest}\n",
        )

    def test_nothing_extracting_writes_nothing(self) -> None:
        sources = _Sources({1: None, 2: "refuse"})
        with self.assertRaises(SystemExit) as caught:
            _run(sources, None)
        self.assertEqual(str(caught.exception), "no plants extracted")


class MergeDeferredTests(unittest.TestCase):
    def test_deferred_rounds_that_now_extract_join_the_committed_plants(self) -> None:
        committed = _round(1) + _round(2)
        replaced = dataclasses.replace(committed[0], goal="re-extracted")
        sources = _Sources({3: _round(3) + (replaced,), 4: None, 5: "refuse"})
        status, plants_text, header, printed = _run(sources, (committed, [5, 3, 4]))

        expected = sorted(
            (replaced,) + committed[1:] + _round(3),
            key=lambda plant: (plant.source_round, plant.index),
        )
        self.assertEqual(status, 0)
        self.assertEqual(sources.extracted, [("r3.py", 3), ("r5.py", 5)])
        self.assertEqual(plants_text, _payload(expected))
        self.assertEqual(header["rounds"], [1, 2, 3])
        self.assertEqual(header["extract"]["deferred_rounds"], [4, 5])
        landed = 3 - len(committed) // BUILDER.QUOTA_PER_ROUND
        self.assertIn(f"rounds=3 landed_slice={landed} deferred=2 ", printed)

    def test_a_merge_that_adds_no_plant_is_refused(self) -> None:
        committed = _round(1)
        sources = _Sources({2: None, 3: "refuse", 1: committed})
        with self.assertRaises(SystemExit) as caught:
            _run(sources, (committed, [1, 2, 3]))
        self.assertEqual(str(caught.exception), "no new plants extracted")


if __name__ == "__main__":
    unittest.main()
