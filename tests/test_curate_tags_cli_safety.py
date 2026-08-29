import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
_PIPELINES = _TESTS.parent / "pipelines"
for _path in (_TESTS, _PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import curate_tags  # noqa: E402
import tag_write  # noqa: E402
from tag_test_support import (  # noqa: E402
    _preflight_destinations,
    _write_destinations,
    run_tag_cli,
    write_tag_source,
)


class CliSafetyTests(unittest.TestCase):
    def _refuse(self, source, extra_args, missing=None):
        result = run_tag_cli(source, extra_args)
        self.assertNotEqual(result.returncode, 0, result.stderr)
        if missing is not None:
            self.assertFalse(missing.exists())
        return result

    def test_cli_preflights_all_destinations_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_tag_source(root)
            output = root / "new" / "tags.jsonl"
            manifest = root / "existing-manifest.jsonl"
            manifest.write_text("sentinel\n", encoding="utf-8")
            self._refuse(
                source,
                ["--output-jsonl", str(output), "--manifest-jsonl", str(manifest)],
                missing=output,
            )
            self.assertEqual(manifest.read_text(), "sentinel\n")

    def test_cli_rejects_destinations_that_contain_one_another(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_tag_source(root)
            output = root / "artifact"
            self._refuse(
                source,
                [
                    "--output-jsonl",
                    str(output),
                    "--manifest-jsonl",
                    str(output / "manifest.jsonl"),
                ],
                missing=output,
            )

    def test_cli_refuses_any_destination_under_outputs_raw(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_tag_source(root)
            output = root / "outputs" / "raw" / "forbidden.jsonl"
            self._refuse(source, ["--output-jsonl", str(output)], missing=output)

    def test_cli_refuses_a_lexical_raw_path_through_a_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_tag_source(root)
            external = root / "external-raw"
            external.mkdir()
            raw = root / "outputs" / "raw"
            raw.parent.mkdir()
            raw.symlink_to(external, target_is_directory=True)
            output = raw / "forbidden.jsonl"
            self._refuse(source, ["--output-jsonl", str(output)])
            self.assertFalse((external / "forbidden.jsonl").exists())

    def test_cli_refuses_to_overwrite_its_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_tag_source(root)
            before = source.read_text()
            self._refuse(source, ["--output-jsonl", str(source)])
            self.assertEqual(source.read_text(), before)

    def test_cli_rejects_an_invalid_taxonomy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_tag_source(root)
            taxonomy = root / "broken.json"
            taxonomy.write_text("{", encoding="utf-8")
            self._refuse(source, ["--taxonomy", str(taxonomy)])

    def test_destination_race_preserves_competitor_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "output.jsonl"
            manifest = root / "manifest.jsonl"
            _preflight_destinations([output, manifest])
            manifest.write_text("competitor\n", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                _write_destinations([(output, [{"id": "x"}]), (manifest, [])])
            self.assertFalse(output.exists())
            self.assertEqual(manifest.read_text(encoding="utf-8"), "competitor\n")


class TagCliInProcessSafetyTests(unittest.TestCase):
    def _stderr_exit(self, args):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            curate_tags.main(args)
        return stderr.getvalue()

    def test_main_rejects_source_clobber_and_existing_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_tag_source(root, tags=["MODIFY"], name="in.jsonl")
            output = root / "out.jsonl"
            with contextlib.redirect_stdout(io.StringIO()):
                curate_tags.main([str(source), "--output-jsonl", str(output)])
            self._stderr_exit([str(source), "--output-jsonl", str(source)])
            self._stderr_exit([str(source), "--output-jsonl", str(output)])

    def test_main_rejects_nested_and_raw_destinations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_tag_source(root, tags=["MODIFY"], name="in.jsonl")
            nested = root / "nested"
            self._stderr_exit(
                [
                    str(source),
                    "--output-jsonl",
                    str(nested / "a.jsonl"),
                    "--manifest-jsonl",
                    str(nested),
                ]
            )
            raw = root / "outputs" / "raw" / "x.jsonl"
            self._stderr_exit([str(source), "--output-jsonl", str(raw)])

    def test_main_rejects_missing_taxonomy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = write_tag_source(root, tags=["MODIFY"], name="in.jsonl")
            self._stderr_exit(
                [
                    str(source),
                    "--taxonomy",
                    str(root / "missing-taxonomy.json"),
                    "--output-jsonl",
                    str(root / "fresh.jsonl"),
                ]
            )


class ParentFdWriteTests(unittest.TestCase):
    def test_parent_symlink_swap_cannot_redirect_into_raw(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            safe = root / "safe"
            safe.mkdir()
            dest_dir = root / "dest"
            dest_dir.symlink_to(safe, target_is_directory=True)
            dest = dest_dir / "out.jsonl"
            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            real_open = os.open
            opened_parent = False

            def swapper(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal opened_parent
                result = real_open(path, flags, mode, dir_fd=dir_fd)
                if dir_fd is None and not opened_parent:
                    dest_dir.unlink()
                    dest_dir.symlink_to(raw, target_is_directory=True)
                    opened_parent = True
                return result

            with mock.patch.object(tag_write.os, "open", side_effect=swapper):
                tag_write._write_new_jsonl(dest, [{"id": "x"}])

            self.assertTrue(opened_parent)
            self.assertTrue((safe / "out.jsonl").is_file())
            self.assertFalse((raw / "out.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
