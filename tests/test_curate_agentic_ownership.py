#!/usr/bin/env python3
"""Mill-ownership context: what may name a home factory, and what refuses."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PIPELINES = TESTS.parent / "pipelines"
for _path in (TESTS, PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import curate_agentic  # noqa: E402
from curate_agentic import (  # noqa: E402
    ACTION_RETAINED,
    REASON_FOREIGN_PAYLOAD_FACTORY,
    curate_source,
)
from curate_agentic_fixtures import (  # noqa: E402
    STAMPEDE_CONTROLS,
    curate_mill_run,
    mill_episode,
    step,
    thalamic_fixture,
    write_mill_run,
)


def _write_prefix_probe(root, placements):
    """One single-record batch per ``(factory, record id)`` placement."""
    for factory, identifier in placements:
        directory = root / factory
        directory.mkdir(parents=True)
        (directory / "batch-r01.jsonl").write_text(
            json.dumps(mill_episode(identifier, "fix verify", factory)) + "\n",
            encoding="utf-8",
        )


class MillOwnershipContext(unittest.TestCase):
    """Incomplete mill ownership must be reported, never silently resolved."""

    def test_side_stamped_preference_mill_is_reported(self):
        """Codex #96 P1: a preference attesting its factory on both sides.

        The wrapper carries no ``meta.factory`` -- the legacy shape
        ``curate_identity._payload_factory`` accepts. With a native
        destination-stamped id prefix and a stopword-only goal, the id-prefix
        and goal-family axes see nothing, so a wrapper-only payload lookup let
        the record through with no FOREIGN_PAYLOAD_FACTORY at all. It is
        reported rather than quarantined here because naming an out-of-scope
        home factory leaves the ownership context incomplete, exactly as in
        test_partial_context_reports_foreign_payload_without_quarantine.
        """

        def side(label, success):
            return {
                "steps": [
                    step(1, "Observation: the probe reproduced the report"),
                    step(2, f"Observation: the {label} branch was taken"),
                ],
                "outcome": f"{label} outcome",
                "reward": {"success": success},
                "meta": {
                    "factory": "docker-build-cache-factory",
                    "round": 1,
                    "generator": "grok-4.6",
                },
            }

        side_stamped = {
            "id": "cst-r05-side-stamped-preference",
            "goal": "fix verify",
            "chosen": side("fixed", True),
            "rejected": side("failed", False),
        }
        self.assertIsNone(side_stamped.get("meta"))

        run = curate_mill_run(list(STAMPEDE_CONTROLS) + [side_stamped])

        self.assertEqual(run["summary"]["input_records"], 5)
        mix = run["summary"]["mill_family"]
        self.assertEqual(mix["record_ids"], [side_stamped["id"]])
        self.assertEqual(mix["reason_codes"], {REASON_FOREIGN_PAYLOAD_FACTORY: 1})
        self.assertFalse(mix["context_complete"])
        self.assertEqual(run["summary"]["quarantined_foreign_mill_records"], 0)

    def test_tied_snapshot_identity_refuses_cleaned_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run"
            root.mkdir()
            write_mill_run(root, list(STAMPEDE_CONTROLS))
            snapshot = root / "staging-copy"
            snapshot.mkdir()
            (snapshot / "batch-r01.jsonl").write_text(
                "".join(
                    json.dumps(record) + "\n"
                    for record in (
                        mill_episode(
                            "snapshot-cache",
                            "fix verify",
                            "cache-stampede-factory",
                        ),
                        mill_episode(
                            "snapshot-graphql",
                            "fix verify",
                            "graphql-nplusone-factory",
                        ),
                    )
                ),
                encoding="utf-8",
            )
            run = curate_source(root)
            out = Path(temporary) / "cleaned"

            mill_summary = run["summary"]["mill_family"]
            self.assertFalse(mill_summary["context_complete"])
            self.assertEqual(
                mill_summary["unresolved_destinations"], ["staging-copy"]
            )
            with self.assertRaisesRegex(ValueError, "multi-factory"):
                curate_agentic.write_cleaned_tree(run, out)
            self.assertFalse(out.exists())

    def test_unverified_resolved_snapshot_identity_refuses_cleaned_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run"
            root.mkdir()
            write_mill_run(root, list(STAMPEDE_CONTROLS))
            snapshot = root / "staging-copy"
            snapshot.mkdir()
            absent = "unknown-absent-factory"
            record = mill_episode(
                "snapshot-unknown",
                "fix verify",
                absent,
            )
            (snapshot / "batch-r01.jsonl").write_text(
                json.dumps(record) + "\n",
                encoding="utf-8",
            )
            run = curate_source(root)
            out = Path(temporary) / "cleaned"

            mill_summary = run["summary"]["mill_family"]
            self.assertFalse(mill_summary["context_complete"])
            self.assertFalse(mill_summary["quarantine_applied"])
            self.assertEqual(
                mill_summary["missing_home_factories"], [absent]
            )
            self.assertIn(
                record["id"],
                {
                    item["id"]
                    for records in run["records_by_rel"].values()
                    for item in records
                },
            )
            with self.assertRaisesRegex(ValueError, "multi-factory"):
                curate_agentic.write_cleaned_tree(run, out)
            self.assertFalse(out.exists())

    def test_partial_context_reports_foreign_payload_without_quarantine(self):
        with tempfile.TemporaryDirectory() as temporary:
            factory = Path(temporary) / "cache-stampede-factory"
            factory.mkdir()
            record = mill_episode(
                "foreign-payload",
                "fix verify",
                "graphql-nplusone-factory",
            )
            (factory / "batch-r01.jsonl").write_text(
                json.dumps(record) + "\n", encoding="utf-8"
            )

            run = curate_source(factory)

        mill_summary = run["summary"]["mill_family"]
        self.assertFalse(mill_summary["context_complete"])
        self.assertFalse(mill_summary["quarantine_applied"])
        self.assertEqual(mill_summary["records"], 1)
        self.assertEqual(
            mill_summary["reason_codes"],
            {REASON_FOREIGN_PAYLOAD_FACTORY: 1},
        )
        self.assertEqual(mill_summary["record_ids"], [record["id"]])
        self.assertEqual(
            run["summary"]["quarantined_foreign_mill_records"], 0
        )
        self.assertEqual(run["summary"]["output_records"], 1)
        self.assertEqual(run["decisions"][0]["action"], ACTION_RETAINED)
        self.assertNotIn("mill_family", run["decisions"][0])

    def test_registry_only_factory_root_is_verified_not_payload_redefined(self):
        """A factory registered in FACTORY-REGISTRY.json with no round quota
        (an identity-only generator, e.g. gpt-5.6-sol-coding-factory) must be
        verified the same way a quota-bearing factory root is. Verification
        was previously keyed on FACTORY_QUOTAS alone, so a directory named
        after such a factory was treated as unverified and its destination
        could be silently redefined by a foreign payload declaration instead
        of being flagged. Mirrors
        test_partial_context_reports_foreign_payload_without_quarantine but
        for a registry-only root."""
        with tempfile.TemporaryDirectory() as temporary:
            factory = Path(temporary) / "gpt-5.6-sol-coding-factory"
            factory.mkdir()
            record = mill_episode(
                "foreign-payload",
                "fix verify",
                "cache-stampede-factory",
            )
            (factory / "batch-r01.jsonl").write_text(
                json.dumps(record) + "\n", encoding="utf-8"
            )

            run = curate_source(factory)

        mill_summary = run["summary"]["mill_family"]
        self.assertFalse(mill_summary["context_complete"])
        self.assertFalse(mill_summary["quarantine_applied"])
        self.assertEqual(mill_summary["records"], 1)
        self.assertEqual(
            mill_summary["reason_codes"],
            {REASON_FOREIGN_PAYLOAD_FACTORY: 1},
        )
        self.assertEqual(mill_summary["record_ids"], [record["id"]])
        self.assertEqual(
            run["summary"]["quarantined_foreign_mill_records"], 0
        )
        self.assertEqual(run["summary"]["output_records"], 1)
        self.assertEqual(run["decisions"][0]["action"], ACTION_RETAINED)
        self.assertNotIn("mill_family", run["decisions"][0])

    def _assert_xyz_prefix_stays_unresolved(self, second_placement):
        """The 'xyz' prefix names no home factory, so the run refuses output."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run"
            _write_prefix_probe(
                root,
                (
                    ("cache-stampede-factory", "xyz-r1405-cache-copy"),
                    second_placement,
                ),
            )
            run = curate_source(root)
            out = Path(temporary) / "cleaned"

            mill_summary = run["summary"]["mill_family"]
            self.assertFalse(mill_summary["context_complete"])
            self.assertEqual(mill_summary["unresolved_prefixes"], ["xyz"])
            self.assertFalse(mill_summary["quarantine_applied"])
            with self.assertRaisesRegex(ValueError, "multi-factory"):
                curate_agentic.write_cleaned_tree(run, out)
            self.assertFalse(out.exists())

    def test_partial_context_with_ambiguous_prefix_refuses_output(self):
        self._assert_xyz_prefix_stays_unresolved(
            ("k8s-crashloop-factory", "xyz-r1406-k8s-copy")
        )

    def test_partial_context_with_unique_unknown_prefix_refuses_output(self):
        self._assert_xyz_prefix_stays_unresolved(
            ("k8s-crashloop-factory", "kcl-r1406-k8s-native")
        )

    def test_partial_context_with_native_terms_and_unknown_goal_refuses_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run"
            cache = root / "cache-stampede-factory"
            cache.mkdir(parents=True)
            strays = [
                mill_episode(
                    "cst-r99-unregistered-expiry-family",
                    "TTL expiry QuuxAlpha quuxBeta quuxGamma",
                    "cache-stampede-factory",
                )
            ]
            (cache / "batch-r01.jsonl").write_text(
                "".join(
                    json.dumps(record) + "\n"
                    for record in (*STAMPEDE_CONTROLS, *strays)
                ),
                encoding="utf-8",
            )
            k8s = root / "k8s-crashloop-factory"
            k8s.mkdir()
            (k8s / "batch-r01.jsonl").write_text(
                "".join(
                    json.dumps(
                        mill_episode(
                            f"kcl-r0{index}-probe",
                            "CrashLoopBackOff liveness probe container restart",
                            "k8s-crashloop-factory",
                        )
                    )
                    + "\n"
                    for index in (1, 2)
                ),
                encoding="utf-8",
            )
            run = curate_source(root)
            out = Path(temporary) / "cleaned"

            self.assertFalse(
                run["summary"]["mill_family"]["context_complete"]
            )
            self.assertEqual(
                run["summary"]["mill_family"]["unresolved_goal_records"],
                sorted(record["id"] for record in strays),
            )
            self.assertFalse(
                run["summary"]["mill_family"]["quarantine_applied"]
            )
            with self.assertRaisesRegex(ValueError, "multi-factory"):
                curate_agentic.write_cleaned_tree(run, out)
            self.assertFalse(out.exists())

    def test_skipped_records_do_not_teach_factory_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run"
            root.mkdir()
            write_mill_run(root, [STAMPEDE_CONTROLS[0]])
            cache_batch = root / "cache-stampede-factory" / "batch-r01.jsonl"
            skipped = []
            for index in range(2):
                record = thalamic_fixture()
                record["id"] = f"legacy-{index}"
                record["meta"] = {"factory": "docker-build-cache-factory"}
                skipped.append(record)
            with cache_batch.open("a", encoding="utf-8") as handle:
                for record in skipped:
                    handle.write(json.dumps(record) + "\n")
            run = curate_source(root)

        control_id = STAMPEDE_CONTROLS[0]["id"]
        control_decision = next(
            item
            for item in run["decisions"]
            if item["output_id"] == control_id
        )
        self.assertNotIn(
            REASON_FOREIGN_PAYLOAD_FACTORY,
            control_decision["reason_codes"],
        )
        self.assertEqual(run["summary"]["skipped_records"], 2)
        self.assertIn(
            control_id,
            {
                record["id"]
                for records in run["records_by_rel"].values()
                for record in records
            },
        )


if __name__ == "__main__":
    unittest.main()
