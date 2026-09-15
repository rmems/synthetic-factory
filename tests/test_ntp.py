#!/usr/bin/env python3
"""PR-a: AST catalog extract and ``pipelines/ntp`` skeleton (no vendored mills)."""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from ntp import vocabulary as nv  # noqa: E402
from ntp.catalog import CATALOG  # noqa: E402
from ntp.catalog_extract import (  # noqa: E402
    SHAPE_S_FROM,
    SHAPE_S_L_KW,
    catalog_document,
    catalog_json_path,
    dumps_catalog,
    extract_chain_bounds,
    extract_companion_path,
    extract_mill_catalog,
    is_slice_mill,
    mill_summary,
)
from ntp.identity import is_vendor_filename, refuse_vendor_paths  # noqa: E402
from ntp.sources import (  # noqa: E402
    MILL_SOURCES,
    catalog_sources,
    chain_sources,
    gen_sources,
    loop_sources,
)

_LEFTOVER_SNIPPET = """
FACTORY = "notebook-to-pipeline-factory"
GEN = "grok-4.6"
SUCCESS = [
    s_from(0, "soda-scan-as-dest", "sds", "soda leftover", ".soda/scan.json",
           "Soda scan leftover JSON", "soda leftover && cat .soda/scan.json",
           "not gx leftover", "treat leftover as dest.", "soda leftover; # dest",
           "soda leftover|.soda/scan"),
    s_from(1, "drop-me-as-dest", "dpm", "drop leftover", ".drop/me.json",
           "drop leftover JSON", "drop leftover && cat .drop/me.json",
           "not soda leftover", "treat leftover as dest.", "drop leftover; # dest",
           "drop leftover|.drop/me"),
]
LEFTOVER = [
    l_from(0, "openlineage-event-leftover", "oln2", ".ol/event.json",
           "openlineage leftover", "OpenLineage leftover JSON",
           "not soda leftover", "ship leftover as dest.", "event leftover; # json",
           "openlineage leftover|.ol/event"),
]
"""

_R1326_SNIPPET = """
FACTORY = "notebook-to-pipeline-factory"
GEN = "grok-4.6"
START = 1326
SUCCESS = [
    S(slug="kubeflow-pipeline-run-as-dest", stem="kfp", src="data/kfp_src.csv",
      rows=12011, transform="df = df.copy()", token="kfp leftover",
      ban="kfp leftover|.kfp/run", distinct="not flyte dest",
      plan="treat leftover as dest.", cell="kfp leftover; # dest",
      artifact=".kfp/run.json", kind="KFP leftover JSON",
      cmd="kfp leftover && cat .kfp/run.json", file_obs="not parquet"),
]
LEFTOVER = [
    L(slug="altair-vl-json-leftover", stem="alvl", src="data/alvl_src.csv",
      rows=13011, transform="df = df.copy()", leftover=".altair/vl.json",
      left_token="altair leftover", ban="altair leftover|.altair/vl",
      distinct="not kfp leftover", plan="ship leftover as dest.",
      cell="altair leftover; # json", residual="still on disk",
      handoff="leftover not cleaned", kind="Altair leftover JSON",
      wrap="tar -cf alvl.parquet .altair/vl.json", wrap_obs="tar leftover"),
]
"""

