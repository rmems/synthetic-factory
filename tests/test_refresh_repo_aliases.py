"""The alias-cache refresh resolves through ``gh api`` and writes only a new, valid cache (#494)."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
sys.path.insert(0, str(REPO / "scripts"))
import refresh_repo_aliases as refresh  # noqa: E402

import eval_exclusion_aliases as aliases  # noqa: E402
import eval_exclusion_lists as lists  # noqa: E402

FIXTURE_CACHE = REPO / "tests" / "fixtures" / "eval-exclusion" / "repo-aliases.json"
NOW = datetime(2026, 10, 19, 1, 2, 3, tzinfo=UTC)
GITHUB = {
    "kbknapp/clap-rs": {"full_name": "clap-rs/clap", "id": 101},
    "clap-rs/clap": {"full_name": "clap-rs/clap", "id": 101},
    "thealgorithms/python": {"full_name": "TheAlgorithms/Python", "id": 202},
}


def fake_fetch(name):
    return GITHUB[name]


class RefreshTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.document = json.loads(FIXTURE_CACHE.read_text(encoding="utf-8"))

    def _main(self, *names, out="out.json", fetch=fake_fetch, cache=FIXTURE_CACHE):
        stdout, stderr = io.StringIO(), io.StringIO()
        argv = [*names, "--cache", str(cache), "--out", str(self.root / out)]
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = refresh.main(argv, fetch=fetch, now=lambda: NOW)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_a_rename_is_recorded_with_its_id_time_and_canonical_self_entry(self):
        code, stdout, _ = self._main("KBKnapp/clap-rs")
        self.assertEqual(code, 0)
        out = self.root / "out.json"
        cache = aliases.load_cache(out)
        self.assertEqual(cache.resolve("kbknapp/clap-rs"), "clap-rs/clap")
        self.assertEqual(cache.updated_at, "2026-10-19T01:02:03Z")
        document = json.loads(out.read_text(encoding="utf-8"))
        entries = {entry["name"]: entry for entry in document["entries"]}
        self.assertEqual(entries["kbknapp/clap-rs"], {
            "name": "kbknapp/clap-rs", "canonical": "clap-rs/clap", "method": "github_api",
            "github_id": 101, "resolved_at": "2026-10-19T01:02:03Z",
        })
        self.assertEqual(entries["clap-rs/clap"]["method"], "github_api")
        self.assertEqual(entries["thealgorithms/python"]["method"], "reviewed_source_pin")
        self.assertEqual(json.loads(stdout)["resolved"], {"KBKnapp/clap-rs": "clap-rs/clap"})
        self.assertEqual(out.read_bytes(), lists.canonical_bytes(document))

    def test_a_moved_canonical_repoints_its_aliases_so_the_cache_stays_closed(self):
        moved = dict(GITHUB, **{"clap-rs/clap": {"full_name": "clap/clap", "id": 101}})
        code, _, stderr = self._main("clap-rs/clap", fetch=moved.__getitem__)
        self.assertEqual(code, 0, stderr)
        cache = aliases.load_cache(self.root / "out.json")
        self.assertEqual(cache.resolve("kbknapp/clap-rs"), "clap/clap")
        self.assertEqual(cache.resolve("clap-rs/clap"), "clap/clap")

    def test_every_unresolved_answer_writes_nothing(self):
        answers = (
            ("no repository object", []),
            ("no repository id", {"full_name": "a/b"}),
            ("no repository id", {"full_name": "a/b", "id": True}),
            ("unusable full_name", {"full_name": "a/b/c", "id": 3}),
        )
        for pattern, answer in answers:
            with self.subTest(pattern=pattern):
                code, _, stderr = self._main("a/b", fetch=lambda name, answer=answer: answer)
                self.assertEqual(code, 1)
                self.assertIn(pattern, stderr)
                self.assertFalse((self.root / "out.json").exists())
        code, _, stderr = self._main("not a repo")
        self.assertEqual(code, 1)
        self.assertIn("not a GitHub owner/name", stderr)

    def test_an_existing_destination_or_invalid_cache_is_refused(self):
        (self.root / "taken.json").write_text("keep\n")
        code, _, stderr = self._main("kbknapp/clap-rs", out="taken.json")
        self.assertEqual(code, 1)
        self.assertEqual((self.root / "taken.json").read_text(), "keep\n")
        broken = self.root / "broken.json"
        broken.write_text("{}\n")
        code, _, stderr = self._main("kbknapp/clap-rs", cache=broken)
        self.assertEqual(code, 1)
        self.assertIn("keys differ", stderr)

    def test_gh_api_failures_fail_closed(self):
        def run(stdout="", returncode=0, stderr=""):
            return subprocess.CompletedProcess(["gh"], returncode, stdout, stderr)

        with mock.patch.object(refresh.subprocess, "run", return_value=run('{"id": 1}')) as call:
            self.assertEqual(refresh.gh_api_repo("a/b"), {"id": 1})
        self.assertEqual(call.call_args.args[0], ["gh", "api", "repos/a/b"])
        cases = {
            "failed: Not Found": run(returncode=1, stderr="Not Found\n"),
            "invalid JSON": run("<html>"),
        }
        for pattern, result in cases.items():
            with (
                self.subTest(pattern=pattern),
                mock.patch.object(refresh.subprocess, "run", return_value=result),
                self.assertRaisesRegex(refresh.RefreshError, pattern),
            ):
                refresh.gh_api_repo("a/b")
        with (
            mock.patch.object(refresh.subprocess, "run", side_effect=OSError("no gh")),
            self.assertRaisesRegex(refresh.RefreshError, "could not run"),
        ):
            refresh.gh_api_repo("a/b")


if __name__ == "__main__":
    unittest.main()
