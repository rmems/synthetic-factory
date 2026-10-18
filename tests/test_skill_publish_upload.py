"""upload_pr.py / upload_fix.py refuse bad arguments before anything reaches the hf argv.

Offline: ``subprocess.run`` and the read-only Hub PR lookup are stubbed, and every
path the scripts write under is a TemporaryDirectory.
"""

import importlib
import io
import json
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
support = importlib.import_module("skill_publish_test_support")

FACTORY = support.FACTORY
NAME = support.NAME
REPO_ID = support.REPO_ID
BAD_NAMES = (
    "", "../escape", "a/b", "-h", "--create-pr", "trailing-", ".hidden", "sp ace",
    "name\n", "name;rm", "$(id)",
)
BAD_SIBLINGS = (
    "thalamic-relay-trajectories", "rmems/../x", "rmems/a b", "-rmems/x", "rmems/x\n",
    "rmems/x/y", "/rmems", "rmems/",
)
SIBLING = "rmems/thalamic-relay-trajectories"
PR_SUMMARY = {
    "repo": REPO_ID, "factory": FACTORY, "rounds": ["r01", "r02c"],
    "superseded": ["batch-r02.jsonl"], "notes": 1, "records": 4, "files": 2, "rows": 4,
    "parquet_bytes": 100,
}
FIX_SUMMARY = {
    "repo": REPO_ID, "factory": FACTORY, "added_files": ["data/raw/batch-r02.jsonl"],
    "added_records": 1, "omitted_duplicates": [], "rounds_after": ["r01", "r02", "r02c"],
    "files_after": 3, "parquet_rows_before": 4, "parquet_rows_after": 5,
    "parquet_bytes_before": 100, "parquet_bytes_after": 120, "records_after": 5,
}


def _pipelines_dataset_id_pattern() -> str:
    pattern = getattr(support.rights_document, "_DATASET_ID_RE", None)
    if pattern is None:  # the procedural rights route moves it to rights_document_support
        pattern = importlib.import_module("rights_document_support").DATASET_ID_RE
    return pattern.pattern


class UploadScriptChecks(support.ScriptChecks):
    """Checks shared by both upload scripts; mixed into one TestCase per script."""

    script = ""
    root_attr = ""
    summary = None

    def setUp(self):
        super().setUp()
        self.up = support.script(self.script)
        self.root = self.tmp / "bundles"
        (self.root / NAME).mkdir(parents=True)
        (self.tmp / "work").mkdir()
        self.enterContext(mock.patch.multiple(
            self.up, BASE=self.tmp, SUMMARIES={REPO_ID: self.summary},
            **{self.root_attr: self.root},
        ))
        self.run = self.enterContext(mock.patch.object(self.up.subprocess, "run"))

    def test_hub_id_pattern_is_the_one_the_pipelines_enforce(self):
        self.assertEqual(self.up.HUB_DATASET_ID.pattern, _pipelines_dataset_id_pattern())

    def test_known_repo_refuses_ids_outside_the_strict_pattern(self):
        for name in BAD_NAMES:
            with self.subTest(name=name):
                self.assert_refuses(
                    self.up.UploadInputError, f"not an owner/name Hub id: {'rmems/' + name!r}",
                    self.up._known_repo, name,
                )

    def test_known_repo_refuses_a_repo_without_a_summary(self):
        with self.assertRaises(self.up.UploadInputError) as caught:
            self.up._known_repo("never-built-grok46")
        self.assertIn("summary for rmems/never-built-grok46", str(caught.exception))
        self.assertEqual(self.up._known_repo(NAME), REPO_ID)

    def test_bundle_dir_refuses_a_missing_directory_or_a_plain_file(self):
        self.assert_refuses(
            self.up.UploadInputError, f"no bundle directory at {self.root / 'absent'}",
            self.up._bundle_dir, self.root, "absent",
        )
        (self.root / "plain").write_text("not a directory")
        self.assert_refuses(
            self.up.UploadInputError, f"no bundle directory at {self.root / 'plain'}",
            self.up._bundle_dir, self.root, "plain",
        )
        self.assertEqual(self.up._bundle_dir(self.root, NAME), self.root / NAME)

    def test_bundle_dir_refuses_a_symlink_that_leaves_the_root(self):
        outside = self.tmp / "outside"
        outside.mkdir()
        (self.root / "escape").symlink_to(outside, target_is_directory=True)
        self.assert_refuses(
            self.up.UploadInputError, f"bundle path is a symlink: {self.root / 'escape'}",
            self.up._bundle_dir, self.root, "escape",
        )
        self.assert_refuses(
            self.up.UploadInputError, f"bundle path leaves {self.root}: {self.root / '..'}",
            self.up._bundle_dir, self.root, "..",
        )

    def test_bundle_dir_refuses_a_symlink_to_a_sibling_bundle(self):
        (self.root / "other-grok46").mkdir()
        (self.root / "alias-grok46").symlink_to(self.root / "other-grok46")
        self.assert_refuses(
            self.up.UploadInputError, f"bundle path is a symlink: {self.root / 'alias-grok46'}",
            self.up._bundle_dir, self.root, "alias-grok46",
        )

    def assert_refused_without_side_effects(self, argv, message):
        with mock.patch("sys.stderr", new_callable=io.StringIO) as stderr:
            self.assertEqual(self.up.main(argv), 2)
        self.assertEqual(stderr.getvalue(), f"refused: {message}\n")
        self.run.assert_not_called()
        self.assertEqual(list((self.tmp / "work").iterdir()), [])

    def stub_upload(self, returncode):
        """What main reads from the completed hf process: returncode, stdout, stderr."""
        url = f"https://huggingface.co/datasets/{REPO_ID}/discussions/1"
        self.run.return_value = types.SimpleNamespace(
            returncode=returncode, stdout=f"PR at {url}\n", stderr="",
        )
        return url

    def expected_argv(self, message, desc):
        return [
            self.up.HF, "upload", REPO_ID, str(self.root / NAME), ".", "--repo-type", "dataset",
            "--create-pr", "--commit-message", message, "--commit-description", desc,
        ]


