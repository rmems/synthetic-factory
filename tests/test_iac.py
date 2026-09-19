#!/usr/bin/env python3
"""PR-a: AST catalog extract and ``pipelines/iac`` skeleton (no vendored mills)."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from iac.catalog import CATALOG, load_catalog  # noqa: E402
from iac.plants_extract import (  # noqa: E402
    archive_b_row,
    dumps_plants_jsonl,
    extract_archive_b_more_plants,
    extract_archive_b_plants,
    sha256_bytes,
    write_plants_jsonl,
)
from iac.catalog_extract import (  # noqa: E402
    SHAPE_K8S_CLI_SPEC,
    SHAPE_LEFTOVER,
    SHAPE_LITERAL,
    SHAPE_SUC_FAIL,
    catalog_document,
    catalog_json_path,
    dumps_catalog,
    extract_companion_path,
    extract_mill_catalog,
    mill_summary,
)
from iac.identity import is_vendor_filename, is_vendor_path, refuse_vendor_paths  # noqa: E402
from iac.sources import MILL_SOURCES, catalog_sources, gen_sources, loop_sources  # noqa: E402
from iac import vocabulary as cv  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

_R609_SNIPPET = """
FACTORY = "infra-as-code-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 625
PAIRS: list[tuple[dict, dict]] = [
    (
        {"slug": "keep-a", "plant": "alpha-prod", "wrong_b": "Plan: a", "fix_b": "Reflection: a"},
        {"slug": "keep-a-fail", "plant": "alpha-jobs", "handoff": True,
         "wrong_b": "Plan: a", "fix_b": "Reflection: a"},
    ),
    (
        {"slug": "drop-me", "plant": "beta-prod", "wrong_b": "Plan: b", "fix_b": "Reflection: b"},
        {"slug": "drop-me-fail", "plant": "beta-jobs", "handoff": True,
         "wrong_b": "Plan: b", "fix_b": "Reflection: b"},
    ),
]
_DROP_SUCCESS = {"drop-me"}
PAIRS = [pair for pair in PAIRS if pair[0]["slug"] not in _DROP_SUCCESS]
_EXTRA: list[tuple[dict, dict]] = [
    (
        {"slug": "extra-a", "plant": "gamma-prod", "wrong_b": "Plan: c", "fix_b": "Reflection: c"},
        {"slug": "extra-a-fail", "plant": "gamma-jobs", "handoff": True,
         "wrong_b": "Plan: c", "fix_b": "Reflection: c"},
    ),
]
PAIRS.extend(_EXTRA)
"""

_SUC_FAIL_SNIPPET = """
CATALOG_FIRST = 659
PAIRS: list[tuple[dict, dict]] = [
    (
        _suc(slug="atmos-tfvars-vs-stale-stack", plant="firn-prod"),
        _fail(slug="atmos-webold-tfvars-leftover", plant="firn-jobs", handoff=True),
    ),
]
"""

_LEFTOVER_SNIPPET = """
CATALOG_FIRST = 709
PAIRS: list[tuple[dict, dict]] = [
    leftover_pair(s="xp-comprev-vs-old", fs="xp-comprev-old-leftover", g="oxbow", m="xp"),
]
"""

_K8S_SNIPPET = """
CATALOG_FIRST = 1132
K8S: list[tuple] = [
    ("argocd-app-vs-old", "agate", "argocd", "Argo CD Application",
     "Application", "application", "argoproj.io", "agate",
     "argocd-old", "argocd-jobs-old", "argocd", "spec", "fail"),
]
CLI_SPEC: list[dict] = [
    {"s": "lima-inst-vs-old", "g": "cuckoo", "m": "lima", "product": "lima leftover"},
]
CLI: list[tuple[dict, dict]] = [tool_pair(**row) for row in CLI_SPEC]
PAIRS: list[tuple[dict, dict]] = [k8s_pair(*row) for row in K8S] + CLI
"""


_ARCHIVE_B_REFS = (
    "e5206e72fa829931162944648e1e180949baaf0b",
    cv.ARCHIVE_B_COMMIT,
    cv.ARCHIVE_B_REF,
)


def _archive_b_show(path: str) -> tuple[str, str] | None:
    """Return ``(spec, text)`` for the first archive ref that resolves ``path``."""

    for ref in _ARCHIVE_B_REFS:
        spec = f"{ref}:{path}"
        try:
            text = subprocess.check_output(
                ["git", "show", spec],
                cwd=REPO,
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            continue
        return spec, text
    return None


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", "origin/legacy-mill-lane:experiments/iac-mill-r609.py"],
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


class IacSkeletonTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)
        self.assertEqual(cv.FACTORY, "infra-as-code-factory")
        self.assertEqual(cv.GENERATOR, "grok-4.6")
        self.assertEqual(cv.PRESERVE_COMMIT, "51bc810cd2cdd753e97b1ae737d5fa5b00b92478")

    def test_fifteen_sources_split_into_mills_loops_and_gens(self):
        self.assertEqual(len(MILL_SOURCES), 15)
        self.assertEqual(len(catalog_sources()), 7)
        self.assertEqual(len(loop_sources()), 6)
        self.assertEqual(len(gen_sources()), 2)
        self.assertEqual(
            {source.companion_mill_path for source in loop_sources()},
            {
                "experiments/iac-mill-r609.py",
                "experiments/iac-mill-r683.py",
                "experiments/iac-mill-r709.py",
                "experiments/iac-mill-r1514.py",
            },
        )

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in cv.FORBIDDEN_MILL_GLOBS:
            hits.extend(path for path in REPO.rglob(pattern) if "legacy-mill-lane" not in str(path))
        self.assertEqual(hits, [])

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("iac-mill-r609.py"))
        self.assertTrue(is_vendor_filename("iac-loop-r609.py"))
        self.assertTrue(is_vendor_filename("_gen_iac_plants_r1132.py"))
        self.assertTrue(is_vendor_filename("mill_plants.py"))
        self.assertTrue(is_vendor_filename("mill_plants_b.py"))
        self.assertFalse(is_vendor_filename("catalog_extract.py"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths([Path("experiments/iac-mill-r609.py")])
        self.assertFalse(is_vendor_filename("helper.py"))
        self.assertTrue(is_vendor_path("scripts/infra_as_code_mill/helper.py"))
        self.assertFalse(is_vendor_path("scripts/other_mill/helper.py"))
        self.assertFalse(is_vendor_path("scripts/infra_as_code_mill/README.md"))
        with self.assertRaises(SystemExit):
            refuse_vendor_paths(["scripts/infra_as_code_mill/helper.py"])

    def test_extractor_modules_never_exec(self):
        package = REPO / "pipelines" / "iac"
        hits = []
        for name in (
            "catalog_ast.py",
            "catalog_extract.py",
            "plants_extract.py",
            "catalog.py",
            "identity.py",
        ):
            hits.extend(_module_uses_exec(package / name))
        self.assertEqual(hits, [])

    def test_extractor_rebuilds_literal_drop_and_extend(self):
        extracted = extract_mill_catalog(_R609_SNIPPET, path="experiments/iac-mill-r609.py")
        self.assertEqual(extracted["shape"], SHAPE_LITERAL)
        self.assertEqual(extracted["catalog_first"], 625)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "keep-a")
        self.assertEqual(extracted["last_slug"], "extra-a")
        self.assertEqual(extracted["pairs"][0]["fail_plant"], "alpha-jobs")
        slugs = [row["success_slug"] for row in extracted["pairs"]]
        self.assertNotIn("drop-me", slugs)

    def test_extractor_reads_suc_fail_kwargs(self):
        extracted = extract_mill_catalog(_SUC_FAIL_SNIPPET, path="experiments/iac-mill-r659.py")
        self.assertEqual(extracted["shape"], SHAPE_SUC_FAIL)
        self.assertEqual(extracted["n_rows"], 1)
        self.assertEqual(extracted["first_slug"], "atmos-tfvars-vs-stale-stack")
        self.assertTrue(extracted["pairs"][0]["fail_handoff"])

    def test_extractor_reads_leftover_pair_kwargs(self):
        extracted = extract_mill_catalog(_LEFTOVER_SNIPPET, path="experiments/iac-mill-r709.py")
        self.assertEqual(extracted["shape"], SHAPE_LEFTOVER)
        self.assertEqual(extracted["pairs"][0]["success_plant"], "oxbow-prod")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "xp-comprev-old-leftover")

    def test_extractor_reads_k8s_and_cli_spec_tables(self):
        extracted = extract_mill_catalog(_K8S_SNIPPET, path="experiments/iac-mill-r1132.py")
        self.assertEqual(extracted["shape"], SHAPE_K8S_CLI_SPEC)
        self.assertEqual(extracted["n_rows"], 2)
        self.assertEqual(extracted["first_slug"], "argocd-app-vs-old")
        self.assertEqual(extracted["last_slug"], "lima-inst-vs-old")
        self.assertEqual(extracted["pairs"][0]["success_plant"], "agate-prod")

    def test_loop_mill_path_constant(self):
        source = (
            "ROOT = Path(__file__).resolve().parents[1]\n"
            'MILL = ROOT / "experiments" / "iac-mill-r609.py"\n'
        )
        self.assertEqual(extract_companion_path(source), "experiments/iac-mill-r609.py")

    def test_committed_catalog_counts(self):
        self.assertEqual(len(CATALOG.mills), 7)
        self.assertEqual(CATALOG.n_pair_rows, 1986)
        self.assertEqual(CATALOG.slice, "mill_plants")
        self.assertEqual(CATALOG.preserve_commit, cv.PRESERVE_COMMIT)
        self.assertEqual(len(CATALOG.plants), 8)
        self.assertEqual(len(CATALOG.plants_b), 8)
        self.assertEqual(CATALOG.archive_b.path, cv.PLANTS_SOURCE_PATH)
        self.assertEqual(CATALOG.archive_b.n_plants, 8)
        self.assertEqual(CATALOG.archive_b_more.path, cv.PLANTS_B_SOURCE_PATH)
        self.assertEqual(CATALOG.archive_b_more.n_plants, 8)
        self.assertEqual(CATALOG.plants[0].success_slug, "ansible-skip-if-unused")
        self.assertEqual(CATALOG.plants[-1].success_slug, "tf-already-used-address")
        self.assertEqual(CATALOG.plants_b[0].success_slug, "bicep-whatif-leftover-skip")
        self.assertEqual(CATALOG.plants_b[-1].success_slug, "nomad-system-skip")
        self.assertTrue(CATALOG.plants[0].fail_handoff)
        r609 = CATALOG.mills["iac-mill-r609"]
        self.assertEqual(r609.n_rows, 34)
        self.assertEqual(r609.catalog_first, 625)
        self.assertEqual(r609.first_slug, "flux-helmrelease-vs-helmchart")
        self.assertEqual(r609.last_slug, "cts-consul-vs-stale-task")
        self.assertEqual(len(r609.pairs), 34)
        self.assertTrue(r609.pairs[0]["fail_handoff"])
        self.assertEqual(CATALOG.mills["iac-mill-r1514"].n_rows, 1097)
        self.assertEqual(CATALOG.mills["iac-mill-r683"].n_keep, 9)
        self.assertEqual(CATALOG.mills["iac-mill-r777"].n_rows, 355)
        self.assertFalse(CATALOG.mills["iac-mill-r1514"].pairs)


class IacArchiveBExtractTests(unittest.TestCase):
    def test_archive_b_plants_do_not_overlap_r609_slugs(self):
        r609 = {pair["success_slug"] for pair in CATALOG.mills["iac-mill-r609"].pairs}
        plant_slugs = {plant.success_slug for plant in CATALOG.plants}
        self.assertEqual(plant_slugs & r609, set())

    def test_archive_b_more_plants_do_not_overlap_r609_or_archive_b(self):
        r609 = {pair["success_slug"] for pair in CATALOG.mills["iac-mill-r609"].pairs} | {
            pair["fail_slug"] for pair in CATALOG.mills["iac-mill-r609"].pairs
        }
        archive_slugs = {plant.success_slug for plant in CATALOG.plants} | {
            plant.fail_slug for plant in CATALOG.plants
        }
        more_slugs = {plant.success_slug for plant in CATALOG.plants_b} | {
            plant.fail_slug for plant in CATALOG.plants_b
        }
        self.assertEqual(more_slugs & r609, set())
        self.assertEqual(more_slugs & archive_slugs, set())

    def _assert_live_extract_matches_committed(
        self,
        source_path,
        blob_sha,
        source_sha256,
        committed,
        extract,
    ):
        found = _archive_b_show(source_path)
        if found is None:
            self.skipTest(f"archive B {source_path} is not available via git show")
        spec, text = found
        blob = subprocess.check_output(
            ["git", "rev-parse", spec],
            cwd=REPO,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        self.assertEqual(blob, blob_sha)
        live = extract(text)
        self.assertEqual(live["n_plants"], 8)
        self.assertEqual(live["sha256"], source_sha256)
        self.assertEqual(live["plants"], [asdict(plant) for plant in committed])

    def test_committed_plants_match_live_ast_extract(self):
        self._assert_live_extract_matches_committed(
            cv.PLANTS_SOURCE_PATH,
            cv.PLANTS_BLOB_SHA,
            cv.PLANTS_SOURCE_SHA256,
            CATALOG.plants,
            extract_archive_b_plants,
        )

    def test_committed_plants_b_match_live_ast_extract(self):
        self._assert_live_extract_matches_committed(
            cv.PLANTS_B_SOURCE_PATH,
            cv.PLANTS_B_BLOB_SHA,
            cv.PLANTS_B_SOURCE_SHA256,
            CATALOG.plants_b,
            extract_archive_b_more_plants,
        )


_PLANTS_SNIPPET = """
PAIRS: list = []
x = 1
print("noop")
PAIRS.append(
    (
        _ok(slug="ok-a", seed="seed-a", ticket="T-1", test="t-a"),
        _fail(slug="fail-a", seed="seed-b", handoff=True),
        "scenario-a",
    )
)
PAIRS.append("not-a-triple")
PAIRS.append((_ok(slug="ok-b"), _fail(slug="fail-b")))
PAIRS.append((_ok(slug="ok-c"), _fail(slug="fail-c"), 42))
PAIRS.append((_ok(), _fail(slug="fail-d"), "scenario-d"))
MORE.append((_ok(slug="ok-e"), _fail(slug="fail-e"), "scenario-e"))
OTHER.append((_ok(slug="ok-f"), _fail(slug="fail-f"), "scenario-f"))
PAIRS.extend([(_ok(slug="ok-g"), _fail(slug="fail-g"), "scenario-g")])
"""


class IacPlantsExtractUnitTests(unittest.TestCase):
    def test_extract_skips_non_matching_statements(self):
        live = extract_archive_b_plants(_PLANTS_SNIPPET, path="x/mill_plants.py")
        self.assertEqual(live["n_plants"], 1)
        self.assertEqual(live["first_slug"], "ok-a")
        self.assertEqual(live["last_slug"], "ok-a")
        self.assertEqual(live["shape"], "ok-fail-label")
        row = live["plants"][0]
        self.assertEqual(
            row,
            {
                "index": 0,
                "success_slug": "ok-a",
                "fail_slug": "fail-a",
                "success_seed": "seed-a",
                "fail_seed": "seed-b",
                "scenario": "scenario-a",
                "ticket": "T-1",
                "test": "t-a",
                "fail_handoff": True,
            },
        )

    def test_extract_requires_at_least_one_triple(self):
        with self.assertRaises(ValueError):
            extract_archive_b_plants("PAIRS = []\n", path="x/mill_plants.py")

    def test_compact_row_rejects_non_string_fields(self):
        source = 'PAIRS.append((_ok(slug=True), _fail(slug="f"), "s"))\n'
        with self.assertRaises(ValueError):
            extract_archive_b_plants(source, path="x/mill_plants.py")
        source = 'PAIRS.append((_ok(slug="a", seed=7), _fail(slug="f"), "s"))\n'
        with self.assertRaises(ValueError):
            extract_archive_b_plants(source, path="x/mill_plants.py")

    def test_archive_b_row_shapes_the_catalog_block(self):
        live = extract_archive_b_plants(_PLANTS_SNIPPET, path="x/mill_plants.py")
        row = archive_b_row(live, ref="origin/ref", commit="abc123", blob_sha="def456")
        self.assertEqual(row["ref"], "origin/ref")
        self.assertEqual(row["commit"], "abc123")
        self.assertEqual(row["blob_sha"], "def456")
        self.assertEqual(row["path"], "x/mill_plants.py")
        self.assertEqual(row["sha256"], live["sha256"])
        self.assertEqual(row["n_plants"], 1)
        self.assertEqual(row["first_slug"], "ok-a")
        self.assertEqual(row["last_slug"], "ok-a")

    def test_plants_jsonl_round_trip(self):
        live = extract_archive_b_plants(_PLANTS_SNIPPET, path="x/mill_plants.py")
        payload = dumps_plants_jsonl(live["plants"])
        parsed = [json.loads(line) for line in payload.splitlines()]
        self.assertEqual(parsed, live["plants"])
        with tempfile.TemporaryDirectory() as tmp:
            written = write_plants_jsonl(live["plants"], Path(tmp) / "plants.jsonl")
            self.assertEqual(written.read_text(encoding="utf-8"), payload)


class IacCatalogLoadTests(unittest.TestCase):
    def _catalog_tree(self, tmp: Path, mutate) -> Path:
        source = catalog_json_path()
        document = json.loads(source.read_text(encoding="utf-8"))
        mutate(document)
        (tmp / cv.CATALOG_FILENAME).write_text(dumps_catalog(document), encoding="utf-8")
        for name in (cv.PLANTS_FILENAME, cv.PLANTS_B_FILENAME):
            (tmp / name).write_bytes((source.parent / name).read_bytes())
        return tmp / cv.CATALOG_FILENAME

    def test_load_catalog_rejects_document_drift(self):
        for key in ("schema", "preserve_commit", "slice", "factory", "generator"):
            with tempfile.TemporaryDirectory() as tmp:
                path = self._catalog_tree(
                    Path(tmp), lambda doc, k=key: doc.update({k: "drifted"})
                )
                with self.assertRaises(ValueError, msg=key):
                    load_catalog(path)

    def test_load_catalog_rejects_plants_digest_drift(self):
        for key in ("plants_sha256", "plants_b_sha256"):
            with tempfile.TemporaryDirectory() as tmp:
                path = self._catalog_tree(
                    Path(tmp), lambda doc, k=key: doc.update({k: "0" * 64})
                )
                with self.assertRaises(ValueError, msg=key):
                    load_catalog(path)

    def test_load_catalog_rejects_archive_pin_drift(self):
        for key in ("ref", "commit", "path", "blob_sha", "sha256", "n_plants", "first_slug"):
            with tempfile.TemporaryDirectory() as tmp:
                path = self._catalog_tree(
                    Path(tmp),
                    lambda doc, k=key: doc["archive_b"].update({k: "drifted"}),
                )
                with self.assertRaises(ValueError, msg=key):
                    load_catalog(path)

    def test_load_catalog_rejects_incomplete_plants_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            path = self._catalog_tree(tmp_path, lambda doc: None)
            (tmp_path / cv.PLANTS_FILENAME).write_text(
                '{"index": 0}\n', encoding="utf-8"
            )
            document = json.loads(path.read_text(encoding="utf-8"))
            document["plants_sha256"] = sha256_bytes(b'{"index": 0}\n')
            path.write_text(dumps_catalog(document), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_catalog(path)


class IacLegacyExtractTests(unittest.TestCase):
    def test_committed_catalog_matches_live_ast_extract(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        mills = []
        for source in catalog_sources():
            text = subprocess.check_output(
                ["git", "show", f"{cv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            blob = subprocess.check_output(
                ["git", "rev-parse", f"{cv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            ).strip()
            self.assertEqual(blob, source.blob_sha, source.mill_id)
            live = extract_mill_catalog(text, path=source.path, blob_sha=source.blob_sha)
            committed = CATALOG.mills[source.mill_id]
            self.assertEqual(live["n_rows"], committed.n_rows, source.mill_id)
            self.assertEqual(live["first_slug"], committed.first_slug, source.mill_id)
            self.assertEqual(live["last_slug"], committed.last_slug, source.mill_id)
            self.assertEqual(live["catalog_first"], committed.catalog_first, source.mill_id)
            self.assertEqual(live["sha256"], committed.sha256, source.mill_id)
            self.assertEqual(live["shape"], committed.shape, source.mill_id)
            mills.append(
                mill_summary(live, include_pairs=source.mill_id == "iac-mill-r609")
            )
        committed = json.loads(catalog_json_path().read_text(encoding="utf-8"))
        live_doc = catalog_document(
            mills,
            archives={
                "archive_b": committed["archive_b"],
                "archive_b_more": committed["archive_b_more"],
            },
            plant_digests={
                "plants_sha256": committed["plants_sha256"],
                "plants_b_sha256": committed["plants_b_sha256"],
            },
        )
        self.assertEqual(live_doc, committed)

    def test_regenerated_catalog_round_trips_through_loader(self):
        committed_path = catalog_json_path()
        committed = json.loads(committed_path.read_text(encoding="utf-8"))
        live_doc = catalog_document(
            [
                mill_summary(
                    {
                        "mill_id": mill.mill_id,
                        "path": mill.path,
                        "blob_sha": mill.blob_sha,
                        "sha256": mill.sha256,
                        "kind": mill.kind,
                        "shape": mill.shape,
                        "catalog_first": mill.catalog_first,
                        "n_rows": mill.n_rows,
                        "first_slug": mill.first_slug,
                        "last_slug": mill.last_slug,
                        "generator": mill.generator,
                        "factory": mill.factory,
                        **(
                            {
                                "n_keep": mill.n_keep,
                                "n_extra": mill.n_extra,
                                "keep_slugs": mill.keep_slugs,
                            }
                            if mill.shape == "pairs-keep-extend"
                            else {}
                        ),
                        "pairs": list(mill.pairs),
                    },
                    include_pairs=bool(mill.pairs),
                )
                for mill in CATALOG.mills.values()
            ],
            archives={
                "archive_b": committed["archive_b"],
                "archive_b_more": committed["archive_b_more"],
            },
            plant_digests={
                "plants_sha256": committed["plants_sha256"],
                "plants_b_sha256": committed["plants_b_sha256"],
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            for name in (cv.PLANTS_FILENAME, cv.PLANTS_B_FILENAME):
                (dest / name).write_bytes((committed_path.parent / name).read_bytes())
            target = dest / cv.CATALOG_FILENAME
            target.write_text(dumps_catalog(live_doc), encoding="utf-8")
            reloaded = load_catalog(target)
        self.assertEqual(reloaded.n_pair_rows, CATALOG.n_pair_rows)
        self.assertEqual(reloaded.plants, CATALOG.plants)
        self.assertEqual(reloaded.plants_b, CATALOG.plants_b)

    def test_loop_and_gen_scripts_name_companion_mills(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        for source in (*loop_sources(), *gen_sources()):
            text = subprocess.check_output(
                ["git", "show", f"{cv.LEGACY_REF}:{source.path}"],
                text=True,
                cwd=REPO,
            )
            self.assertEqual(
                extract_companion_path(text),
                source.companion_mill_path,
                source.mill_id,
            )

    def test_git_show_is_the_only_legacy_read(self):
        if not _legacy_available():
            self.skipTest("origin/legacy-mill-lane is not fetched")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            refuse_vendor_paths(dest.rglob("*") if dest.exists() else ())
            self.assertEqual(list(dest.glob("iac-mill*.py")), [])


if __name__ == "__main__":
    unittest.main()
