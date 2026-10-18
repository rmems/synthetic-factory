"""The release verifier's ``rights.json`` sidecar cross-checks.

``verify_dataset`` also enforces the configured repositories' card contract, so
these fixtures reuse the first configured repository name for both routes; the
rights checks under test depend only on the sidecar and ``release-status.json``.
"""

from __future__ import annotations

import json
import multiprocessing
import sys
import unittest
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parent
for _path in (TESTS, ROOT / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import rights_import_probe
import verify_hf_release
import verify_hf_release_rights
from test_rights_document import anthropic_document
from test_rights_document_procedural import repair_document
from test_verify_hf_release import (
    LICENSE_TEXT,
    RAW_BYTES,
    REVISION,
    VALID_PARQUET,
    _card,
    _provenance,
)

REPO = verify_hf_release.DATASET_REPOS[0]
RIGHTS_URL_SUFFIX = "/raw/main/rights.json"


def procedural_sidecar(**changes: object) -> dict[str, object]:
    document = repair_document()
    document["dataset_id"] = REPO
    document.update(changes)
    return document


def hosted_sidecar(**changes: object) -> dict[str, object]:
    document = anthropic_document()
    document["dataset_id"] = REPO
    document.update(changes)
    return document


def release_status(**changes: object) -> dict[str, object]:
    status: dict[str, object] = {
        "schema_version": "1.0.0",
        "dataset_id": REPO,
        "release_stage": "raw_uncurated_public",
        "visibility": "public",
        "payload_published": True,
        "training_ready": False,
        "license": "apache-2.0",
        "intended_use": "training_candidate",
        "project_training_policy": "allowed",
        "rights_record": "rights.json",
    }
    status.update(changes)
    return status


class RightsSidecarVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.texts = {
            "README.md": _card(),
            "provenance.json": _provenance(),
            "LICENSE": LICENSE_TEXT,
            "release-status.json": json.dumps(release_status()),
        }
        self.rights: bytes | Exception = json.dumps(procedural_sidecar()).encode("utf-8")
        self.rights_fetches = 0

    def text_fetcher(self, url: str, _timeout: float) -> str:
        for name, value in self.texts.items():
            if url.endswith(f"/raw/main/{name}"):
                return value
        raise AssertionError(url)

    def bytes_fetcher(self, url: str, _timeout: float) -> bytes:
        if url.endswith("/data/viewer/records.parquet"):
            return VALID_PARQUET
        if url.endswith(f"/{REVISION}/data/raw/batch.jsonl"):
            return RAW_BYTES
        if url.endswith(RIGHTS_URL_SUFFIX):
            self.rights_fetches += 1
            if isinstance(self.rights, Exception):
                raise self.rights
            return self.rights
        raise AssertionError(url)

    def set_status(self, status: dict[str, object]) -> None:
        self.texts["release-status.json"] = json.dumps(status)

    def set_rights(self, document: dict[str, object]) -> None:
        self.rights = json.dumps(document, ensure_ascii=False).encode("utf-8")

    def errors(self) -> tuple[str, ...]:
        return verify_hf_release.verify_dataset(
            REPO, text_fetcher=self.text_fetcher, bytes_fetcher=self.bytes_fetcher
        ).errors

    def test_declared_procedural_sidecar_that_agrees_passes(self) -> None:
        self.assertEqual(self.errors(), ())
        self.assertEqual(self.rights_fetches, 1)

    def test_declared_hosted_sidecar_that_agrees_passes(self) -> None:
        self.set_rights(hosted_sidecar())
        self.set_status(
            release_status(intended_use="research_only", project_training_policy="blocked")
        )
        self.assertEqual(self.errors(), ())
        self.assertEqual(self.rights_fetches, 1)

    def test_release_without_a_rights_record_is_not_fetched_or_checked(self) -> None:
        self.rights = AssertionError("an undeclared sidecar must not be fetched")
        absent = release_status()
        del absent["rights_record"]
        for status in (release_status(rights_record=None), absent):
            self.set_status(status)
            with self.subTest(status=status.get("rights_record", "absent")):
                self.assertEqual(self.errors(), ())
        self.assertEqual(self.rights_fetches, 0)

    def test_any_other_rights_record_fails_closed_without_a_fetch(self) -> None:
        for record in ("RIGHTS.json", "data/rights.json", True, ["rights.json"]):
            self.set_status(release_status(rights_record=record))
            with self.subTest(record=record):
                self.assertIn(
                    'release-status.json rights_record must be null or "rights.json"',
                    self.errors(),
                )
        self.assertEqual(self.rights_fetches, 0)

    def test_declared_sidecar_that_cannot_be_fetched_fails_the_repository(self) -> None:
        self.rights = OSError("HTTP Error 404: Not Found")
        errors = self.errors()
        self.assertEqual(len(errors), 1)
        self.assertRegex(errors[0], r"^public fetch failed: .*404")

    def test_invalid_sidecar_is_reported(self) -> None:
        cases = (
            b"{not json",
            json.dumps(procedural_sidecar(catalog_sha256="0" * 64)).encode(),
            json.dumps(procedural_sidecar(path_id="thalamic-relay-factory")).encode(),
            json.dumps(hosted_sidecar(schema_version="0.2.0")).encode(),
        )
        for payload in cases:
            self.rights = payload
            with self.subTest(payload=payload[:40]):
                errors = self.errors()
                self.assertEqual(len(errors), 1, errors)
                self.assertTrue(
                    errors[0].startswith("shipped rights sidecar is invalid: rights.json:"),
                    errors,
                )

    def test_sidecar_must_name_the_repository(self) -> None:
        self.set_rights(procedural_sidecar(dataset_id="rmems/python-function-repair-20261006"))
        self.assertEqual(self.errors(), (f"rights.json dataset_id must be {REPO}",))

    def test_public_decision_must_agree_with_release_status(self) -> None:
        self.set_status(
            release_status(intended_use="research_only", project_training_policy="blocked")
        )
        self.assertEqual(
            self.errors(),
            (
                (
                    'rights.json declares intended_use "training_candidate", '
                    'but release-status.json declares "research_only"'
                ),
                (
                    'rights.json declares project_training_policy "allowed", '
                    'but release-status.json declares "blocked"'
                ),
            ),
        )

    def test_hosted_decision_must_agree_with_release_status(self) -> None:
        self.set_rights(hosted_sidecar())
        self.assertIn(
            'rights.json declares intended_use "research_only", '
            'but release-status.json declares "training_candidate"',
            self.errors(),
        )

    def test_decision_fields_release_status_omits_are_not_invented(self) -> None:
        status = release_status()
        del status["intended_use"], status["project_training_policy"]
        self.set_status(status)
        self.assertEqual(self.errors(), ())

    def test_procedural_release_license_must_match_the_card(self) -> None:
        self.texts["README.md"] = _card(license_name="mit")
        self.assertIn(
            'rights.json declares release_license "apache-2.0", '
            'but the card front matter declares "mit"',
            self.errors(),
        )

    def test_procedural_release_license_must_match_release_status(self) -> None:
        for license_name, shown in (("mit", '"mit"'), (None, "null"), (7, "null")):
            self.set_status(release_status(license=license_name))
            with self.subTest(license=license_name):
                self.assertIn(
                    'rights.json declares release_license "apache-2.0", '
                    f"but release-status.json declares {shown}",
                    self.errors(),
                )

    def test_procedural_release_license_must_match_the_license_text(self) -> None:
        self.texts["LICENSE"] = LICENSE_TEXT.replace("Apache License", "Other License")
        self.assertIn(
            'rights.json declares release_license "apache-2.0", but LICENSE declares null',
            self.errors(),
        )

    def test_release_license_comparison_tolerates_case_and_space_like_the_card_check(
        self,
    ) -> None:
        self.texts["README.md"] = _card(license_name="'Apache-2.0'")
        self.set_status(release_status(license=" Apache-2.0 "))
        self.assertEqual(self.errors(), ())

    def test_procedural_training_ready_must_match_release_status(self) -> None:
        for value in (True, "false", None):
            self.set_status(release_status(training_ready=value))
            with self.subTest(training_ready=value):
                self.assertIn(
                    "rights.json declares training_ready false, "
                    "but release-status.json does not",
                    self.errors(),
                )

    def test_duplicate_rights_keys_in_release_status_fail(self) -> None:
        text = json.dumps(release_status())
        for field, value in (
            ("rights_record", '"rights.json"'),
            ("intended_use", '"training_candidate"'),
            ("project_training_policy", '"allowed"'),
        ):
            self.texts["release-status.json"] = text[:-1] + f', "{field}": {value}}}'
            with self.subTest(field=field):
                self.assertIn(
                    f"release-status.json must not contain duplicate {field} keys",
                    self.errors(),
                )

    def test_declared_but_unfetched_sidecar_is_refused_by_the_checker(self) -> None:
        self.assertEqual(
            verify_hf_release_rights.rights_sidecar_errors(
                REPO,
                release_status(),
                None,
                verify_hf_release_rights.LicenseDeclarations("apache-2.0", "apache-2.0"),
            ),
            ["release-status.json declares rights.json, but it was not fetched"],
        )


class RightsSidecarImportFormTests(unittest.TestCase):
    def test_package_and_cli_forms_bind_one_module_in_either_order(self) -> None:
        # Fresh spawned interpreters, so nothing this suite imported can mask a
        # split; the module preludes alone bind the twins.
        context = multiprocessing.get_context("spawn")
        for first in ("cli", "package"):
            with (
                self.subTest(first_form=first),
                ProcessPoolExecutor(max_workers=1, mp_context=context) as pool,
            ):
                split = pool.submit(rights_import_probe.split_twins, first).result(timeout=180)
                self.assertEqual(split, [])


if __name__ == "__main__":
    unittest.main()
