#!/usr/bin/env python3
"""Refusals that protect the destination, the source members, and the CLI."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from export_test_support import (  # noqa: E402
    compose_fixture,
)
from test_compose_curated import (  # noqa: E402
    multi_agent,
    write_jsonl,
)
import compose_curated  # noqa: E402
import export_hf  # noqa: E402


def _should_swap_destination_parent(path, destination, dir_fd, already_swapped):
    """Return whether this mkdir is the one guarded parent-race injection."""

    if path != destination.name:
        return False
    if dir_fd is None:
        return False
    return not already_swapped


class ExportDestinationSafety(unittest.TestCase):
    def test_refuses_empty_missing_and_existing_destinations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)

            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(root / "no-such-root", root / "export-a")

            empty = root / "empty-curated"
            (empty / compose_curated.RECORDS_DIRNAME).mkdir(parents=True)
            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(empty, root / "export-b")

            export_hf.export_run(curated, root / "export")
            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(curated, root / "export")
            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(curated, curated / "nested-export")
            with self.assertRaises(export_hf.ExportError):
                export_hf.export_run(curated, root / "missing-parent" / "export")

    def test_refuses_export_destinations_lexically_or_resolved_under_raw(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            safe = root / "safe"
            safe.mkdir()

            lexical = raw / ".." / ".." / "safe" / "lexical-export"
            with self.assertRaisesRegex(export_hf.ExportError, "immutable raw"):
                export_hf.export_run(curated, lexical)
            self.assertFalse((safe / "lexical-export").exists())

            raw_link = root / "raw-link"
            raw_link.symlink_to(raw, target_is_directory=True)
            with self.assertRaisesRegex(export_hf.ExportError, "immutable raw"):
                export_hf.export_run(curated, raw_link / "resolved-export")
            self.assertFalse((raw / "resolved-export").exists())

            real_parent = root / "real-destination-parent"
            real_parent.mkdir()
            symlink_parent = root / "destination-parent-alias"
            symlink_parent.symlink_to(real_parent, target_is_directory=True)
            with self.assertRaisesRegex(
                export_hf.ExportError, "exact non-symlink"
            ):
                export_hf.export_run(curated, symlink_parent / "export")
            self.assertFalse((real_parent / "export").exists())

    def test_refuses_a_destination_under_the_authenticated_compose_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            summary = json.loads(
                (curated / compose_curated.SUMMARY_FILENAME).read_text(encoding="utf-8")
            )
            destination = Path(summary["source_run"]) / "export"

            with self.assertRaisesRegex(
                export_hf.ExportError, "authenticated compose source"
            ):
                export_hf.export_run(curated, destination)
            self.assertFalse(destination.exists())

    def test_destination_parent_swap_cannot_redirect_creation_or_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            parent = root / "destination-parent"
            parent.mkdir()
            moved_parent = root / "original-parent-moved"
            destination = parent / "export"
            raw = root / "outputs" / "raw"
            real_mkdir = os.mkdir
            swapped = False

            def swap_parent_before_create(path, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                if _should_swap_destination_parent(
                    path, destination, dir_fd, swapped
                ):
                    swapped = True
                    parent.rename(moved_parent)
                    raw.mkdir(parents=True)
                    parent.symlink_to(raw, target_is_directory=True)
                return real_mkdir(path, mode, dir_fd=dir_fd)

            with mock.patch.object(
                compose_curated.os,
                "mkdir",
                side_effect=swap_parent_before_create,
            ):
                with self.assertRaisesRegex(
                    export_hf.ExportError,
                    "destination parent changed while it was pinned",
                ):
                    export_hf.export_run(curated, destination)

            self.assertTrue(swapped)
            self.assertFalse((moved_parent / destination.name).exists())
            self.assertFalse((raw / destination.name).exists())
            self.assertFalse(destination.exists())


class ExportCompositionMemberSafety(unittest.TestCase):
    # ---- one alias per mutation, each swapping exactly one compose member ----

    @staticmethod
    def _swap_for_symlink(path, target):
        path.replace(target)
        path.symlink_to(target)

    @staticmethod
    def _swap_for_hardlink(path, target):
        path.replace(target)
        os.link(target, path)

    @classmethod
    def _alias_summary_symlink(cls, root, curated, summary_path, summary):
        cls._swap_for_symlink(summary_path, root / "outside-COMPOSE.json")

    @classmethod
    def _alias_manifest_symlink(cls, root, curated, summary_path, summary):
        cls._swap_for_symlink(
            curated / summary["manifest"]["path"], root / "outside-manifest.jsonl"
        )

    @classmethod
    def _alias_source_symlink(cls, root, curated, summary_path, summary):
        source_root = Path(summary["source_run"])
        cls._swap_for_symlink(
            next(source_root.rglob("*.jsonl")), root / "outside-source.jsonl"
        )

    @classmethod
    def _alias_source_hardlink(cls, root, curated, summary_path, summary):
        source_root = Path(summary["source_run"])
        cls._swap_for_hardlink(
            next(source_root.rglob("*.jsonl")), root / "outside-source.jsonl"
        )

    @classmethod
    def _alias_source_directory_symlink(cls, root, curated, summary_path, summary):
        source_root = Path(summary["source_run"])
        path = next(source_root.rglob("*.jsonl")).parent
        target = root / "outside-source-directory"
        path.replace(target)
        path.symlink_to(target, target_is_directory=True)

    @classmethod
    def _alias_output_lexical_alias(cls, root, curated, summary_path, summary):
        summary["outputs"][0]["path"] = summary["outputs"][0]["path"].replace(
            "/", "//", 1
        )
        summary_path.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def _alias_output_symlink(cls, root, curated, summary_path, summary):
        cls._swap_for_symlink(
            curated / summary["outputs"][0]["path"], curated / "aliased-output.bin"
        )

    @classmethod
    def _alias_output_hardlink(cls, root, curated, summary_path, summary):
        cls._swap_for_hardlink(
            curated / summary["outputs"][0]["path"], curated / "aliased-output.bin"
        )

    def test_rejects_symlink_and_hardlink_aliases_for_every_compose_member(self):
        mutations = (
            "summary_symlink",
            "manifest_symlink",
            "output_lexical_alias",
            "output_symlink",
            "output_hardlink",
            "source_symlink",
            "source_hardlink",
            "source_directory_symlink",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                curated = compose_fixture(root)
                summary_path = curated / compose_curated.SUMMARY_FILENAME
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                getattr(self, f"_alias_{mutation}")(root, curated, summary_path, summary)

                with self.assertRaises(export_hf.ExportError):
                    export_hf.export_run(curated, root / "export")
                self.assertFalse((root / "export").exists())

    def test_rejects_a_compose_member_symlink_loop_as_export_error(self):
        """An unresolvable member alias must stay inside the export contract."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            member = curated / compose_curated.SUMMARY_FILENAME
            member.unlink()
            member.symlink_to(member)

            try:
                export_hf.export_run(curated, root / "export")
            except export_hf.ExportError as exc:
                self.assertIn("cannot resolve", str(exc))
            except (OSError, RuntimeError) as exc:
                self.fail(f"filesystem exception escaped the export contract: {exc}")
            else:
                self.fail("symlink-loop member was accepted")
            self.assertFalse((root / "export").exists())


