"""Loaded SIR catalogs reject altered metadata and preserve immutable rows."""

import json
import tempfile
import unittest
from pathlib import Path

from pipelines.sir.catalog import load_catalog
from pipelines.sir.catalog_extract import catalog_json_path, pairs_jsonl_path


class SirCatalogIntegrity(unittest.TestCase):
    def test_loader_integer_metadata_rejects_booleans(self):
        for field in ("catalog_first", "n_rounds", "n_rows", "n_hops", "source_lines"):
            with self.subTest(field=field):
                self._assert_catalog_refuses("sir-mill-leftover3-r72", field, False)

    def test_source_derived_metadata_cannot_be_fabricated(self):
        for mill_id in ("sir-mill-leftover3-r72", "sir_r108_leftover3d_mill"):
            for field, value in (("source_lines", 1), ("doc_first_line", "forged description")):
                with self.subTest(mill_id=mill_id, field=field):
                    self._assert_catalog_refuses(mill_id, field, value)

    def test_header_count_and_extraction_claims_are_pinned(self):
        for field in ("n_mills", "n_source_files", "extraction"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                header = json.loads(catalog_json_path().read_bytes())
                header[field] = "publisher was executed" if field == "extraction" else 1
                destination = directory / "CATALOG.json"
                destination.write_text(json.dumps(header), encoding="utf-8")
                (directory / "pairs.jsonl").write_bytes(pairs_jsonl_path().read_bytes())
                with self.assertRaisesRegex(ValueError, field):
                    load_catalog(destination)

    def test_validated_catalog_mappings_cannot_be_changed_after_loading(self):
        catalog = load_catalog()
        mill = next(iter(catalog.mills.values()))
        with self.assertRaises(TypeError):
            catalog.mills[mill.mill_id] = mill
        with self.assertRaises(TypeError):
            mill.pairs[0]["success_slug"] = "forged"

    def test_header_json_refuses_duplicate_keys_and_nonfinite_values(self):
        original = catalog_json_path().read_text(encoding="utf-8")
        mutations = (
            original.replace('"n_mills": 2', '"n_mills": 99, "n_mills": 2'),
            original.replace('"n_mills": 2', '"unsupported": NaN, "n_mills": 2'),
            original.replace('"n_mills": 2', '"unsupported": 1e999, "n_mills": 2'),
        )
        for header in mutations:
            with self.subTest(header=header), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                destination = directory / "CATALOG.json"
                destination.write_text(header, encoding="utf-8")
                (directory / "pairs.jsonl").write_bytes(pairs_jsonl_path().read_bytes())
                with self.assertRaises(ValueError):
                    load_catalog(destination)

    def test_catalog_document_and_mills_require_mapping_shapes(self):
        original = json.loads(catalog_json_path().read_bytes())
        missing = dict(original)
        del missing["mills"]
        documents = [None, [], "catalog", 42, missing]
        documents.extend(dict(original, mills=value) for value in (None, [], "mills", 42))
        malformed_mill = dict(original)
        malformed_mill["mills"] = dict(malformed_mill["mills"])
        malformed_mill["mills"]["sir-mill-leftover3-r72"] = None
        documents.append(malformed_mill)
        for document in documents:
            with self.subTest(document=document), tempfile.TemporaryDirectory() as tmp:
                destination = Path(tmp) / "CATALOG.json"
                destination.write_text(json.dumps(document), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_catalog(destination)

    def test_loader_rejects_valid_string_content_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "CATALOG.json").write_bytes(catalog_json_path().read_bytes())
            lines = pairs_jsonl_path().read_text(encoding="utf-8").splitlines()
            pair = json.loads(lines[1])
            pair["success_url"] = "https://example.invalid/replaced-source"
            lines[1] = json.dumps(pair, separators=(",", ":"))
            (directory / "pairs.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                load_catalog(directory / "CATALOG.json")

    def _assert_catalog_refuses(self, mill_id, field, value):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            header = json.loads(catalog_json_path().read_text(encoding="utf-8"))
            header["mills"][mill_id][field] = value
            destination = directory / "CATALOG.json"
            destination.write_text(json.dumps(header), encoding="utf-8")
            (directory / "pairs.jsonl").write_bytes(pairs_jsonl_path().read_bytes())
            with self.assertRaisesRegex(ValueError, field):
                load_catalog(destination)

    def test_loader_refuses_malformed_hops_with_matching_count(self):
        for hops in ("abcdefghijk", [1] * 11, [""] * 11, ["other"] * 11):
            with self.subTest(hops=hops):
                self._assert_catalog_refuses("sir_r108_leftover3d_mill", "hops", hops)

    def test_loader_refuses_valid_hop_names_that_drift_from_preserved_source(self):
        self._assert_catalog_refuses("sir_r108_leftover3d_mill", "hops", ["forged-factory"] * 11)

    def test_loader_refuses_fabricated_sha256_without_reading_git(self):
        for mill_id in ("sir-mill-leftover3-r72", "sir_r108_leftover3d_mill"):
            with self.subTest(mill_id=mill_id):
                self._assert_catalog_refuses(mill_id, "sha256", "0" * 64)

