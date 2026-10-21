"""Error branches for the dry-run plan and Ollama digest reader."""

import sys
import unittest
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(PIPELINES))

import honest_stop.vocabulary as cv
from honest_stop.generate import dry_run_plan
from honest_stop.ollama import (
    digest_from_show,
    embedding_request,
    perform,
    transport,
    writer_request,
)
from honest_stop.records import build_record

PRODUCED_AT = "2026-10-20T23:00:00Z"


def built(scenario_id: str = "missing-credential") -> dict:
    return build_record(scenario_id, produced_at=PRODUCED_AT, run_seed=1)


class PlanTests(unittest.TestCase):
    def test_dry_run_and_digest_readers_reject_bad_inputs(self):
        self.assertEqual(built()["context"]["scenario_id"], "missing-credential")
        for seed in (True, -1, "1"):
            with self.subTest(seed=seed):
                with self.assertRaises(cv.FamilyError) as caught:
                    dry_run_plan(seed=seed, count=1)
                self.assertEqual(caught.exception.code, "seed")
        for count in (0, 5, True):
            with self.subTest(count=count):
                with self.assertRaises(cv.FamilyError) as caught:
                    dry_run_plan(seed=1, count=count)
                self.assertEqual(caught.exception.code, "count")
        self.assertEqual(writer_request("plan")["body"]["model"], cv.WRITER_MODEL)
        self.assertEqual(embedding_request("task")["body"]["model"], cv.DEDUP_MODEL)
        self.assertIs(transport(), urllib.request.urlopen)
        with self.assertRaises(cv.FamilyError) as caught:
            perform({})
        self.assertEqual(caught.exception.code, "ollama.disabled")
        for document in (None, [], {"digest": "sha256:ab"}, {"digest": "sha256:" + ("A" * 64)}):
            with self.subTest(document=document):
                with self.assertRaises(cv.FamilyError) as caught:
                    digest_from_show(document)
                self.assertEqual(caught.exception.code, "model.digest")


if __name__ == "__main__":
    unittest.main()