class UploadPrTests(UploadScriptChecks, unittest.TestCase):
    script = "upload_pr"
    root_attr = "BUNDLES"
    summary = PR_SUMMARY

    def test_main_refuses_bad_arguments_before_writing_or_running(self):
        cases = [
            ([NAME], self.up.USAGE),
            ([NAME, SIBLING, "extra"], self.up.USAGE),
            (["../escape", SIBLING], "not an owner/name Hub id: 'rmems/../escape'"),
        ] + [
            ([NAME, bad], f"sibling is not an owner/name Hub id: {bad!r}") for bad in BAD_SIBLINGS
        ]
        for argv, message in cases:
            with self.subTest(argv=argv):
                self.assert_refused_without_side_effects(argv, message)

    def test_main_runs_hf_upload_with_a_fixed_argv(self):
        url = self.stub_upload(0)
        stdout = self.enterContext(mock.patch("sys.stdout", new_callable=io.StringIO))

        self.assertEqual(self.up.main([NAME, SIBLING]), 0)

        desc = self.up.description(PR_SUMMARY, SIBLING)
        self.run.assert_called_once_with(
            self.expected_argv(self.up.COMMIT_MESSAGE, desc),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual((self.tmp / "work" / f"pr-description-{NAME}.md").read_text(), desc)
        self.assertEqual(json.loads(stdout.getvalue())["urls"], [url])


class UploadFixTests(UploadScriptChecks, unittest.TestCase):
    script = "upload_fix"
    root_attr = "FIX"
    summary = FIX_SUMMARY

    def setUp(self):
        super().setUp()
        self.lookup = self.enterContext(
            mock.patch.object(self.up, "_pull_requests", return_value=[{"num": 1}])
        )
        self.result_path = self.tmp / "work" / f"fix-pr-{NAME}.json"

    def test_main_refuses_bad_arguments_before_writing_or_running(self):
        cases = [([], self.up.USAGE), ([NAME, "extra"], self.up.USAGE)] + [
            ([bad], f"not an owner/name Hub id: {'rmems/' + bad!r}") for bad in BAD_NAMES
        ]
        for argv, message in cases:
            with self.subTest(argv=argv):
                self.assert_refused_without_side_effects(argv, message)
        self.lookup.assert_not_called()

    def test_main_runs_hf_upload_then_the_read_only_lookup(self):
        self.stub_upload(0)
        self.enterContext(mock.patch("sys.stdout", new_callable=io.StringIO))

        self.assertEqual(self.up.main([NAME]), 0)

        message = self.up._commit_message(1)
        self.assertEqual(
            message, "Add the 1 base-round batch omitted by the mistaken supersede rule"
        )
        self.run.assert_called_once_with(
            self.expected_argv(message, self.up.description(FIX_SUMMARY)),
            capture_output=True, text=True, check=False,
        )
        self.lookup.assert_called_once_with(REPO_ID, message)
        self.assertEqual(json.loads(self.result_path.read_text())["pull_requests"], [{"num": 1}])

    def test_failed_upload_skips_the_lookup_and_returns_its_exit_code(self):
        self.stub_upload(1)
        self.enterContext(mock.patch("sys.stdout", new_callable=io.StringIO))
        self.enterContext(mock.patch("sys.stderr", new_callable=io.StringIO))

        self.assertEqual(self.up.main([NAME]), 1)

        self.lookup.assert_not_called()

    def test_failed_lookup_still_records_the_upload_and_raises(self):
        self.stub_upload(0)
        self.lookup.side_effect = ConnectionError("hub unreachable")

        with self.assertRaises(ConnectionError):
            self.up.main([NAME])

        result = json.loads(self.result_path.read_text())
        self.assertEqual((result["exit"], result["urls"][0][-14:]), (0, "/discussions/1"))
        self.assertNotIn("pull_requests", result)


if __name__ == "__main__":
    unittest.main()
