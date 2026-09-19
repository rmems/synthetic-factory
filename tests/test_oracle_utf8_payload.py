"""Manifest byte authentication does not authorize alternate JSON encodings."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
import oracle_validate
from test_oracle_grounded_cli import build, canon, families, write_test_manifest


class OracleUtf8PayloadTests(unittest.TestCase):
    def test_manifested_utf16_or_utf32_record_without_final_lf_is_rejected(self):
        item = build(families.ENCODER_FAMILY)
        text = canon.dumps_record(item)
        for encoding in ("utf-16", "utf-16-le", "utf-16-be", "utf-32"):
            with self.subTest(encoding=encoding), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                relative = f"{families.ENCODER_FAMILY}/accepted-r01.jsonl"
                path = root / relative
                path.parent.mkdir()
                path.write_text(text, encoding="utf-8")
                write_test_manifest(root)
                baseline, findings = oracle_validate.validate_run(root)
                self.assertEqual(findings, [])
                self.assertEqual(baseline["accepted"], 1)

                payload = text.encode(encoding)
                path.write_bytes(payload)
                manifest_path = root / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["files"][relative]["sha256"] = hashlib.sha256(payload).hexdigest()
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                self.assertEqual(oracle_validate.authenticate_manifest(root)[2], [])

                report, findings = oracle_validate.validate_run(root)
                self.assertEqual(report["parse_failures"], 1)
                self.assertEqual(report["accepted"], 0)
                self.assertTrue(any("JSON parse error" in error for error in findings), findings)


if __name__ == "__main__":
    unittest.main()
