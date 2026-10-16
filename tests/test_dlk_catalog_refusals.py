"""Plant-file refusals of the dlk catalog loader, in the order a caller sees them.

Each case copies the committed ``config/dlk`` into a temporary directory,
rewrites ``plants-r1214.json``, and re-pins its sha256 in ``CATALOG.json`` so
the drift check passes and the plant-file checks behind it decide the outcome.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pipelines.dlk import catalog as cat

PLANT_FILE = "plants-r1214.json"


class DlkPlantFileRefusals(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="dlk-catalog-")
        self.addCleanup(self._tmp.cleanup)

    def _config_dir(self, mutate: Callable[[dict[str, Any]], Any]) -> Path:
        directory = Path(tempfile.mkdtemp(dir=self._tmp.name)) / "dlk"
        shutil.copytree(cat.default_config_dir(), directory)
        plant_path = directory / PLANT_FILE
        payload = mutate(json.loads(plant_path.read_text(encoding="utf-8")))
        blob = json.dumps(payload).encode("utf-8")
        plant_path.write_bytes(blob)
        index_path = directory / cat.CATALOG_FILENAME
        index = json.loads(index_path.read_text(encoding="utf-8"))
        index["plant_files"]["r1214"]["sha256"] = hashlib.sha256(blob).hexdigest()
        index_path.write_text(json.dumps(index), encoding="utf-8")
        return directory

    def _with(self, **changes: Any) -> Path:
        def mutate(payload: dict[str, Any]) -> dict[str, Any]:
            payload.update(changes)
            return payload

        return self._config_dir(mutate)

    def _with_duplicate_slug(self, **changes: Any) -> Path:
        def mutate(payload: dict[str, Any]) -> dict[str, Any]:
            payload["plants"][1] = dict(payload["plants"][0])
            payload.update(changes)
            return payload

        return self._config_dir(mutate)

    def test_a_plant_file_that_is_not_an_object_is_a_type_error(self):
        directory = self._config_dir(lambda payload: [payload])
        with self.assertRaisesRegex(TypeError, rf"^{PLANT_FILE} is not a JSON object$"):
            cat.load_catalog(1214, directory)

    def test_plants_that_are_not_a_list_of_objects_are_refused(self):
        for label, plants in (("missing", None), ("string", "abc"), ("scalar row", [3])):
            directory = self._with(plants=plants)
            with self.subTest(label), self.assertRaisesRegex(
                ValueError, rf"^{PLANT_FILE} \.plants is not a list of objects$"
            ):
                cat.load_catalog(1214, directory)

    def test_a_duplicate_slug_is_refused_before_the_factory_is_read(self):
        directory = self._with_duplicate_slug(factory="other-factory")
        with self.assertRaisesRegex(
            ValueError,
            r"^round r1214 has duplicate plant slugs: \['mongo-findandmodify-leftover-vs-drop'\]$",
        ):
            cat.load_catalog(1214, directory)

    def test_a_foreign_factory_is_refused_before_the_generator(self):
        directory = self._with(factory="other-factory", generator="other-generator")
        with self.assertRaisesRegex(
            ValueError,
            rf"^{PLANT_FILE} factory 'other-factory' != 'distributed-lock-factory'$",
        ):
            cat.load_catalog(1214, directory)

    def test_a_foreign_generator_is_refused(self):
        directory = self._with(generator="other-generator")
        with self.assertRaisesRegex(
            ValueError, rf"^{PLANT_FILE} generator 'other-generator' != 'grok-4\.6'$"
        ):
            cat.load_catalog(1214, directory)

    def test_an_empty_plant_list_loads_as_an_empty_round(self):
        directory = self._with(plants=[])
        catalog = cat.load_catalog(1214, str(directory))
        self.assertEqual(catalog.plants, ())
        self.assertEqual(catalog.source_file, directory / PLANT_FILE)


class DlkConfigDirDefault(unittest.TestCase):
    def test_string_and_omitted_config_dirs_load_the_same_index(self):
        default = cat.default_config_dir()
        self.assertEqual(cat.catalog_index(), cat.catalog_index(str(default)))
        self.assertEqual(cat.load_all(), cat.load_all(default))


if __name__ == "__main__":
    unittest.main()
