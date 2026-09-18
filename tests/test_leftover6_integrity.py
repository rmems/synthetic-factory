"""A full archived catalog cannot redefine its own provenance or cardinality."""

import copy
import json
import unittest
from unittest import mock

from pipelines.leftover6 import catalog
from pipelines.leftover6.catalog_extract import dumps_jsonl
from tests import test_leftover6 as support


class CatalogIntegrity(unittest.TestCase):
    def test_self_consistent_truncation_is_refused(self):
        header = json.loads(support.CATALOG_JSON.read_bytes())
        rows = support._catalog_rows()
        del rows[15]
        header["catalogs"][0].update(n_rows=15, last_slug=rows[14]["slug"])
        header.update(n_pair_rows_committed=31, n_pair_rows_extracted=31)
        with support._fixture(header=json.dumps(header), pairs=dumps_jsonl(rows)) as root:
            with self.assertRaises(catalog.CatalogError):
                catalog.load_catalog(root)

    def test_each_mill_descriptor_field_is_independently_pinned(self):
        original = json.loads(support.CATALOG_JSON.read_bytes())
        for index, mill in enumerate(original["catalogs"]):
            for key, value in mill.items():
                with self.subTest(index=index, field=key):
                    header = copy.deepcopy(original)
                    header["catalogs"][index][key] = value + 1 if isinstance(value, int) else value + "-forged"
                    with support._fixture(header=json.dumps(header)) as root:
                        with self.assertRaises(catalog.CatalogError):
                            catalog.load_catalog(root)

    def test_plant_kind_is_closed(self):
        rows = [json.loads(line) for line in support.PLANTS_JSONL.read_bytes().splitlines()]
        rows[0]["kind"] = "not-sbox"
        with support._fixture(plants=dumps_jsonl(rows)) as root:
            with self.assertRaises(catalog.CatalogError):
                catalog.load_catalog(root)

    def test_an_explicit_file_path_must_name_the_catalog_header(self):
        with support._fixture() as root:
            for name in ("missing.json", "candidate.json"):
                with self.subTest(name=name), self.assertRaises(catalog.CatalogError):
                    catalog.load_catalog(root / name)
            self.assertEqual(catalog.load_catalog(root / "CATALOG.json"), catalog.load_catalog(root))

    def test_returned_rows_are_immutable(self):
        loaded = catalog.load_catalog()
        for row in (loaded.pairs[0], loaded.plants[0]):
            with self.subTest(kind=row["kind"]), self.assertRaises(TypeError):
                row["kind"] = "forged"

    def test_legacy_probe_covers_every_commit_that_extraction_reads(self):
        with mock.patch.object(support.subprocess, "check_output", return_value=b"") as probe:
            self.assertTrue(support._legacy_available())
        refs = {call.args[0][-1] for call in probe.call_args_list}
        self.assertEqual(refs, {f"{mill.preserve_commit}^{{commit}}" for mill in catalog.CATALOG.catalogs})
