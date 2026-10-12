"""Pin ``mac.catalog`` load/check refusals and the order they fire in.

Each case writes a perturbed copy of ``CATALOG.json`` (and ``plants.jsonl``
when the plants change) into a temporary directory and checks the first
refusal ``catalog_check`` raises.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from mac import catalog as cat
from mac._contract import MacRefusal

_PACKAGE = REPO / "pipelines" / "mac"
_CATALOG = json.loads((_PACKAGE / "CATALOG.json").read_text(encoding="utf-8"))
_PLANTS = (_PACKAGE / "plants.jsonl").read_text(encoding="utf-8")
_LINES = _PLANTS.splitlines()


def _check(mutate=None, plants: str | None = None) -> str:
    """Run ``catalog_check`` on a perturbed copy; return the refusal text."""
    document = copy.deepcopy(_CATALOG)
    body = _PLANTS if plants is None else plants
    if plants is not None:
        document["plants_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if mutate is not None:
        mutate(document)
    with tempfile.TemporaryDirectory(prefix="mac-pins-") as td:
        root = Path(td)
        (root / "CATALOG.json").write_text(json.dumps(document), encoding="utf-8")
        (root / "plants.jsonl").write_text(body, encoding="utf-8")
        try:
            cat.catalog_check(root / "CATALOG.json")
        except MacRefusal as exc:
            return str(exc)
    return "ok"


class CatalogPinTests(unittest.TestCase):
    def test_committed_copy_passes(self):
        self.assertEqual(_check(), "ok")

    def test_identity_provenance_and_plants_pin_refusals(self):
        cases = (
            (lambda d: d.pop("schema"), "CATALOG_FIELD_MISSING: CATALOG.json missing ['schema']"),
            (lambda d: d.update(family="x", factory="y"), "CATALOG_FIELD_INVALID: family 'x' != mac"),
            (lambda d: d.update(source=[]), "CATALOG_FIELD_INVALID: source must be an object"),
            (lambda d: d["source"].update(method="exec"), "CATALOG_FIELD_INVALID: source.method must be"),
            (lambda d: d["source"].update(exec=0), "CATALOG_FIELD_INVALID: source.exec must be false"),
            (lambda d: d.update(extract=[]), "CATALOG_FIELD_INVALID: extract must be an object"),
            (lambda d: d.update(sources=[]), "CATALOG_EMPTY: catalog has no source pins"),
            (lambda d: d.update(plants_filename="x.jsonl"), "CATALOG_FIELD_INVALID: plants_filename 'x.jsonl'"),
            (lambda d: d.update(plants_sha256="ABC"), "CATALOG_FIELD_INVALID: plants_sha256 is not a lowercase"),
            (lambda d: d.update(plants_sha256="0" * 64), "CATALOG_SHA256_MISMATCH: plants.jsonl digest"),
            (lambda d: d["sources"][0].update(sha256="A" * 64), "CATALOG_FIELD_INVALID: sources[0].sha256 is not"),
        )
        for mutate, prefix in cases:
            with self.subTest(prefix=prefix):
                self.assertTrue(_check(mutate).startswith(prefix), _check(mutate))

    def test_duplicate_slugs_are_refused(self):
        message = _check(plants="\n".join([*_LINES, _LINES[0]]) + "\n")
        self.assertTrue(message.startswith("CATALOG_DUPLICATE_FAMILY: slug "), message)

    def test_extract_counts_must_agree_with_the_pins(self):
        cases = (
            (lambda d: d["sources"][1].update(n_rows=0), "a catalog source pin has n_rows < 1"),
            (lambda d: d["extract"].update(full_row_count=1), "extract.full_row_count 1 != 1401"),
            (lambda d: d["extract"].update(committed_rows=1), "extract.committed_rows drifted"),
            (lambda d: d["extract"].update(deferred_rows="0"), "extract.deferred_rows must be a non-negative int"),
            (lambda d: d["extract"].update(deferred_rows=-1), "extract.deferred_rows must be a non-negative int"),
            (lambda d: d["extract"].update(deferred_rows=3), "extract committed + deferred rows must equal"),
            (lambda d: d["extract"].update(full_source_files=1), "extract.full_source_files drifted"),
        )
        for mutate, fragment in cases:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, _check(mutate))


if __name__ == "__main__":
    unittest.main()
