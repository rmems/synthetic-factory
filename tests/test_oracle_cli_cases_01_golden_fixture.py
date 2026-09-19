"""Focused cases split from test_oracle_grounded_cli.py."""

from test_oracle_grounded_cli import (
    GOLDEN,
    INVALID,
    Path,
    families,
    json,
    oracles,
    read_jsonl,
    record,
    replay_diagnostic_fixture,
    tempfile,
    unittest,
)


class GoldenFixtureCase01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((GOLDEN / "manifest.json").read_text())
    def test_the_fixture_regenerates_byte_for_byte(self):
        with tempfile.TemporaryDirectory(prefix="oracle-golden-") as temp:
            out = Path(temp) / "run"
            replay_diagnostic_fixture(self.manifest, out)
            committed = sorted(
                path.relative_to(GOLDEN) for path in GOLDEN.rglob("*") if path.is_file()
            )
            produced = sorted(path.relative_to(out) for path in out.rglob("*") if path.is_file())
            self.assertEqual(committed, produced)
            for relative in committed:
                with self.subTest(path=str(relative)):
                    self.assertEqual(
                        (out / relative).read_text(),
                        (GOLDEN / relative).read_text(),
                        f"{relative} drifted; regenerate the fixture if this was intended",
                    )


class GoldenFixtureCase02(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((GOLDEN / "manifest.json").read_text())
    def test_the_manifest_digests_match_the_committed_files(self):
        for relative, entry in self.manifest["files"].items():
            path = GOLDEN / relative
            with self.subTest(path=relative):
                self.assertTrue(path.is_file())
                self.assertEqual(len(read_jsonl(path)), entry["records"])


class GoldenFixtureCase03(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((GOLDEN / "manifest.json").read_text())
    def test_the_manifest_pins_the_current_implementation(self):
        self.assertEqual(self.manifest["module_digest"], oracles.module_digest())
        self.assertNotEqual(self.manifest["oracle_commit"], "unknown")


class GoldenFixtureCase04(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((GOLDEN / "manifest.json").read_text())
    def test_the_fixture_covers_every_family(self):
        self.assertEqual(sorted(self.manifest["families"]), sorted(families.FAMILY_NAMES))
        for family in families.FAMILY_NAMES:
            with self.subTest(family=family):
                self.assertTrue((GOLDEN / family).is_dir())


class GoldenFixtureCase05(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((GOLDEN / "manifest.json").read_text())
    def test_historical_fixture_records_are_diagnostic_and_nonpublishable(self):
        # Replay proves deterministic measurements, not checkout provenance.
        # Current-checkout publication is tested separately by generation and
        # sealed procedural curation tests.
        for path in GOLDEN.rglob("*.jsonl"):
            for item in read_jsonl(path):
                with self.subTest(record=item["id"]):
                    self.assertEqual(item["oracle"]["implementation"], "reference")
                    self.assertFalse(item["oracle"]["runtime_bound"])
                    self.assertIsNone(item["oracle"]["dirty"])
                    self.assertFalse(item["validation"]["publishable"])


class GoldenFixtureCase06(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((GOLDEN / "manifest.json").read_text())
    def _assert_accepted_records_are_valid(self):
        for path in GOLDEN.rglob("accepted-*.jsonl"):
            for item in read_jsonl(path):
                with self.subTest(record=item["id"]):
                    self.assertEqual(item["validation"]["status"], "accepted")
                    self.assertEqual(record.validate_record(item), [])
    def _assert_rejected_records_are_reasoned(self):
        for path in GOLDEN.rglob("rejected-*.jsonl"):
            for item in read_jsonl(path):
                with self.subTest(record=item["id"]):
                    self.assertEqual(item["validation"]["status"], "rejected")
                    self.assertTrue(item["validation"]["reasons"])
                    self.assertEqual(record.classify(item)["envelope"], [])
    def test_accepted_and_rejected_records_are_filed_separately(self):
        self._assert_accepted_records_are_valid()
        self._assert_rejected_records_are_reasoned()


class GoldenFixtureCase07(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((GOLDEN / "manifest.json").read_text())
    def test_the_rejected_temporal_memory_records_say_why(self):
        path = GOLDEN / families.MEMORY_FAMILY / "rejected-r01.jsonl"
        items = read_jsonl(path)
        self.assertTrue(items, "the fixture should retain at least one rejected trial")
        for item in items:
            with self.subTest(record=item["id"]):
                self.assertTrue(
                    any("temporal dependence" in r for r in item["validation"]["reasons"])
                )
                self.assertFalse(item["result"]["measured"]["temporal_dependence"]["demonstrated"])


class GoldenFixtureCase08(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((GOLDEN / "manifest.json").read_text())
    def test_every_fixture_record_reproduces_from_its_stored_scenario(self):
        for path in sorted(GOLDEN.rglob("*.jsonl")):
            for item in read_jsonl(path):
                with self.subTest(record=item["id"]):
                    status, detail = record.reproduce(item, environ={})
                    self.assertEqual(status, "reproduced", detail)


class GoldenFixtureCase09(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((GOLDEN / "manifest.json").read_text())
    def test_every_fixture_record_retains_oracle_provenance(self):
        for path in sorted(GOLDEN.rglob("*.jsonl")):
            for item in read_jsonl(path):
                oracle = item["oracle"]
                with self.subTest(record=item["id"]):
                    self.assertEqual(oracle["repo"], oracles.REPO_SLUG)
                    self.assertNotEqual(oracle["commit"], "unknown")
                    self.assertEqual(oracle["module_digest"], oracles.module_digest())
                    self.assertTrue(oracle["configuration"])
                    self.assertTrue(oracle["units"])
                    self.assertTrue(oracle["stages"])


class InvalidFixturesCase01(unittest.TestCase):
    def defects(self, name):
        # The tag names the committed defect for the reader. It is popped out
        # of the record before validation because the meta vocabulary is
        # closed: left in place it would be rejected first and mask the one
        # defect each fixture exists to prove.
        pairs = []
        for item in read_jsonl(INVALID / f"{name}.jsonl"):
            pairs.append((item["meta"].pop("_defect"), item))
        return pairs
    def test_every_invalid_oracle_record_is_rejected(self):
        pairs = self.defects("invalid-oracle")
        self.assertGreaterEqual(len(pairs), 9)
        for defect, item in pairs:
            with self.subTest(defect=defect):
                self.assertTrue(
                    record.validate_record(item),
                    f"{defect} was accepted",
                )

