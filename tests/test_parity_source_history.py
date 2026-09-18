"""Reviewed immutable source stamps coexist with complete current validation."""

import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import hardware_parity as hp
import hardware_parity_provenance as hp_provenance
import nir_equivalence as nir
import nir_equivalence_provenance as nir_provenance

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "tests/fixtures/parity-history/0bbeb5e6"
CASES = (
    (hp, "hardware-parity-spike-trajectories", "312fa3eb5589413ec3f9804f5235f417ca671fc98cdfd410d4585a7f5d27f9a1"),
    (nir, "nir-cross-runtime-equivalence", "de0582292c4d2a98eaca91c35998580cc991e466ba953f1cd7c8b0543c59da90"),
)
NEXT_SOURCE_STAMPS = (
    ("sha256:86a54ae338155603aa1e5291f34f843ea2856f3fd7aa24be3fb770792a25f449",
     "a526b33c278a217a6f3cda319b6664fec2ee9b929a15e4074a1ab4d8a1e4bddc"),
    ("sha256:f8069de53c4955c474f3b15493c1e044a3444567d931773e6dfc664d7d2fa3d4",
     "0950baba0ef558259f88c43b8fc3a40e71a4f66b36d1c420eca6ebbe0801e628"),
)
LATEST_SOURCE_STAMPS = (
    ("sha256:13d02b4bb48c2a568d14099230020fb1cfc8caa67a1a868b304014bf6ff2cde6",
     "78acb439bd8c1236ee61e1e6ea467a7f4db7d73b022e556cfd88812ffd43dff8"),
    ("sha256:033a6a90bbc65a34d5f306c36e25cb411d91bf8206105ab0fe3fb6b200a0cb62",
     "24c042c31da4c8174560cc0b41fd09888fb2f9e91c2086909917b6b648309fe3"),
)

RECENT_SOURCE_STAMPS = (
    ("sha256:ebe175c583a73488c5fdc23fcacb51a60c3088743fdf0d788090b72a9168a600",
     "088aaa8476bb97d9217253b894258f13f7647e65e1fd89992fa3dddbc43eb7ab"),
    ("sha256:1973de002f744fceeddff9c2e13bb4f8dcc9256ef2cdc2663d66cc6a03faa5f6",
     "515c4e444aaa83c472d4a5e5701d4b3bff2381f7d2737f9203a9f4e5992c3f41"),
)


SELECTED_CAPTURE_SOURCE_STAMPS = (
    ('sha256:10adc613345266b99469f07324c07b6a7c8bac6189bf1c05d446dc92b4d1f7b8',
     'd1ede19755b25c7bc7e8d7fe417f82b73a46c65155dacca3887432958cde1fae'),
    ('sha256:1165884bb47c71b68db70b3f49e1d6a1357ae3fc92daebdc74085f54b1142d0a',
     '87f57427d678301afc2e33f6cd9c24bc804ea1ae42fb3af7b85805f7ef291fbd'),
)

CURRENT_CATALOG_SOURCE_STAMPS = (
    ('sha256:0678792200503ef3c9e1d9a717a481411c9ea34d0b8d25ad133840e784a910e6',
     'df36b001ec78b9d2c0f37d9fb4baa93622d1dc9b07d0e605210a2a401eda6063'),
    ('sha256:03b7dc18c8b9b9927b8310d57949e03f600c35d236f09be5eabe2a521a226eaa',
     '449fa8bc214dba2d1cc5e6a5eec74d7f591ff44d85e65c232f0d809dad416445'),
)

DEPLOYMENT_SOURCE_STAMPS = (
    ('sha256:9ea2564618adbb3b497667b65505151bbd0de8850002394ca43a3623c62e87f1',
     '6b5543e1c0c795752cfe09633281d698c2375329cde6f4f19988a298739d4cf5'),
    ('sha256:04c48e47779b12d044d9eafec8efc6eec2855bc91c8b1b70a3e2e47aec957b8c',
     '96c5c2de5c4dada6b7c63d80645946aede51c9ff6563fd23df99874fb33af810'),
)


