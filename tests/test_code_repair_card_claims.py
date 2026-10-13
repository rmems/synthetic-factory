#!/usr/bin/env python3
"""Code-repair Hub card claims are derived from, and checked against, the evidence (#420)."""

import copy
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from code_repair import card_claims as cc  # noqa: E402


def _not_replayed(outcome: str, oracle_status: str, count: int) -> list[dict]:
    return [
        {"record_id": f"{outcome}-{oracle_status}-{i}", "status": "not_replayed",
         "reason": "natural ineligibility", "outcome": outcome, "oracle_status": oracle_status}
        for i in range(count)
    ]


# The counts published on rmems/python-function-repair-20261006 (Hub main 48fbdc4).
REPLAY = {
    "status": "passed",
    "counts": {"records": 132, "positives": 97, "passed": 97, "failed": 0,
               "not_replayed": 35, "failed_by_code": {}},
    "records": [
        *({"record_id": f"pos-{i}", "status": "replayed", "code": "REPLAY_PASSED"}
          for i in range(97)),
        *_not_replayed("rejected", "validated", 18),
        *_not_replayed("rejected", "provisional", 4),
        *_not_replayed("accepted", "provisional", 13),
    ],
}
RUN = {
    "records": 132, "count": 150,
    "catalog": {"catalog_id": "python-repair-v1", "program_count": 197},
    "outcomes": {"accepted": 110, "rejected": 22},
    "oracle_statuses": {"provisional": 17, "validated": 115},
    "skips": {"DUPLICATE_MUTANT_IN_RUN": 18, "MUTATION_NO_SITES": 4},
}

# The card as published: it sells a 97-of-132 replay as the full batch and counts
# the four siteless programs as skipped draws.
OVERCLAIMING_CARD = """# Python Function Repair Records

> **Verification:** every candidate carries its execution evidence and the
> full batch passed independent replay (`evidence/REPLAY.json`: status
> passed).

## Contents

132 candidates (150 requested; 18 duplicate mutants + 4 siteless programs skipped):
"""

# The corrected card proposed in the card-only Hub PR, written by hand.
HONEST_CARD = """# Python Function Repair Records

> **Verification:** every candidate carries its execution evidence, but
> independent replay covered only part of the batch: `evidence/REPLAY.json`
> reports 97 of 132 candidates replayed and passed, 0 failed, and 35 not
> replayed (all 22 rejected rows plus 13 accepted rows whose hidden check was
> unavailable); its overall `status: passed` applies to the replayed subset.
> The 132 rows mix 110 accepted and 22 rejected outcomes, with 115 validated
> and 17 provisional oracle statuses (`evidence/RUN.json`).

## Contents

132 candidates (110 accepted, 22 rejected) from 150 requested draws: 18 draws
were skipped as duplicate mutants; separately, 4 of the 197 catalog programs
have no mutation sites and were excluded from the draw pool:
"""


def rendered_card(replay: dict, run: dict) -> str:
    coverage = cc.replay_coverage(replay)
    return (
        f"{cc.VERIFICATION_MARKER} {cc.verification_statement(coverage)}\n"
        f"> {cc.split_statement(run)}\n\n## Contents\n\n{cc.contents_statement(run)}\n"
    )


def with_failures(replay: dict, failed: int) -> dict:
    """A copy whose first ``failed`` replayed records failed, with counts and status to match."""
    replay = copy.deepcopy(replay)
    replayed = [e for e in replay["records"] if e["status"] == "replayed"]
    for entry in replayed[:failed]:
        entry["code"] = "REPLAY_HASH_MISMATCH"
    replay["counts"].update(passed=len(replayed) - failed, failed=failed)
    replay["status"] = "failed"
    return replay


def fully_replayed_with_failures() -> tuple[dict, dict]:
    replay, run = complete_evidence()
    return with_failures(replay, 2), run


def complete_evidence() -> tuple[dict, dict]:
    replay = {
        "status": "passed",
        "counts": {"records": 3, "positives": 3, "passed": 3, "failed": 0, "not_replayed": 0},
        "records": [
            {"record_id": str(i), "status": "replayed", "code": "REPLAY_PASSED"} for i in range(3)
        ],
    }
    run = {"records": 3, "count": 3, "catalog": {"program_count": 5},
           "outcomes": {"accepted": 3}, "oracle_statuses": {"validated": 3}, "skips": {}}
    return replay, run


