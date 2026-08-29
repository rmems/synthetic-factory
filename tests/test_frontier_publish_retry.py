#!/usr/bin/env python3
"""Cohesive frontier execution-gate regression suite."""

import json
import tempfile
import unittest

from tests.frontier_gate_helpers import (
    FrontierGateTestCaseMixin,
    round_txn,
)


class FrontierPublishRetry(FrontierGateTestCaseMixin, unittest.TestCase):
    def test_publish_retry_preserves_recorded_waivers(self):
        for tag, retry_arg in (
            ("gate-retry", "reworded on retry, same batch"),
            ("gate-resume", None),
        ):
            with tempfile.TemporaryDirectory() as td:
                factory = self.factory(td)
                reservation, reason = self._setup_retry_waiver(factory, tag)
                args = [factory, 1, reservation["token"]]
                if retry_arg is not None:
                    args.append(retry_arg)
                manifest = round_txn.publish(*args)
                self.assertEqual(
                    manifest["execution_verification"]["override"]["reason"], reason
                )
                self.assertTrue((factory / "ROUND-r01.complete.json").is_file())


    def test_publish_retry_migrates_a_pre_gate_publishing_marker(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)

            def mutate(payload):
                payload["version"] = 1
                payload.pop("execution_verification", None)
                return payload

            reservation = self._mutate_publishing_marker(
                factory, "gate-legacy-retry", mutate
            )

            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(
                manifest["execution_verification"]["counts"]["verified"], 1
            )
            self.assertIsNone(manifest["execution_verification"]["override"])
            self.assertEqual(
                json.loads((factory / "ROUND-r01.complete.json").read_text()),
                manifest,
            )


    def test_publish_retry_rejects_corrupted_execution_verification(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)

            def mutate(payload):
                payload["execution_verification"]["counts"]["verified"] = 999
                return payload

            self._assert_retry_publish_rejected(
                factory,
                "gate-corrupt-retry",
                mutate,
                "execution verification conflicts",
            )


    def test_publish_retry_migrates_a_legacy_v1_publishing_marker(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)

            def mutate(payload):
                payload["version"] = 1
                return payload

            reservation = self._mutate_publishing_marker(
                factory, "gate-v1-retry", mutate
            )

            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(manifest["version"], 2)
            self.assertEqual(
                manifest["execution_verification"]["counts"]["verified"], 1
            )
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())


    def test_publish_retry_rejects_version_2_marker_missing_verification(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)

            def mutate(payload):
                payload.pop("execution_verification", None)
                return payload

            self._assert_retry_publish_rejected(
                factory,
                "gate-v2-missing",
                mutate,
                "version 2 publishing marker is missing execution verification",
            )



if __name__ == "__main__":
    unittest.main()
