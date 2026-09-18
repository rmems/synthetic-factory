"""Gate authentication replays the complete preserved native parity mapping."""
import copy
import unittest
from pipelines import curate_identity as identity
from pipelines import curate_gate_manifests as manifests
from pipelines import curate_gate_identity_gate as claims
from pipelines import curate_gate_identity_mapping as mappings
from tests.test_parity_curation import fresh_parity_records

def _stage_native_lanes(fixture, records, entries):
    import json
    payloads = {}
    for factory in {record['meta']['factory'] for record in records}:
        family_records = [record for record in records if record['meta']['factory'] == factory]
        relative = factory + '/fresh.jsonl'
        lines = [json.dumps(record, separators=(',', ':')) for record in family_records]
        payloads[relative] = ('\n'.join(lines) + '\n').encode()
        for root in (fixture.source_run, fixture.lane_core):
            target = root / relative
            target.parent.mkdir()
            target.write_bytes(payloads[relative])
        for line, (record, text) in enumerate(zip(family_records, lines), 1):
            source = identity.SourceRecord(record, relative, line,
                                           identity.sha256_bytes(text.encode()), text)
            entries.append(identity.curate_record(source).mapping)
    return payloads



class ParityIdentityGate(unittest.TestCase):
    def _entry(self):
        record = fresh_parity_records()[0]
        result = identity.curate_record(identity.SourceRecord(record, record['meta']['factory'] + '/fresh.jsonl', 1))
        entry = manifests._normalize_entry(result.mapping, {'order': 1, 'transform': 'curate_identity',
                                                            'version': identity.TRANSFORM_VERSION})
        return record, entry

    def test_complete_replay_passes_identity_gate_without_training_authority(self):
        record, entry = self._entry()
        entry['source_originals_sha256'] = claims._authenticate_identity_source_claims(entry, record, 'parity')
        result = mappings._identity_mapping_gate([entry], {(entry['source_path'], 1): record})
        self.assertTrue(result['passed'], result)

    def test_outer_and_sealed_authority_mutations_fail_replay(self):
        record, entry = self._entry()
        for field, value in (('source_line', True), ('output_id', 'forged'), ('record_kind', 'thalamic')):
            with self.subTest(field=field):
                changed = copy.deepcopy(entry)
                changed[field] = value
                with self.assertRaises(claims.GateError):
                    claims._authenticate_identity_source_claims(changed, record, 'parity')

    def test_real_gate_composition_preserves_fresh_native_physical_lines(self):
        import json
        import tempfile
        from pathlib import Path
        from pipelines import training_audit
        from tests.gate_fixture import GateFixture, _captured_main
        records = fresh_parity_records()
        with tempfile.TemporaryDirectory() as temporary:
            fixture = GateFixture(Path(temporary))
            entries = json.loads(fixture.manifest_paths[1].read_text())
            for entry in entries:
                entry['transform_version'] = identity.TRANSFORM_VERSION
            payloads = _stage_native_lanes(fixture, records, entries)
            fixture.manifest_paths[1].write_text(json.dumps(entries))
            plan = json.loads(fixture.plan_path.read_text())
            plan['lanes'][1]['version'] = identity.TRANSFORM_VERSION
            fixture.plan_path.write_text(json.dumps(plan))
            code, _report, errors = _captured_main(['integrate', '--plan', str(fixture.plan_path),
                                                  '--cleaned-out', str(fixture.cleaned)])
            self.assertTrue(fixture.cleaned.exists(), (code, errors))
            result = fixture.manifest()['gates']['identity_mappings']
            self.assertTrue(result['passed'], result)
            for relative, payload in payloads.items():
                self.assertEqual((fixture.cleaned / relative).read_bytes(), payload)
            report = training_audit.audit_run(fixture.cleaned)
            self.assertFalse(report['training_ready'])
            self.assertEqual(report['totals']['parity_research_records'], 15, report['totals'])