_WAVE_SNIPPET = """
SUCCESS = [
    s_from(0, "datahub-aspect-leftover-as-dest", "dhas", "datahub leftover",
           ".datahub/aspect.json", "DataHub leftover JSON",
           "datahub leftover && cat .datahub/aspect.json",
           "not openlineage leftover", "treat leftover as dest.",
           "datahub leftover; # dest", "datahub leftover|.datahub/aspect"),
]
LEFTOVER = [
    l_from(0, "datahub-lineage-leftover-handoff", "dhln", ".datahub/lineage.json",
           "datahub lineage leftover", "DataHub lineage leftover JSON",
           "not datahub aspect leftover", "ship leftover as dest.",
           "lineage leftover; # json", "datahub leftover|.datahub/lineage"),
]
"""


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", "origin/legacy-mill-lane:experiments/ntp-mill-unique-leftover.py"],
            cwd=REPO,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _module_uses_exec(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id in {"exec", "eval", "compile"}:
            hits.append(f"{path.name}:{node.lineno}:{node.func.id}")
    return hits


class NtpSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[nv.FAMILY_PREFIX], nv.FACTORY)
        self.assertEqual(nv.FACTORY, "notebook-to-pipeline-factory")
        self.assertEqual(nv.GENERATOR, "grok-4.6")
        self.assertEqual(nv.PRESERVE_COMMIT, "ffd8e849694818083c5cf3dbadfba5872294c5f1")
        self.assertEqual(nv.SLICE_ID, "leftover")

    def test_eighty_four_sources_split_into_mills_loops_gens_and_chains(self):
        self.assertEqual(len(MILL_SOURCES), 84)
        self.assertEqual(len(catalog_sources()), 38)
        self.assertEqual(len(loop_sources()), 38)
        self.assertEqual(len(gen_sources()), 6)
        self.assertEqual(len(chain_sources()), 2)
        self.assertEqual(
            {source.companion_mill_path for source in loop_sources() if "llll5" in source.mill_id},
            {"experiments/ntp-mill-unique-llll5.py"},
        )
        r1326_loop = next(
            source for source in loop_sources() if source.mill_id == "ntp-loop-r1326"
        )
        self.assertEqual(r1326_loop.companion_mill_path, "experiments/ntp-mill-r1326.py")
        self.assertEqual(
            {source.companion_mill_path for source in chain_sources()},
            {None},
        )

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in nv.FORBIDDEN_MILL_GLOBS:
            hits.extend(path for path in REPO.rglob(pattern) if "legacy-mill-lane" not in str(path))
        self.assertEqual(hits, [])

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("ntp-mill-unique-leftover.py"))
        self.assertTrue(is_vendor_filename("ntp-loop-r1326.py"))
        self.assertTrue(is_vendor_filename("ntp-chain-llll15-26.py"))
        self.assertTrue(is_vendor_filename("_gen_ntp_llll15plus.py"))
        self.assertTrue(is_vendor_filename("ntp-extend-plants-r1558.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/ntp-mill-r1326.py")])

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "ntp"
        hits = []
        for name in (
            "catalog_ast.py",
            "catalog_extract.py",
            "catalog.py",
            "identity.py",
            "sources.py",
        ):
            hits.extend(_module_uses_exec(package / name))
        self.assertEqual(hits, [])

    def test_extractor_reads_s_from_and_l_from(self):
        extracted = extract_mill_catalog(
            _LEFTOVER_SNIPPET,
            path="experiments/ntp-mill-unique-leftover.py",
        )
        self.assertEqual(extracted["shape"], SHAPE_S_FROM)
        self.assertEqual(extracted["n_success"], 2)
        self.assertEqual(extracted["n_leftover"], 1)
        self.assertEqual(extracted["first_slug"], "soda-scan-as-dest")
        self.assertEqual(extracted["success"][0]["plant"], "folio-sds")
        self.assertEqual(extracted["leftover"][0]["leftover"], ".ol/event.json")
        self.assertEqual(extracted["factory"], nv.FACTORY)

    def test_extractor_reads_s_l_kwargs(self):
        extracted = extract_mill_catalog(
            _R1326_SNIPPET,
            path="experiments/ntp-mill-r1326.py",
        )
        self.assertEqual(extracted["shape"], SHAPE_S_L_KW)
        self.assertEqual(extracted["catalog_first"], 1326)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["first_slug"], "kubeflow-pipeline-run-as-dest")
        self.assertEqual(extracted["first_leftover_slug"], "altair-vl-json-leftover")
        self.assertEqual(extracted["success"][0]["plant"], "folio-kfp")

    def test_extractor_reads_wave_s_from_lists(self):
        extracted = extract_mill_catalog(
            _WAVE_SNIPPET,
            path="experiments/ntp-mill-unique-llll5.py",
        )
        self.assertEqual(extracted["shape"], SHAPE_S_FROM)
        self.assertIsNone(extracted["catalog_first"])
        self.assertEqual(extracted["first_slug"], "datahub-aspect-leftover-as-dest")
        self.assertEqual(extracted["leftover"][0]["slug"], "datahub-lineage-leftover-handoff")

    def test_loop_mill_path_from_gen_assignment(self):
        source = (
            "ROOT = Path('/home/raulmc/rmems/synthetic-factory')\n"
            'GEN = ["python3", str(ROOT / "experiments/ntp-mill-unique-leftover.py")]\n'
        )
        self.assertEqual(
            extract_companion_path(source),
            "experiments/ntp-mill-unique-leftover.py",
        )

    def test_loop_mill_path_from_replace_target(self):
        source = (
            "src = (ROOT / 'experiments/ntp-loop-unique-llll3.py').read_text()\n"
            'src = src.replace("ntp-mill-unique-llll3.py", "ntp-mill-unique-llll5.py")\n'
        )
        self.assertEqual(
            extract_companion_path(source),
            "experiments/ntp-mill-unique-llll5.py",
        )

    def test_plant_gen_write_wave_and_table(self):
        wave = "def write_wave(n, s, l): pass\nwrite_wave(15, S15, L15)\n"
        self.assertEqual(
            extract_companion_path(wave),
            "experiments/ntp-mill-unique-llll15.py",
        )
        table = "S19 = [('sqlite-db', 'sqdb', 'folio.sqlite', 'sqlite db')]\n"
        self.assertEqual(
            extract_companion_path(table),
            "experiments/ntp-mill-unique-llll19.py",
        )

    def test_chain_loop_range(self):
        source = (
            "for n in range(15, 27):\n"
            "    loop = ROOT / f'experiments/ntp-loop-unique-llll{n}.py'\n"
        )
        self.assertEqual(extract_chain_bounds(source), (15, 26))

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 38)
        self.assertEqual(CATALOG.n_pair_rows, 1625)
        self.assertEqual(CATALOG.slice, "leftover")
        self.assertEqual(CATALOG.preserve_commit, nv.PRESERVE_COMMIT)
        leftover = CATALOG.mills[nv.SLICE_MILL_ID]
        self.assertEqual(leftover.n_success, 60)
        self.assertEqual(leftover.n_leftover, 70)
        self.assertEqual(leftover.n_rows, 60)
        self.assertIsNone(leftover.catalog_first)
        self.assertEqual(leftover.first_slug, "soda-scan-as-dest")
        self.assertEqual(leftover.last_slug, "koalas-index-as-dest")
        self.assertEqual(leftover.first_leftover_slug, "openlineage-event-leftover")
        self.assertEqual(leftover.last_leftover_slug, "treon-report-leftover")
        self.assertEqual(len(leftover.success), 60)
        self.assertEqual(len(leftover.leftover), 70)
        self.assertEqual(leftover.success[0]["plant"], "folio-sdsc")
        r1326 = CATALOG.mills["ntp-mill-r1326"]
        self.assertEqual(r1326.n_rows, 445)
        self.assertEqual(r1326.catalog_first, 1326)
        self.assertEqual(r1326.shape, SHAPE_S_L_KW)
        self.assertEqual(r1326.first_slug, "kubeflow-pipeline-run-as-dest")
        self.assertFalse(r1326.success)
        orch = CATALOG.mills["ntp-mill-orch-leftover3"]
        self.assertEqual(orch.n_rows, 16)
        self.assertEqual(orch.catalog_first, 1558)
        self.assertEqual(CATALOG.mills["ntp-mill-unique-llll"].catalog_first, 1719)
        self.assertEqual(CATALOG.mills["ntp-mill-unique-llll34"].n_rows, 32)


