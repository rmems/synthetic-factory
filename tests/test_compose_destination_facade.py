#!/usr/bin/env python3
"""Compatibility seams for the split compose destination facade."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
PIPELINES = TESTS.parent / "pipelines"
for _path in (TESTS, PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_contract  # noqa: E402
import compose_destination  # noqa: E402


class FacadeSentinel(RuntimeError):
    """A patched compatibility seam reached by a real facade call."""


class ComposeDestinationFacadeCompatibility(unittest.TestCase):
    def test_historical_error_and_parent_label_remain_importable(self):
        self.assertIs(compose_destination.ComposeError, compose_contract.ComposeError)
        self.assertEqual(
            compose_destination._DESTINATION_PARENT_LABEL,
            "destination parent",
        )

    def _assert_exact_read_reaches(self, facade_name: str) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "member.jsonl").write_bytes(b'{}\n')
            with mock.patch.object(
                compose_destination,
                facade_name,
                side_effect=FacadeSentinel(facade_name),
            ):
                with self.assertRaisesRegex(FacadeSentinel, facade_name):
                    compose_destination._read_exact_regular_file(
                        root,
                        "member.jsonl",
                        "source member",
                    )

    def test_exact_read_reaches_the_facade_opened_identity_seam(self):
        self._assert_exact_read_reaches("_assert_opened_source_identity")

    def test_exact_read_reaches_the_facade_descriptor_drain_seam(self):
        self._assert_exact_read_reaches("_drain_descriptor")

    def test_exact_read_reaches_the_facade_path_reauthentication_seam(self):
        self._assert_exact_read_reaches("_assert_source_path_unchanged")

    def _assert_pinned_read_reaches(self, facade_name: str) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "child.json").write_bytes(b'{}\n')
            parent = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            descriptor = None
            try:
                before, descriptor = compose_destination._open_pinned_child(
                    "child.json",
                    parent,
                    "source child",
                )
                with mock.patch.object(
                    compose_destination,
                    facade_name,
                    side_effect=FacadeSentinel(facade_name),
                ):
                    with self.assertRaisesRegex(FacadeSentinel, facade_name):
                        compose_destination._read_pinned_child_bytes(
                            "child.json",
                            parent,
                            descriptor,
                            before,
                            "source child",
                        )
            finally:
                if descriptor is not None:
                    os.close(descriptor)
                os.close(parent)

    def test_pinned_read_reaches_the_facade_opened_identity_seam(self):
        self._assert_pinned_read_reaches("_assert_opened_source_identity")

    def test_pinned_read_reaches_the_facade_descriptor_drain_seam(self):
        self._assert_pinned_read_reaches("_drain_descriptor")

    def test_source_enumeration_reaches_the_facade_visibility_seam(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "member.jsonl").write_bytes(b'{}\n')
            with mock.patch.object(
                compose_destination,
                "_round_visible_members",
                side_effect=FacadeSentinel("round visibility"),
            ):
                with self.assertRaisesRegex(FacadeSentinel, "round visibility"):
                    compose_destination.source_jsonl_members(root)

    def test_round_visibility_reaches_the_facade_marker_root_seam(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(
                compose_destination,
                "_enclosing_marker_root",
                side_effect=FacadeSentinel("marker root"),
            ):
                with self.assertRaisesRegex(FacadeSentinel, "marker root"):
                    compose_destination._round_visible_members(
                        root,
                        ["member.jsonl"],
                    )

    def test_round_visibility_reaches_the_facade_committed_paths_seam(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "member.jsonl").write_bytes(b'{}\n')
            with mock.patch.object(
                compose_destination,
                "_enclosing_marker_root",
                return_value=root,
            ), mock.patch.object(
                compose_destination,
                "_committed_paths",
                side_effect=FacadeSentinel("committed paths"),
            ):
                with self.assertRaisesRegex(FacadeSentinel, "committed paths"):
                    compose_destination._round_visible_members(
                        root,
                        ["member.jsonl"],
                    )


if __name__ == "__main__":
    unittest.main()
