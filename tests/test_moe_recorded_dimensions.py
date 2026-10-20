"""Recorded routing must fit its declared teacher before it can be emitted."""

import copy
import unittest

from test_moe_router import mr, oc, recording_from_reference


class RecordedDimensions(unittest.TestCase):
    def test_inconsistent_recorded_dimensions_are_refused_at_route(self):
        text = "recorded dimension boundary"
        original = recording_from_reference([text])
        changes = {
            "layer_count": lambda layers: layers.pop(),
            "top_k": lambda layers: layers[0]["top_k_experts"].append(7),
            "expert_range": lambda layers: layers[0]["top_k_experts"].__setitem__(0, 999),
            "logit_width": lambda layers: layers[0]["router_logits"].append(0.0),
        }
        for name, change in changes.items():
            recording = copy.deepcopy(original)
            layers = recording["observations"][mr.RecordedTeacherRouter.key_for(text)]["layers"]
            change(layers)
            router = mr.RecordedTeacherRouter(recording)
            with self.subTest(name=name), self.assertRaises(oc.OracleUnavailable):
                router.route(text)

    def test_valid_recording_remains_replayable(self):
        text = "valid recorded dimensions"
        recording = recording_from_reference([text])
        result = mr.RecordedTeacherRouter(recording).route(text)
        self.assertEqual(len(result.layers), recording["teacher"]["num_layers"])

    def test_malformed_layer_data_chains_the_original_error(self):
        text = "malformed recorded layer"
        recording = recording_from_reference([text])
        router = mr.RecordedTeacherRouter(recording)
        layer = copy.deepcopy(recording["observations"][router.key_for(text)]["layers"][0])
        del layer["routing_entropy"]
        with self.assertRaisesRegex(oc.OracleUnavailable, "malformed layer data") as caught:
            router._routing_from_recorded(layer, layer["layer"])
        self.assertIsInstance(caught.exception.__cause__, KeyError)
        self.assertEqual(caught.exception.__cause__.args, ("routing_entropy",))
