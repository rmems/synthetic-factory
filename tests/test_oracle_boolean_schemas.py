"""Unsupported Boolean schema nodes fail as findings, not Python exceptions."""

from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipelines'))
from oracle_grounded import schema_validation as validation


class OracleBooleanSchemas(unittest.TestCase):
    def test_boolean_nodes_are_reported_at_every_schema_entry(self):
        cases = (True, False, {'properties': {'x': True}}, {'anyOf': [False]},
                 {'$defs': {'item': True}, '$ref': '#/$defs/item'})
        for schema in cases:
            with self.subTest(schema=schema):
                self.assertTrue(validation._unsupported_keyword_errors(schema))
                findings = validation._validate({'x': 1}, schema, schema, '$')
                self.assertTrue(findings)

    def test_public_schema_validation_stops_unsupported_documents(self):
        schemas = (True, False, {'not': False}, {'items': True},
                   {'properties': {'x': True}}, {'anyOf': [False]},
                   {'$defs': {'item': True}, '$ref': '#/$defs/item'})
        for schema in schemas:
            validation._schema_keyword_findings.cache_clear()
            try:
                with mock.patch.object(validation, '_load_schema', return_value=schema):
                    with mock.patch.object(validation, '_validate', side_effect=AssertionError('validated unsupported schema')):
                        for completed in (False, True):
                            with self.subTest(schema=schema, completed=completed):
                                findings = validation.validate_record_schemas({}, 'example', include_validation=completed)
                                self.assertTrue(any('schema' in finding for finding in findings))
            finally:
                validation._schema_keyword_findings.cache_clear()

    def test_boolean_additional_properties_keeps_supported_meaning(self):
        for allowed in (False, True):
            with self.subTest(allowed=allowed):
                schema = {'type': 'object', 'additionalProperties': allowed}
                self.assertEqual(validation._unsupported_keyword_errors(schema), [])
                findings = validation._validate({'extra': 1}, schema, schema, '$')
                self.assertEqual(bool(findings), not allowed)


if __name__ == '__main__':
    unittest.main()