class ExportSnapshotCoherence(unittest.TestCase):
    """Codex #97: replay authenticates one coherent source state, never a hybrid."""

    def test_a_member_changed_during_capture_refuses_the_export(self):
        import export_replay

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            source_root = Path(
                json.loads(
                    (curated / compose_curated.SUMMARY_FILENAME).read_text(
                        encoding="utf-8"
                    )
                )["source_run"]
            )
            members = sorted(source_root.rglob("*.jsonl"))
            self.assertGreater(len(members), 1)
            original_read = export_replay._read_exact_regular_file
            mutated = {"done": False}

            def racing_read(root_dir, relative, label):
                result = original_read(root_dir, relative, label)
                if not mutated["done"]:
                    # After the first member is captured, rewrite the last one.
                    mutated["done"] = True
                    victim = members[-1]
                    original = victim.stat()
                    victim.write_bytes(victim.read_bytes())
                    os.utime(
                        victim,
                        ns=(original.st_atime_ns, original.st_mtime_ns),
                    )
                return result

            with mock.patch.object(
                export_replay, "_read_exact_regular_file", racing_read
            ):
                with self.assertRaisesRegex(
                    export_hf.ExportError, "changed while the replay snapshot"
                ):
                    export_hf.export_run(curated, root / "export")
            self.assertFalse((root / "export").exists())

    def test_a_symlinked_directory_in_records_refuses_the_export(self):
        """Codex #97 P2: an aliased subtree must fail closed, not vanish.

        ``rglob`` does not descend a symlinked directory, so its JSONL would
        silently drop out of the snapshot while compose authentication still
        matched the declared outputs.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            records_dir = curated / compose_curated.RECORDS_DIRNAME
            target = root / "outside-subtree"
            target.mkdir()
            (target / "extra.jsonl").write_text("{}\n", encoding="utf-8")
            (records_dir / "aliased-subtree").symlink_to(
                target, target_is_directory=True
            )

            with self.assertRaisesRegex(
                export_hf.ExportError, "symlink alias"
            ):
                export_hf.export_run(curated, root / "export")
            self.assertFalse((root / "export").exists())

    def test_a_directory_named_like_jsonl_refuses_the_export(self):
        """Codex #97 P2: a ``*.jsonl``-named directory must fail closed.

        The alias-refusing walker used to descend such an entry as a
        container, so an empty directory named ``ignored.jsonl`` vanished
        from the snapshot and the export still authenticated — leaving an
        apparent curated payload entry in the tree that was never checked.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            records_dir = curated / compose_curated.RECORDS_DIRNAME
            (records_dir / "ignored.jsonl").mkdir()

            with self.assertRaisesRegex(
                export_hf.ExportError, "not an exact regular file"
            ):
                export_hf.export_run(curated, root / "export")
            self.assertFalse((root / "export").exists())

    def test_a_member_added_during_capture_refuses_the_export(self):
        """Codex #97 P2: replay must re-discover members after its capture.

        Identity rechecks only cover the members enumerated before the first
        read, so a visible JSONL added to a legacy source tree mid-capture
        used to let export authenticate and publish the old subset of a
        source run that no longer exists.
        """
        import export_replay

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            source_root = Path(
                json.loads(
                    (curated / compose_curated.SUMMARY_FILENAME).read_text(
                        encoding="utf-8"
                    )
                )["source_run"]
            )
            original_read = export_replay._read_exact_regular_file
            added = {"done": False}

            def racing_read(root_dir, relative, label):
                result = original_read(root_dir, relative, label)
                if not added["done"]:
                    # After the first member is captured, add a new one.
                    added["done"] = True
                    write_jsonl(
                        source_root / "late-factory" / "late-batch.jsonl",
                        [multi_agent("late")],
                    )
                return result

            with mock.patch.object(
                export_replay, "_read_exact_regular_file", racing_read
            ):
                with self.assertRaisesRegex(
                    export_hf.ExportError,
                    "member set changed while the replay snapshot",
                ):
                    export_hf.export_run(curated, root / "export")
            self.assertFalse((root / "export").exists())

    def test_a_curated_member_added_after_the_initial_snapshot_is_refused(self):
        """Audit, compose authentication, and exported bytes use one member set."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            records_dir = curated / compose_curated.RECORDS_DIRNAME
            real_metadata = export_hf._compose_metadata

            def authenticate_then_add(*args, **kwargs):
                metadata = real_metadata(*args, **kwargs)
                write_jsonl(
                    records_dir / "late-factory" / "late.jsonl",
                    [multi_agent("late-curated")],
                )
                return metadata

            with mock.patch.object(
                export_hf,
                "_compose_metadata",
                side_effect=authenticate_then_add,
            ):
                with self.assertRaisesRegex(
                    export_hf.ExportError,
                    "curated member set changed after the initial snapshot",
                ):
                    export_hf.export_run(curated, root / "export")
            self.assertFalse((root / "export").exists())

    def test_a_completed_export_artifact_is_reauthenticated_before_finish(self):
        """A post-write mutation must roll back the whole new destination."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            destination = root / "export"
            real_write = export_hf._write_new_bytes

            def write_then_mutate(root_descriptor, relative, payload):
                digest = real_write(root_descriptor, relative, payload)
                if relative == export_hf.PROVENANCE_PATH:
                    (destination / export_hf.TRAIN_PATH).write_bytes(b"{}\n")
                return digest

            with mock.patch.object(
                export_hf, "_write_new_bytes", side_effect=write_then_mutate
            ):
                with self.assertRaisesRegex(
                    export_hf.ExportError, "changed before export commit"
                ):
                    export_hf.export_run(curated, destination)
            self.assertFalse(destination.exists())