class ImportFormTests(unittest.TestCase):
    def test_package_and_direct_forms_are_one_module(self):
        sys.path.insert(0, str(REPO))
        try:
            from pipelines.code_repair import card_claims as packaged
        finally:
            sys.path.remove(str(REPO))
        self.assertIs(packaged, cc)
        self.assertIs(packaged.CardClaimError, cc.CardClaimError)


class ReplayCoverageTests(unittest.TestCase):
    def test_coverage_reads_the_partial_replay_and_its_not_replayed_kinds(self):
        coverage = cc.replay_coverage(REPLAY)
        self.assertFalse(coverage.complete)
        self.assertEqual((coverage.records, coverage.passed, coverage.failed,
                          coverage.not_replayed), (132, 97, 0, 35))
        self.assertEqual(dict(coverage.not_replayed_outcomes), {"accepted": 13, "rejected": 22})
        self.assertEqual(dict(coverage.not_replayed_statuses), {"provisional": 17, "validated": 18})

    def test_counts_that_do_not_add_up_are_refused(self):
        replay = copy.deepcopy(REPLAY)
        replay["counts"]["passed"] = 132
        with self.assertRaisesRegex(cc.CardClaimError, "do not add up"):
            cc.replay_coverage(replay)

    def test_not_replayed_list_must_match_its_count(self):
        replay = copy.deepcopy(REPLAY)
        replay["records"] = replay["records"][:-1]
        with self.assertRaisesRegex(cc.CardClaimError, "lists 34 not_replayed records"):
            cc.replay_coverage(replay)

    def test_non_integer_and_missing_counts_are_refused(self):
        for bad in (True, -1, "97", None):
            replay = copy.deepcopy(REPLAY)
            replay["counts"]["passed"] = bad
            with self.subTest(bad=bad), self.assertRaises(cc.CardClaimError):
                cc.replay_coverage(replay)

    def test_missing_status_or_records_list_is_refused(self):
        for key in ("status", "records"):
            replay = copy.deepcopy(REPLAY)
            del replay[key]
            with self.subTest(key=key), self.assertRaises(cc.CardClaimError):
                cc.replay_coverage(replay)


class RenderedStatementTests(unittest.TestCase):
    def test_partial_replay_statement_states_the_replayed_subset(self):
        text = cc.verification_statement(cc.replay_coverage(REPLAY))
        self.assertIn("97 of 132 candidates replayed and passed, 0 failed", text)
        self.assertIn("35 not replayed (13 accepted and 22 rejected; oracle statuses "
                      "17 provisional and 18 validated)", text)
        self.assertIn("applies to the replayed subset only", text)
        self.assertNotIn("full batch", text)

    def test_complete_replay_statement_says_all(self):
        replay, _run = complete_evidence()
        text = cc.verification_statement(cc.replay_coverage(replay))
        self.assertIn("re-executed all 3 candidates and every one passed", text)

    def test_split_statement_discloses_outcomes_and_oracle_statuses(self):
        self.assertEqual(
            cc.split_statement(RUN),
            "The 132 rows mix 110 accepted and 22 rejected outcomes, with 17 provisional and "
            "115 validated oracle statuses (`evidence/RUN.json`).",
        )

    def test_contents_statement_keeps_pool_exclusions_apart_from_draw_skips(self):
        text = cc.contents_statement(RUN)
        self.assertIn("132 candidates from 150 requested draws "
                      "(18 draws skipped as `DUPLICATE_MUTANT_IN_RUN`)", text)
        self.assertIn("4 of the 197 catalog programs have no mutation sites and were "
                      "excluded from the draw pool, so they used no draws", text)

    def test_fully_replayed_batch_with_failures_states_them(self):
        # Every record replayed, two failed: no not-replayed breakdown to join (CodeAnt on #434).
        replay, run = fully_replayed_with_failures()
        text = cc.verification_statement(cc.replay_coverage(replay))
        self.assertIn("re-executed all 3 candidates: 1 of 3 passed and 2 failed", text)
        self.assertEqual(cc.card_claim_errors(rendered_card(replay, run), replay, run), [])

    def test_contents_statement_without_skips(self):
        _replay, run = complete_evidence()
        self.assertEqual(cc.contents_statement(run),
                         "3 candidates from 3 requested draws (no draws skipped).")