class HistoricalSourceStamps(unittest.TestCase):
    def _records(self, slug, expected_hash):
        raw = (HISTORY / slug / "batch-r01.jsonl").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), expected_hash)
        return [json.loads(line) for line in raw.split(b"\n") if line]

    def test_reviewed_historical_bytes_still_require_current_semantics(self):
        for module, slug, checksum in CASES:
            with self.subTest(family=slug):
                self._assert_current_semantics(module, self._records(slug, checksum))

    def test_reviewed_followup_stamps_do_not_authorize_obsolete_scenarios(self):
        for stamps in (NEXT_SOURCE_STAMPS, LATEST_SOURCE_STAMPS, RECENT_SOURCE_STAMPS, SELECTED_CAPTURE_SOURCE_STAMPS):
            self._check_followup_stamps(stamps)

    def test_reviewed_current_catalog_bytes_survive_validator_refactors(self):
        self._check_current_catalog_stamps(CURRENT_CATALOG_SOURCE_STAMPS)
        self._check_current_catalog_stamps(DEPLOYMENT_SOURCE_STAMPS)

    def _check_current_catalog_stamps(self, stamps):
        for case, (source, checksum) in zip(CASES, stamps, strict=True):
            module, slug, _ = case
            raw = (ROOT / 'tests/fixtures/parity-run' / slug / 'batch-r01.jsonl').read_bytes()
            current = json.loads(raw.split(b'\n')[0])['provenance']['generator_version']
            reviewed = raw.replace(current.encode(), source.encode())
            # Independently pinned raw bytes from the reviewed published commit.
            self.assertEqual(hashlib.sha256(reviewed).hexdigest(), checksum)
            records = [json.loads(line) for line in reviewed.split(b'\n') if line]
            self.assertEqual(module.validate_records(records), [])

    def _check_followup_stamps(self, stamps):
        for case, (source, checksum) in zip(CASES, stamps, strict=True):
            module, slug, original_checksum = case
            records = self._records(slug, original_checksum)
            previous = records[0]["provenance"]["generator_version"]
            raw = (HISTORY / slug / "batch-r01.jsonl").read_bytes()
            next_raw = raw.replace(previous.encode(), source.encode())
            self.assertEqual(hashlib.sha256(next_raw).hexdigest(), checksum)
            records = [json.loads(line) for line in next_raw.split(b"\n") if line]
            with self.subTest(family=slug):
                self._assert_current_semantics(module, records)

    def _assert_current_semantics(self, module, records):
        if module is hp:
            self.assertEqual(module.validate_records(records), [])
            return
        obsolete = [r for r in records if r["scenario"]["id"] == "nir-recurrent-cycle"]
        unchanged = [r for r in records if r not in obsolete]
        self.assertEqual(len(obsolete), 1)
        self.assertEqual(len(unchanged), 8)
        self.assertEqual(module.validate_records(unchanged), [])
        errors = module.validate_record(obsolete[0], "historical")
        self.assertTrue(any("scenario.graph does not match" in error for error in errors), errors)
        _, view_errors = module.build_training_views(unchanged)
        self.assertTrue(any("catalog" in error for error in view_errors), view_errors)

    def test_historical_stamp_does_not_authorize_catalog_or_policy_tampering(self):
        changes = (
            ("generator", "forged.generator"),
            ("generator_version", "sha256:" + "a" * 64),
            ("catalog_digest", "sha256:" + "b" * 64),
            ("catalog_authorship", {"project_training_policy": "allowed"}),
        )
        for module, slug, checksum in CASES:
            original = self._records(slug, checksum)[0]
            for field, value in changes:
                record = copy.deepcopy(original)
                record["provenance"][field] = value
                with self.subTest(family=slug, field=field):
                    self.assertTrue(module.validate_record(record, "history"))

    def test_historical_stamp_still_requires_measurement_replay(self):
        for module, slug, checksum in CASES:
            record = self._records(slug, checksum)[0]
            if module is hp:
                record["oracle"]["software"]["spikes"][0][0] ^= 1
            else:
                runtime = next(row for row in record["oracle"]["runtimes"] if row["status"] == "executed")
                runtime["outputs"]["spike_count"] += 1
            with self.subTest(family=slug):
                self.assertTrue(module.validate_record(record, "history"))


class SharedSourceClosure(unittest.TestCase):
    def test_shared_source_changes_change_both_generator_versions(self):
        shared = (
            "oracle_grounded/parity_terms.py", "oracle_grounded/envelope.py",
            "oracle_grounded/family_digest.py", "oracle_grounded/import_twins.py",
            "exact_json.py", "exact_json_encoding.py", "tag_jsonutil.py", "raw_tree_guard.py",
            "validate_run_provenance.py", "validate_run_spikes.py",
            "../schemas/thalamic-trajectory.schema.json",
        )
        read_text = Path.read_text
        for module in (hp_provenance, nir_provenance):
            before = module._module_source_digest()
            for relative in shared:
                target = (ROOT / "pipelines" / relative).resolve()

                def changed(path, *args, target=target, **kwargs):
                    text = read_text(path, *args, **kwargs)
                    return text + "\n# source changed\n" if path.resolve() == target else text

                with self.subTest(family=module.__name__, source=relative):
                    with patch.object(Path, "read_text", new=changed):
                        self.assertNotEqual(before, module._module_source_digest())
