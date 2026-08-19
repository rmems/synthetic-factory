#!/usr/bin/env python3
"""Focused tests for the read-only public Hugging Face release verifier."""

import json
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
import verify_hf_release  # noqa: E402


def _card(license_name="apache-2.0", include_grok=True):
    grok = "Grok Build (Grok 4.6(xhigh))" if include_grok else "Grok"
    return f"""---
pretty_name: Example
license: {license_name}
configs:
- config_name: viewer
  data_files:
  - split: train
    path: data/viewer/records.parquet
---

Claude Fable 5 (Ultracode)
Meta Muse Spark 1.2
Codex (GPT-5.6-Sol(max))
{grok}
This raw release is not training-ready.
"""


def _provenance():
    contributors = []
    for name, roles in verify_hf_release.REQUIRED_CONTRIBUTORS.items():
        contributors.append({"name": name, "roles": sorted(roles)})
    return json.dumps(
        {
            "payload_published": True,
            "training_ready": False,
            "contributors": contributors,
        }
    )


class ReleaseVerifierTests(unittest.TestCase):
    def setUp(self):
        self.repo = verify_hf_release.DATASET_REPOS[0]
        self.values = {
            "README.md": _card(),
            "provenance.json": _provenance(),
            "LICENSE": "Apache License\nVersion 2.0, January 2004\n",
        }

    def text_fetcher(self, url, timeout):
        del timeout
        for name, value in self.values.items():
            if url.endswith(f"/{name}"):
                return value
        raise AssertionError(url)

    @staticmethod
    def bytes_fetcher(url, timeout):
        del timeout
        if url.endswith("/data/viewer/records.parquet"):
            return b"PAR1projection"
        raise AssertionError(url)

    def test_valid_public_release_passes(self):
        result = verify_hf_release.verify_dataset(
            self.repo,
            text_fetcher=self.text_fetcher,
            bytes_fetcher=self.bytes_fetcher,
        )
        self.assertTrue(result.ok, result.errors)

    def test_license_front_matter_is_required(self):
        self.values["README.md"] = _card(license_name="mit")
        result = verify_hf_release.verify_dataset(
            self.repo,
            text_fetcher=self.text_fetcher,
            bytes_fetcher=self.bytes_fetcher,
        )
        self.assertIn(
            "README front matter must declare license: apache-2.0", result.errors
        )

    def test_exact_grok_identity_is_required(self):
        self.values["README.md"] = _card(include_grok=False)
        result = verify_hf_release.verify_dataset(
            self.repo,
            text_fetcher=self.text_fetcher,
            bytes_fetcher=self.bytes_fetcher,
        )
        self.assertIn(
            "README missing required text: Grok Build (Grok 4.6(xhigh))",
            result.errors,
        )

    def test_missing_provenance_role_fails(self):
        provenance = json.loads(_provenance())
        for contributor in provenance["contributors"]:
            if contributor["name"] == "Grok Build (Grok 4.6(xhigh))":
                contributor["roles"].remove("quality-audit")
        self.values["provenance.json"] = json.dumps(provenance)
        result = verify_hf_release.verify_dataset(
            self.repo,
            text_fetcher=self.text_fetcher,
            bytes_fetcher=self.bytes_fetcher,
        )
        self.assertIn(
            "provenance roles missing for Grok Build (Grok 4.6(xhigh)): quality-audit",
            result.errors,
        )

    def test_public_url_rejects_other_owners(self):
        with self.assertRaises(ValueError):
            verify_hf_release.public_url(
                "someone-else/dataset", "README.md", "https://huggingface.co"
            )


if __name__ == "__main__":
    unittest.main()
