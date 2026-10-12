"""The RLB catalog refuses any identity drift with one fixed message per field."""

import dataclasses
import unittest

from pipelines.rlb import CATALOG, CatalogError
from pipelines.rlb.catalog import _refuse_identity

MISMATCH = "catalog identity does not match the reviewed RLB family"


class RefuseIdentity(unittest.TestCase):
    def test_the_committed_catalog_passes(self):
        self.assertIsNone(_refuse_identity(CATALOG))

    def test_family_factory_and_generator_drift_share_one_message(self):
        for field in ("family", "factory", "generator"):
            drifted = dataclasses.replace(CATALOG, **{field: "drifted"})
            with self.subTest(field=field), self.assertRaises(CatalogError) as caught:
                _refuse_identity(drifted)
            self.assertEqual(str(caught.exception), MISMATCH)

    def test_schema_drift_is_reported_first(self):
        drifted = dataclasses.replace(CATALOG, schema_version="v0", family="drifted")
        with self.assertRaises(CatalogError) as caught:
            _refuse_identity(drifted)
        self.assertEqual(str(caught.exception), "unsupported schema version: 'v0'")


if __name__ == "__main__":
    unittest.main()