class CardClaimTests(unittest.TestCase):
    def test_overclaiming_card_fails(self):
        errors = cc.card_claim_errors(OVERCLAIMING_CARD, REPLAY, RUN)
        self.assertIn("Card overclaims replay ('full batch passed'): 97 of 132 passed, "
                      "0 failed, 35 not replayed", errors)
        for phrase in ("'97 of 132'", "'35 not replayed'", "'0 failed'", "'13 accepted'"):
            self.assertTrue(any(phrase in e for e in errors), phrase)
        for disclosure in ("110 accepted", "22 rejected", "115 validated", "17 provisional"):
            self.assertTrue(any(disclosure in e for e in errors), disclosure)
        self.assertTrue(any("excluded from the draw pool" in e for e in errors))
        self.assertTrue(any("'4 of the 197 catalog programs'" in e for e in errors))
        self.assertTrue(any("'18 draws'" in e for e in errors))

    def test_hand_written_honest_card_passes(self):
        self.assertEqual(cc.card_claim_errors(HONEST_CARD, REPLAY, RUN), [])

    def test_rendered_card_passes_its_own_check(self):
        self.assertEqual(cc.card_claim_errors(rendered_card(REPLAY, RUN), REPLAY, RUN), [])
        replay, run = complete_evidence()
        self.assertEqual(cc.card_claim_errors(rendered_card(replay, run), replay, run), [])

    def test_all_records_claim_is_an_overclaim_for_a_partial_replay(self):
        card = HONEST_CARD.replace("covered only part of the batch", "covered all 132 records")
        errors = cc.card_claim_errors(card, REPLAY, RUN)
        self.assertTrue(any("'all 132'" in e for e in errors))

    def test_coverage_wording_outside_the_verification_block_is_not_its_claim(self):
        card = HONEST_CARD + (
            "\nA future full batch replay is planned; all 132 rows carry evidence.\n"
        )
        self.assertEqual(cc.card_claim_errors(card, REPLAY, RUN), [])

    def test_pass_overclaim_anywhere_on_the_card_fails(self):
        card = HONEST_CARD + "\nIn short, the full batch passed.\n"
        errors = cc.card_claim_errors(card, REPLAY, RUN)
        self.assertEqual(errors, ["Card overclaims replay ('full batch passed'): 97 of 132 "
                                  "passed, 0 failed, 35 not replayed"])

    def test_parenthesized_draw_skip_reason_stays_with_its_count(self):
        card = HONEST_CARD.replace(
            "18 draws\nwere skipped as duplicate mutants",
            "18 draws (skipped as duplicate mutants)",
        )
        self.assertEqual(cc.card_claim_errors(card, REPLAY, RUN), [])

    def test_draw_skip_count_must_sit_beside_its_own_reason(self):
        card = HONEST_CARD.replace("skipped as duplicate mutants", "skipped as `MUTATION_NO_SITES`")
        expected = (
            "card must state '18 draws' beside its reason ('duplicate_mutant_in_run' or "
            "'duplicate mutant') from evidence/RUN.json"
        )
        self.assertEqual(cc.card_claim_errors(card, REPLAY, RUN), [expected])

    def test_siteless_programs_must_be_the_ones_excluded_from_the_draw_pool(self):
        card = HONEST_CARD.replace(
            "have no mutation sites and were excluded", "were skipped. Others were excluded"
        )
        expected = (
            "card must state '4 of the 197 catalog programs' beside its reason "
            "('excluded from the draw pool') from evidence/RUN.json"
        )
        self.assertEqual(cc.card_claim_errors(card, REPLAY, RUN), [expected])

    def test_indented_quote_does_not_supply_a_contents_phrase(self):
        card = HONEST_CARD.replace("132 candidates (110", "the candidates (110")
        card += "\n  > 132 candidates\n"
        self.assertEqual(cc.card_claim_errors(card, REPLAY, RUN), [
            "card must state '132 candidates' from evidence/RUN.json",
        ])

    def test_failures_must_be_stated(self):
        replay = with_failures(REPLAY, 2)
        card = HONEST_CARD.replace("97 of 132", "95 of 132").replace(
            "status: passed", "status: failed")
        errors = cc.card_claim_errors(card, replay, RUN)
        self.assertEqual(errors, ["Verification must state '2 failed' from evidence/REPLAY.json"])

    def test_replay_status_must_match_the_evidence(self):
        replay = with_failures(REPLAY, 2)
        card = HONEST_CARD.replace("97 of 132", "95 of 132").replace("0 failed", "2 failed")
        self.assertEqual(cc.card_claim_errors(card, replay, RUN),
                         ["Verification must state 'status: failed' from evidence/REPLAY.json"])

    def test_counts_match_whole_numbers_only(self):
        replay = with_failures(REPLAY, 10)
        card = HONEST_CARD.replace("97 of 132", "87 of 132").replace("0 failed", "10 failed")
        card = card.replace("status: passed", "status: failed")
        self.assertEqual(cc.card_claim_errors(card, replay, RUN), [])
        card = card.replace("87 of 132", "97 of 132").replace("status: failed", "status: passed")
        self.assertEqual(cc.card_claim_errors(card, REPLAY, RUN),
                         ["Verification must state '0 failed' from evidence/REPLAY.json"])

    def test_summary_counts_must_match_the_listed_records(self):
        replay = copy.deepcopy(REPLAY)
        replay["records"][0]["code"] = "REPLAY_HASH_MISMATCH"
        with self.assertRaisesRegex(cc.CardClaimError, "lists 96 passed records but counts 97"):
            cc.replay_coverage(replay)
        replay = copy.deepcopy(REPLAY)
        replay["records"].append({"record_id": "x", "status": "skipped"})
        with self.assertRaisesRegex(cc.CardClaimError, "lists 1 malformed records but counts 0"):
            cc.replay_coverage(replay)

    def test_a_later_verification_block_is_checked_too(self):
        card = HONEST_CARD + "\n> **Verification:** the full batch passed.\n"
        errors = cc.card_claim_errors(card, REPLAY, RUN)
        self.assertTrue(any("'full batch passed'" in e for e in errors))

    def test_complete_replay_must_say_all(self):
        replay, run = complete_evidence()
        card = rendered_card(replay, run).replace("all 3 candidates", "the candidates")
        self.assertEqual(cc.card_claim_errors(card, replay, run),
                         ["Verification must state 'all 3' from evidence/REPLAY.json"])

    def test_not_replayed_breakdown_must_be_stated(self):
        card = HONEST_CARD.replace("13 accepted rows", "some accepted rows")
        self.assertEqual(cc.card_claim_errors(card, REPLAY, RUN),
                         ["Verification must state '13 accepted' from evidence/REPLAY.json"])

    def test_produced_candidates_must_be_stated(self):
        card = HONEST_CARD.replace("132 candidates (110", "the candidates (110")
        self.assertEqual(cc.card_claim_errors(card, REPLAY, RUN),
                         ["card must state '132 candidates' from evidence/RUN.json"])

    def test_run_tallies_must_count_every_record(self):
        for key, tally in (("outcomes", {"accepted": 110, "rejected": 21}),
                           ("oracle_statuses", {"provisional": 17, "validated": 116})):
            with self.subTest(key=key), self.assertRaisesRegex(cc.CardClaimError, key):
                cc.card_claim_errors(HONEST_CARD, REPLAY, dict(RUN, **{key: tally}))

    def test_contents_numbers_must_match_the_run(self):
        card = HONEST_CARD.replace("from 150 requested", "from 160 requested")
        self.assertEqual(cc.card_claim_errors(card, REPLAY, RUN),
                         ["card must state '150 requested' from evidence/RUN.json"])

    def test_card_without_a_verification_statement_fails(self):
        errors = cc.card_claim_errors("# Card\n\n110 accepted\n", REPLAY, RUN)
        self.assertIn("card has no '> **Verification:**' statement", errors)

    def test_run_and_replay_of_different_sizes_are_refused(self):
        run = dict(RUN, records=131)
        with self.assertRaisesRegex(cc.CardClaimError, "131 records"):
            cc.card_claim_errors(HONEST_CARD, REPLAY, run)

    def test_malformed_run_tallies_are_refused(self):
        run = dict(RUN, outcomes=["accepted"])
        with self.assertRaisesRegex(cc.CardClaimError, "must be an object of counts"):
            cc.card_claim_errors(HONEST_CARD, REPLAY, run)


if __name__ == "__main__":
    unittest.main()
