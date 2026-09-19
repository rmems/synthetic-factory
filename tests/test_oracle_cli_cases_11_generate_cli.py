"""Focused cases split from test_oracle_grounded_cli.py."""

from test_oracle_grounded_cli import (
    GENERATE,
    PINNED_COMMIT,
    Path,
    VALIDATE,
    generate_status,
    json,
    mock,
    oracle_generate,
    os,
    read_jsonl,
    run_cli,
    tempfile,
    unittest,
)


class GenerateCliCase14(unittest.TestCase):
    def test_a_generated_run_passes_its_own_validator(self):
        with tempfile.TemporaryDirectory(prefix="oracle-roundtrip-") as temp:
            out = Path(temp) / "run"
            generated = run_cli(
                GENERATE,
                "--count",
                2,
                "--round",
                3,
                "--seed",
                777,
                "--oracle-commit",
                PINNED_COMMIT,
                "--no-oracle-dirty",
                out,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            validated = run_cli(VALIDATE, "--reproduce", out)
            self.assertEqual(validated.returncode, 0, validated.stderr)
            report = json.loads(validated.stdout)
            self.assertEqual(report["invalid"], 0)
            self.assertEqual(report["records"], 10)
            self.assertEqual(report["reproduce"], {"reproduced": 10})
            for path in out.rglob("*.jsonl"):
                for item in read_jsonl(path):
                    self.assertEqual(item["meta"]["round"], 3)
                    self.assertIn("r03", item["id"])


class GenerateCliCase15(unittest.TestCase):
    def test_an_oversized_file_refuses_to_publish(self):
        # oracle_validate.py always rejects a run over its serialized-byte
        # limits; refuse to publish one instead of exiting successfully.
        with tempfile.TemporaryDirectory(prefix="oracle-oversized-file-") as temp:
            out = Path(temp) / "run"
            status, err = generate_status(
                out, mock.patch.object(oracle_generate, "MAX_JSONL_BYTES", 1))
            self.assertEqual(status, 1)
            self.assertFalse(out.exists())
            self.assertIn("exceeding the validator's", err)
            self.assertIn("per-file limit", err)


class GenerateCliCase16(unittest.TestCase):
    def test_reservation_refuses_a_parent_swapped_into_the_raw_tree(self):
        # _raw_destination_error runs on the caller's path before anything is
        # written; a non-cooperating process can then swap an ancestor for a
        # symlink into outputs/raw/. The reservation must authenticate where
        # its parent descriptor actually landed and refuse the raw tree, or
        # the lock and staging files would be created inside the raw tree.
        with tempfile.TemporaryDirectory(prefix="oracle-raw-swap-") as temp:
            temp = Path(temp)
            fake_raw = temp / "outputs" / "raw"
            (fake_raw / "runs").mkdir(parents=True)
            swapped = temp / "workdir"
            swapped.symlink_to(fake_raw / "runs")
            with mock.patch.object(oracle_generate, "RAW_TREE", fake_raw):
                with self.assertRaises(OSError) as context:
                    oracle_generate.reserve_run(swapped / "run")
            self.assertIn("immutable raw tree", str(context.exception))
            self.assertEqual(list((fake_raw / "runs").iterdir()), [])


class GenerateCliCase17(unittest.TestCase):
    def test_a_publication_race_never_deletes_the_impostor(self):
        # If a non-cooperating writer swaps its own directory in after our
        # rename, the mismatch is quarantined aside and publication fails,
        # but the foreign inode's content must survive: it is known NOT to
        # be our staging tree, so deleting it would be third-party data loss.
        with tempfile.TemporaryDirectory(prefix="oracle-race-") as temp:
            staging = Path(temp) / "staging"
            staging.mkdir()
            (staging / "payload.txt").write_text("theirs", encoding="utf-8")
            out = Path(temp) / "run"
            real_identity = oracle_generate._directory_identity(staging)
            forged_identity = (real_identity[0] + 1, real_identity[1] + 1)
            with mock.patch.object(
                oracle_generate,
                "_directory_identity",
                side_effect=[real_identity, forged_identity],
            ):
                with self.assertRaises(OSError):
                    oracle_generate.publish_noreplace(staging, out, real_identity)
            quarantined = [
                path
                for path in Path(temp).iterdir()
                if path.name.startswith(".run.rejected-")
            ]
            self.assertEqual(len(quarantined), 1, list(Path(temp).iterdir()))
            self.assertEqual(
                (quarantined[0] / "payload.txt").read_text(), "theirs"
            )
            self.assertFalse(out.exists())


class GenerateCliCase18(unittest.TestCase):
    def test_staging_cleanup_only_quarantines_the_authenticated_inode(self):
        # The pre-publication counterpart of the publication race: cleanup
        # must quarantine only the staging inode it created, never delete a directory
        # another writer swapped in at the same path.
        with tempfile.TemporaryDirectory(prefix="oracle-staging-race-") as temp:
            staging = Path(temp) / "staging"
            staging.mkdir()
            identity = oracle_generate._directory_identity(staging)
            moved = Path(temp) / "moved-away"
            os.rename(staging, moved)
            staging.mkdir()
            (staging / "payload.txt").write_text("theirs", encoding="utf-8")
            oracle_generate._cleanup_staging(staging, identity)
            self.assertTrue(staging.exists())
            self.assertEqual((staging / "payload.txt").read_text(), "theirs")
            # The authenticated inode is detached for recovery, not deleted.
            oracle_generate._cleanup_staging(moved, identity)
            self.assertFalse(moved.exists())
            quarantines = list(Path(temp).glob(".synthetic-factory-rollback-*"))
            self.assertEqual(len(quarantines), 1)
            self.assertEqual(oracle_generate._directory_identity(quarantines[0]), identity)
            # And an unknown identity never deletes anything.
            oracle_generate._cleanup_staging(staging, None)
            self.assertTrue(staging.exists())