class ExportMemberFifoSwap(unittest.TestCase):
    def test_same_inode_mutation_during_chunked_read_is_rejected(self):
        """A reader must never return bytes from two source-file states."""
        import export_members

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            member = root / "member.jsonl"
            chunk_size = 1024 * 1024
            member.write_bytes(b"A" * (chunk_size * 2))
            real_read = export_members.os.read
            mutated = False

            def read_then_mutate(descriptor, size):
                nonlocal mutated
                chunk = real_read(descriptor, size)
                if chunk and not mutated:
                    mutated = True
                    writer = os.open(member, os.O_WRONLY)
                    try:
                        os.pwrite(writer, b"B" * chunk_size, chunk_size)
                    finally:
                        os.close(writer)
                return chunk

            with mock.patch.object(
                export_members.os,
                "read",
                side_effect=read_then_mutate,
            ):
                with self.assertRaisesRegex(
                    export_hf.ExportError,
                    "changed while reading",
                ):
                    export_members._read_exact_regular_file(
                        root,
                        member.name,
                        "curated payload",
                    )

            self.assertTrue(mutated)

    def test_a_member_swapped_for_a_fifo_is_rejected_without_blocking(self):
        """Codex #97 P2: a FIFO swapped in after lstat must not hang the open.

        O_NOFOLLOW does not protect against a file-type swap, and a read-only
        FIFO open blocks until a writer appears; O_NONBLOCK lets the open
        return so the descriptor validation can reject it.
        """
        import export_members

        with tempfile.TemporaryDirectory() as td:
            fifo = Path(td) / "swapped.jsonl"
            os.mkfifo(fifo)
            before = fifo.lstat()
            with self.assertRaisesRegex(
                export_hf.ExportError, "not a unique regular file"
            ):
                export_members._read_pinned_descriptor(
                    fifo, before, "swapped.jsonl", "curated payload"
                )


