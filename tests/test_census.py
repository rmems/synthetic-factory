#!/usr/bin/env python3
"""census.py prints a read-only JSON census of a run directory."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CENSUS = REPO / "pipelines" / "census.py"
MINI_RUN = REPO / "tests" / "fixtures" / "mini-run"

EXPECTED = {
    "files": 2,
    "records": 3,
    "parse_failures": 1,
    "by_kind": {
        "thalamic": 2,
        "preference": 1,
        "bridge_pair": 0,
        "multi_agent": 0,
        "safety_case": 0,
        "episode": 0,
        # The oracle-grounded parity families are absent from this fixture but
        # still reported, so a run that contains none is distinguishable from a
        # census that cannot see them.
        "hardware_parity": 0,
        "nir_equivalence": 0,
        "unknown": 0,
    },
    "sim_or_real": {
        "real": 1,
        "real*": 1,
        "sim*": 1,
        "hil*": 0,
        "other": 0,
        "<missing>": 0,
    },
    "by_factory": {
        "failure-as-fuel-preference-cascade": 1,
        "thalamic-trajectory-factory": 2,
    },
    "decode_failures": 0,
    "unreadable_files": [],
    "eligible_records": 3,
    "eligible_by_factory": {
        "failure-as-fuel-preference-cascade": 1,
        "thalamic-trajectory-factory": 2,
    },
    "mill_mix": {
        "records": 0,
        "reason_codes": {},
        "by_factory": {},
        "record_ids": [],
        "record_ids_truncated": False,
        "quarantined_records": [],
    },
}


def _episode(record_id, goal, factory):
    """A generic episode slug with no destination-family field."""
    return {
        "id": record_id,
        "goal": goal,
        "steps": [
            {
                "n": 1,
                "decision_basis": "Observation: reproduced",
                "tool_call": {"name": "bash", "args": {"command": "run"}},
                "observation": "ok",
            }
        ],
        "outcome": "resolved",
        "reward": {"success": True},
        "meta": {"factory": factory, "round": 1, "generator": "grok-4.6"},
    }


def _snapshot(root: Path):
    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            st = path.stat()
            out[str(path.relative_to(root))] = (st.st_mtime_ns, st.st_size)
    return out


def _invoke(*args):
    return subprocess.run(
        [sys.executable, str(CENSUS), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class CensusMiniRun(unittest.TestCase):
    def test_fixture_counts_and_histogram(self):
        result = _invoke(str(MINI_RUN))
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        for key, value in EXPECTED.items():
            self.assertEqual(report[key], value, key)
        self.assertEqual(Path(report["run_dir"]).resolve(), MINI_RUN.resolve())

    def test_does_not_write_into_run_dir(self):
        before = _snapshot(MINI_RUN)
        result = _invoke(str(MINI_RUN))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_snapshot(MINI_RUN), before)
        self.assertFalse((MINI_RUN / "manifest.json").exists())


def _write_marker_mode(factory: Path):
    """Put ``factory`` into round-marker mode."""

    (factory / ".round-marker-mode.json").write_text(
        '{"version":1,"legacy_baseline":0,'
        '"commit_point":"ROUND-rNN.complete.json"}\n',
        encoding="utf-8",
    )


def _write_episode_batch(path: Path, record_id: str, factory_name: str):
    """Write a one-record episode batch at ``path``."""

    path.write_text(
        json.dumps(_episode(record_id, "fix verify", factory_name)) + "\n",
        encoding="utf-8",
    )


def _write_round_complete(factory: Path, round_number: int, files):
    """Write the completion marker that commits ``files`` for one round."""

    commit_point = f"ROUND-r{round_number:02d}.complete.json"
    (factory / commit_point).write_text(
        json.dumps(
            {
                "version": 1,
                "factory": factory.name,
                "round": round_number,
                "records": 1,
                "expected_records": 1,
                "commit_point": commit_point,
                "files": [
                    {
                        "name": path.name,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                    for path in files
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )


class CensusMillMix(unittest.TestCase):
    """A dest-stamped leftover mill on a generic episode slug must be counted."""

    def _run_tree(self, root):
        stampede = root / "cache-stampede-factory"
        stampede.mkdir()
        (stampede / "batch-r01.jsonl").write_text(
            "".join(
                json.dumps(record) + "\n"
                for record in (
                    _episode(
                        "cst-r01-ttl-expiry-thundering-herd",
                        "Resolve TTL expiry thundering herd: add singleflight "
                        "so one origin request refills the cache.",
                        "cache-stampede-factory",
                    ),
                    _episode(
                        "cst-r02-singleflight-lock",
                        "Resolve stampede: the singleflight lock times out and "
                        "every request refills the origin cache.",
                        "cache-stampede-factory",
                    ),
                    # Dest-stamped, no 'leftover' in the id, no dest-family key.
                    _episode(
                        "gql-r1405-postgraphile-wrap-resolver-after-plugin-order",
                        "Fix PostGraphile makeWrapResolvers leftover after "
                        "plugin order swap: leftover wrapMass after bind to "
                        "wrapPull. Do not drop wrap resolvers.",
                        "cache-stampede-factory",
                    ),
                )
            ),
            encoding="utf-8",
        )
        graphql = root / "graphql-nplusone-factory"
        graphql.mkdir()
        (graphql / "batch-r01.jsonl").write_text(
            "".join(
                json.dumps(record) + "\n"
                for record in (
                    _episode(
                        "gql-r1400-postgraphile-wrap-resolver",
                        "Fix PostGraphile makeWrapResolvers leftover after "
                        "plugin order swap: leftover wrapMass after bind to "
                        "wrapPull.",
                        "graphql-nplusone-factory",
                    ),
                    _episode(
                        "gql-r1401-postgraphile-plugin-order",
                        "Fix PostGraphile makeWrapResolvers leftover on unions: "
                        "leftover wrapMass after bind to wrapPull.",
                        "graphql-nplusone-factory",
                    ),
                )
            ),
            encoding="utf-8",
        )

    def test_dest_stamped_mill_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run"
            root.mkdir()
            self._run_tree(root)
            result = _invoke(str(root))
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["by_kind"]["episode"], 5)
        mix = report["mill_mix"]
        self.assertEqual(mix["records"], 1)
        self.assertEqual(
            mix["record_ids"],
            ["gql-r1405-postgraphile-wrap-resolver-after-plugin-order"],
        )
        self.assertEqual(
            mix["by_factory"],
            {
                "cache-stampede-factory": {
                    "records": 1,
                    "foreign_prefixes": {"gql": 1},
                }
            },
        )
        self.assertEqual(
            mix["reason_codes"].get("FOREIGN_MILL_ID_PREFIX"), 1
        )
        # The mix is invisible to a factory-mix check: it is dest-stamped.
        self.assertNotIn("FOREIGN_PAYLOAD_FACTORY", mix["reason_codes"])

    def test_registry_only_factory_root_is_verified_not_payload_redefined(self):
        """Codex #96 P2: verify census roots from the reviewed registry.

        ``config/FACTORY-REGISTRY.json`` registers two identity-only
        generators (``gpt-5.6-sol-coding-factory``,
        ``muse-spark-1.2-coding-factory``) that carry no round quota. Keying
        verification on ``FACTORY_QUOTAS`` left a directory named after either
        one unverified, and an unverified root falls back to trusting the
        payload's own declaration -- so an all-foreign batch redefined the
        destination and ``mill_mix`` reported nothing. Mirrors the
        ``curate_agentic`` fix in 71c5401 for this report-only audit.
        """

        for root_name in (
            "gpt-5.6-sol-coding-factory",
            "muse-spark-1.2-coding-factory",
        ):
            with self.subTest(factory=root_name), tempfile.TemporaryDirectory() as td:
                root = Path(td) / "run"
                factory = root / root_name
                factory.mkdir(parents=True)
                (factory / "batch-r01.jsonl").write_text(
                    json.dumps(
                        _episode(
                            "gql-r1405-postgraphile-wrap-resolver",
                            "Fix PostGraphile makeWrapResolvers leftover after "
                            "plugin order swap: leftover wrapMass after bind to "
                            "wrapPull.",
                            "graphql-nplusone-factory",
                        )
                    )
                    + "\n",
                    encoding="utf-8",
                )
                result = _invoke(str(root))

                self.assertEqual(result.returncode, 0, result.stderr)
                mix = json.loads(result.stdout)["mill_mix"]
                self.assertEqual(mix["records"], 1)
                self.assertEqual(
                    mix["by_factory"],
                    {root_name: {"records": 1, "foreign_prefixes": {"gql": 1}}},
                )
                self.assertEqual(
                    mix["reason_codes"].get("FOREIGN_PAYLOAD_FACTORY"), 1
                )

    def test_nested_batches_keep_their_enclosing_factory_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run"
            root.mkdir()
            self._run_tree(root)
            for factory in (
                "cache-stampede-factory",
                "graphql-nplusone-factory",
            ):
                directory = root / factory
                archive = directory / "archive"
                archive.mkdir()
                (directory / "batch-r01.jsonl").rename(
                    archive / "batch-r01.jsonl"
                )
            result = _invoke(str(root))

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(
            report["by_factory"],
            {
                "cache-stampede-factory": 3,
                "graphql-nplusone-factory": 2,
            },
        )
        self.assertNotIn("archive", report["by_factory"])
        self.assertEqual(report["mill_mix"]["records"], 1)

    def test_suffixed_outer_snapshot_keeps_child_factory_identities(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "pre-window-factory"
            root.mkdir()
            self._run_tree(root)
            result = _invoke(str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

        self.assertEqual(
            report["by_factory"],
            {
                "cache-stampede-factory": 3,
                "graphql-nplusone-factory": 2,
            },
        )
        self.assertNotIn("pre-window-factory", report["by_factory"])
        self.assertEqual(report["mill_mix"]["records"], 1)

    def test_direct_off_registry_factory_keeps_nested_storage_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "custom-experiment-factory"
            archive = root / "archive"
            archive.mkdir(parents=True)
            (archive / "batch-r01.jsonl").write_text(
                json.dumps(
                    _episode(
                        "cef-r01-control",
                        "fix verify",
                        "custom-experiment-factory",
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            result = _invoke(str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

        self.assertEqual(report["by_factory"], {"custom-experiment-factory": 1})
        self.assertEqual(report["mill_mix"]["records"], 0)

    def test_suffix_only_snapshot_root_infers_payload_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "staging-copy-factory"
            root.mkdir()
            (root / "batch-r01.jsonl").write_text(
                "".join(
                    json.dumps(record) + "\n"
                    for record in (
                        _episode(
                            "cst-r01-cache-control",
                            "Resolve cache thundering herd with singleflight",
                            "cache-stampede-factory",
                        ),
                        _episode(
                            "cst-r02-cache-control",
                            "Resolve cache thundering herd with singleflight",
                            "cache-stampede-factory",
                        ),
                    )
                ),
                encoding="utf-8",
            )
            result = _invoke(str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

        self.assertEqual(report["by_factory"], {"staging-copy-factory": 2})
        self.assertEqual(report["mill_mix"]["records"], 0)

    def test_all_foreign_known_destination_uses_directory_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "email-webhook-retry-factory"
            root.mkdir()
            (root / "batch-r01.jsonl").write_text(
                json.dumps(
                    _episode(
                        "sir-r56-meili-swap",
                        "fix verify",
                        "search-index-rebuild-factory",
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            result = _invoke(str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

        self.assertEqual(report["mill_mix"]["records"], 1)
        self.assertEqual(
            report["mill_mix"]["reason_codes"]["FOREIGN_PAYLOAD_FACTORY"],
            1,
        )

    def test_marker_mode_excludes_uncommitted_batches(self):
        with tempfile.TemporaryDirectory() as temporary:
            factory = Path(temporary) / "agentic-factory"
            factory.mkdir()
            _write_marker_mode(factory)
            batch = factory / "batch-r01.jsonl"
            _write_episode_batch(batch, "agt-r01-committed", factory.name)
            notes = factory / "NOTES-r01.md"
            notes.write_text("Novel coverage: 80%\n", encoding="utf-8")
            _write_round_complete(factory, 1, (batch, notes))
            _write_episode_batch(
                factory / "batch-r02.jsonl",
                "gql-r02-uncommitted",
                factory.name,
            )
            (factory / "ROUND-r02.publishing.json").write_text(
                "{}\n", encoding="utf-8"
            )
            result = _invoke(str(factory))
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

        self.assertEqual(report["files"], 1)
        self.assertEqual(report["records"], 1)
        self.assertEqual(report["mill_mix"]["records"], 0)

    def test_cli_bounds_unsafe_marker_mode_transaction_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            factory = Path(temporary) / "agentic-factory"
            factory.mkdir()
            (factory / "batch-r01.jsonl").write_text(
                json.dumps(
                    _episode(
                        "agt-r01-unsafe-marker",
                        "fix verify",
                        factory.name,
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            (factory / ".round-marker-mode.json").mkdir()

            result = _invoke(str(factory))

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("census failed: unsafe marker mode file", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class CensusBuckets(unittest.TestCase):
    def setUp(self):
        pipeline_path = str(REPO / "pipelines")
        self._inserted_pipeline_path = pipeline_path not in sys.path
        if self._inserted_pipeline_path:
            sys.path.insert(0, pipeline_path)
        import census  # noqa: E402

        self.census = census

    def tearDown(self):
        if self._inserted_pipeline_path:
            sys.path.remove(str(REPO / "pipelines"))
        sys.modules.pop("census", None)

    def test_kind_routing(self):
        six = {
            "state": {},
            "proposed_action": {},
            "safety_decision": {},
            "executed_action": {},
            "future_outcome": {},
            "reward_components": {},
        }
        self.assertEqual(self.census.classify_kind(six), "thalamic")
        self.assertEqual(
            self.census.classify_kind({"chosen": {}, "rejected": {}}),
            "preference",
        )
        self.assertEqual(
            self.census.classify_kind({"language_view": {}, "spike_events": []}),
            "bridge_pair",
        )
        self.assertEqual(
            self.census.classify_kind({"agents": [], "transcript": []}),
            "multi_agent",
        )
        self.assertEqual(self.census.classify_kind({"case_type": "correct_refusal"}), "safety_case")
        self.assertEqual(
            self.census.classify_kind({"goal": "x", "steps": []}),
            "episode",
        )
        self.assertEqual(self.census.classify_kind({"meta": {}}), "unknown")

    def test_unhashable_declared_kind_is_unknown_instead_of_crashing(self):
        for malformed in ([], {}):
            with self.subTest(malformed=malformed):
                self.assertEqual(
                    self.census.classify_kind({"record_kind": malformed}),
                    "unknown",
                )

    def test_overlapping_keys_follow_census_agentic_order(self):
        six = {
            "state": {},
            "proposed_action": {},
            "safety_decision": {},
            "executed_action": {},
            "future_outcome": {},
            "reward_components": {},
        }
        self.assertEqual(
            self.census.classify_kind({**six, "goal": "x", "steps": []}),
            "thalamic",
        )
        self.assertEqual(
            self.census.classify_kind(
                {"case_type": "correct_refusal", "goal": "x", "steps": []}
            ),
            "safety_case",
        )
        self.assertEqual(
            self.census.classify_kind(
                {"transcript": [], "agents": [], "goal": "x", "steps": []}
            ),
            "multi_agent",
        )
        self.assertEqual(
            self.census.classify_kind({**six, "chosen": {}, "rejected": {}}),
            "thalamic",
        )
        self.assertEqual(
            self.census.classify_kind({"chosen": dict(six), "rejected": dict(six)}),
            "preference",
        )

    def test_sim_or_real_buckets(self):
        bucket = self.census.bucket_sim_or_real
        self.assertEqual(bucket("real"), "real")
        self.assertEqual(bucket("real (production, actions live)"), "real*")
        self.assertEqual(bucket("live allocation; arbiter writes schedules"), "real*")
        self.assertEqual(
            bucket("high-fidelity plant simulation calibrated on telemetry"),
            "sim*",
        )
        self.assertEqual(
            bucket("hardware-in-the-loop (flight SPAD array)"),
            "hil*",
        )
        self.assertEqual(bucket("hil-rig-3"), "hil*")
        self.assertEqual(
            bucket(
                "operations-grade simulation calibrated on HIL valve testbench"
            ),
            "sim*",
        )
        self.assertEqual(
            bucket(
                "decision-support in live IOC; the relay's disposition drives recovery"
            ),
            "other",
        )


if __name__ == "__main__":
    unittest.main()
