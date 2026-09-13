#!/usr/bin/env python3
"""Tests for card-schema declaration file I/O.

Covers ``card_schema.load`` / ``declared_datasets`` / ``declaration_path``:
missing vs. malformed declarations, symlink and unsafe-root rejection, and
misnamed declaration files.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
sys.path.insert(0, str(REPO / "scripts"))

import card_schema  # noqa: E402

MINIMAL = {
    "version": 1,
    "dataset": "example-trajectories",
    "note": "Declared because raw meta shapes vary.",
    "features": [
        {"name": "id", "dtype": "string"},
        {"name": "meta", "dtype": "json"},
    ],
}


def write_declaration(root: Path, dataset: str, payload: dict) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{dataset}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class DeclarationLoadingTests(unittest.TestCase):
    def test_missing_declaration_returns_none_and_bad_one_raises(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "card-schemas"
            root.mkdir()
            self.assertIsNone(card_schema.load("example-trajectories", root))

            write_declaration(root, "example-trajectories", {**MINIMAL, "version": 9})
            with self.assertRaisesRegex(card_schema.CardSchemaError, "version must be 1"):
                card_schema.load("example-trajectories", root)

            (root / "example-trajectories.json").write_text("{not json", encoding="utf-8")
            with self.assertRaisesRegex(card_schema.CardSchemaError, "cannot read"):
                card_schema.load("example-trajectories", root)

    def test_a_symlinked_declaration_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "card-schemas"
            root.mkdir()
            outside = Path(td) / "outside.json"
            outside.write_text(json.dumps(MINIMAL), encoding="utf-8")
            (root / "example-trajectories.json").symlink_to(outside)
            with self.assertRaisesRegex(card_schema.CardSchemaError, "unsafe card schema entry"):
                card_schema.load("example-trajectories", root)
            with self.assertRaisesRegex(card_schema.CardSchemaError, "unsafe card schema"):
                card_schema.declared_datasets(root)

    def test_an_unsafe_schema_root_is_rejected_by_discovery_and_loading(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            outside = base / "outside"
            outside.mkdir()
            write_declaration(outside, "example-trajectories", MINIMAL)
            linked = base / "linked"
            linked.symlink_to(outside, target_is_directory=True)
            regular_file = base / "not-a-directory"
            regular_file.write_text("x", encoding="utf-8")

            for root in (linked, regular_file):
                with self.subTest(root=root):
                    with self.assertRaisesRegex(
                        card_schema.CardSchemaError, "unsafe card schema root"
                    ):
                        card_schema.declared_datasets(root)
                    with self.assertRaisesRegex(
                        card_schema.CardSchemaError, "unsafe card schema root"
                    ):
                        card_schema.load("example-trajectories", root)

            missing = base / "missing"
            self.assertEqual(card_schema.declared_datasets(missing), [])
            self.assertIsNone(card_schema.load("example-trajectories", missing))

    def test_declared_datasets_refuses_a_misnamed_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "card-schemas"
            root.mkdir()
            write_declaration(root, "example-trajectories", MINIMAL)
            self.assertEqual(card_schema.declared_datasets(root), ["example-trajectories"])
            (root / "notes.yaml").write_text("x\n", encoding="utf-8")
            with self.assertRaisesRegex(
                card_schema.CardSchemaError, "expected <dataset>.json"
            ):
                card_schema.declared_datasets(root)


if __name__ == "__main__":
    unittest.main()
