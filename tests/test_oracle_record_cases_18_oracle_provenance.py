"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    DOUBLE,
    PINNED_COMMIT,
    Path,
    build,
    canon,
    copy,
    families,
    json,
    oracles,
    record,
    subprocess,
    sys,
    unittest,
)


class OracleProvenanceCase04(unittest.TestCase):
    def test_resolve_commit_reports_unknown_outside_a_repository(self):
        commit, dirty = oracles.resolve_commit(repo_root=Path("/"))
        self.assertEqual((commit, dirty), ("unknown", None))


class OracleProvenanceCase05(unittest.TestCase):
    def test_the_oracle_block_retains_the_configuration_and_seed(self):
        for family in families.FAMILY_NAMES:
            item = build(family)
            with self.subTest(family=family):
                self.assertTrue(item["oracle"]["configuration"])
                self.assertIsInstance(item["oracle"]["seed"], int)
                self.assertTrue(item["oracle"]["units"])
                self.assertEqual(item["oracle"]["repo"], oracles.REPO_SLUG)
                self.assertEqual(item["oracle"]["commit"], PINNED_COMMIT)


class OracleProvenanceCase06(unittest.TestCase):
    def test_the_stored_configuration_is_what_the_oracle_was_handed(self):
        for family in families.FAMILY_NAMES:
            item = build(family)
            spec = families.spec_for(family)
            request = spec.build_request(item["scenario"], item["intervention"])
            with self.subTest(family=family):
                self.assertEqual(
                    canon.normalize(request["configuration"]),
                    canon.normalize(item["oracle"]["configuration"]),
                )


class OracleProvenanceCase07(unittest.TestCase):
    def test_reproduction_rejects_a_tampered_stored_configuration(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["configuration"]["max_rate_hz"] = 1
        status, detail = record.reproduce(item, environ={})
        self.assertEqual(status, "mismatch")
        self.assertIn("configuration", detail)


class OracleProvenanceCase08(unittest.TestCase):
    def test_the_double_is_a_runnable_script(self):
        completed = subprocess.run(  # nosec B603 -- executes the fixed protocol fixture
            [sys.executable, str(DOUBLE), "ok"],
            input=json.dumps({"family": "f", "request": {}}),
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["measured"]["protocol_double"])


class RecordIsSelfContainedCase01(unittest.TestCase):
    def test_a_record_survives_deep_copy_and_still_validates(self):
        item = build(families.MESH_FAMILY)
        self.assertEqual(record.validate_record(copy.deepcopy(item)), [])


class RecordIsSelfContainedCase02(unittest.TestCase):
    def test_a_non_object_record_is_refused(self):
        for value in ("a string", 5, None, []):
            with self.subTest(value=value):
                layers = record.classify(value)
                self.assertTrue(layers["envelope"])


class RecordIsSelfContainedCase03(unittest.TestCase):
    def test_a_missing_envelope_key_is_refused(self):
        item = build(families.MESH_FAMILY)
        del item["oracle"]
        findings = record.validate_record(item)
        self.assertTrue(any("missing envelope keys" in f for f in findings), findings)


class RecordIsSelfContainedCase04(unittest.TestCase):
    def test_a_wrong_schema_id_is_refused(self):
        item = build(families.MESH_FAMILY)
        item["schema"] = "something-else/v9"
        findings = record.validate_record(item)
        self.assertTrue(any("schema must be" in f for f in findings), findings)


class RecordIsSelfContainedCase05(unittest.TestCase):
    def test_meta_identifies_the_family_and_round(self):
        item = build(families.MESH_FAMILY, round_number=4)
        self.assertEqual(item["meta"]["round"], 4)
        self.assertIn(families.MESH_FAMILY, item["meta"]["tags"])
        self.assertTrue(item["id"].startswith(families.MESH_FAMILY))
        self.assertIn("r04", item["id"])
