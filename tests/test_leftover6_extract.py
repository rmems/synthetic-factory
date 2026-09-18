"""Literal extraction works and fails closed without fetched archival Git refs."""

import ast
import copy
import hashlib
import unittest

from pipelines.leftover6.catalog_extract import GQL_PATH, SBOX_PATH, SSL_PATH, extract_source
from tests.test_leftover6 import _GQL_SNIPPET


SSL_SOURCE = '''
FACTORY = 'stateful-service-lineage-factory'
GEN = 'grok-4.6'
START = 164
N_ROUNDS = 1
PAIRS = [{'slug': 'bind', 'lslug': 'lose', 'stack': 'api', 'lstack': 'stale-api',
    'obj': 'record', 'naive': 'ignore', 'fix': 'bind', 'docs': 'fixture docs',
    'novel': 1, 'new_vs': 'prior fixture', 'ticket': 'SSL-164'}]
'''

SBOX_SOURCE = '''
def _row(family: str, dump: str, miss_dump: str, secret: str, pin: str,
         pin_path: str, pin_needle: str, grep_hit: str, distinct: str, ext: str,
         miss_ext: str, live_bin: str, inc: int, over_slug: str, miss_slug: str,
         proc: str, allow: str, rotate: str) -> dict:
    return dict(family=family, dump=dump, miss_dump=miss_dump, secret=secret,
                pin=pin, pin_path=pin_path, pin_needle=pin_needle, grep_hit=grep_hit,
                distinct=distinct, ext=ext, miss_ext=miss_ext, ignore=f"*.{ext}",
                live_bin=live_bin, inc=inc, over_slug=over_slug, miss_slug=miss_slug,
                proc=proc, allow=allow, rotate=rotate)
_ROWS = [_row('fixture-family', 'dump', 'miss-dump', 'secret', 'pin', 'path',
    'needle', 'grep-hit', 'distinct', 'ext', 'miss-ext', 'live-bin', 4,
    'over-slug', 'miss-slug', 'process', 'allow', 'rotate')]
'''


def _sbox_increment_source(increment):
    tree = ast.parse(SBOX_SOURCE)
    second = ast.parse(SBOX_SOURCE).body[-1].value.elts[0]
    second.args[0] = ast.Constant(value="second-family")
    second.args[12] = ast.Constant(value=increment)
    tree.body[-1].value.elts.append(second)
    return ast.unparse(tree)


