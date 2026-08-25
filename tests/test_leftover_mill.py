#!/usr/bin/env python3
"""Issue #43 ledger and shared-detector quarantine reporting."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import leftover_mill  # noqa: E402
from mill_family import (  # noqa: E402
    MillIndex,
    REASON_FOREIGN_PAYLOAD_FACTORY,
)

MILL = REPO / "pipelines" / "leftover_mill.py"
ISSUE_43_COUNTS = {
    "email-webhook-retry-factory": 6,
    "eval-harness-trajectory-factory": 5,
    "observability-debug-factory": 1,
    "rag-retrieval-debug-factory": 18,
}


def episode(record_id, factory, goal="rebuild the index"):
    return {
        "id": record_id,
        "goal": goal,
        "steps": [
            {
                "decision_basis": "fixture observation",
                "tool_call": {"name": "inspect", "args": {}},
                "observation": "fixture result",
            }
        ],
        "outcome": "fixture complete",
        "reward": {"success": True},
        "meta": {"factory": factory, "round": 1},
    }


def write(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


class FrozenLedger(unittest.TestCase):
    def test_ledger_covers_the_thirty_ids_in_four_dumps(self):
        self.assertEqual(
            {
                destination: len(records)
                for destination, records in leftover_mill.PUBLISHED_FACTORY_MIX.items()
            },
            ISSUE_43_COUNTS,
        )
        self.assertEqual(len(leftover_mill.expected_factory_mix_ids()), 30)

    def test_every_ledger_row_is_rederived_by_the_shared_detector(self):
        for destination, records in leftover_mill.PUBLISHED_FACTORY_MIX.items():
            index = MillIndex()
            index.add(
                destination,
                episode(
                    f"native-r1-{destination}",
                    destination,
                    "native destination task",
                ),
            )
            for record_id, declared_factory in records.items():
                index.add(
                    destination,
                    episode(record_id, declared_factory),
                    ref=record_id,
                )
            findings = {finding.ref: finding for finding in index.findings()}
            self.assertEqual(set(findings), set(records))
            for record_id, finding in findings.items():
                self.assertIn(
                    REASON_FOREIGN_PAYLOAD_FACTORY,
                    finding.reason_codes,
                    record_id,
                )

    def test_ledger_does_not_claim_sibling_issue_destinations(self):
        self.assertNotIn(
            "code-review-preference-factory",
            leftover_mill.PUBLISHED_FACTORY_MIX,
        )
        self.assertNotIn(
            "browser-tool-use-factory",
            leftover_mill.PUBLISHED_FACTORY_MIX,
        )
        self.assertNotIn(
            "cascading-error-recovery-factory",
            leftover_mill.PUBLISHED_FACTORY_MIX,
        )


class AuditRun(unittest.TestCase):
    def _tree(self, root):
        write(
            root / "email-webhook-retry-factory" / "batch-r56.jsonl",
            [
                episode(
                    "sir-r56-meili-swap-leftover3c-rebuild",
                    "search-index-rebuild-factory",
                ),
                episode(
                    "sir-r56-meili-drop-index-leftover3c-handoff",
                    "search-index-rebuild-factory",
                ),
                episode(
                    "ewh-r56-webhook-leftover-pk-retry",
                    "email-webhook-retry-factory",
                ),
            ],
        )

    def test_eligible_denominator_uses_shared_findings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._tree(root)
            report = leftover_mill.audit_run(root)

        self.assertEqual(report["records"], 3)
        self.assertEqual(report["quarantined"], 2)
        self.assertEqual(report["eligible_records"], 1)
        self.assertEqual(
            report["reason_codes"],
            {
                "FOREIGN_MILL_ID_PREFIX": 2,
                "FOREIGN_PAYLOAD_FACTORY": 2,
            },
        )
        self.assertEqual(
            report["by_factory"]["email-webhook-retry-factory"],
            {"records": 3, "eligible": 1, "quarantined": 2},
        )
        self.assertEqual(
            [row["record_id"] for row in report["quarantined_records"]],
            [
                "sir-r56-meili-swap-leftover3c-rebuild",
                "sir-r56-meili-drop-index-leftover3c-handoff",
            ],
        )

    def test_leftover_in_id_alone_stays_eligible(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(
                root / "email-webhook-retry-factory" / "batch-r56.jsonl",
                [
                    episode(
                        "ewh-r56-webhook-leftover-pk-retry",
                        "email-webhook-retry-factory",
                    )
                ],
            )
            report = leftover_mill.audit_run(root)

        self.assertEqual(report["quarantined"], 0)
        self.assertEqual(report["eligible_records"], 1)

    def test_does_not_write_into_the_run_dir(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._tree(root)
            before = {
                str(path.relative_to(root)): (
                    path.stat().st_mtime_ns,
                    path.stat().st_size,
                )
                for path in sorted(root.rglob("*"))
                if path.is_file()
            }
            leftover_mill.audit_run(root)
            after = {
                str(path.relative_to(root)): (
                    path.stat().st_mtime_ns,
                    path.stat().st_size,
                )
                for path in sorted(root.rglob("*"))
                if path.is_file()
            }

        self.assertEqual(after, before)


class Cli(unittest.TestCase):
    def _invoke(self, *args):
        return subprocess.run(
            [sys.executable, str(MILL), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_json_report_and_strict_exit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._tree(root)
            regular = self._invoke(str(root))
            strict = self._invoke("--strict", str(root))

        self.assertEqual(regular.returncode, 0, regular.stderr)
        self.assertEqual(json.loads(regular.stdout)["quarantined"], 1)
        self.assertEqual(strict.returncode, 1, strict.stdout)

    def _tree(self, root):
        write(
            root / "observability-debug-factory" / "batch-r500.jsonl",
            [
                episode(
                    "srl-r500-networkd-dhcp-ipv4-only-c67a",
                    "sparse-reward-long-task-factory",
                ),
                episode(
                    "obs-r500-native",
                    "observability-debug-factory",
                ),
            ],
        )

    def test_invalid_utf8_is_reported_not_replacement_decoded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "email-webhook-retry-factory" / "bad.jsonl"
            path.parent.mkdir(parents=True)
            valid = json.dumps(
                episode(
                    "ewh-r01-valid-after-bad",
                    "email-webhook-retry-factory",
                )
            ).encode("utf-8")
            path.write_bytes(
                b'{"id":"bad","goal":"\xff","steps":[]}\n' + valid + b"\n"
            )
            result = self._invoke("--strict", str(root))

        self.assertEqual(result.returncode, 1, result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["records"], 1)
        self.assertEqual(report["decode_failures"], 1)
        self.assertEqual(report["eligible_records"], 1)
        self.assertEqual(report["unreadable_files"][0]["line"], 1)

    def test_strict_rejects_non_standard_json_constants(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "email-webhook-retry-factory" / "bad.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(
                '{"id":"bad","goal":"x","steps":[],"reward":{"x":Infinity}}\n',
                encoding="utf-8",
            )
            result = self._invoke("--strict", str(root))

        self.assertEqual(result.returncode, 1, result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["records"], 0)
        self.assertEqual(report["parse_failures"], 1)
        self.assertEqual(report["eligible_records"], 0)

    def test_missing_directory_is_a_usage_error(self):
        result = self._invoke(str(REPO / "pipelines" / "not-a-directory"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a directory", result.stderr)

    def test_marker_error_is_a_bounded_cli_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            factory = Path(temporary) / "email-webhook-retry-factory"
            write(
                factory / "batch-r01.jsonl",
                [
                    episode(
                        "ewh-r01-native",
                        "email-webhook-retry-factory",
                    )
                ],
            )
            (factory / ".round-marker-mode.json").mkdir()
            result = self._invoke(str(factory))

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("leftover_mill failed: unsafe marker mode file", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