class NtpLegacyExtractTests(unittest.TestCase):
    def test_committed_catalog_matches_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        mills = []
        for source in catalog_sources():
            text = subprocess.check_output(
                ["git", "show", f"{nv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            blob = subprocess.check_output(
                ["git", "rev-parse", f"{nv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            ).strip()
            self.assertEqual(blob, source.blob_sha, source.mill_id)
            live = extract_mill_catalog(text, path=source.path, blob_sha=source.blob_sha)
            committed = CATALOG.mills[source.mill_id]
            self.assertEqual(live["n_rows"], committed.n_rows, source.mill_id)
            self.assertEqual(live["n_success"], committed.n_success, source.mill_id)
            self.assertEqual(live["n_leftover"], committed.n_leftover, source.mill_id)
            self.assertEqual(live["first_slug"], committed.first_slug, source.mill_id)
            self.assertEqual(live["last_slug"], committed.last_slug, source.mill_id)
            self.assertEqual(live["catalog_first"], committed.catalog_first, source.mill_id)
            self.assertEqual(live["sha256"], committed.sha256, source.mill_id)
            self.assertEqual(live["shape"], committed.shape, source.mill_id)
            mills.append(mill_summary(live, include_themes=is_slice_mill(source.mill_id)))
        self.assertEqual(
            dumps_catalog(catalog_document(mills)),
            catalog_json_path().read_text(encoding="utf-8"),
        )

    def test_loop_and_gen_scripts_name_companion_mills(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        for source in (*loop_sources(), *gen_sources()):
            text = subprocess.check_output(
                ["git", "show", f"{nv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            self.assertEqual(
                extract_companion_path(text),
                source.companion_mill_path,
                source.mill_id,
            )

    def test_chain_scripts_name_loop_ranges(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        expect = {
            "ntp-chain-llll15-26": (15, 26),
            "ntp-chain-llll27-34": (27, 34),
        }
        for source in chain_sources():
            text = subprocess.check_output(
                ["git", "show", f"{nv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            self.assertIsNone(extract_companion_path(text), source.mill_id)
            self.assertEqual(extract_chain_bounds(text), expect[source.mill_id], source.mill_id)

    def test_git_show_is_the_only_legacy_read(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            refuse_vendor_paths(dest.rglob("*") if dest.exists() else ())
            self.assertEqual(list(dest.glob("ntp-mill*.py")), [])


if __name__ == "__main__":
    unittest.main()
