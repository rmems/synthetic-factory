#!/usr/bin/env python3
"""Focused tests for the read-only public Hugging Face release verifier."""

import hashlib
import json
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
LICENSE_TEXT = (REPO / "LICENSE").read_text(encoding="utf-8")
RAW_BYTES = b'{"synthetic":true}\n'
REVISION = "a" * 40
sys.path.insert(0, str(REPO / "pipelines"))
import verify_hf_release  # noqa: E402


def _card(*, license_name: str = "apache-2.0", include_grok: bool = True) -> str:
    grok = "Grok Build (Grok 4.6(xhigh))" if include_grok else "Grok"
    return f"""---
pretty_name: Example
license: {license_name}
configs:
- config_name: viewer
  data_files:
  - split: train
    path: data/viewer/records.parquet
dataset_info:
- config_name: viewer
  features:
  - name: source_file
    dtype: string
  - name: source_line
    dtype: int64
  - name: record_json
    dtype: string
  splits:
  - name: train
    num_examples: 1
---

> **Release status:** The raw, uncurated payload is published and is not training-ready.

Purpose-specific trajectories for relay-gated state assessment.

## Intended model target

This dataset is designed as one component of **Spikenaut** training.

## Generation attribution

Claude Fable 5 (Ultracode), Meta Muse Spark 1.2, Codex (GPT-5.6-Sol(max)),
and {grok} contributed research, quality-audit, and curation-review work.
Codex contributed curation design, validation, and release engineering.

## Published raw payload

The viewer is data/viewer/records.parquet.

## Links

[Synthetic Data Factory](https://github.com/rmems/synthetic-factory)

## License
"""


def _provenance(*, raw_digest: str | None = None) -> str:
    contributors = [
        {"name": name, "roles": sorted(roles)}
        for name, roles in verify_hf_release.REQUIRED_CONTRIBUTORS.items()
    ]
    return json.dumps(
        {
            "payload_published": True,
            "training_ready": False,
            "contributors": contributors,
            "raw_snapshot": {
                "revision": REVISION,
                "files": [
                    {
                        "path": "data/raw/batch.jsonl",
                        "sha256": raw_digest or hashlib.sha256(RAW_BYTES).hexdigest(),
                    }
                ],
            },
        }
    )


def _parquet_frame(metadata: bytes = b"metadata") -> bytes:
    return b"PAR1" + metadata + len(metadata).to_bytes(4, "little") + b"PAR1"


class ReleaseVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = verify_hf_release.DATASET_REPOS[0]
        self.values = {
            "README.md": _card(),
            "provenance.json": _provenance(),
            "LICENSE": LICENSE_TEXT,
        }

    def text_fetcher(self, url: str, timeout: float) -> str:
        del timeout
        for name, value in self.values.items():
            if url.endswith(f"/{name}"):
                return value
        raise AssertionError(url)

    @staticmethod
    def bytes_fetcher(url: str, timeout: float) -> bytes:
        del timeout
        if url.endswith("/data/viewer/records.parquet"):
            return _parquet_frame()
        if url.endswith(f"/{REVISION}/data/raw/batch.jsonl"):
            return RAW_BYTES
        raise AssertionError(url)

    def verify(self) -> verify_hf_release.CheckResult:
        return verify_hf_release.verify_dataset(
            self.repo,
            text_fetcher=self.text_fetcher,
            bytes_fetcher=self.bytes_fetcher,
        )

    def test_valid_public_release_passes(self) -> None:
        result = self.verify()
        self.assertTrue(result.ok, result.errors)

    def test_license_front_matter_is_required(self) -> None:
        self.values["README.md"] = _card(license_name="mit")
        self.assertIn(
            "README front matter must declare license: apache-2.0", self.verify().errors
        )

    def test_exact_grok_identity_is_required(self) -> None:
        self.values["README.md"] = _card(include_grok=False)
        self.assertIn(
            "README missing required card marker: Grok Build (Grok 4.6(xhigh))",
            self.verify().errors,
        )

    def test_repository_specific_purpose_is_required(self) -> None:
        self.values["README.md"] = _card().replace(
            "relay-gated state assessment", "generic assessment"
        )
        self.assertIn(
            "README missing repository purpose marker: relay-gated state assessment",
            self.verify().errors,
        )

    def test_missing_provenance_role_fails(self) -> None:
        provenance = json.loads(_provenance())
        for contributor in provenance["contributors"]:
            if contributor["name"] == "Grok Build (Grok 4.6(xhigh))":
                contributor["roles"].remove("quality-audit")
        self.values["provenance.json"] = json.dumps(provenance)
        self.assertIn(
            "provenance roles missing for Grok Build (Grok 4.6(xhigh)): quality-audit",
            self.verify().errors,
        )

    def test_incomplete_license_fails(self) -> None:
        self.values["LICENSE"] = "Apache License\nVersion 2.0\n"
        self.assertIn(
            "LICENSE does not match the complete Apache License 2.0 text",
            self.verify().errors,
        )

    def test_raw_snapshot_digest_mismatch_fails(self) -> None:
        self.values["provenance.json"] = _provenance(raw_digest="0" * 64)
        self.assertIn(
            "raw payload digest mismatch for data/raw/batch.jsonl", self.verify().errors
        )

    def test_invalid_parquet_framing_fails(self) -> None:
        def invalid_viewer(url: str, timeout: float) -> bytes:
            if url.endswith("/data/viewer/records.parquet"):
                return b"PAR1not-a-footer"
            return self.bytes_fetcher(url, timeout)

        result = verify_hf_release.verify_dataset(
            self.repo,
            text_fetcher=self.text_fetcher,
            bytes_fetcher=invalid_viewer,
        )
        self.assertIn("viewer projection is missing the Parquet footer magic", result.errors)

    def test_public_url_rejects_other_owners(self) -> None:
        with self.assertRaises(ValueError):
            verify_hf_release.public_url(
                "someone-else/dataset", "README.md", "https://huggingface.co"
            )


if __name__ == "__main__":
    unittest.main()