class LiteralCatalogExtract(unittest.TestCase):
    def test_blob_identity_does_not_trust_custom_equality(self):
        class ForgedBlob(str):
            def __eq__(self, other):
                return True

        class ForgedObject:
            __eq__ = ForgedBlob.__eq__

        for blob in (ForgedBlob('forged-git-identity'), ForgedObject()):
            with self.subTest(kind=type(blob)), self.assertRaisesRegex(ValueError, 'blob'):
                extract_source(SSL_SOURCE, path=SSL_PATH, blob_sha=blob)

    def test_supplied_blob_identity_must_match_exact_utf8_source(self):
        source = SSL_SOURCE + '\n# caf\u00e9\n'
        payload = source.encode('utf-8')
        blob = hashlib.sha1(b'blob ' + str(len(payload)).encode('ascii') + b'\0' + payload,
                            usedforsecurity=False).hexdigest()
        self.assertEqual(extract_source(source, path=SSL_PATH, blob_sha=blob)['blob_sha'], blob)
        self.assertEqual(extract_source(source, path=SSL_PATH)['blob_sha'], '')
        self.assertEqual(extract_source(source, path=SSL_PATH, blob_sha='')['blob_sha'], '')
        for bad in ('definitely-not-a-sha', 'a' * 40, None, 42):
            with self.subTest(blob=bad), self.assertRaisesRegex(ValueError, 'blob'):
                extract_source(source, path=SSL_PATH, blob_sha=bad)
        with self.assertRaisesRegex(ValueError, 'blob'):
            extract_source(source + '\n', path=SSL_PATH, blob_sha=blob)

    def test_future_imports_must_stay_in_the_original_module_header(self):
        future = 'from __future__ import annotations\n'
        for prefix in (future, '\"module docstring\"\n' + future + future):
            with self.subTest(prefix=prefix):
                self.assertEqual(extract_source(prefix + SSL_SOURCE, path=SSL_PATH)['n_rows'], 1)
        invalid = (SSL_SOURCE + future, 'pass\n' + future + SSL_SOURCE,
                   '\"doc\"\n\"second string\"\n' + future + SSL_SOURCE,
                   SSL_SOURCE + '\ndef unused():\n    ' + future,
                   SSL_SOURCE + '\nif __name__ == "__main__":\n    ' + future)
        for source in invalid:
            with self.subTest(source=source), self.assertRaises(ValueError):
                extract_source(source, path=SSL_PATH)

    def test_ssl_source_preserves_literal_fields_and_declared_round(self):
        found = extract_source(SSL_SOURCE, path=SSL_PATH)
        self.assertEqual((found['kind'], found['shape'], found['n_rows']), ('ssl-pairs', 'literal-dicts', 1))
        self.assertEqual(found['blob_sha'], '')
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
            SSL_SOURCE.replace("'novel': 1", "'novel': '1'"),
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
            SBOX_SOURCE.replace('[_row(', '[factory._row('),
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

    def test_rebinding_module_name_cannot_hide_script_guard_mutation(self):
        rebindings = ('__name__ = "__main__"', '__name__: str = "__main__"',
                      '(__name__, extra) = ("__main__", 0)',
                      'if condition:\n    __name__ = "__main__"',
                      'import replacement as __name__')
        guard = '\nif __name__ == "__main__":\n    PAIRS = []'
        for rebinding in rebindings:
            with self.subTest(rebinding=rebinding), self.assertRaises(ValueError):
                extract_source(SSL_SOURCE + '\n' + rebinding + guard, path=SSL_PATH)
        deferred = '\ndef unused():\n    __name__ = "__main__"' + guard
        self.assertEqual(extract_source(SSL_SOURCE + deferred, path=SSL_PATH)['n_rows'], 1)

    def test_module_registry_writes_cannot_preserve_literal_rows(self):
        mutations = ('import sys\nsys.modules[__name__].PAIRS = []',
                     'import sys as s\ns.modules[__name__].PAIRS = []',
                     'from sys import modules as registry\nregistry[__name__].PAIRS = []',
                     'import sys\nmodule = sys.modules[__name__]\nmodule.PAIRS = []')
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                extract_source(SSL_SOURCE + '\n' + mutation, path=SSL_PATH)
        deferred = '\ndef unused():\n    import sys\n    sys.modules[__name__].PAIRS = []'
        self.assertEqual(extract_source(SSL_SOURCE + deferred, path=SSL_PATH)['n_rows'], 1)

    def test_definition_time_expressions_cannot_mutate_extracted_literals(self):
        definitions = ('def publish(value=PAIRS.clear()):\n    pass',
                       '@decorate(PAIRS.clear())\ndef publish():\n    pass',
                       'class Publisher:\n    PAIRS.clear()',
                       'publish = lambda value=PAIRS.clear(): None',
                       'def publish() -> PAIRS.clear():\n    pass',
                       'async def publish() -> PAIRS.clear():\n    pass')
        for definition in definitions:
            with self.subTest(definition=definition), self.assertRaises(ValueError):
                extract_source(SSL_SOURCE + '\n' + definition, path=SSL_PATH)

    def test_mutable_aliases_cannot_preserve_stale_pair_values(self):
        for alias in ('PAIRS', '[PAIRS]', '{"rows": PAIRS}'):
            source = SSL_SOURCE + '\nALIAS = ' + alias + '\nALIAS.clear()'
            with self.subTest(alias=alias), self.assertRaises(ValueError):
                extract_source(source, path=SSL_PATH)

    def test_unresolved_access_alias_cannot_hide_catalog_mutations(self):
        for alias in ('PAIRS[0]', 'PAIRS[:]', 'PAIRS[0:1]', 'PAIRS if condition else []', 'PAIRS or []'):
            source = SSL_SOURCE + '\nALIAS = ' + alias + '\nALIAS.clear()'
            with self.subTest(alias=alias), self.assertRaises(ValueError):
                extract_source(source, path=SSL_PATH)

    def test_unresolved_dependency_aliases_remain_unproven_transitively(self):
        mutations = (
            'ALIAS = (PAIRS, unknown)\nALIAS[0].clear()',
            'ALIAS = [row for row in PAIRS]\nALIAS[0].clear()',
            'ALIAS = (PAIRS, unknown)\nNEXT = ALIAS\nNEXT[0].clear()',
            'ALIAS = (PAIRS, unknown)\nBOX = {"rows": ALIAS}\nBOX["rows"][0].clear()',
            'def clear():\n    PAIRS.clear()\nALIAS = (clear, unknown)\nALIAS[0]()',
            'execute = exec\nexecute("PAIRS=[]")',
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                extract_source(SSL_SOURCE + '\n' + mutation, path=SSL_PATH)
        unproven = SSL_SOURCE + '\nALIAS = (PAIRS, unknown)\nPAIRS = ALIAS'
        with self.assertRaises(ValueError):
            extract_source(unproven, path=SSL_PATH)

    def test_wildcard_import_cannot_keep_preimport_catalog_bindings(self):
        source = SSL_SOURCE + '\nfrom replacement import *'
        with self.assertRaises(ValueError):
            extract_source(source, path=SSL_PATH)

    def test_dynamic_namespace_calls_and_aliases_fail_closed(self):
        statements = ('exec("PAIRS=[]")', 'eval("PAIRS.clear()")',
                      'globals()["PAIRS"] = []',
                      'import builtins as b\nb.exec("PAIRS=[]")',
                      'from builtins import exec as execute\nexecute("PAIRS=[]")')
        for statement in statements:
            with self.subTest(statement=statement), self.assertRaises(ValueError):
                extract_source(SSL_SOURCE + '\n' + statement, path=SSL_PATH)
        deferred = SSL_SOURCE + '\ndef publish():\n    exec("PAIRS=[]")'
        self.assertEqual(extract_source(deferred, path=SSL_PATH)['n_rows'], 1)

    def test_sbox_extraction_requires_every_four_step_increment(self):
        for increment in (4, 5, 9, 12):
            with self.subTest(increment=increment), self.assertRaises(ValueError):
                extract_source(_sbox_increment_source(increment), path=SBOX_PATH)
        rows = extract_source(_sbox_increment_source(8), path=SBOX_PATH)['rows']
        self.assertEqual([row['inc'] for row in rows], [4, 8])

    def test_known_basename_cannot_authenticate_an_unrelated_path(self):
        for prefix in ('/untrusted/', 'unreviewed/', './'):
            with self.subTest(prefix=prefix), self.assertRaisesRegex(ValueError, 'unsupported leftover6 source'):
                extract_source(SSL_SOURCE, path=prefix + SSL_PATH)

    def test_overwritten_alias_is_invalidated_before_its_identity_is_lost(self):
        source = SSL_SOURCE + '\nALIAS = PAIRS\nALIAS = ALIAS.clear()'
        with self.assertRaises(ValueError):
            extract_source(source, path=SSL_PATH)

    def test_source_line_count_includes_final_unterminated_line(self):
        for source in (SSL_SOURCE, SSL_SOURCE.rstrip(), SSL_SOURCE.replace('\n', '\r\n')):
            with self.subTest(source=source):
                self.assertEqual(extract_source(source, path=SSL_PATH)['source_lines'],
                                 len(source.splitlines()))

    def test_extracted_integer_ranges_match_loader_contract(self):
        cases = ((SSL_SOURCE, SSL_PATH, 'START = 164', 'START = -1'),
                 (SSL_SOURCE, SSL_PATH, "'novel': 1", "'novel': 0"),
                 (SSL_SOURCE, SSL_PATH, "'novel': 1", "'novel': -1"),
                 (SBOX_SOURCE, SBOX_PATH, "'live-bin', 4", "'live-bin', 0"),
                 (SBOX_SOURCE, SBOX_PATH, "'live-bin', 4", "'live-bin', -1"))
        for source, path, old, new in cases:
            with self.subTest(new=new), self.assertRaises(ValueError):
                extract_source(source.replace(old, new), path=path)
        self.assertEqual(extract_source(SSL_SOURCE.replace('START = 164', 'START = 0'),
                                        path=SSL_PATH)['catalog_first'], 0)

    def test_reported_shapes_require_the_original_ast_constructor(self):
        cases = ((_GQL_SNIPPET, GQL_PATH, 'PAIRS'), (SSL_SOURCE, SSL_PATH, 'PAIRS'),
                 (SBOX_SOURCE, SBOX_PATH, '_ROWS'))
        for source, path, name in cases:
            row = extract_source(source, path=path)['rows'][0]
            fields = {key: value for key, value in row.items() if key not in ('kind', 'round')}
            syntax = ('dict(' + ', '.join(f'{key}={value!r}' for key, value in fields.items()) + ')'
                      if path == SSL_PATH else repr(fields))
            with self.subTest(path=path), self.assertRaises(ValueError):
                extract_source(source + f'\n{name} = [{syntax}]', path=path)

    def test_named_expressions_cannot_preserve_overwritten_bindings(self):
        for expression in ('X = (PAIRS := [])', 'X = [(PAIRS := [])]',
                           'X = (ALIAS := PAIRS.clear())'):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                extract_source(SSL_SOURCE + '\n' + expression, path=SSL_PATH)

    def test_pattern_and_exception_names_invalidate_prior_catalog_bindings(self):
        statements = ('match []:\n    case PAIRS: pass',
                      'match []:\n    case [*PAIRS]: pass',
                      'match {}:\n    case {**PAIRS}: pass',
                      'try:\n    raise Exception()\nexcept Exception as PAIRS:\n    pass')
        for statement in statements:
            with self.subTest(statement=statement), self.assertRaises(ValueError):
                extract_source(SSL_SOURCE + '\n' + statement, path=SSL_PATH)

    def test_extracted_strings_cannot_be_whitespace_only(self):
        for field in ('slug', 'stack', 'docs'):
            tree = ast.parse(SSL_SOURCE)
            pairs = tree.body[-1].value
            row = pairs.elts[0]
            index = next(i for i, key in enumerate(row.keys) if key.value == field)
            row.values[index] = ast.Constant(value=' \t\n ')
            with self.subTest(field=field), self.assertRaises(ValueError):
                extract_source(ast.unparse(tree), path=SSL_PATH)

    def test_invoked_local_code_cannot_preserve_prior_catalog_values(self):
        definition = '\ndef clear():\n    PAIRS.clear()\n'
        for call in ('clear()', 'X = clear()', 'alias = (clear,)\nalias[0]()'):
            with self.subTest(call=call), self.assertRaises(ValueError):
                extract_source(SSL_SOURCE + definition + call, path=SSL_PATH)
        with self.assertRaises(ValueError):
            extract_source(SSL_SOURCE + '\nclear = lambda: PAIRS.clear()\nclear()', path=SSL_PATH)

    def test_script_entry_body_is_deferred_and_import_else_is_checked(self):
        source = SSL_SOURCE + '\ndef clear():\n    PAIRS.clear()\n'
        guarded = source + "if __name__ == '__main__':\n    clear()\n"
        self.assertEqual(extract_source(guarded, path=SSL_PATH)['n_rows'], 1)
        with self.assertRaises(ValueError):
            extract_source(guarded + 'else:\n    clear()\n', path=SSL_PATH)

    def test_unknown_module_calls_and_import_effects_refuse_literal_rows(self):
        effects = ('import sys\nsys._getframe().f_globals["PAIRS"] = []',
                   'import inspect\ninspect.currentframe().f_globals["PAIRS"] = []',
                   'import builtins\nexecute = getattr(builtins, "exec")\nexecute("PAIRS=[]")',
                   'unrelated()', 'result = unrelated()', 'import extension',
                   'from extension import *', 'if unknown:\n    unrelated()',
                   'def unused(value=unrelated()):\n    pass',
                   'unused = lambda value=unrelated(): None')
        for effect in effects:
            with self.subTest(effect=effect), self.assertRaises(ValueError):
                extract_source(SSL_SOURCE + '\n' + effect, path=SSL_PATH)
        deferred = '\ndef unused():\n    unrelated()\ncallback = lambda: unrelated()'
        self.assertEqual(extract_source(SSL_SOURCE + deferred, path=SSL_PATH)['n_rows'], 1)

    def test_catalog_constructors_require_proven_bindings(self):
        cases = ((_GQL_SNIPPET, GQL_PATH, 'dict = lambda **kwargs: {}\n'),
                 (_GQL_SNIPPET, GQL_PATH, 'def dict(**kwargs):\n    return {}\n'),
                 (SBOX_SOURCE.replace('return dict(', 'return altered('), SBOX_PATH, ''))
        for source, path, replacement in cases:
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                extract_source(replacement + source, path=path)

    def test_duplicate_source_row_identities_are_refused(self):
        for source, path in ((_GQL_SNIPPET, GQL_PATH), (SSL_SOURCE, SSL_PATH),
                             (SBOX_SOURCE, SBOX_PATH)):
            tree = ast.parse(source)
            rows = tree.body[-1].value.elts
            duplicate = copy.deepcopy(rows[0])
            if path == SBOX_PATH:
                duplicate.args[12] = ast.Constant(value=8)
            rows.append(duplicate)
            changed = ast.unparse(tree).replace('N_ROUNDS = 1', 'N_ROUNDS = 2')
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'duplicate'):
                extract_source(changed, path=path)

    def test_inert_redefinition_cannot_erase_shadowed_constructor_bindings(self):
        redefinitions = '\ndef unused():\n    pass\ndef unused():\n    pass\n'
        for shadow in ('dict = lambda **kwargs: {}',
                       'replacement = lambda **kwargs: {}\ndict = replacement'):
            with self.subTest(shadow=shadow), self.assertRaises(ValueError):
                extract_source(shadow + redefinitions + _GQL_SNIPPET, path=GQL_PATH)
        for replacement in ('_row = lambda *args: {}',
                            'replacement = lambda *args: {}\n_row = replacement'):
            source = SBOX_SOURCE.replace('_ROWS =', replacement + redefinitions + '_ROWS =')
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                extract_source(source, path=SBOX_PATH)
        self.assertEqual(extract_source(redefinitions + _GQL_SNIPPET, path=GQL_PATH)['n_rows'], 1)

    def test_rebinding_builtins_cannot_authenticate_helper_calls(self):
        rebindings = ('__builtins__ = {"dict": replacement}',
                      '__builtins__: dict = {"dict": replacement}',
                      'namespace = {"dict": replacement}\n__builtins__ = namespace',
                      'def __builtins__():\n    pass',
                      'async def __builtins__():\n    pass')
        for rebinding in rebindings:
            source = 'replacement = lambda **kwargs: {}\n' + rebinding + '\n' + SBOX_SOURCE
            with self.subTest(rebinding=rebinding), self.assertRaises(ValueError):
                extract_source(source, path=SBOX_PATH)
        deferred = 'def unused():\n    __builtins__ = {}\n'
        self.assertEqual(extract_source(deferred + SBOX_SOURCE, path=SBOX_PATH)['n_rows'], 1)
