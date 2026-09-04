#!/usr/bin/env python3
"""Training-audit coverage for foreign-mill quarantine denominators."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from training_audit_test_helpers import REPO, thalamic, write  # noqa: E402

import training_audit  # noqa: E402
import training_audit_mill  # noqa: E402
from exact_json import MAX_JSON_NESTING_DEPTH  # noqa: E402


class LeftoverMillDenominator(unittest.TestCase):
    """Issue #43: mill leftovers leave the destination's eligible denominator."""

    @staticmethod
    def _episode(record_id, factory):
        return {
            "id": record_id,
            "goal": "rebuild the search index",
            "steps": [
                {
                    "decision_basis": "fixture observation",
                    "tool_call": {"name": "inspect", "args": {}},
                    "observation": "fixture result",
                }
            ],
            "outcome": "fixture complete",
            "reward": {"success": True},
            "meta": {"factory": factory, "round": 1, "tags": ["audit", "fixture"]},
        }

    def test_factory_mix_is_quarantined_but_never_a_training_blocker(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            foreign = self._episode(
                "evh-r21-cite-orphan-c3e8",
                "eval-harness-trajectory-factory",
            )
            # This would be a readiness blocker if quarantine fell through to
            # check_record or the episode metrics.
            foreign["steps"][0].pop("decision_basis")
            write(
                root / "rag-retrieval-debug-factory" / "batch-r21.jsonl",
                [
                    foreign,
                    self._episode("rag-r21-chunk-leftover-cite", "rag-retrieval-debug-factory"),
                ],
            )
            report = training_audit.audit_run(root)

        self.assertEqual(report["totals"]["records"], 2)
        self.assertEqual(report["totals"]["eligible_records"], 1)
        self.assertEqual(
            report["factories"]["rag-retrieval-debug-factory"]["eligible_records"], 1
        )
        mill = report["mill_mix"]
        self.assertEqual(mill["records"], 1)
        self.assertEqual(
            mill["reason_codes"],
            {
                "FOREIGN_MILL_ID_PREFIX": 1,
                "FOREIGN_PAYLOAD_FACTORY": 1,
            },
        )
        self.assertEqual(
            [row["record_id"] for row in mill["quarantined_records"]],
            ["evh-r21-cite-orphan-c3e8"],
        )
        self.assertEqual(report["record_invariants"]["errors"], 0)
        self.assertEqual(report["episodes"]["episodes"], 1)
        self.assertEqual(report["episodes"]["missing_decision_basis_steps"], 0)
        self.assertEqual(report["identity"]["coverage_pct"], 100.0)

    def test_quarantined_record_is_excluded_from_token_metrics(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            foreign = self._episode(
                "evh-r21-cite-orphan-c3e8",
                "eval-harness-trajectory-factory",
            )
            foreign["steps"][0]["observation"] = "foreign payload " * 1_000
            eligible = self._episode(
                "rag-r21-chunk-leftover-cite",
                "rag-retrieval-debug-factory",
            )
            write(
                root / "rag-retrieval-debug-factory" / "batch-r21.jsonl",
                [foreign, eligible],
            )
            report = training_audit.audit_run(root)

        expected = max(1, (len(json.dumps(eligible).encode("utf-8")) + 3) // 4)
        bucket = report["factories"]["rag-retrieval-debug-factory"]
        self.assertEqual(report["totals"]["approx_tokens"], expected)
        self.assertEqual(bucket["approx_tokens"], expected)
        self.assertEqual(
            bucket["length_tokens"],
            {"median": float(expected), "p95": expected, "max": expected},
        )

    def test_quarantined_record_skips_exact_json_training_invariants(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            foreign = self._episode(
                "evh-r21-cite-orphan-c3e8",
                "eval-harness-trajectory-factory",
            )
            foreign["extension"] = "DEPTH_SENTINEL"
            eligible = self._episode(
                "rag-r21-chunk-leftover-cite",
                "rag-retrieval-debug-factory",
            )
            foreign_payload = json.dumps(foreign).replace(
                '"DEPTH_SENTINEL"',
                "[" * (MAX_JSON_NESTING_DEPTH + 1)
                + "0"
                + "]" * (MAX_JSON_NESTING_DEPTH + 1),
                1,
            )
            path = root / "rag-retrieval-debug-factory" / "batch-r21.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(
                foreign_payload + "\n" + json.dumps(eligible) + "\n",
                encoding="utf-8",
            )

            report = training_audit.audit_run(root)

        self.assertEqual(report["mill_mix"]["records"], 1)
        self.assertEqual(report["totals"]["eligible_records"], 1)
        self.assertEqual(report["totals"]["exact_json_contract_errors"], 0)
        self.assertEqual(report["record_invariants"]["errors"], 0)
        self.assertTrue(report["training_ready"], report["blockers"])

    def test_all_foreign_registered_destination_keeps_verified_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(
                root / "email-webhook-retry-factory" / "batch-r56.jsonl",
                [
                    self._episode(
                        "sir-r56-meili-swap-leftover3c-rebuild",
                        "search-index-rebuild-factory",
                    )
                ],
            )
            report = training_audit.audit_run(root)
            strict = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "pipelines" / "training_audit.py"),
                    "--strict",
                    str(root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(report["totals"]["records"], 1)
        self.assertEqual(report["totals"]["eligible_records"], 0)
        self.assertEqual(report["mill_mix"]["records"], 1)
        self.assertFalse(report["training_ready"])
        self.assertIn(
            "0 eligible training records remain after foreign-mill quarantine",
            report["blockers"],
        )
        self.assertEqual(strict.returncode, 1, strict.stdout)
        self.assertEqual(
            report["mill_mix"]["reason_codes"],
            {
                "FOREIGN_MILL_ID_PREFIX": 1,
                "FOREIGN_PAYLOAD_FACTORY": 1,
            },
        )

    def test_invalid_utf8_line_does_not_hide_a_foreign_sibling(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "email-webhook-retry-factory" / "batch-r56.jsonl"
            path.parent.mkdir(parents=True)
            foreign = json.dumps(
                self._episode(
                    "sir-r56-meili-swap-leftover3c-rebuild",
                    "search-index-rebuild-factory",
                )
            ).encode("utf-8")
            path.write_bytes(b'{"id":"bad-\xff"}\n' + foreign + b"\n")
            report = training_audit.audit_run(root)

        self.assertEqual(report["totals"]["records"], 1)
        self.assertEqual(report["totals"]["eligible_records"], 0)
        self.assertEqual(report["mill_mix"]["records"], 1)
        self.assertEqual(
            report["mill_mix"]["quarantined_records"][0]["line"],
            2,
        )
        self.assertFalse(report["training_ready"])

    def test_snapshot_index_preserves_physical_line_coordinates(self):
        """Malformed rows are skipped without renumbering later mill findings."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            relative = Path("email-webhook-retry-factory/batch-r56.jsonl")
            foreign = self._episode(
                "sir-r56-meili-swap-leftover3c-rebuild",
                "search-index-rebuild-factory",
            )
            payload = b'{"id":"bad-\xff"}\n\n' + json.dumps(foreign).encode() + b"\n"

            findings = training_audit_mill._index_findings(
                root,
                [(relative, payload)],
            )

        self.assertTrue(findings)
        self.assertEqual({finding.ref for finding in findings}, {(relative.as_posix(), 3)})

    def test_clean_corpus_reports_a_full_eligible_denominator(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(
                root / "thalamic-trajectory-factory" / "batch-r01.jsonl",
                [thalamic("clean-1")],
            )
            report = training_audit.audit_run(root)

        self.assertEqual(report["totals"]["eligible_records"], 1)
        self.assertEqual(report["mill_mix"]["records"], 0)
        self.assertEqual(report["mill_mix"]["quarantined_records"], [])
        markdown = training_audit.render_markdown(report)
        self.assertIn("Eligible after foreign-mill quarantine", markdown)
