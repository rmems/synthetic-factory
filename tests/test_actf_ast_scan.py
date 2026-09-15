#!/usr/bin/env python3
"""ACTF AST scan classifies operations and never executes the source."""

from __future__ import annotations

import unittest

from actf_test_support import cv, ast_scan


class AstScanTests(unittest.TestCase):
    def test_scan_does_not_execute_a_module_level_exit(self):
        result = ast_scan.scan_source(
            'raise SystemExit("recovered source must not execute")\n',
            filename="poison.py",
        )
        self.assertEqual(result.syntax_status, cv.SYNTAX_OK)
        self.assertIsNotNone(result.features)

    def test_write_text_on_a_name_receiver_is_a_file_write(self):
        result = ast_scan.scan_source("target.write_text(payload)\n")
        self.assertIn(cv.FINDING_FILE_WRITE, _categories(result))

    def test_open_write_is_a_file_write_and_open_read_is_not(self):
        write = ast_scan.scan_source("open(path, 'w')\n")
        read = ast_scan.scan_source("open(path)\n")
        self.assertIn(cv.FINDING_FILE_WRITE, _categories(write))
        self.assertNotIn(cv.FINDING_FILE_WRITE, _categories(read))

    def test_subprocess_and_os_system_are_process_execution(self):
        result = ast_scan.scan_source("import subprocess\nsubprocess.run(['true'])\nos.system('true')\n")
        self.assertIn(cv.FINDING_PROCESS_EXECUTION, _categories(result))
        self.assertIn(cv.FINDING_SENSITIVE_IMPORT, _categories(result))

    def test_exec_eval_and_compile_are_dynamic_code(self):
        result = ast_scan.scan_source("exec(src)\neval(src)\ncompile(src, 'x', 'exec')\n")
        self.assertEqual(_categories(result).count(cv.FINDING_DYNAMIC_CODE), 3)

    def test_import_module_is_dynamic_import(self):
        result = ast_scan.scan_source("importlib.import_module('os')\n__import__('os')\n")
        self.assertEqual(_categories(result).count(cv.FINDING_DYNAMIC_IMPORT), 2)

    def test_unlink_and_rmtree_are_deletes(self):
        result = ast_scan.scan_source("os.remove(path)\nshutil.rmtree(path)\npath.unlink()\n")
        self.assertIn(cv.FINDING_DELETE, _categories(result))
        self.assertIn(cv.FINDING_RECURSIVE_DELETE, _categories(result))

    def test_outputs_raw_string_is_a_raw_path_reference(self):
        result = ast_scan.scan_source('DEST = "outputs/raw/2026-09-02"\n')
        self.assertIn(cv.FINDING_RAW_DATASET_PATH_REFERENCE, _categories(result))

    def test_open_write_to_outputs_raw_is_a_raw_mutation(self):
        result = ast_scan.scan_source('open("outputs/raw/batch.jsonl", "w")\n')
        self.assertIn(cv.FINDING_FILE_WRITE, _categories(result))
        self.assertIn(cv.FINDING_RAW_DATASET_MUTATION, _categories(result))
        self.assertIn(cv.FINDING_RAW_DATASET_PATH_REFERENCE, _categories(result))

    def test_rm_rf_string_is_a_shell_recursive_delete_reference(self):
        result = ast_scan.scan_source('cmd = "rm -rf /tmp/x"\n')
        self.assertIn(cv.FINDING_SHELL_RECURSIVE_DELETE_REFERENCE, _categories(result))

    def test_curl_as_a_word_is_a_network_command(self):
        result = ast_scan.scan_source('cmd = "curl https://example.test"\n')
        self.assertIn(cv.FINDING_NETWORK_COMMAND_REFERENCE, _categories(result))

    def test_a_substring_that_is_not_a_word_is_not_a_network_command(self):
        result = ast_scan.scan_source('note = "scurlable stuff"\n')
        self.assertNotIn(cv.FINDING_NETWORK_COMMAND_REFERENCE, _categories(result))

    def test_syntax_error_is_reported_without_features(self):
        result = ast_scan.scan_source("def broken(\n")
        self.assertEqual(result.syntax_status, cv.SYNTAX_ERROR)
        self.assertIsNone(result.features)
        self.assertEqual(result.excluded_reason, cv.REASON_SYNTAX_ERROR)

    def test_empty_source_is_an_empty_exclusion(self):
        result = ast_scan.scan_source("   \n")
        self.assertTrue(result.empty)
        self.assertEqual(result.excluded_reason, cv.REASON_EMPTY_SOURCE)

    def test_episode_functions_and_factory_literals_are_extracted(self):
        result = ast_scan.scan_source(
            'FACTORY = "agentic-coding-trajectory-factory"\n'
            "def ep1():\n    return FACTORY\n"
            "def helper():\n    return 1\n"
        )
        self.assertEqual(result.features.episode_functions, ("ep1",))
        self.assertEqual(result.features.factory_literals, (cv.FACTORY,))
        self.assertEqual(result.features.functions, 2)

    def test_source_sha256_is_stable(self):
        first = ast_scan.scan_source("x = 1\n")
        second = ast_scan.scan_source("x = 1\n")
        self.assertEqual(first.source_sha256, second.source_sha256)
        self.assertEqual(len(first.source_sha256), 64)


def _categories(result) -> list[str]:
    return [item.category for item in result.operations]


if __name__ == "__main__":
    unittest.main()
