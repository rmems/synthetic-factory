#!/usr/bin/env python3
"""Focused tests for the read-only public Hugging Face release verifier."""

import hashlib
import base64
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
LICENSE_TEXT = (REPO / "LICENSE").read_text(encoding="utf-8")
RAW_BYTES = b'{"synthetic":true}\n'
REVISION = "a" * 40
VALID_PARQUET = base64.b64decode(
    "UEFSMRUEFRYVGkwVAhUAEgAACygHAAAAYS5qc29ubBUAFRIVFiwVAhUQFQYVBhw2ACgHYS5qc29ubBgHYS5qc29ubBERAAAACSACAAAAAgEBAgAVBBUQFRRMFQIVABIAAAgcAQAAAAAAAAAVABUSFRYsFQIVEBUGFQYcGAgBAAAAAAAAABgIAQAAAAAAAAAWACgIAQAAAAAAAAAYCAEAAAAAAAAAEREAAAAJIAIAAAACAQECABUEFQwVEEwVAhUAEgAABhQCAAAAe30VABUSFRYsFQIVEBUGFQYcNgAoAnt9GAJ7fRERAAAACSACAAAAAgEBAgAVBBlMNQAYBnNjaGVtYRUGABUMJQIYC3NvdXJjZV9maWxlJQBMHAAAABUEJQIYC3NvdXJjZV9saW5lABUMJQIYC3JlY29yZF9qc29uJQBMHAAAABYCGRwZPCYAHBUMGTUABhAZGAtzb3VyY2VfZmlsZRUCFgIWlgEWngEmPiYIHDYAKAdhLmpzb25sGAdhLmpzb25sEREAGSwVBBUAFQIAFQAVEBUCADwWDhkGGSYAAgAAACYAHBUEGTUABhAZGAtc291cmNlX2xpbmUVAhYCFq8BFsQBJsYBJqYBHGAgBAAAAAAAAABgIAQAAAAAAAAAWACgIAQAAAAAAAAAYCAEAAAAAAAAAEREAGSwVBBUAFQIAFQAVEBUCADwpBhkmAAIAAAAmABwVDBk1AAYQGRgLcmVjb3JkX2pzb24VAhYCFngWgAEmlgMm6gIcNgAoAnt9GAJ7fRERABksFQQVABUCABUAFRAVAgA8FgQZBhkmAAIAAAAWygMWAiYIFuIDABkcGAxBUlJPVzpzY2hlbWEYwAIvLy8vLytnQUFBQVFBQUFBQUFBS0FBd0FCZ0FGQUFnQUNnQUFBQUFCQkFBTUFBQUFDQUFJQUFBQUJBQUlBQUFBQkFBQUFBTUFBQUNFQUFBQU5BQUFBQVFBQUFDWS8vLy9BQUFCQlJBQUFBQWNBQUFBQkFBQUFBQUFBQUFMQUFBQWNtVmpiM0prWDJwemIyNEFpUC8vLzhULy8vOEFBQUVDRUFBQUFDUUFBQUFFQUFBQUFBQUFBQXNBQUFCemIzVnlZMlZmYkdsdVpRQUlBQXdBQ0FBSEFBZ0FBQUFBQUFBQlFBQUFBQkFBRkFBSUFBWUFCd0FNQUFBQUVBQVFBQUFBQUFBQkJSQUFBQUFnQUFBQUJBQUFBQUFBQUFBTEFBQUFjMjkxY21ObFgyWnBiR1VBQkFBRUFBUUFBQUFBQUFBQQAYIHBhcnF1ZXQtY3BwLWFycm93IHZlcnNpb24gMjQuMC4wGTwcAAAcAAAcAAAAAQMAAFBBUjE="
)
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
Do not train on `thought` or `internal_reasoning*`; this raw Hub copy is
evidence only.

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


def _release_status(*, license_name: str | object = "apache-2.0") -> str:
    status = {
        "schema_version": "1.0.0",
        "dataset_id": verify_hf_release.DATASET_REPOS[0],
        "release_stage": "raw_uncurated_public",
        "visibility": "public",
        "payload_published": True,
        "training_ready": False,
        "license": license_name,
    }
    if license_name is None:
        del status["license"]
    return json.dumps(status)


class ReleaseVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = verify_hf_release.DATASET_REPOS[0]
        self.values = {
            "README.md": _card(),
            "provenance.json": _provenance(),
            "LICENSE": LICENSE_TEXT,
            "release-status.json": _release_status(),
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
            return VALID_PARQUET
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

    def test_single_quoted_license_front_matter_is_supported(self) -> None:
        self.values["README.md"] = _card(license_name="'apache-2.0'")
        self.assertTrue(self.verify().ok, self.verify().errors)

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

    def test_purpose_may_follow_research_only_blockquotes_and_headings(self) -> None:
        """The 2026-08-31 Hub reframe put rights prose before the purpose sentence."""

        self.values["README.md"] = _card().replace(
            "> **Release status:** The raw, uncurated payload is published "
            "and is not training-ready.\n\n"
            "Purpose-specific trajectories for relay-gated state assessment.\n",
            "> **Rights & intended use:** public research corpus, not "
            "training data.\n\n"
            "> **Release status:** The raw, uncurated payload is published "
            "and is not training-ready.\n\n"
            "## Rights and intended use\n\n"
            "Purpose-specific trajectories for relay-gated state assessment.\n",
        )
        self.assertTrue(self.verify().ok, self.verify().errors)

    def test_purpose_marker_in_html_comment_does_not_count(self) -> None:
        self.values["README.md"] = _card().replace(
            "Purpose-specific trajectories for relay-gated state assessment.\n",
            "<!-- Purpose-specific trajectories for relay-gated state "
            "assessment. -->\n",
        )
        self.assertIn(
            "README missing repository purpose marker: relay-gated state assessment",
            self.verify().errors,
        )

    def test_hidden_reasoning_warning_is_required_on_the_card(self) -> None:
        self.values["README.md"] = _card().replace(
            "Do not train on `thought` or `internal_reasoning*`; this raw Hub copy is\n"
            "evidence only.\n",
            "",
        )
        self.assertIn(
            "README missing required card marker: "
            "Do not train on `thought` or `internal_reasoning*`",
            self.verify().errors,
        )

    def test_hidden_reasoning_warning_must_sit_in_the_payload_section(self) -> None:
        self.values["README.md"] = _card().replace(
            "## Published raw payload",
            "## Notes\nDo not train on `thought` or `internal_reasoning*`; this raw\n"
            "Hub copy is evidence only.\n\n## Published raw payload",
        ).replace(
            "The viewer is data/viewer/records.parquet.\n"
            "Do not train on `thought` or `internal_reasoning*`; this raw Hub copy is\n"
            "evidence only.\n",
            "The viewer is data/viewer/records.parquet.\n",
        )
        self.assertIn(
            "README missing required card marker: "
            "Do not train on `thought` or `internal_reasoning*`",
            self.verify().errors,
        )

    def test_hidden_reasoning_warning_in_html_comment_does_not_count(self) -> None:
        self.values["README.md"] = _card().replace(
            "Do not train on `thought` or `internal_reasoning*`; this raw Hub copy is\n"
            "evidence only.\n",
            "<!-- Do not train on `thought` or `internal_reasoning*`; this raw Hub "
            "copy is\nevidence only. -->\n",
        )
        errors = self.verify().errors
        self.assertIn(
            "README missing required card marker: "
            "Do not train on `thought` or `internal_reasoning*`",
            errors,
        )
        self.assertIn(
            "README missing required card marker: raw Hub copy is evidence only",
            errors,
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

    def test_undeclared_release_status_license_fails(self) -> None:
        self.values["release-status.json"] = _release_status(
            license_name="not_yet_declared"
        )
        self.assertIn(
            "release-status.json leaves the license undeclared: 'not_yet_declared'; "
            "LICENSE and the card declare 'apache-2.0'",
            self.verify().errors,
        )

    def test_release_status_license_must_match_card_and_license_file(self) -> None:
        self.values["release-status.json"] = _release_status(license_name="cc-by-4.0")
        self.assertIn(
            "release-status.json declares license 'cc-by-4.0', "
            "but LICENSE and the card declare 'apache-2.0'",
            self.verify().errors,
        )

    def test_release_status_license_is_case_and_space_insensitive(self) -> None:
        self.values["release-status.json"] = _release_status(
            license_name="  Apache-2.0  "
        )
        self.assertTrue(self.verify().ok, self.verify().errors)

    def test_release_status_must_match_raw_publication_contract(self) -> None:
        cases = (
            (
                "release_stage",
                "curated_public",
                "release-status.json must declare release_stage: raw_uncurated_public",
            ),
            (
                "visibility",
                "private",
                "release-status.json must declare visibility: public",
            ),
            (
                "payload_published",
                False,
                "release-status.json must mark payload_published true",
            ),
            (
                "training_ready",
                True,
                "release-status.json must mark training_ready false",
            ),
        )
        for field, invalid, expected_error in cases:
            with self.subTest(field=field):
                status = json.loads(_release_status())
                status[field] = invalid
                self.values["release-status.json"] = json.dumps(status)
                self.assertIn(expected_error, self.verify().errors)

    def test_missing_release_status_license_fails(self) -> None:
        self.values["release-status.json"] = _release_status(license_name=None)
        self.assertIn(
            "release-status.json must declare a string license", self.verify().errors
        )

    def test_non_string_release_status_license_fails(self) -> None:
        self.values["release-status.json"] = _release_status(license_name=42)
        self.assertIn(
            "release-status.json must declare a string license", self.verify().errors
        )

    def test_non_object_release_status_fails_without_crashing(self) -> None:
        self.values["release-status.json"] = "[]"
        result = self.verify()
        self.assertIn("release-status.json must contain a JSON object", result.errors)

    def test_invalid_release_status_json_fails(self) -> None:
        self.values["release-status.json"] = "{"
        errors = self.verify().errors
        self.assertTrue(
            any(error.startswith("release-status.json is invalid JSON:") for error in errors),
            errors,
        )

    def test_release_status_dataset_id_must_match_the_repository(self) -> None:
        status = json.loads(_release_status())
        status["dataset_id"] = verify_hf_release.DATASET_REPOS[1]
        self.values["release-status.json"] = json.dumps(status)
        self.assertIn(
            f"release-status.json dataset_id must be {self.repo}",
            self.verify().errors,
        )

    def test_duplicate_release_status_license_fails(self) -> None:
        self.values["release-status.json"] = (
            '{"license":"not_yet_declared","license":"apache-2.0"}'
        )
        self.assertIn(
            "release-status.json must not contain duplicate license keys",
            self.verify().errors,
        )

    def test_unrecognized_license_text_still_pins_the_expected_family(self) -> None:
        self.values["LICENSE"] = "Some other license\n"
        self.values["README.md"] = _card(license_name="mit")
        self.values["release-status.json"] = _release_status(license_name="mit")
        errors = self.verify().errors
        self.assertIn(
            "LICENSE does not match the complete Apache License 2.0 text", errors
        )
        self.assertIn("README front matter must declare license: apache-2.0", errors)
        self.assertIn(
            "release-status.json declares license 'mit', "
            "but LICENSE and the card declare 'apache-2.0'",
            errors,
        )

    def test_raw_snapshot_digest_mismatch_fails(self) -> None:
        self.values["provenance.json"] = _provenance(raw_digest="0" * 64)
        self.assertIn(
            "raw payload digest mismatch for data/raw/batch.jsonl", self.verify().errors
        )

    def test_non_object_provenance_fails_without_crashing(self) -> None:
        self.values["provenance.json"] = "[]"
        result = self.verify()
        self.assertIn("provenance.json must contain a JSON object", result.errors)

    def test_required_card_markers_must_be_in_owned_sections(self) -> None:
        self.values["README.md"] = _card().replace(
            "Grok Build (Grok 4.6(xhigh))", "Grok Build (Grok 4.6(xhigh))"
        ).replace(
            "## Generation attribution",
            "## Notes\nGrok Build (Grok 4.6(xhigh))\n\n## Generation attribution",
        ).replace(
            "Grok Build (Grok 4.6(xhigh)) contributed",
            "Grok Build contributed",
        )
        result = self.verify()
        self.assertIn(
            "README missing required card marker: Grok Build (Grok 4.6(xhigh))",
            result.errors,
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

    def test_parquet_schema_is_required(self) -> None:
        invalid = VALID_PARQUET.replace(b"source_line", b"other_field")

        def invalid_viewer(url: str, timeout: float) -> bytes:
            if url.endswith("/data/viewer/records.parquet"):
                return invalid
            return self.bytes_fetcher(url, timeout)

        result = verify_hf_release.verify_dataset(
            self.repo,
            text_fetcher=self.text_fetcher,
            bytes_fetcher=invalid_viewer,
        )
        self.assertIn("viewer projection missing required column: source_line", result.errors)

    def test_front_matter_source_file_marker_keeps_underscore(self) -> None:
        self.values["README.md"] = _card().replace(
            "- name: source_file\n", "- name: sourcefile\n"
        )
        self.assertIn(
            "README missing required card marker: name: source_file",
            self.verify().errors,
        )

    def test_payload_disclosure_rejects_negated_wrap_schema(self) -> None:
        self.repo = "rmems/multi-agent-ouroboros-swarm"
        card = _card().replace(
            "Purpose-specific trajectories for relay-gated state assessment.",
            "Purpose-specific safety-gate adjudication trajectories.",
        ).replace(
            "designed as one component of **Spikenaut** training",
            "not labeled as Spikenaut training data",
        ).replace(
            "The viewer is data/viewer/records.parquet.\n",
            "The viewer is data/viewer/records.parquet.\n"
            "These records are not a thalamic-gate wrap schema. "
            "7 of the 14 records are wrap-only; the rest live in "
            "sidecars, not JSONL training records.\n",
        )
        self.values["README.md"] = card
        self.values["release-status.json"] = _release_status()
        result = verify_hf_release.verify_dataset(
            self.repo,
            text_fetcher=self.text_fetcher,
            bytes_fetcher=self.bytes_fetcher,
        )
        self.assertIn(
            "README retains obsolete payload-kind claim: "
            "not a thalamic-gate wrap schema",
            result.errors,
        )

    def test_public_url_rejects_other_owners(self) -> None:
        with self.assertRaises(ValueError):
            verify_hf_release.public_url(
                "someone-else/dataset", "README.md", "https://huggingface.co"
            )


CODE_REPAIR_REPO = "rmems/python-function-repair-20261006"
REPLAY_EVIDENCE = {
    "status": "passed",
    "counts": {"records": 3, "positives": 2, "passed": 2, "failed": 0, "not_replayed": 1},
    "records": [
        {"record_id": "a", "status": "replayed", "code": "REPLAY_PASSED"},
        {"record_id": "b", "status": "replayed", "code": "REPLAY_PASSED"},
        {"record_id": "c", "status": "not_replayed", "outcome": "rejected",
         "oracle_status": "validated"},
    ],
}
RUN_EVIDENCE = {
    "records": 3, "count": 3, "catalog": {"program_count": 4},
    "outcomes": {"accepted": 2, "rejected": 1},
    "oracle_statuses": {"validated": 3}, "skips": {},
}
HONEST_REPLAY_CARD = """# Card

> **Verification:** independent replay covered only part of the batch: 2 of 3
> candidates replayed and passed, 0 failed, and 1 not replayed (the rejected row); its
> overall `status: passed` applies to the replayed subset.
> The rows mix 2 accepted and 1 rejected outcomes, with 3 validated oracle statuses.

3 candidates from 3 requested draws.
"""


class ReplayClaimVerifierTests(unittest.TestCase):
    """Issue #420: a code-repair card may claim no more replay than its evidence shows."""

    def setUp(self) -> None:
        self.files = {
            "README.md": HONEST_REPLAY_CARD,
            "evidence/REPLAY.json": json.dumps(REPLAY_EVIDENCE),
            "evidence/RUN.json": json.dumps(RUN_EVIDENCE),
        }

    def text_fetcher(self, url: str, timeout: float) -> str:
        prefix = f"https://huggingface.co/datasets/{CODE_REPAIR_REPO}/raw/main/"
        self.assertTrue(url.startswith(prefix), url)
        return self.files[url.removeprefix(prefix)]

    def verify(self) -> verify_hf_release.CheckResult:
        return verify_hf_release.verify_replay_claims(
            CODE_REPAIR_REPO, text_fetcher=self.text_fetcher
        )

    def test_code_repair_release_is_verified_by_its_evidence(self) -> None:
        self.assertIn(CODE_REPAIR_REPO, verify_hf_release.REPLAY_CLAIM_REPOS)
        self.assertNotIn(CODE_REPAIR_REPO, verify_hf_release.DATASET_REPOS)

    def test_honest_card_passes(self) -> None:
        self.assertEqual(self.verify().errors, ())

    def test_full_batch_overclaim_fails(self) -> None:
        self.files["README.md"] = (
            "> **Verification:** every candidate carries its execution evidence and the\n"
            "> full batch passed independent replay (`evidence/REPLAY.json`: status\n"
            "> passed). 2 accepted, 1 rejected, 3 validated.\n"
        )
        result = self.verify()
        self.assertFalse(result.ok)
        self.assertIn(
            "Card overclaims replay ('full batch passed'): 2 of 3 passed, 0 failed, "
            "1 not replayed",
            result.errors,
        )
        self.assertIn(
            "Verification must state '2 of 3' from evidence/REPLAY.json", result.errors
        )

    def test_invalid_evidence_json_fails_closed(self) -> None:
        self.files["evidence/REPLAY.json"] = "{"
        self.assertEqual(len(self.verify().errors), 1)
        self.assertIn("evidence/REPLAY.json is invalid JSON", self.verify().errors[0])
        self.files["evidence/REPLAY.json"] = "[]"
        self.assertIn("must contain a JSON object", self.verify().errors[0])

    def test_self_contradicting_evidence_fails_closed(self) -> None:
        self.files["evidence/RUN.json"] = json.dumps(dict(RUN_EVIDENCE, records=4))
        self.assertIn("evidence cannot support a card claim", self.verify().errors[0])

    def test_fetch_failure_is_reported(self) -> None:
        def failing(url: str, timeout: float) -> str:
            raise OSError("offline")

        result = verify_hf_release.verify_replay_claims(
            CODE_REPAIR_REPO, text_fetcher=failing
        )
        self.assertEqual(result.errors, ("public fetch failed: offline",))

    def test_unexpected_fetch_errors_are_not_swallowed(self) -> None:
        def broken(url: str, timeout: float) -> str:
            raise KeyError("bug in the fetcher")

        with self.assertRaises(KeyError):
            verify_hf_release.verify_replay_claims(CODE_REPAIR_REPO, text_fetcher=broken)

    def test_repositories_dispatch_to_their_contract(self) -> None:
        dataset_repo = verify_hf_release.DATASET_REPOS[0]
        with (
            mock.patch.object(verify_hf_release, "verify_replay_claims") as claims,
            mock.patch.object(verify_hf_release, "verify_dataset") as dataset,
        ):
            verify_hf_release.verify_repositories((CODE_REPAIR_REPO, dataset_repo))
        self.assertEqual(claims.call_args_list, [mock.call(CODE_REPAIR_REPO, timeout=30.0)])
        self.assertEqual(dataset.call_args_list, [mock.call(dataset_repo, timeout=30.0)])


class ParquetFooterReaderTests(unittest.TestCase):
    def test_skip_reads_fixed_width_fields(self) -> None:
        reader = verify_hf_release._CompactReader(bytes(9))
        reader.skip(reader.BOOLEAN_TRUE)  # the value rides in the type nibble
        self.assertEqual(reader.offset, 0)
        reader.skip(reader.BYTE)
        self.assertEqual(reader.offset, 1)
        reader.skip(reader.DOUBLE)
        self.assertEqual(reader.offset, 9)

    def test_truncated_footer_metadata_is_reported(self) -> None:
        footer = bytes([0x15])  # field 1, type I32, with its varint missing
        viewer = b"PAR1" + footer + len(footer).to_bytes(4, "little") + b"PAR1"
        errors = verify_hf_release._viewer_errors(_card(), viewer)
        self.assertTrue(
            any("invalid Parquet footer metadata" in error for error in errors), errors
        )


def run_cli(argv: list[str], ok: bool) -> tuple[int, list[str]]:
    """Run the verifier CLI with every repository check stubbed; return exit code and repos."""
    calls: list[str] = []

    def fake(repo: str, *, timeout: float) -> verify_hf_release.CheckResult:
        calls.append(repo)
        return verify_hf_release.CheckResult(repo, () if ok else ("bad card",))

    with (
        mock.patch.object(verify_hf_release, "verify_repository", side_effect=fake),
        mock.patch("sys.stdout", new_callable=io.StringIO),
        mock.patch("sys.stderr", new_callable=io.StringIO),
    ):
        code = verify_hf_release.main(argv)
    return code, calls


class VerifierCliTests(unittest.TestCase):
    def test_default_run_covers_only_releases_that_pass_today(self) -> None:
        # The code-repair card still overclaims on the Hub (#420), so it is checked on
        # request until its card-only fix merges; the default run must stay green.
        code, calls = run_cli([], ok=True)
        self.assertEqual(code, 0)
        self.assertEqual(calls, list(verify_hf_release.DATASET_REPOS))
        self.assertNotIn(CODE_REPAIR_REPO, verify_hf_release.DEFAULT_REPOS)

    def test_code_repair_release_can_be_selected_and_fails_the_run(self) -> None:
        code, calls = run_cli(["--repo", CODE_REPAIR_REPO], ok=False)
        self.assertEqual((code, calls), (1, [CODE_REPAIR_REPO]))


if __name__ == "__main__":
    unittest.main()
