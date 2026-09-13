#!/usr/bin/env python3
"""Schema-parity tests for Bridge raster and gate sidecars."""

from __future__ import annotations

import json
import re
import unittest

try:
    from tests.test_curate_bridge import RASTER_SCHEMA, curate_bridge, gate_snn_fixture
except ModuleNotFoundError:
    from test_curate_bridge import (  # type: ignore[no-redef]
        RASTER_SCHEMA,
        curate_bridge,
        gate_snn_fixture,
    )


class RasterSchemaParity(unittest.TestCase):
    """Every runtime-supported sidecar carrier shares one schema definition."""

    def setUp(self):
        self.schema = json.loads(RASTER_SCHEMA.read_text(encoding="utf-8"))

    def test_excerpt_schema_uses_bounded_microsecond_timestamps(self):
        event = self.schema["$defs"]["raster"]["properties"]["excerpt"]["items"]
        self.assertEqual(event["required"], ["t_us", "neuron_id"])
        self.assertEqual(event["properties"]["t_us"]["type"], "integer")
        self.assertEqual(event["properties"]["t_us"]["minimum"], 0)
        self.assertEqual(event["properties"]["t_us"]["maximum"], 50_000)
        self.assertNotIn("t_ms", event["properties"])

    def test_nested_gate_snn_carriers_reference_the_canonical_definition(self):
        trajectory = self.schema["properties"]["language_view"]["properties"]["trajectory"][
            "properties"
        ]

        self.assertEqual(trajectory["gate_snn"], {"$ref": "#/$defs/gate_snn"})
        self.assertEqual(
            trajectory["safety_decision"]["properties"]["gate_snn"],
            {"$ref": "#/$defs/gate_snn"},
        )

    def test_nested_gate_compute_carriers_reference_the_canonical_definition(self):
        """Every carrier ``_gate_compute_sidecar`` accepts is schema-constrained."""

        ref = {"$ref": "#/$defs/gate_compute"}
        trajectory = self.schema["properties"]["language_view"]["properties"]["trajectory"][
            "properties"
        ]

        self.assertEqual(self.schema["properties"]["gate_compute"], ref)
        self.assertEqual(trajectory["gate_compute"], ref)
        self.assertEqual(trajectory["safety_decision"]["properties"]["gate_compute"], ref)
        self.assertIn("per_check", self.schema["$defs"]["gate_compute"]["properties"])

        for location in (
            "gate_compute",
            "language_view.trajectory.gate_compute",
            "language_view.trajectory.safety_decision.gate_compute",
        ):
            with self.subTest(location=location):
                record = gate_snn_fixture()
                record.pop("gate_compute", None)
                target = record
                for key in location.split(".")[:-1]:
                    target = target.setdefault(key, {})
                target["gate_compute"] = {"per_check": []}

                found, _value = curate_bridge._gate_compute_sidecar(record)

                self.assertEqual(found, location)
                node = self.schema["properties"]
                for key in location.split("."):
                    node = node[key]
                    node = node.get("properties", node)
                self.assertEqual(node, ref)

    def test_schema_requires_nonblank_routing_endpoints_like_the_validator(self):
        table_entry = self.schema["$defs"]["raster"]["properties"]["routing"]["properties"][
            "table"
        ]["items"]

        for endpoint in ("from", "to"):
            for blank in ("", "   ", "\t\n"):
                with self.subTest(endpoint=endpoint, value=repr(blank)):
                    keywords = table_entry["properties"][endpoint]
                    record = gate_snn_fixture()
                    entry = {"from": "a", "to": "b"}
                    entry[endpoint] = blank
                    record["raster"]["routing"]["table"] = [entry]

                    status = curate_bridge.raster_status(record)

                    self.assertFalse(status["raster_valid"])
                    self.assertIn(curate_bridge.REASON_RASTER_ROUTING, status["reason_codes"])
                    self.assertTrue(
                        len(blank) < keywords["minLength"]
                        or re.compile(keywords["pattern"]).search(blank) is None,
                        "schema must reject what the runtime validator rejects",
                    )

        for endpoint in ("from", "to"):
            with self.subTest(endpoint=endpoint, value="accepted"):
                keywords = table_entry["properties"][endpoint]
                self.assertGreaterEqual(len("thalamus"), keywords["minLength"])
                self.assertIsNotNone(re.compile(keywords["pattern"]).search("thalamus"))

    def test_schema_pins_the_runtime_gate_and_routing_requirements(self):
        gate = self.schema["$defs"]["gate_snn"]
        raster = self.schema["$defs"]["raster"]
        routing = raster["properties"]["routing"]
        table_entry = routing["properties"]["table"]["items"]

        self.assertEqual(gate["required"], ["decision", "populations"])
        self.assertIn("third_factor", routing["required"])
        self.assertEqual(
            routing["properties"]["third_factor"]["required"],
            ["modulator", "eligibility"],
        )
        self.assertEqual(table_entry["required"], ["from", "to", "weight"])
        self.assertEqual(table_entry["properties"]["weight"]["type"], "number")
        population = gate["properties"]["populations"]["items"]
        self.assertTrue(population["allOf"])

    def test_schema_rejects_a_blank_gate_decision_like_the_validator_does(self):
        decision = self.schema["$defs"]["gate_snn"]["properties"]["decision"]
        self.assertEqual(decision["type"], "string")
        self.assertGreaterEqual(decision["minLength"], 1)
        pattern = re.compile(decision["pattern"])
        gate = {
            "decision_window_ms": 10,
            "populations": [{"name": "p", "neurons": 4, "threshold": 0.5}],
        }

        for blank in ("", "   ", "\t\n"):
            with self.subTest(decision=repr(blank)):
                reason_codes: list[str] = []
                curate_bridge._validate_gate_snn(
                    {**gate, "decision": blank},
                    reason_codes=reason_codes,
                    evidence={},
                )
                self.assertIn(curate_bridge.REASON_GATE_SNN_INVALID, reason_codes)
                self.assertTrue(
                    len(blank) < decision["minLength"] or pattern.search(blank) is None,
                    "schema must reject what the runtime validator rejects",
                )

        accepted: list[str] = []
        curate_bridge._validate_gate_snn(
            {**gate, "decision": "ACCEPT"}, reason_codes=accepted, evidence={}
        )
        self.assertEqual(accepted, [])
        self.assertGreaterEqual(len("ACCEPT"), decision["minLength"])
        self.assertIsNotNone(pattern.search("ACCEPT"))


if __name__ == "__main__":
    unittest.main()