class ExportAuditByteCapture(unittest.TestCase):
    def test_audit_uses_captured_bytes_when_output_changes_before_the_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "multi-agent-coordination-factory"
            first = multi_agent("a")
            second = multi_agent("b")
            second["goal"] = "cover the TTL race before merge"
            second["transcript"][0]["content"] = "The race is real; stop the patch."
            second["joint_outcome"] = "reverted until the TTL test lands"
            records = [first, second]
            write_jsonl(source / "batch-r01.jsonl", records)
            curated = root / "curated"
            compose_curated.compose_run(root / "run", curated)
            output = (
                curated
                / compose_curated.RECORDS_DIRNAME
                / "multi-agent-coordination-factory"
                / "batch-r01.jsonl"
            )
            safe_payload = output.read_bytes()
            unsafe_documents = [
                json.loads(line)
                for line in safe_payload.decode("utf-8").split("\n")
                if line
            ]
            unsafe_documents[0]["thought"] = "hidden payload captured before the audit"
            unsafe_payload = "".join(
                compose_curated.canonical_json(record) + "\n"
                for record in unsafe_documents
            ).encode("utf-8")
            output.write_bytes(unsafe_payload)
            real_collect = export_hf.collect_files

            def capture_then_replace(records_dir):
                captured = real_collect(records_dir)
                output.write_bytes(safe_payload)
                return captured

            with mock.patch.object(
                export_hf, "collect_files", side_effect=capture_then_replace
            ):
                with self.assertRaisesRegex(export_hf.ExportError, "hidden-thought"):
                    export_hf.export_run(curated, root / "export")
            self.assertFalse((root / "export").exists())


class ExportCli(unittest.TestCase):
    def test_cli_prints_provenance_and_reports_refusals(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                status = export_hf.main([str(curated), str(root / "export")])
            self.assertEqual(status, 0)
            self.assertTrue(json.loads(stdout.getvalue())["training_ready"])

            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                status = export_hf.main([str(curated), str(root / "export")])
            self.assertEqual(status, 2)
            self.assertIn("refusing to overwrite", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
