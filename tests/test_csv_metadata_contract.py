"""Catalog metadata snapshots and structured row-refusal classifications."""

from dataclasses import replace
import json
import unittest

from pipelines.csv_mill import catalog
from pipelines.csv_mill._contract import CsvRefusal, PAIR_KEYS
from pipelines.csv_mill.catalog_validation import _plant_from_row
from tests.test_csv import COMMITTED, invoke


class MetadataContract(unittest.TestCase):
    def test_excessive_metadata_depth_has_a_coded_refusal(self):
        original = catalog.load_catalog(COMMITTED)
        nested = "leaf"
        for _ in range(800):
            nested = [nested]
        with self.assertRaises(CsvRefusal) as caught:
            replace(original, meta={"extra": nested})
        self.assertEqual(caught.exception.code, "CATALOG_FIELD_INVALID")

    def test_loaded_metadata_is_recursively_read_only(self):
        loaded = catalog.load_catalog(COMMITTED)
        with self.assertRaises(TypeError):
            loaded.meta['catalog_id'] = 'forged'
        with self.assertRaises(TypeError):
            loaded.meta['source']['commit'] = 'forged'
        with self.assertRaises(TypeError):
            loaded.meta['mills'][0]['source'] = 'forged'
        self.assertIsInstance(loaded.meta['mills'], tuple)

    def test_constructor_metadata_is_an_independent_recursive_snapshot(self):
        original = catalog.load_catalog(COMMITTED)
        raw = json.loads((COMMITTED / 'CATALOG.json').read_text())
        snapshot = replace(original, meta=raw)
        expected_source = raw['source']['commit']
        raw['source']['commit'] = 'forged'
        raw['mills'][0]['source'] = 'forged'
        raw['mills'].clear()
        self.assertEqual(snapshot.meta['source']['commit'], expected_source)
        self.assertEqual(snapshot.meta['mills'][0]['source'], original.mills[0].source)
        self.assertEqual(snapshot.plants, original.plants)
        self.assertEqual(snapshot.mills, original.mills)
        self.assertEqual(snapshot.plant(original.plants[0].plant_id), original.plants[0])

    def test_catalog_check_json_does_not_serialize_readonly_metadata(self):
        code, out, err = invoke(['catalog-check', '--json'])
        self.assertEqual(code, 0)
        self.assertEqual(err, '')
        self.assertEqual(json.loads(out)['plants'], 16)


class PlantRefusalCodes(unittest.TestCase):
    def setUp(self):
        self.row = json.loads((COMMITTED / 'plants.jsonl').read_text().splitlines()[0])

    def _assert_refusal(self, row, expected_code):
        with self.assertRaises(CsvRefusal) as caught:
            _plant_from_row(row, 'plant')
        self.assertEqual(caught.exception.code, expected_code)
        return str(caught.exception)

    def test_all_required_fields_report_missing_when_absent(self):
        for key in (*PAIR_KEYS, 'mill_id', 'plant_id', 'source', 'base_round', 'index'):
            with self.subTest(key=key):
                row = dict(self.row)
                del row[key]
                self._assert_refusal(row, 'PLANT_FIELD_MISSING')

    def test_present_invalid_text_reports_invalid(self):
        for key in (*PAIR_KEYS, 'mill_id', 'plant_id', 'source'):
            for value in (None, 7, '', ' ', '\ud800'):
                with self.subTest(key=key, value=value):
                    self._assert_refusal(dict(self.row, **{key: value}), 'PLANT_FIELD_INVALID')

    def test_present_invalid_numbers_report_invalid(self):
        for key in ('base_round', 'index'):
            for value in (None, True, '1', -1):
                with self.subTest(key=key, value=value):
                    self._assert_refusal(dict(self.row, **{key: value}), 'PLANT_FIELD_INVALID')

    def test_pair_fields_still_validate_before_identity(self):
        row = dict(self.row, slug=None)
        del row['mill_id']
        message = self._assert_refusal(row, 'PLANT_FIELD_INVALID')
        self.assertIn('plant.slug', message)
        row['slug'] = self.row['slug']
        message = self._assert_refusal(row, 'PLANT_FIELD_MISSING')
        self.assertIn('plant.mill_id', message)


if __name__ == '__main__':
    unittest.main()
