"""Pin ``irc.pipe_catalog``'s live family check and pipe-row parser.

``catalog_family_check`` shells out to ``git``; these tests stub the ref probe,
the legacy source reader and the loaded catalog so each branch (skipped
sources, digest/field/row-count refusals, index gaps, early returns) is
exercised offline, exactly as main behaves.
"""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from irc import pipe_catalog as pc
from irc._contract import IrcRefusal

_LIVE = "SPECS = '''\nrow-a\n# comment\n\nrow-b\n'''\n"
_SHA = hashlib.sha256(_LIVE.encode()).hexdigest()
_PATH = "experiments/irc-mill-r3400.py"


def _source(**overrides):
    source = {"path": _PATH, "sha256": _SHA, "committed": True, "field": "SPECS", "n_rows_extracted": 2}
    source.update(overrides)
    return {key: value for key, value in source.items() if value is not None}


def _rows(*indexes, pipe="p"):
    return tuple(
        pc.SpecRow(mill_round=3400, index=index, pipe=f"{pipe}{index}", path=_PATH, field="SPECS")
        for index in indexes
    )


def _family_check(sources, spec_rows, *, live_legacy=True, ref="present"):
    """Run the check with stubbed git; ``ref`` is "present", "unknown" or "no-git".

    Returns (result is the loaded catalog, rev-parse commands, legacy paths read).
    """
    catalog = pc.FamilyCatalog(catalog_id="fixture", sources=tuple(sources), spec_rows=spec_rows)
    probes: list[list[str]] = []
    shown: list[str] = []

    def rev_parse(cmd, **kwargs):
        probes.append(cmd)
        if ref == "no-git":
            raise FileNotFoundError("git")
        if ref == "unknown":
            raise pc.subprocess.CalledProcessError(128, cmd)
        return b""

    def legacy(path):
        shown.append(path)
        return _LIVE

    which = None if ref == "no-git" else "/usr/bin/git"
    with (
        mock.patch.object(pc, "load_family_catalog", return_value=catalog),
        mock.patch.object(pc.subprocess, "check_output", side_effect=rev_parse),
        mock.patch("shutil.which", return_value=which),
        mock.patch.object(pc, "_legacy_source", side_effect=legacy),
    ):
        result = pc.catalog_family_check(live_legacy)
    return result is catalog, probes, shown


class CatalogFamilyCheckTests(unittest.TestCase):
    def _check(self, sources, spec_rows, *, live_legacy=True, ref="present"):
        same, probes, shown = _family_check(sources, spec_rows, live_legacy=live_legacy, ref=ref)
        self.assertTrue(same)
        for cmd in probes:
            self.assertEqual(Path(cmd[0]).name, "git")
            self.assertEqual(cmd[1:], ["rev-parse", pc.SOURCE_REF])
        return shown

    def test_committed_mill_sources_are_rechecked_against_the_legacy_ref(self):
        self.assertEqual(self._check([_source()], _rows(0, 1)), [_PATH])

    def test_sources_that_are_not_committed_mill_sources_are_skipped(self):
        skipped = (
            _source(sha256=None),
            _source(path=5),
            _source(committed=False, sha256="0" * 64),
            _source(path="experiments/other.py", sha256="0" * 64),
        )
        for source in skipped:
            with self.subTest(source=source):
                self.assertEqual(self._check([source], _rows(0, 1)), [])

    def test_digest_field_and_row_count_drift_are_refused(self):
        cases = (
            (_source(sha256="0" * 64), f"{_PATH}"),
            (_source(field="ROWS"), f"{_PATH} field"),
            (_source(n_rows_extracted=3), f"{_PATH} n_rows"),
        )
        for source, detail in cases:
            with self.subTest(detail=detail):
                with self.assertRaises(IrcRefusal) as caught:
                    self._check([source], _rows(0, 1))
                self.assertEqual(str(caught.exception), f"irc.catalog_sha256_mismatch: {detail}")

    def test_spec_row_index_gaps_are_refused_only_on_the_live_path(self):
        with self.assertRaises(IrcRefusal) as caught:
            self._check([_source()], _rows(0, 2))
        self.assertEqual(str(caught.exception), "irc.catalog_field_invalid: mill 3400 index gap")
        # Behaviour on main: the early returns skip the index check entirely.
        self.assertEqual(self._check([_source()], _rows(0, 2), live_legacy=False), [])
        self.assertEqual(self._check([_source()], _rows(0, 2), ref="unknown"), [])

    def test_missing_git_skips_the_live_check(self):
        same, _probes, shown = _family_check([_source(sha256="0" * 64)], _rows(0, 2), ref="no-git")
        self.assertTrue(same)
        self.assertEqual(shown, [])

    def test_git_is_invoked_by_absolute_path(self):
        calls: list[list[str]] = []
        with (
            mock.patch("shutil.which", return_value="/opt/bin/git"),
            mock.patch.object(pc.subprocess, "check_output", side_effect=lambda cmd, **kw: calls.append(cmd) or "x"),
        ):
            self.assertEqual(pc._legacy_source(_PATH), "x")
        self.assertEqual(calls, [["/opt/bin/git", "show", f"{pc.SOURCE_REF}:{_PATH}"]])
        with mock.patch("shutil.which", return_value=None), self.assertRaises(FileNotFoundError):
            pc._legacy_source(_PATH)

    def test_spec_row_pipe_text_is_not_compared_with_the_live_source(self):
        # Behaviour on main: only the digest, field name and row count are compared.
        self.assertEqual(self._check([_source()], _rows(0, 1, pipe="EDITED")), [_PATH])


class PipeRowsFromSourceTests(unittest.TestCase):
    def test_first_specs_or_rows_assignment_is_parsed(self):
        self.assertEqual(pc.pipe_rows_from_source(_LIVE), ("SPECS", ("row-a", "row-b")))
        source = "x.y = 1\na, b = 1, 2\nOTHER = 'z'\nROWS = 'q\\n#c\\nr'\nSPECS = 's'\n"
        self.assertEqual(pc.pipe_rows_from_source(source), ("ROWS", ("q", "r")))

    def test_unparseable_non_literal_and_non_string_fields_are_refused(self):
        cases = (
            ("SPECS = ", "irc.source_not_parseable: "),
            ("SPECS = load()", "irc.source_not_parseable: malformed node or string"),
            ("SPECS = 1", "irc.source_not_parseable: field not str"),
            ("X = 1", "irc.source_not_parseable: missing one of"),
        )
        for source, prefix in cases:
            with self.subTest(source=source):
                with self.assertRaises(IrcRefusal) as caught:
                    pc.pipe_rows_from_source(source)
                self.assertTrue(str(caught.exception).startswith(prefix), str(caught.exception))


if __name__ == "__main__":
    unittest.main()
