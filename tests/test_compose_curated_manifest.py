#!/usr/bin/env python3
"""The compose manifest and reward-sidecar evidence for one composed run."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
for _path in (TESTS, REPO / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated  # noqa: E402
from compose_curated_test_support import (  # noqa: E402
    build_source_run,
    read_jsonl,
)


class ComposeManifestEvidence(unittest.TestCase):
    """Split from test_compose_curated.py: per-record manifest evidence."""

    def _compose_manifest_fixture(self, root):
        """Compose the shared build_source_run fixture and return its manifest parts.

        Split out of one combined test so each concern below (counts, digest,
        per-entry structure, retained-entry output linkage, exclusion reason)
        fails independently instead of stopping at the first broken assertion
        in one long method.
        """
        source = build_source_run(root / "run")
        summary = compose_curated.compose_run(source, root / "curated")
        manifest_path = root / "curated" / summary["manifest"]["path"]
        entries = read_jsonl(manifest_path)
        sidecars = read_jsonl(root / "curated" / summary["reward_sidecars"]["path"])
        return summary, manifest_path, entries, sidecars

    def test_manifest_entry_and_sidecar_counts_match_the_summary(self):
        with tempfile.TemporaryDirectory() as td:
            summary, manifest_path, entries, sidecars = self._compose_manifest_fixture(
                Path(td)
            )

            self.assertEqual(len(entries), summary["manifest"]["entries"])
            self.assertEqual(len(entries), summary["counts"]["source_records"])
            self.assertEqual(
                summary["manifest"]["sha256"],
                hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(len(sidecars), summary["counts"]["reward_sidecars"])

            retained = [item for item in entries if item["action"] == "retained"]
            excluded = [item for item in entries if item["action"] == "excluded"]
            self.assertEqual(len(retained), summary["counts"]["retained"])
            self.assertEqual(len(excluded), summary["counts"]["excluded"])

    def test_manifest_entries_carry_compose_version_hashes_and_lane_order(self):
        with tempfile.TemporaryDirectory() as td:
            _summary, _manifest_path, entries, _sidecars = self._compose_manifest_fixture(
                Path(td)
            )

            for entry in entries:
                self.assertEqual(entry["compose_version"], compose_curated.COMPOSE_VERSION)
                self.assertRegex(entry["source_sha256"], r"^[0-9a-f]{64}$")
                self.assertRegex(entry["source_file_sha256"], r"^[0-9a-f]{64}$")
                lanes = [stage["lane"] for stage in entry["stages"]]
                self.assertEqual(lanes, list(compose_curated.LANE_ORDER)[: len(lanes)])
                for stage in entry["stages"]:
                    self.assertTrue(stage["transform_version"])
                    self.assertTrue(stage["transform_name"])

    def test_retained_manifest_entries_point_at_their_emitted_line_and_sidecar(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _summary, _manifest_path, entries, sidecars = self._compose_manifest_fixture(
                root
            )
            sidecar_ids = {item["sidecar_id"] for item in sidecars}
            retained = [item for item in entries if item["action"] == "retained"]

            for entry in retained:
                emitted = (root / "curated" / entry["output_path"]).read_text(
                    encoding="utf-8"
                ).splitlines()[entry["output_line"] - 1]
                self.assertEqual(
                    entry["output_sha256"],
                    hashlib.sha256(emitted.encode("utf-8")).hexdigest(),
                )
                self.assertEqual(json.loads(emitted)["id"], entry["output_id"])
                if "reward_sidecar_id" in entry:
                    self.assertIn(entry["reward_sidecar_id"], sidecar_ids)

    def test_excluded_manifest_entry_keeps_its_reason_code_and_no_output(self):
        with tempfile.TemporaryDirectory() as td:
            _summary, _manifest_path, entries, _sidecars = self._compose_manifest_fixture(
                Path(td)
            )
            excluded = [item for item in entries if item["action"] == "excluded"]

            # The exclusion keeps its machine-readable reason and no output.
            self.assertEqual(len(excluded), 1)
            self.assertIsNone(excluded[0]["output_path"])
            self.assertIn(
                "PROPOSED_ACTION_CONTEXT_DIVERGES", excluded[0]["reason_codes"]
            )


if __name__ == "__main__":
    unittest.main()
