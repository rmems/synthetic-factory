#!/usr/bin/env python3
"""Focused coverage for publisher factory metadata assembly."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import publish_grok46_hub as publisher  # noqa: E402


class PublisherFactoryMetadata(unittest.TestCase):
    def test_factories_builds_safe_deduplicated_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for slug in ("unit-factory", "unit-preference-factory"):
                (root / slug).mkdir()
            metadata = {
                "unit-factory": ("Unit trajectories.", ["unit", "unit"]),
                "unit-preference-factory": ("Unit pairs.", ["unit"]),
            }
            with (
                mock.patch.object(publisher, "FACTORY_ROOT", root),
                mock.patch.object(publisher, "META", metadata),
                mock.patch.dict(
                    publisher.leftover_mill.PUBLISHED_HUB_NAME, {}, clear=True
                ),
            ):
                result = publisher.factories()

        self.assertEqual(
            [item["hub"] for item in result],
            ["unit-trajectories", "unit-preference-pairs"],
        )
        self.assertIn("trajectories", result[0]["tags"])
        self.assertIn("preference-data", result[1]["tags"])
        self.assertEqual(result[0]["tags"].count("unit"), 1)

    def test_factory_metadata_rejects_missing_policy_and_banned_tags(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "unknown-factory").mkdir()
            with (
                mock.patch.object(publisher, "FACTORY_ROOT", root),
                mock.patch.object(publisher, "META", {}),
            ):
                with self.assertRaisesRegex(SystemExit, "missing META"):
                    publisher.factories()

        with self.assertRaisesRegex(SystemExit, "banned tag"):
            publisher._factory_tags(
                "unit-trajectories", ["spikenaut-private"], "unit-factory"
            )

    def test_factory_hub_rejects_issue_43_name_drift(self):
        slug = "email-webhook-retry-factory"
        with mock.patch.dict(
            publisher.leftover_mill.PUBLISHED_HUB_NAME,
            {slug: "wrong-hub"},
            clear=True,
        ):
            with self.assertRaisesRegex(SystemExit, "hub name drift"):
                publisher._factory_hub(slug)


if __name__ == "__main__":
    unittest.main()
