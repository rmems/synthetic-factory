"""The VSET pin refresher's drift report, rewrite, and refusals, on a copied fixture tree.

``scripts/refresh_vset_fixture_pins.py`` rewrites committed fixtures in place,
so every writing case here runs against a copy of ``tests/fixtures/vset`` in a
temporary directory with the module's path constants pointed at it. Only the
script entry point runs against the committed tree, in read-only ``--check``.
"""

import contextlib
import io
import json
import runpy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import refresh_vset_fixture_pins as pins

REPO = Path(__file__).resolve().parents[1]
VSET = Path("tests") / "fixtures" / "vset"
MANIFEST_NAME = VSET / "manifests" / "pilot-v1.json"
CURRENT = "VSET fixture pins already match the live repository.\n"


def _write_json(path: Path, document) -> None:
    """Serialize exactly as the refresher does, so an untouched shape is not drift."""

    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _edit_json(path: Path, edit) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    edit(document)
    _write_json(path, document)


@contextlib.contextmanager
def _sandboxed_fixtures(*extra_verdicts: str):
    """Copy the VSET fixtures to a temp root and point the refresher at the copy."""

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        fixtures = root / VSET
        shutil.copytree(pins.FIXTURES, fixtures, symlinks=True)
        record_dirs = tuple(
            fixtures / "records" / verdict for verdict in ("accept", "reject", *extra_verdicts)
        )
        with mock.patch.multiple(
            pins,
            REPO=root,
            FIXTURES=fixtures,
            PACK=fixtures / pins.PACK.relative_to(pins.FIXTURES),
            MANIFEST=root / MANIFEST_NAME,
            RECORD_DIRS=record_dirs,
        ):
            yield root


def _main(argv: list[str]) -> tuple[int, str]:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = pins.main(argv)
    return code, stdout.getvalue()


class RefreshVsetPinsDrift(unittest.TestCase):
    def test_check_reports_drift_without_writing_and_a_rewrite_restores_the_bytes(self):
        drifted = (
            VSET / "records" / "accept" / "provisional.json",
            VSET / "records" / "reject" / "missing-actor-role.json",
            MANIFEST_NAME,
        )
        with _sandboxed_fixtures() as root:
            _edit_json(root / drifted[0],
                       lambda doc: doc["environment"].update(repo_snapshot_hash="stale"))
            _edit_json(root / drifted[1],
                       lambda doc: doc["release"].update(factory_registry_sha256="0" * 64))
            _edit_json(root / drifted[2], lambda doc: doc["counts"].update(records=99))
            stale_bytes = {path: (root / path).read_bytes() for path in drifted}

            checked = _main(["--check"])
            unchanged = {path: (root / path).read_bytes() for path in drifted}
            rewritten = _main([])
            restored = {path: (root / path).read_bytes() for path in drifted}
            rechecked = _main(["--check"])

        self.assertEqual(checked, (1, "".join(f"stale: {path}\n" for path in drifted)))
        self.assertEqual(unchanged, stale_bytes)
        self.assertEqual(
            rewritten, (0, "".join(f"rewrote: {path}\n" for path in sorted(drifted)))
        )
        self.assertEqual(restored, {path: (REPO / path).read_bytes() for path in drifted})
        self.assertEqual(rechecked, (0, CURRENT))

    def test_documents_without_pinned_fields_are_left_as_they_are(self):
        unpinned = {
            "zz-no-environment.json": {"record_kind": "issue_patch_v1", "release": "withheld"},
            "zz-partial-release.json": {
                "environment": {"runtime": "python"},
                "release": {"schema_version": "vset-record-v1"},
            },
        }
        with _sandboxed_fixtures() as root:
            reject = root / VSET / "records" / "reject"
            for name, document in unpinned.items():
                _write_json(reject / name, document)

            def without_counts(manifest):
                manifest["counts"] = None
                manifest["entries"].append("not-an-entry")

            _edit_json(root / MANIFEST_NAME, without_counts)
            rewritten = _main([])
            records = {
                name: json.loads((reject / name).read_text(encoding="utf-8")) for name in unpinned
            }
            manifest = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))

        self.assertEqual(rewritten, (0, f"rewrote: {MANIFEST_NAME}\n"))
        self.assertEqual(records, unpinned)
        self.assertIsNone(manifest["counts"])
        self.assertEqual(manifest["entries"][-1], "not-an-entry")
        self.assertEqual(manifest["manifest_hash"], pins.manifest_body_hash(manifest))

    def test_a_stale_fixture_outside_the_enumerated_verdicts_is_refused(self):
        with _sandboxed_fixtures("quarantine") as root:
            quarantine = root / VSET / "records" / "quarantine"
            quarantine.mkdir()
            shutil.copy(root / VSET / "records" / "accept" / "provisional.json", quarantine)
            stray = quarantine / "provisional.json"
            _edit_json(stray, lambda doc: doc["environment"].update(repo_snapshot_hash="stale"))
            before = stray.read_bytes()

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout), self.assertRaises(SystemExit) as refused:
                pins.main([])

            self.assertEqual(stray.read_bytes(), before)

        self.assertEqual(
            refused.exception.code, "refusing to write an unlisted fixture verdict: quarantine"
        )
        self.assertEqual(stdout.getvalue(), "")

    def test_script_entry_point_checks_the_committed_fixtures_read_only(self):
        stdout = io.StringIO()
        script = str(Path(pins.__file__))
        with (
            mock.patch.object(sys, "argv", [Path(script).name, "--check"]),
            mock.patch.object(sys, "path", list(sys.path)),
            contextlib.redirect_stdout(stdout),
            self.assertRaises(SystemExit) as exited,
        ):
            runpy.run_path(script, run_name="__main__")

        self.assertEqual(exited.exception.code, 0)
        self.assertEqual(stdout.getvalue(), CURRENT)


if __name__ == "__main__":
    unittest.main()
