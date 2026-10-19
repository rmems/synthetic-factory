"""The alias-cache refresh resolves through ``gh api`` and writes only a new, valid cache (#494)."""

import contextlib
import io
import json
import os
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


def api_cache(path, mapping, ids):
    """Write a github_api-only cache: ``mapping`` name -> canonical, ``ids`` name -> id."""

    entries = [
        {"name": name, "canonical": canonical, "method": "github_api",
         "github_id": ids[name], "resolved_at": "2026-10-18T00:00:00Z"}
        for name, canonical in sorted(mapping.items())
    ]
    path.write_bytes(lists.canonical_bytes({
        "schema_version": "repo-alias-cache-v1", "updated_at": "2026-10-18T00:00:00Z",
        "entries": entries,
    }))
    return path


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
        moved = dict(GITHUB, **{"clap-rs/clap": {"full_name": "clap/clap", "id": 101},
                                "kbknapp/clap-rs": {"full_name": "clap/clap", "id": 101}})
        code, _, stderr = self._main("clap-rs/clap", fetch=moved.__getitem__)
        self.assertEqual(code, 0, stderr)
        cache = aliases.load_cache(self.root / "out.json")
        self.assertEqual(cache.resolve("kbknapp/clap-rs"), "clap/clap")
        self.assertEqual(cache.resolve("clap-rs/clap"), "clap/clap")

    def test_every_alias_of_a_moved_target_follows_it(self):
        cache = api_cache(self.root / "siblings.json",
                          {"x/x": "a/a", "y/y": "a/a", "a/a": "a/a"},
                          {"x/x": 7, "y/y": 7, "a/a": 7})
        github = {"x/x": {"full_name": "b/b", "id": 7}, "a/a": {"full_name": "B/b", "id": 7},
                  "y/y": {"full_name": "b/b", "id": 7}}
        code, _, stderr = self._main("x/x", fetch=github.__getitem__, cache=cache)
        self.assertEqual(code, 0, stderr)
        refreshed = aliases.load_cache(self.root / "out.json")
        for name in ("x/x", "y/y", "a/a", "b/b"):
            with self.subTest(name=name):
                self.assertEqual(refreshed.resolve(name), "b/b")

    def test_a_target_that_did_not_move_with_its_alias_refuses_the_refresh(self):
        cache = api_cache(self.root / "siblings.json",
                          {"x/x": "a/a", "y/y": "a/a", "a/a": "a/a"},
                          {"x/x": 7, "y/y": 7, "a/a": 7})
        github = {"x/x": {"full_name": "b/b", "id": 7}, "a/a": {"full_name": "a/a", "id": 9}}
        code, _, stderr = self._main("x/x", fetch=github.__getitem__, cache=cache)
        self.assertEqual(code, 1)
        self.assertIn("a/a: no longer resolves to b/b", stderr)
        self.assertFalse((self.root / "out.json").exists())

    def test_a_reused_sibling_alias_is_refused_rather_than_repointed(self):
        cache = api_cache(self.root / "siblings.json",
                          {"x/x": "a/a", "y/y": "a/a", "a/a": "a/a"},
                          {"x/x": 7, "y/y": 7, "a/a": 7})
        github = {"x/x": {"full_name": "b/b", "id": 7}, "a/a": {"full_name": "b/b", "id": 7},
                  "y/y": {"full_name": "y/y", "id": 8}}
        code, _, stderr = self._main("x/x", fetch=github.__getitem__, cache=cache)
        self.assertEqual(code, 1)
        self.assertIn("y/y: no longer resolves to b/b (github_id 7)", stderr)
        self.assertEqual([path.name for path in self.root.iterdir()], ["siblings.json"])

    def test_a_reused_name_with_a_new_repository_id_is_refused(self):
        cache = api_cache(self.root / "cache.json", {"x/x": "a/a", "a/a": "a/a"},
                          {"x/x": 7, "a/a": 7})
        for github in ({"x/x": {"full_name": "a/a", "id": 8}},
                       {"a/a": {"full_name": "a/a", "id": 8}}):
            name = next(iter(github))
            with self.subTest(name=name):
                code, _, stderr = self._main(name, fetch=github.__getitem__, cache=cache)
                self.assertEqual(code, 1)
                self.assertIn("repository identity changed (cached github_id 7, GitHub now "
                              "returns 8)", stderr)
                self.assertFalse((self.root / "out.json").exists())

    def test_a_failed_write_leaves_neither_the_output_nor_a_temporary(self):
        with mock.patch.object(refresh.os, "fsync", side_effect=OSError("disk full")):
            code, _, stderr = self._main("kbknapp/clap-rs")
        self.assertEqual(code, 1)
        self.assertIn("disk full", stderr)
        self.assertEqual(list(self.root.iterdir()), [])
        code, _, stderr = self._main("kbknapp/clap-rs")
        self.assertEqual(code, 0, stderr)
        self.assertEqual([path.name for path in self.root.iterdir()], ["out.json"])

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
        self.assertIn("File exists", stderr)
        self.assertEqual((self.root / "taken.json").read_text(), "keep\n")
        self.assertEqual([path.name for path in self.root.iterdir()], ["taken.json"])
        broken = self.root / "broken.json"
        broken.write_text("{}\n")
        code, _, stderr = self._main("kbknapp/clap-rs", cache=broken)
        self.assertEqual(code, 1)
        self.assertIn("keys differ", stderr)

    def _fake_gh(self):
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        gh = bin_dir / "gh"
        gh.write_text("#!/bin/sh\n")
        gh.chmod(0o755)
        return mock.patch.object(refresh.os, "get_exec_path", return_value=[str(bin_dir)]), str(gh)

    def test_gh_api_failures_fail_closed(self):
        def run(stdout="", returncode=0, stderr=""):
            return refresh.subprocess.CompletedProcess(["gh"], returncode, stdout, stderr)

        on_path, gh = self._fake_gh()
        with on_path, mock.patch.object(refresh.subprocess, "run",
                                        return_value=run('{"id": 1}')) as call:
            self.assertEqual(refresh.gh_api_repo("A/b"), {"id": 1})
        self.assertEqual(call.call_args.args[0], [gh, "api", "repos/a/b"])
        self.assertNotIn("shell", call.call_args.kwargs)
        cases = {
            "failed: Not Found": run(returncode=1, stderr="Not Found\n"),
            "invalid JSON": run("<html>"),
        }
        for pattern, result in cases.items():
            with (
                self.subTest(pattern=pattern),
                on_path,
                mock.patch.object(refresh.subprocess, "run", return_value=result),
                self.assertRaisesRegex(refresh.RefreshError, pattern),
            ):
                refresh.gh_api_repo("a/b")
        with (
            on_path,
            mock.patch.object(refresh.subprocess, "run", side_effect=OSError("no gh")),
            self.assertRaisesRegex(refresh.RefreshError, "could not run"),
        ):
            refresh.gh_api_repo("a/b")

    def test_the_script_runs_as_a_cli_and_puts_pipelines_on_its_path(self):
        import runpy

        script = REPO / "scripts" / "refresh_repo_aliases.py"
        pipelines = str(REPO / "pipelines")
        argv = [str(script), "a/b", "--cache", str(self.root / "absent.json"),
                "--out", str(self.root / "out.json")]
        trimmed = [entry for entry in sys.path if entry != pipelines]
        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(sys, "path", trimmed),
            contextlib.redirect_stderr(io.StringIO()) as stderr,
            self.assertRaises(SystemExit) as raised,
        ):
            runpy.run_path(str(script), run_name="__main__")
        self.assertEqual(raised.exception.code, 1)
        self.assertIn("unreadable", stderr.getvalue())
        self.assertFalse((self.root / "out.json").exists())

    def test_gh_is_resolved_to_an_absolute_path_and_names_are_validated_first(self):
        (self.root / "empty").mkdir()
        (self.root / "empty" / "gh").write_text("not executable\n")
        with (
            mock.patch.object(refresh.os, "get_exec_path", return_value=[str(self.root / "empty")]),
            self.assertRaisesRegex(refresh.RefreshError, "gh is not on PATH"),
        ):
            refresh.gh_api_repo("a/b")
        with (
            mock.patch.object(refresh.subprocess, "run") as call,
            self.assertRaisesRegex(refresh.RefreshError, "not a GitHub owner/name"),
        ):
            refresh.gh_api_repo("a/b; rm -rf /")
        call.assert_not_called()

    def test_out_must_stay_inside_the_checkout_or_the_temporary_directory(self):
        outside = self.root.joinpath(*([".."] * 40), "refresh-escape.json")
        (self.root / "up").symlink_to("/")
        raw = self.root / "raw"
        raw.mkdir()
        (self.root / "link.json").symlink_to(self.root / "target.json")
        cases = {
            "resolves outside the repository": outside,
            "resolves outside the repository ": self.root / "up" / "refresh-escape.json",
            "names or aliases outputs/raw": raw / "out.json",
            "is a symlink": self.root / "link.json",
            "is not an existing directory": self.root / "missing" / "out.json",
        }
        for pattern, out in cases.items():
            with (
                self.subTest(pattern=pattern.strip()),
                mock.patch.object(refresh.raw_tree_guard, "DEFAULT_RAW_OUTPUT_ROOT", raw),
                self.assertRaisesRegex(refresh.RefreshError, pattern.strip()),
            ):
                refresh.publish_new_file(out, b"{}\n")
        self.assertFalse(Path("/refresh-escape.json").exists())
        self.assertFalse((self.root / "target.json").exists())
        self.assertEqual(list(raw.iterdir()), [])
        stdout, stderr = io.StringIO(), io.StringIO()
        argv = ["kbknapp/clap-rs", "--cache", str(FIXTURE_CACHE), "--out", str(outside)]
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(refresh.main(argv, fetch=fake_fetch, now=lambda: NOW), 1)
        self.assertIn("resolves outside", stderr.getvalue())

    def test_a_path_inside_the_checkout_is_accepted(self):
        inside = refresh.REPO / "config" / "eval-exclusion"
        self.assertEqual(refresh.confined_output(inside / "x.json"),
                         Path(os.path.realpath(inside / "x.json")))


if __name__ == "__main__":
    unittest.main()
