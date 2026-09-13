#!/usr/bin/env python3
"""Issue #43 census coverage for quarantined foreign-mill records."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
from test_census import _episode, _invoke  # noqa: E402


def _commit_marker_batch(factory: Path, batch: Path):
    """Put ``batch`` behind a valid marker-mode completion point."""

    (factory / ".round-marker-mode.json").write_text(
        '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n',
        encoding="utf-8",
    )
    notes = factory / "NOTES-r01.md"
    notes.write_text("Novel coverage: fixture\n", encoding="utf-8")
    (factory / "ROUND-r01.complete.json").write_text(
        json.dumps(
            {
                "version": 1,
                "factory": factory.name,
                "round": 1,
                "records": 1,
                "expected_records": 1,
                "commit_point": "ROUND-r01.complete.json",
                "files": [
                    {
                        "name": batch.name,
                        "sha256": hashlib.sha256(batch.read_bytes()).hexdigest(),
                    },
                    {
                        "name": notes.name,
                        "sha256": hashlib.sha256(notes.read_bytes()).hexdigest(),
                    },
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
        self.assertEqual(report["eligible_records"], 4)
        self.assertEqual(
            report["eligible_by_factory"],
            {
                "cache-stampede-factory": 2,
                "graphql-nplusone-factory": 2,
            },
        )
        self.assertEqual(
            mix["quarantined_records"][0]["source"],
            "cache-stampede-factory/batch-r01.jsonl",
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
        self.assertEqual(
            report["eligible_by_factory"],
            {
                "cache-stampede-factory": 2,
                "graphql-nplusone-factory": 2,
            },
        )

    def test_suffixed_snapshot_root_does_not_collapse_factory_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "pre-window-factory"
            write_specs = (
                (
                    "cache-stampede-factory",
                    _episode(
                        "cst-r01-cache-refill",
                        "refill the cache with singleflight",
                        "cache-stampede-factory",
                    ),
                ),
                (
                    "graphql-nplusone-factory",
                    _episode(
                        "gql-r01-batch-resolver",
                        "batch the GraphQL resolver",
                        "graphql-nplusone-factory",
                    ),
                ),
            )
            for factory, record in write_specs:
                path = root / factory / "batch-r01.jsonl"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            result = _invoke(str(root))

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(
            report["by_factory"],
            {
                "cache-stampede-factory": 1,
                "graphql-nplusone-factory": 1,
            },
        )
        self.assertNotIn("pre-window-factory", report["by_factory"])

    def test_off_registry_factory_root_keeps_nested_legacy_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "custom-experiment-factory"
            path = root / "archive" / "batch-r01.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps(
                    _episode(
                        "cex-r01-legacy",
                        "preserve the custom experiment identity",
                        root.name,
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            result = _invoke(str(root))

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["by_factory"], {"custom-experiment-factory": 1})
        self.assertNotIn("archive", report["by_factory"])
        self.assertEqual(report["mill_mix"]["records"], 0)

    def test_marker_mode_hides_uncommitted_batch_from_denominators(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run"
            factory = root / "agentic-factory"
            factory.mkdir(parents=True)
            committed = factory / "batch-r01.jsonl"
            committed.write_text(
                json.dumps(
                    _episode(
                        "agt-r01-committed",
                        "keep the committed record visible",
                        factory.name,
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            _commit_marker_batch(factory, committed)
            (factory / "batch-r02.jsonl").write_text(
                json.dumps(
                    _episode(
                        "agt-r02-uncommitted",
                        "hide the interrupted publish",
                        factory.name,
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            (factory / "ROUND-r02.publishing.json").write_text(
                "{}\n", encoding="utf-8"
            )
            result = _invoke(str(root))
            direct_result = _invoke(str(factory))

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["files"], 1)
        self.assertEqual(report["records"], 1)
        self.assertEqual(report["eligible_records"], 1)
        self.assertEqual(report["by_factory"], {"agentic-factory": 1})
        self.assertEqual(direct_result.returncode, 0, direct_result.stderr)
        direct_report = json.loads(direct_result.stdout)
        self.assertEqual(direct_report["files"], 1)
        self.assertEqual(direct_report["records"], 1)
        self.assertEqual(direct_report["mill_mix"]["records"], 0)

    def test_issue_43_factory_mix_is_named_and_subtracted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run"
            destination = root / "email-webhook-retry-factory"
            destination.mkdir(parents=True)
            (destination / "batch-r56.jsonl").write_text(
                "".join(
                    json.dumps(record) + "\n"
                    for record in (
                        _episode(
                            "sir-r56-meili-swap-leftover3c-rebuild",
                            "rebuild the search index",
                            "search-index-rebuild-factory",
                        ),
                        _episode(
                            "ewh-r56-webhook-leftover-pk-retry",
                            "retry the webhook",
                            "email-webhook-retry-factory",
                        ),
                    )
                ),
                encoding="utf-8",
            )
            result = _invoke(str(root))

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["records"], 2)
        self.assertEqual(report["eligible_records"], 1)
        self.assertEqual(
            report["eligible_by_factory"], {"email-webhook-retry-factory": 1}
        )
        mix = report["mill_mix"]
        self.assertEqual(mix["records"], 1)
        self.assertEqual(
            mix["reason_codes"],
            {
                "FOREIGN_MILL_ID_PREFIX": 1,
                "FOREIGN_PAYLOAD_FACTORY": 1,
            },
        )
        self.assertEqual(
            [row["record_id"] for row in mix["quarantined_records"]],
            ["sir-r56-meili-swap-leftover3c-rebuild"],
        )

    def test_invalid_utf8_file_is_reported_and_excluded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run"
            destination = root / "email-webhook-retry-factory"
            destination.mkdir(parents=True)
            (destination / "bad.jsonl").write_bytes(
                b'{"id":"bad","goal":"\xff","steps":[]}\n'
            )
            result = _invoke(str(root))

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["records"], 0)
        self.assertEqual(report["eligible_records"], 0)
        self.assertEqual(report["decode_failures"], 1)
        self.assertEqual(
            [row["source"] for row in report["unreadable_files"]],
            ["email-webhook-retry-factory/bad.jsonl"],
        )

    def test_non_standard_json_constant_is_a_parse_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run"
            destination = root / "email-webhook-retry-factory"
            destination.mkdir(parents=True)
            (destination / "bad.jsonl").write_text(
                '{"id":"bad","goal":"x","steps":[],"reward":{"x":NaN}}\n',
                encoding="utf-8",
            )
            result = _invoke(str(root))

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["records"], 0)
        self.assertEqual(report["eligible_records"], 0)
        self.assertEqual(report["parse_failures"], 1)

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
