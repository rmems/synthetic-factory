"""Only independently reviewed native research rows grant parity identity authority."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from pipelines import curate_identity as identity, curate_parity_policy as policy


class ParityRegistry(unittest.TestCase):
    def _load(self, row, schema='factory-registry-v0.4'):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'registry.json'
            path.write_text(json.dumps({'schema_version': schema, 'lookup_key': 'path_id', 'factories': [row]}))
            return identity.load_registry(path)

    def test_exact_research_routes_without_invented_provider(self):
        for kind in policy.KINDS:
            with self.subTest(kind=kind):
                row = policy.reviewed_row(kind)
                parsed = self._load(row).by_path_id[row['path_id']]
                self.assertIsNone(parsed.provider)
                self.assertIsNone(parsed.channel)
                self.assertEqual(parsed.training_ready_policy, 'never')
                self.assertEqual(parsed.project_training_policy, 'blocked')

    def test_registry_mutations_cannot_grant_authority(self):
        mutations = {'path_id': 'arbitrary', 'payload_factory': 'other', 'source_type': 'hosted',
                     'generator_version': 'sha256:' + '0' * 64, 'catalog_sha256': 'sha256:' + '0' * 64,
                     'provider': 'openai', 'intended_use': 'training_candidate',
                     'project_training_policy': 'allowed', 'identity_authoritative': 1,
                     'parity_policy_sha256': '0' * 64, 'extra': 'unreviewed'}
        for field, value in mutations.items():
            with self.subTest(field=field):
                row = policy.reviewed_row('hardware_parity')
                row[field] = value
                with self.assertRaises(identity.IdentityCurationError):
                    self._load(row)

    def test_legacy_schema_cannot_claim_native_route(self):
        for version in ('factory-registry-v0.1', 'factory-registry-v0.2', 'factory-registry-v0.3'):
            with self.subTest(version=version), self.assertRaises(identity.IdentityCurationError):
                self._load(policy.reviewed_row('hardware_parity'), version)

    def test_modified_policy_copy_has_no_authority(self):
        document = policy.load_policy()
        changed = copy.deepcopy(document)
        changed['rows'][0]['project_training_policy'] = 'allowed'
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'policy.json'
            path.write_text(json.dumps(changed))
            with self.assertRaises(policy.ParityPolicyError):
                policy.load_policy(path)
