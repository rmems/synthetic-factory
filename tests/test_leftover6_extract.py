"""Literal extraction works and fails closed without fetched archival Git refs."""

import unittest

from pipelines.leftover6.catalog_extract import SBOX_PATH, SSL_PATH, extract_source


SSL_SOURCE = '''
FACTORY = 'stateful-service-lineage-factory'
GEN = 'grok-4.6'
START = 164
N_ROUNDS = 1
PAIRS = [dict(slug='bind', lslug='lose', stack='api', lstack='stale-api',
    obj='record', naive='ignore', fix='bind', docs='fixture docs',
    novel=1, new_vs='prior fixture', ticket='SSL-164')]
'''

SBOX_SOURCE = '''
_ROWS = [_row('fixture-family', 'dump', 'miss-dump', 'secret', 'pin', 'path',
    'needle', 'grep-hit', 'distinct', 'ext', 'miss-ext', 'live-bin', 4,
    'over-slug', 'miss-slug', 'process', 'allow', 'rotate')]
'''


class LiteralCatalogExtract(unittest.TestCase):
    def test_ssl_source_preserves_literal_fields_and_declared_round(self):
        found = extract_source(SSL_SOURCE, path=SSL_PATH, blob_sha='a' * 40)
        self.assertEqual((found['kind'], found['shape'], found['n_rows']), ('ssl-pairs', 'literal-dicts', 1))
        self.assertEqual(found['blob_sha'], 'a' * 40)
        self.assertEqual(found['catalog_first'], 164)
        self.assertEqual((found['first_slug'], found['last_slug']), ('bind', 'bind'))
        self.assertEqual(found['rows'][0]['novel'], 1)
        self.assertEqual(found['rows'][0]['round'], 164)

    def test_sbox_constructor_preserves_every_positional_field(self):
        found = extract_source(SBOX_SOURCE, path=SBOX_PATH)
        self.assertEqual((found['kind'], found['shape'], found['n_rows']), ('sbox-plants', 'row-ctor', 1))
        row = found['rows'][0]
        self.assertEqual((row['family'], row['inc'], row['rotate']), ('fixture-family', 4, 'rotate'))
        self.assertEqual(found['catalog_first'], 4)

    def test_ssl_declarations_and_row_types_fail_closed(self):
        invalid = (
            SSL_SOURCE.replace('N_ROUNDS = 1', 'N_ROUNDS = 2'),
            SSL_SOURCE.replace('START = 164', 'START = True'),
            SSL_SOURCE.replace('novel=1', 'novel="1"'),
            SSL_SOURCE.replace("GEN = 'grok-4.6'", 'GEN = 42'),
            SSL_SOURCE + '\nPAIRS = []\n',
            SSL_SOURCE + '\nPAIRS = [None]\n',
            SSL_SOURCE + '\nPAIRS = [dict(slug="only-field")]\n',
        )
        for source in invalid:
            with self.subTest(source=source), self.assertRaises(ValueError):
                extract_source(source, path=SSL_PATH)

    def test_sbox_refuses_calls_with_wrong_arity_or_computed_values(self):
        for source in (
            '_ROWS = [_row()]',
            '_ROWS = [_row(family="fixture")]',
            SBOX_SOURCE.replace("'rotate'", 'evaluate()'),
            SBOX_SOURCE.replace('_row(', 'factory._row('),
        ):
            with self.subTest(source=source), self.assertRaises(ValueError):
                extract_source(source, path=SBOX_PATH)

    def test_unknown_source_path_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'unsupported leftover6 source'):
            extract_source(SSL_SOURCE, path='experiments/unreviewed.py')

    def test_unsupported_top_level_writes_cannot_preserve_stale_literals(self):
        mutations = ('PAIRS += build()', 'del PAIRS', 'PAIRS[0] = build()',
                     'del PAIRS[0]', 'PAIRS.append(build())',
                     'PAIRS, other = build()', 'import unknown as PAIRS',
                     'if condition:\n    PAIRS = build()')
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                extract_source(SSL_SOURCE + '\n' + mutation, path=SSL_PATH)

    def test_unevaluated_function_body_does_not_change_literals(self):
        source = SSL_SOURCE + '\ndef publish():\n    PAIRS.append(build())\n'
        self.assertEqual(extract_source(source, path=SSL_PATH)['n_rows'], 1)

    def test_definition_time_expressions_cannot_mutate_extracted_literals(self):
        definitions = ('def publish(value=PAIRS.clear()):\n    pass',
                       '@decorate(PAIRS.clear())\ndef publish():\n    pass',
                       'class Publisher:\n    PAIRS.clear()',
                       'publish = lambda value=PAIRS.clear(): None')
        for definition in definitions:
            with self.subTest(definition=definition), self.assertRaises(ValueError):
                extract_source(SSL_SOURCE + '\n' + definition, path=SSL_PATH)

    def test_mutable_aliases_cannot_preserve_stale_pair_values(self):
        for alias in ('PAIRS', '[PAIRS]', '{"rows": PAIRS}'):
            source = SSL_SOURCE + '\nALIAS = ' + alias + '\nALIAS.clear()'
            with self.subTest(alias=alias), self.assertRaises(ValueError):
                extract_source(source, path=SSL_PATH)

    def test_overwritten_alias_is_invalidated_before_its_identity_is_lost(self):
        source = SSL_SOURCE + '\nALIAS = PAIRS\nALIAS = ALIAS.clear()'
        with self.assertRaises(ValueError):
            extract_source(source, path=SSL_PATH)
