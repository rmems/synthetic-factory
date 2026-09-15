#!/usr/bin/env python3
"""Mill generate, validate, publish, and CLI: local runs, no hop, no raw."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mill_package_test_support import (  # noqa: E402
    FIXTURE_CATALOG,
    PINNED_AT,
    SEED,
    cli,
    generate,
    load_strict_json,
    publication,
    refusal,
    vocabulary as cv,
)


class GenerateRefusals(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="mill-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def request(self, **overrides):
        fields = {
            "catalog_dir": FIXTURE_CATALOG,
            "out_dir": self.root / "run",
            "seed": SEED,
            "count": 2,
            "produced_at": PINNED_AT,
        }
        fields.update(overrides)
        return generate.RunRequest(**fields)

    def test_seed_count_and_timestamp_domains(self):
        cases = (
            ({"seed": "7"}, cv.FINDING_SEED_NOT_AN_INTEGER),
            ({"seed": True}, cv.FINDING_SEED_NOT_AN_INTEGER),
            ({"seed": -1}, cv.FINDING_SEED_OUT_OF_DOMAIN),
            ({"count": 0}, cv.FINDING_COUNT_OUT_OF_DOMAIN),
            ({"count": 61}, cv.FINDING_COUNT_OUT_OF_DOMAIN),
            ({"produced_at": "yesterday"}, cv.FINDING_PRODUCED_AT_NOT_A_TIMESTAMP),
        )
        for overrides, code in cases:
            with self.subTest(code=code), refusal(self, code):
                generate.run(self.request(**overrides))

    def test_destinations_that_exist_or_alias_the_raw_tree_are_refused(self):
        (self.root / "run").mkdir()
        with refusal(self, cv.FINDING_DESTINATION_EXISTS, "already exists"):
            generate.run(self.request())
        raw = self.root / "outputs" / "raw" / "x"
        with refusal(self, cv.FINDING_DESTINATION_UNDER_RAW, "raw tree"):
            generate.run(self.request(out_dir=raw))
        self.assertFalse(raw.exists())


class GenerateRun(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="mill-run-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_two_pairs_are_mill_identity_and_byte_stable(self):
        first = self.root / "a"
        second = self.root / "b"
        summary = generate.run(generate.RunRequest(FIXTURE_CATALOG, first, SEED, 2, PINNED_AT))
        generate.run(generate.RunRequest(FIXTURE_CATALOG, second, SEED, 2, PINNED_AT))
        self.assertEqual(summary["family"], cv.FAMILY)
        self.assertEqual(summary["factory_id"], cv.FACTORY_ID)
        self.assertEqual(summary["generator"], cv.GENERATOR_NAME)
        self.assertEqual(summary["records"], 4)
        self.assertEqual(summary["produced_at"], PINNED_AT)
        self.assertEqual(
            (first / generate.PAIRS_FILENAME).read_bytes(),
            (second / generate.PAIRS_FILENAME).read_bytes(),
        )
        text = (first / generate.PAIRS_FILENAME).read_text(encoding="utf-8")
        self.assertIn(f'"factory":"{cv.FACTORY_ID}"', text)
        self.assertIn(f'"generator":"{cv.GENERATOR_NAME}"', text)
        self.assertIn(f"{cv.RECORD_ID_PREFIX}-r01-", text)
        self.assertNotIn("grok-4.6", text)
        self.assertNotIn("email-webhook-retry-factory", text)
        self.assertNotIn("leftover leftover leftover", text)
        self.assertNotIn("ewr-r", text)

    def test_full_catalog_emits_sixty_valid_pairs(self):
        out = self.root / "all"
        summary = generate.run(generate.RunRequest(FIXTURE_CATALOG, out, SEED, 60, PINNED_AT))
        self.assertEqual(summary["records"], 120)
        lines = [line for line in (out / generate.PAIRS_FILENAME).read_text().splitlines() if line]
        self.assertEqual(len(lines), 120)


class Publish(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="mill-pub-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.run_dir = self.root / "run"
        generate.run(generate.RunRequest(FIXTURE_CATALOG, self.run_dir, SEED, 1, PINNED_AT))

    def test_publish_copies_a_validated_run_and_refuses_hop_and_raw(self):
        dest = self.root / "published"
        receipt = publication.publish(
            publication.PublishRequest(self.run_dir, dest, FIXTURE_CATALOG)
        )
        self.assertEqual(receipt["factory_id"], cv.FACTORY_ID)
        self.assertEqual(receipt["records"], 2)
        self.assertTrue((dest / "receipt.json").is_file())
        with refusal(self, cv.FINDING_FACTORY_HOP_REFUSED, "hop"):
            publication.publish(
                publication.PublishRequest(
                    self.run_dir, self.root / "hop", FIXTURE_CATALOG,
                    hop_factory="email-webhook-retry-factory",
                )
            )
        with refusal(self, cv.FINDING_FACTORY_MISMATCH):
            publication.publish(
                publication.PublishRequest(
                    self.run_dir, self.root / "foreign", FIXTURE_CATALOG,
                    factory_id="email-webhook-retry-factory",
                )
            )
        raw = self.root / "outputs" / "raw" / "mill"
        with refusal(self, cv.FINDING_DESTINATION_UNDER_RAW, "raw tree"):
            publication.publish(publication.PublishRequest(self.run_dir, raw, FIXTURE_CATALOG))
        self.assertFalse(raw.exists())
        with refusal(self, cv.FINDING_DESTINATION_EXISTS, "already exists"):
            publication.publish(publication.PublishRequest(self.run_dir, dest, FIXTURE_CATALOG))


class CLI(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="mill-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_catalog_check_generate_and_render(self):
        self.assertEqual(cli.run(["catalog-check", "--catalog", str(FIXTURE_CATALOG), "--json"]), 0)
        out = self.root / "run"
        self.assertEqual(
            cli.run([
                "generate", "--catalog", str(FIXTURE_CATALOG), "--seed", str(SEED),
                "--count", "1", "--out", str(out), "--produced-at", PINNED_AT, "--json",
            ]),
            0,
        )
        first = (out / generate.PAIRS_FILENAME).read_text().splitlines()[0]
        record_id = load_strict_json(first)["id"]
        self.assertEqual(cli.run(["render", str(out), record_id, "--json"]), 0)
        self.assertEqual(cli.run(["render", str(out), "missing-id"]), 2)


if __name__ == "__main__":
    unittest.main()
