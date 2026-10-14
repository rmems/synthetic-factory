#!/usr/bin/env python3
"""OBS mill package: catalog pins, AST extract, generate, CLI, no vendored mills."""

from __future__ import annotations

import ast
import contextlib
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
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
    FINDING_CATALOG_FIELD_INVALID,
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

    def test_read_jsonl_invalid_utf8_is_coded_refusal(self):
        with self.assertRaises(ObsRefusal) as caught:
            catalog._read_jsonl(b"\xff\xfe\xfd", "test.jsonl")
        self.assertEqual(caught.exception.code, FINDING_CATALOG_FIELD_INVALID)
        self.assertIn("is not valid UTF-8", str(caught.exception))

    def test_read_jsonl_framing_and_validation_refusals(self):
        with self.assertRaises(ObsRefusal) as caught:
            catalog._read_jsonl(b'{"key": 1}\r\n', "test.jsonl")
        self.assertEqual(caught.exception.code, FINDING_CATALOG_FIELD_INVALID)

        with self.assertRaises(ObsRefusal) as caught:
            catalog._read_jsonl(b'{"key": 1}', "test.jsonl")
        self.assertEqual(caught.exception.code, FINDING_CATALOG_FIELD_INVALID)

        with self.assertRaises(ObsRefusal) as caught:
            catalog._read_jsonl(b'{"key": 1}\n\n', "test.jsonl")
        self.assertEqual(caught.exception.code, FINDING_CATALOG_FIELD_INVALID)

        with self.assertRaises(ObsRefusal) as caught:
            catalog._read_jsonl(b"not json\n", "test.jsonl")
        self.assertEqual(caught.exception.code, FINDING_CATALOG_FIELD_INVALID)


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


R401_ROW = (
    "'tempo', 'tiny-r401', 'tiny-r401-left', 'svc-a', 'lsvc-b', 'dash', 'ldash', '.yq',"
    " 'fail line', 'fix line', 'fv', 'xv', '.false.yq', 'false lead', 'fo', 'fn', 'fp',"
    " 'f2o', 'f2n', 'f2p', 'lie', 'llie', 'new_vs', 73"
)


def _spec_index(**pin) -> dict:
    row = {"mill_id": "obs_leftover9", "count": 1, "first": "a", "last": "b", **pin}
    return {"kind": catalog.SPEC_INDEX_KIND, "total": 1, "mills": [row]}


