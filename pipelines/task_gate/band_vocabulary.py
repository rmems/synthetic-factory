#!/usr/bin/env python3
"""Names of the difficulty-band stage: formats, files, band verdicts, limits and refusal codes.

No logic. The stage runs after the task gate (``kept`` rows of ``tasks.jsonl``) and measures
how hard each verified task is for the current student before it can enter a training set.
"""

from __future__ import annotations

from ._contract import bind_import_twin

BAND_FORMAT = "difficulty-band/1"
CONTRACT_FORMAT = "difficulty-band-contract/1"
ROW_FORMAT = "difficulty-band-row/1"
SUMMARY_FORMAT = "difficulty-band-summary/1"

ROWS_FILENAME = "band-rows.jsonl"
KEPT_FILENAME = "band-kept.jsonl"
SEED_NEEDED_FILENAME = "seed_needed.jsonl"
SUMMARY_FILENAME = "band-summary.json"

BAND_KEPT = "band_kept"
BAND_TOO_EASY = "too_easy"
BAND_TOO_HARD = "too_hard"
BAND_SEED_NEEDED = "seed_needed"
BANDS = (BAND_KEPT, BAND_TOO_EASY, BAND_TOO_HARD, BAND_SEED_NEEDED)

GENERATOR_SELF = "self"

MIN_ATTEMPTS = 2
MAX_ATTEMPTS = 64
MAX_CONTRACT_BYTES = 1 << 16
MAX_TASKS_BYTES = 256 << 20

REFUSE_CONTRACT_MISSING = "BAND_CONTRACT_MISSING"
REFUSE_CONTRACT_MALFORMED = "BAND_CONTRACT_MALFORMED"
REFUSE_TASKS_INVALID = "BAND_TASKS_INVALID"
REFUSE_TASK_PROGRAM_MISMATCH = "BAND_TASK_PROGRAM_MISMATCH"
REFUSE_NO_TASKS = "BAND_NO_KEPT_TASKS"
REFUSE_SOLVER_FAILED = "BAND_SOLVER_FAILED"
REFUSE_HARNESS_FAILED = "BAND_HARNESS_FAILED"
REFUSE_ROW_PROVENANCE = "BAND_ROW_PROVENANCE"
REFUSE_REQUEST_INVALID = "BAND_REQUEST_INVALID"

bind_import_twin(__name__)
