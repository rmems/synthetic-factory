"""Direct replay APIs reject excessive quiet simulations before execution."""

from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipelines'))
from oracle_grounded import families, generators, record, sim


class OracleMeshBounds(unittest.TestCase):
    def test_direct_simulator_refuses_excessive_steps_before_entering_range(self):
        cases = ((5000.5, 0.5), (1e300, 0.5), (1.0, 1e-300),
                 (float('inf'), 0.5), (float('nan'), 0.5), (1.0, 0.0),
                 (0.0, 0.5), (-1.0, 0.5), ('1', 0.5), (True, 0.5), (1.0, True))
        for duration, dt in cases:
            with self.subTest(duration=duration, dt=dt):
                with mock.patch.object(sim, 'range', side_effect=AssertionError('entered simulation'), create=True):
                    with self.assertRaises(ValueError):
                        sim.simulate_mesh([], [], [], duration, dt_ms=dt)

    def test_existing_ten_thousand_step_window_remains_supported(self):
        result = sim.simulate_mesh([sim.mesh_node('quiet')], [], [], 5000.0)
        self.assertEqual(result['total_spikes'], 0)
        self.assertEqual(result['duration_ms'], 5000.0)

    def test_exact_json_numeric_wrapper_retains_supported_numeric_semantics(self):
        from curate_identity_json import ExactJSONFloat
        self.assertEqual(sim.mesh_step_count(ExactJSONFloat('140.0'), 0.5), 280)

    def test_family_request_refuses_duration_above_catalog_window_before_events(self):
        item = record.build_record(families.MESH_FAMILY, 0, seed=7, environ={})
        item['scenario']['duration_ms'] = 140.5
        with mock.patch.object(generators, 'mesh_events', side_effect=AssertionError('built events')):
            with self.assertRaises(ValueError):
                families.mesh_request(item['scenario'], item['intervention'])

    def test_direct_reproduce_refuses_excessive_request_before_adapter_execution(self):
        item = record.build_record(families.MESH_FAMILY, 0, seed=7, environ={})
        item['scenario']['duration_ms'] = 1e300
        item['oracle']['configuration']['duration_ms'] = 1e300
        spec = families.spec_for(families.MESH_FAMILY)
        with mock.patch.object(type(spec), 'oracle', side_effect=AssertionError('selected adapter')):
            status, _detail = record.reproduce(item, environ={})
        self.assertEqual(status, 'invalid')


if __name__ == '__main__':
    unittest.main()