class RefusalBranches(unittest.TestCase):
    """Each extracted check's refusal fires with its code and message."""

    @contextlib.contextmanager
    def _refusal(self, code, message):
        with self.assertRaises(ObsRefusal) as caught:
            yield
        self.assertEqual(caught.exception.code, code)
        self.assertIn(message, str(caught.exception))

    def _catalog_copy(self, edit_meta=None, specs=None) -> Path:
        root = Path(tempfile.mkdtemp(prefix="obs-refusal-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(FIXTURE, dest)
        meta_path = dest / "CATALOG.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if specs is not None:
            payload = (json.dumps(specs, sort_keys=True) + "\n").encode("utf-8")
            (dest / "leftover-specs.jsonl").write_bytes(payload)
            meta["digests"]["leftover_specs_sha256"] = hashlib.sha256(payload).hexdigest()
            meta["plant_count"] = 2
        if edit_meta is not None:
            edit_meta(meta)
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        return dest

    def test_const_eval_reads_containers_and_refuses_the_rest(self):
        expected = [1, (2, -3), {4}, {"k": -1.5}]
        node = ast.parse("[1, (2, -3), {4}, {'k': -1.5}]", mode="eval").body
        self.assertEqual(catalog._const_eval(node), expected)
        for text, message in (
            ("{**extra}", "uses dict unpacking"),
            ("{1: name, **extra}", "uses dict unpacking"),
            ("not 1", "(UnaryOp)"),
            ("name", "(Name)"),
        ):
            node = ast.parse(text, mode="eval").body
            with self.subTest(text=text), self._refusal(FINDING_SOURCE_NOT_PARSEABLE, message):
                catalog._const_eval(node)

    def test_kind_bits_read_one_row_per_kind_and_default_to_am(self):
        for kind in catalog.DEFAULT_KIND_NS:
            with self.subTest(kind=kind):
                bits = catalog._kind_bits(kind, "svc-a", "lsvc-b", "fv")
                self.assertEqual(tuple(bits), catalog._KIND_BIT_KEYS)
                self.assertIn("svc-a", bits["query"])
                self.assertIn("lsvc-b", bits["lquery"])
                self.assertIn("fv", bits["exec_err"] + bits["exec_obs"])
        self.assertEqual(catalog._kind_bits("zzz", "s-1", "l", "f"),
                         catalog._kind_bits("am", "s-1", "l", "f"))

    def test_positional_r401_plants_expand_with_kind_bits(self):
        rows = catalog.plants_from_source(f"PAIRS = [P({R401_ROW})]\n", mill_id="obs_r401",
                                          source="r401.py", shape="hop")
        self.assertEqual(rows[0]["query"], '{resource.service.name="svc-a"}')
        self.assertEqual(rows[0]["ns"], "tempo")
        self.assertEqual(rows[0]["file"], "tempo/dash.yaml")

    def test_plants_from_source_refuses_each_malformed_literal(self):
        hop = {key: "x" for key in catalog.HOP_REQUIRED}
        spec = {key: "x" for key in catalog.SPEC_REQUIRED}
        missing = catalog.FINDING_PLANT_FIELD_MISSING
        invalid = catalog.FINDING_PLANT_FIELD_INVALID
        cases = (
            ("PAIRS = [x.y()]", "obs_r1", FINDING_SOURCE_NOT_PARSEABLE, "(Call)"),
            ("PAIRS = [foo()]", "obs_r1", FINDING_SOURCE_NOT_PARSEABLE, "(Call)"),
            ("PAIRS = [P(1, k=2)]", "obs_r1", FINDING_SOURCE_NOT_PARSEABLE, "(Call)"),
            ("PAIRS = [{'slug': 's'}]", "obs-1", invalid, "is not obs_*"),
            ("PAIRS = [(1, 2)]", "obs_r1", FINDING_SOURCE_NOT_PARSEABLE,
             "s.py[0] is not an object"),
            ("PAIRS = [{'slug': 's'}]", "obs_r1", missing, "s.py[0] missing lslug"),
            (f"PAIRS = [{dict(hop, slug='-x')!r}]", "obs_r1", invalid, "is not a plant slug"),
            ("SPECS = [(1, 2)]", "obs_leftover9", FINDING_SOURCE_NOT_PARSEABLE,
             "is not a 17-tuple"),
            ("SPECS = [{'vendor': 'v'}]", "obs_leftover9", missing, "s.py[0] missing ok_slug"),
            (f"SPECS = [{dict(spec, ok_slug='-x')!r}]", "obs_leftover9", invalid,
             "s.py[0].ok_slug is not a slug"),
        )
        for text, mill_id, code, message in cases:
            with self.subTest(message=message, text=text[:24]), self._refusal(code, message):
                catalog.plants_from_source(text + "\n", mill_id=mill_id, source="s.py")
        origin = catalog._Origin("obs_leftover9", "s.py", 9)
        with self._refusal(FINDING_SOURCE_NOT_PARSEABLE, "s.py[0] is not an object"):
            catalog._spec_from_raw(1, origin, 0, "leftover9")

    def test_plant_rows_refuse_an_unknown_shape_or_missing_key(self):
        row = json.loads((FIXTURE / "hop-plants.jsonl").read_text(encoding="utf-8"))
        loose = dict(row, shape="loose")
        with self._refusal(catalog.FINDING_PLANT_FIELD_INVALID, "p.shape is not a reviewed shape"):
            catalog._plant_from_row(loose, "p")
        trimmed = {key: value for key, value in row.items() if key != "lslug"}
        with self._refusal(catalog.FINDING_PLANT_FIELD_MISSING, "p missing lslug"):
            catalog._plant_from_row(trimmed, "p")

    def test_spec_index_catalog_loads_and_refuses_drifted_pins(self):
        loaded = catalog.load_catalog(self._catalog_copy(specs=_spec_index()))
        self.assertEqual(loaded.leftover_spec_index["total"], 1)
        self.assertEqual(len(loaded.plants), 2)
        cases = (
            (_spec_index(count=2), "obs_leftover9 leftover-spec index does not match"),
            (_spec_index(mill_id="obs_leftover10"), "index mills do not match catalog"),
        )
        for specs, message in cases:
            copy = self._catalog_copy(specs=specs)
            with (
                self.subTest(message=message),
                self._refusal(FINDING_CATALOG_FIELD_INVALID, message),
            ):
                catalog.load_catalog(copy)

    def test_mill_pins_refuse_a_plant_mill_missing_from_the_catalog(self):
        loaded = catalog.load_catalog(FIXTURE)
        with self._refusal(FINDING_CATALOG_FIELD_INVALID, "catalog mills do not match"):
            catalog._refuse_mill_pins(loaded.mills[:2], loaded.plants, None)

    def test_catalog_header_refusals(self):
        cases = (
            (lambda meta: meta.update(format="obs-catalog/0"), "format must be obs-catalog/1"),
            (lambda meta: meta.update(quota_per_round=3), "quota_per_round must be 2"),
        )
        for edit, message in cases:
            copy = self._catalog_copy(edit)
            with (
                self.subTest(message=message),
                self._refusal(FINDING_CATALOG_FIELD_INVALID, message),
            ):
                catalog.load_catalog(copy)
        broken = self._catalog_copy()
        (broken / "CATALOG.json").write_text("{", encoding="utf-8")
        with self._refusal(FINDING_CATALOG_FIELD_INVALID, "CATALOG.json is not strict JSON"):
            catalog.load_catalog(broken)

    def test_job_selection_by_mill_and_with_no_pair_plants(self):
        loaded = catalog.load_catalog(FIXTURE)
        request = generate.GenerateRequest(FIXTURE, Path("unused"), mill_id="obs_r0002")
        selected = generate._selected_plants(loaded, request)
        self.assertEqual(selected, loaded.mill_plants("obs_r0002"))
        specs_only = replace(loaded, plants=loaded.mill_plants("obs_leftover9"))
        everything = generate.GenerateRequest(FIXTURE, Path("unused"), all_plants=True)
        with self._refusal(FINDING_USAGE, "catalog has no hop or leftover3 plants"):
            generate._selected_plants(specs_only, everything)


if __name__ == "__main__":
    unittest.main()
