#!/usr/bin/env python3
"""OBS mill package: catalog pins, AST extract, generate, CLI, no vendored mills."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURE = REPO / "tests" / "fixtures" / "obs" / "catalog"
TINY_HOP = REPO / "tests" / "fixtures" / "obs" / "tiny-source" / "hop-plants.txt"
TINY_L3 = REPO / "tests" / "fixtures" / "obs" / "tiny-source" / "leftover3-pair.txt"
TINY_SPEC = REPO / "tests" / "fixtures" / "obs" / "tiny-source" / "leftover-spec.txt"
COMMITTED = REPO / "config" / "obs"

sys.path.insert(0, str(PIPELINES))

from mill_family import REVIEWED_MILL_PREFIX_HOMES, mill_prefix  # noqa: E402
from obs import catalog, cli, generate  # noqa: E402
from obs._contract import (  # noqa: E402
    FACTORY,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_DESTINATION_VENDOR,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SHAPE_UNSUPPORTED,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_USAGE,
    GENERATOR,
    MILL_PREFIX,
    SOURCE_COMMIT,
    ObsRefusal,
    refuse_vendor_path,
)
from record_kind import classify_kind  # noqa: E402


def invoke(argv: list[str]) -> tuple[int, str, str]:
    out, err = StringIO(), StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


def _legacy_source(relpath: str) -> str | None:
    for spec in (f"{SOURCE_COMMIT}:{relpath}", f"origin/legacy-mill-lane:{relpath}"):
        try:
            return subprocess.check_output(["git", "show", spec], text=True, cwd=REPO)
        except subprocess.CalledProcessError:
            continue
    return None


class CatalogPins(unittest.TestCase):
    def test_committed_catalog_loads_and_matches_registry(self):
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(loaded.catalog_id, "obs-plants-v1")
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(len(loaded.plants), 631)
        self.assertEqual(len(loaded.mills), 10)
        self.assertEqual(len(loaded.pair_plants()), 191)
        self.assertEqual(loaded.meta["pair_counts"]["leftover_specs"], 440)
        self.assertIsNone(loaded.leftover_spec_index)
        spec_plants = [plant for plant in loaded.plants if plant.shape == "leftover_spec"]
        self.assertEqual(len(spec_plants), 440)
        by_mill: dict[str, list[str]] = {}
        for plant in spec_plants:
            by_mill.setdefault(plant.mill_id, []).append(plant.slug)
        self.assertEqual(
            (by_mill["obs_leftover9"][0], by_mill["obs_leftover9"][-1]),
            ("redpanda-metrics-path-drop-leftover", "geode-pulse-bind-drop-leftover"),
        )
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[MILL_PREFIX], FACTORY)

    def test_fixture_catalog_is_three_plants(self):
        loaded = catalog.load_catalog(FIXTURE)
        self.assertEqual(loaded.catalog_id, "obs-fixture-v1")
        self.assertEqual(len(loaded.plants), 3)
        self.assertEqual(loaded.plants[0].plant_id, "obs_r0002:tiny-mimir-cap")
        self.assertEqual(loaded.plant("obs_r0001:tiny-dd-env-drop-leftover").shape, "leftover3")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="obs-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(FIXTURE, dest)
        meta_path = dest / catalog.CATALOG_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["digests"]["hop_plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(ObsRefusal) as caught:
            catalog.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_CATALOG_SHA256_MISMATCH)

    def test_unknown_plant_is_a_coded_refusal(self):
        loaded = catalog.load_catalog(FIXTURE)
        with self.assertRaises(ObsRefusal) as caught:
            loaded.plant("obs_r0002:missing")
        self.assertEqual(caught.exception.code, FINDING_PLANT_NOT_FOUND)


class AstExtract(unittest.TestCase):
    def test_plants_from_source_expands_p_defaults(self):
        rows = catalog.plants_from_source(
            TINY_HOP.read_text(encoding="utf-8"),
            mill_id="obs_r0002",
            source=str(TINY_HOP),
            base_round=2,
            shape="hop",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["slug"], "tiny-mimir-cap")
        self.assertEqual(rows[0]["file"], "mimir/tiny-mimir.yaml")
        self.assertEqual(rows[0]["panel"], "tiny mimir")
        self.assertEqual(rows[0]["novel"], 73)

    def test_plants_from_source_reads_leftover3_annassign(self):
        rows = catalog.plants_from_source(
            TINY_L3.read_text(encoding="utf-8"),
            mill_id="obs_r0001",
            source=str(TINY_L3),
            base_round=1,
            shape="leftover3",
        )
        self.assertEqual(rows[0]["plant_id"], "obs_r0001:tiny-dd-env-drop-leftover")
        self.assertEqual(rows[0]["shape"], "leftover3")

    def test_plants_from_source_reads_leftover_spec_dict_calls(self):
        rows = catalog.plants_from_source(
            TINY_SPEC.read_text(encoding="utf-8"),
            mill_id="obs_leftover9",
            source=str(TINY_SPEC),
            base_round=9,
            shape="leftover_spec",
            family="leftover9",
        )
        self.assertEqual(rows[0]["slug"], "tiny-metrics-off-leftover")
        self.assertEqual(rows[0]["noun"], "keel")

    def test_plants_from_source_refuses_a_non_literal_call(self):
        source = "PAIRS = [dict(slug=other())]\n"
        with self.assertRaises(ObsRefusal) as caught:
            catalog.plants_from_source(source, mill_id="obs_r0001", source="bad.py")
        self.assertEqual(caught.exception.code, FINDING_SOURCE_NOT_PARSEABLE)

    def test_committed_catalog_matches_legacy_ast(self):
        loaded = catalog.load_catalog(COMMITTED)
        committed = loaded.mill_plants("obs_r245")
        self.assertEqual(
            [plant.slug for plant in committed],
            ["mimir-series-cap", "tempo-mg-active", "vm-max-unique", "am-gossip-hold"],
        )
        self.assertIn("Never exec", catalog.plants_from_source.__doc__)
        self.assertEqual(SOURCE_COMMIT, "813f93f1969c1c4421e5663492e9663739efa642")

    def test_committed_leftover_specs_match_legacy_ast(self):
        loaded = catalog.load_catalog(COMMITTED)
        spec_mills = [mill for mill in loaded.mills if mill.shape == "leftover_spec"]
        probe = _legacy_source(spec_mills[0].source) if spec_mills else None
        if probe is None:
            self.skipTest("legacy-mill-lane obs leftover-spec sources are not available")
        for mill in spec_mills:
            text = _legacy_source(mill.source)
            if text is None:
                self.fail(f"legacy source missing for {mill.source}")
            family = mill.mill_id.removeprefix("obs_")
            extracted = catalog.plants_from_source(
                text,
                mill_id=mill.mill_id,
                source=mill.source,
                base_round=mill.base_round,
                shape=mill.shape,
                family=family,
            )
            committed = loaded.mill_plants(mill.mill_id)
            self.assertEqual(
                [plant.payload for plant in committed],
                list(extracted),
            )

    def test_package_tree_has_no_vendored_mill_scripts(self):
        roots = (PIPELINES / "obs", COMMITTED, REPO / "tests" / "fixtures" / "obs")
        hits = []
        for root in roots:
            hits.extend(root.rglob("obs-mill*.py"))
            hits.extend(root.rglob("obs-loop*.py"))
            hits.extend(root.rglob("_gen_obs_leftover*.py"))
            hits.extend(root.rglob("obs_r385_leftover3_mill.py"))
        self.assertEqual(hits, [])
        names = tuple(
            sorted(path.name for path in (PIPELINES / "obs").iterdir() if path.suffix == ".py")
        )
        self.assertEqual(
            names,
            (
                "__init__.py",
                "__main__.py",
                "_contract.py",
                "catalog.py",
                "cli.py",
                "generate.py",
            ),
        )


class GeneratePairs(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="obs-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_fixture_pair_is_an_episode_and_not_hosted_grok(self):
        dest = self.root / "out"
        request = generate.GenerateRequest(
            FIXTURE, dest, plant_id="obs_r0002:tiny-mimir-cap", round=3
        )
        summary = generate.run(request)
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["pairs"], 1)
        self.assertEqual(summary["generator"], GENERATOR)
        self.assertNotEqual(GENERATOR, "grok-4.6")
        lines = (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        ok, leftover = [json.loads(line) for line in lines]
        self.assertEqual(ok["id"], "obs-r3-tiny-mimir-cap")
        self.assertEqual(leftover["id"], "obs-r3-tiny-mimir-handoff")
        self.assertEqual(classify_kind(ok), "episode")
        self.assertEqual(classify_kind(leftover), "episode")
        self.assertEqual(mill_prefix(ok), "obs")
        self.assertEqual(mill_prefix(leftover), "obs")
        self.assertEqual(ok["meta"]["factory"], FACTORY)
        self.assertEqual(ok["meta"]["generator"], GENERATOR)
        self.assertNotEqual(ok["meta"]["generator"], "grok-4.6")
        self.assertEqual(len(ok["steps"]), 8)
        self.assertTrue(ok["reward"]["success"])
        self.assertFalse(leftover["reward"]["success"])
        notes = (dest / generate.NOTES_FILENAME).read_text(encoding="utf-8")
        self.assertIn("not grok-4.6", notes)

    def test_leftover_spec_is_not_generated(self):
        dest = self.root / "spec-out"
        with self.assertRaises(ObsRefusal) as caught:
            generate.run(
                generate.GenerateRequest(
                    FIXTURE, dest, plant_id="obs_leftover9:tiny-metrics-off-leftover"
                )
            )
        self.assertEqual(caught.exception.code, FINDING_SHAPE_UNSUPPORTED)
        self.assertFalse(dest.exists())

    def test_existing_destination_is_refused(self):
        dest = self.root / "exists"
        dest.mkdir()
        with self.assertRaises(ObsRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_EXISTS)

    def test_destination_under_raw_is_refused(self):
        dest = self.root / "outputs" / "raw" / "obs-out"
        with self.assertRaises(ObsRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(dest.exists())

    def test_vendor_mill_destination_is_refused(self):
        dest = self.root / "obs-mill-r245.py"
        with self.assertRaises(ObsRefusal) as caught:
            refuse_vendor_path(dest)
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_VENDOR)

    def test_generate_requires_exactly_one_selector(self):
        dest = self.root / "none"
        with self.assertRaises(ObsRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest))
        self.assertEqual(caught.exception.code, FINDING_USAGE)


class CliSurface(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="obs-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_catalog_check_json_on_the_fixture(self):
        code, out, err = invoke(["catalog-check", "--catalog", str(FIXTURE), "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], 3)
        self.assertEqual(payload["findings"], [])

    def test_generate_json_writes_the_pair(self):
        dest = self.root / "cli-out"
        code, out, err = invoke(
            [
                "generate",
                "--catalog",
                str(FIXTURE),
                "--out",
                str(dest),
                "--plant",
                "obs_r0002:tiny-mimir-cap",
                "--json",
            ]
        )
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 2)
        self.assertTrue((dest / generate.RECORDS_FILENAME).is_file())

    def test_missing_catalog_is_exit_two_and_json_on_stdout(self):
        code, out, err = invoke(["catalog-check", "--catalog", "/nonexistent/obs", "--json"])
        self.assertEqual((code, err), (2, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "refused")
        self.assertTrue(payload["code"].startswith("obs."))


class ImportTwins(unittest.TestCase):
    def test_flat_and_package_catalog_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.insert(0, str(REPO))
        import pipelines.obs.catalog as packaged

        self.assertIs(packaged, catalog)


if __name__ == "__main__":
    unittest.main()
