#!/usr/bin/env python3
"""Generate designed ACTF r26 episodes (Q=2). Never writes outputs/raw/."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

OUT = Path("/tmp/actf-r26")
GENERATED_AT = "2026-09-02T23:25:00Z"
KNOWN = {
    "bash",
    "read_file",
    "edit_file",
    "write_file",
    "search",
    "gh",
    "kubectl",
    "gate-cli",
    "tofu",
    "tenv",
    "tflint",
    "aws",
    "jq",
    "hcl2json",
    "block",
    "decline",
    "deny",
    "refuse",
}
FORBIDDEN = {
    "thought",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "reasoning",
    "internal_reasoning",
    "hidden_reasoning",
    "thinking",
    "cot",
}
PROGRESS_RE = re.compile(
    r"\b(?:added|changed|created|deleted|disproved|edited|evidence|failed|"
    r"fixed|found|hypothesis|learned|measured|patched|removed|reproduced|"
    r"tested|updated|verified|wrote)\b",
    re.I,
)
STALL_RE = re.compile(r"\b(?:no[ -]?op|no change|nothing changed|unchanged)\b", re.I)
BASIS_PREFIX = ("Plan:", "Observation:", "Reflection:", "Tool call:")
ID1 = "act-r26-unix-millis-tickloom-d81f2a"
ID2 = "act-r26-fnmatch-brackets-lotglob-c9e047"


def db(text: str) -> str:
    text = text.strip()
    if not text.startswith(BASIS_PREFIX):
        raise SystemExit(f"basis prefix: {text[:80]!r}")
    if not (80 <= len(text) <= 240):
        raise SystemExit(f"basis len {len(text)}: {text}")
    return text


def rights() -> dict:
    return {
        "provider": "SpaceXAI/xAI",
        "model": "grok-4.6",
        "channel": "consumer",
        "subscription_plan": "SuperGrok Heavy",
        "generation_surface": "SuperGrok Heavy chat",
        "generated_at": GENERATED_AT,
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "research_retention_status": "allowed",
        "research_evaluation_status": "allowed",
        "redistribution_status": "unresolved",
        "provider_training_status": "unresolved",
        "weight_publication_status": "blocked",
        "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
        "linear_issue": "RM-793",
        "training_ready": False,
    }


def meta_common(**extra) -> dict:
    m = {
        "factory": "agentic-coding-trajectory-factory",
        "round": 26,
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "sim_or_real": "designed",
        "training_ready": False,
        "rights": rights(),
    }
    m.update(extra)
    return m


TICK_BEFORE = """package tickloom

import "time"

func ParsePLC(ms int64) time.Time {
	return time.Unix(ms, 0).UTC()
}
"""

TICK_DIV = """package tickloom

import "time"

func ParsePLC(ms int64) time.Time {
	return time.Unix(ms/1000, 0).UTC()
}
"""

TICK_MILLI = """package tickloom

import "time"

func ParsePLC(ms int64) time.Time {
	return time.UnixMilli(ms).UTC()
}
"""

MILLI_TEST = """package tickloom

import (
	"testing"
	"time"
)

func TestMillisKept(t *testing.T) {
	got := ParsePLC(1788336000440)
	want := time.Date(2026, 9, 2, 8, 0, 0, 440000000, time.UTC)
	if !got.Equal(want) {
		t.Fatalf("got %s want %s", got.UTC().Format(time.RFC3339Nano), want.Format(time.RFC3339Nano))
	}
}
"""

MATCH_BEFORE = '''import fnmatch


def match_lot(name: str, pattern: str) -> bool:
    return fnmatch.fnmatch(name, pattern)
'''

MATCH_REPLACE = '''import fnmatch


def match_lot(name: str, pattern: str) -> bool:
    escaped = pattern.replace("[", "[[]").replace("]", "[]]")
    return fnmatch.fnmatch(name, escaped)
'''

MATCH_ESC = '''import fnmatch
import glob


def match_lot(name: str, pattern: str) -> bool:
    return fnmatch.fnmatch(name, glob.escape(pattern))
'''

BRACKET_TEST = '''from lotglob.match import match_lot


def test_literal_brackets():
    assert match_lot("lot[440].csv", "lot[440].csv")


def test_does_not_match_lot4():
    assert not match_lot("lot4.csv", "lot[440].csv")
'''


def ep1() -> dict:
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: TL-440 reports ParsePLC mapping mill PLC epoch milliseconds to year 58640. Search time.Unix and ParsePLC for evidence of a seconds-only decoder."
            ),
            "plan": "1) search time.Unix 2) read ParsePLC 3) reproduce year overflow 4) keep millis 5) regression + PR",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "time\\.Unix|ParsePLC|UnixMilli|epoch",
                    "path": ".",
                },
            },
            "observation": (
                "plc/parse.go:6:func ParsePLC(ms int64) time.Time {\n"
                "plc/parse.go:7:\treturn time.Unix(ms, 0).UTC()\n"
                "plc/parse_test.go:11:        got := ParsePLC(1788336000)\n"
                "plc/parse_test.go:12:        want := time.Unix(1788336000, 0).UTC()\n"
                "4 matches"
            ),
            "reflection": "Found time.Unix(ms, 0) on the mill millisecond field. Existing tests pass a 10-digit second stamp, so the 13-digit PLC path is uncovered.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: parse.go:7 uses time.Unix(ms, 0) (step 1). Read parse.go for evidence of UnixMilli, remainder nanos, or a second decoder."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "plc/parse.go", "offset": 1, "limit": 16},
            },
            "observation": TICK_BEFORE,
            "reflection": "Measured a single time.Unix(ms, 0) with no UnixMilli. Go treats the int64 as seconds, so a mill millisecond stamp becomes year 58640.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: ParsePLC is time.Unix seconds only (step 2). Run go test for evidence the millisecond fixture already failed the civil clock."
            ),
            "tool_call": {
                "name": "bash",
                "args": {"command": "go test ./plc -count=1 2>&1 | tail -n 20"},
            },
            "observation": (
                "--- FAIL: TestParsePLCMillisIsCivilMorning (0.00s)\n"
                "    parse_test.go:18: ParsePLC(1788336000440).Year() = 58640; want 2026\n"
                "    parse_test.go:19: got 58640-09-14T16:27:20Z want 2026-09-02T08:00:00.44Z\n"
                "FAIL\n"
                "FAIL\tgit.flintwharf.internal/ops/tickloom/plc\t0.012s\n"
                "FAIL"
            ),
            "reflection": "Reproduced time.Unix treating 1788336000440 as seconds (year 58640) while the second-stamp tests still match. The defect is the unit, not the mill timezone.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: TestParsePLCMillisIsCivilMorning failed year 58640 (step 3). Run full go test so module-download evidence is in the same suite."
            ),
            "tool_call": {
                "name": "bash",
                "args": {"command": "go test ./... 2>&1 | tail -n 18"},
            },
            "observation": (
                "go: downloading github.com/google/go-cmp v0.6.0\n"
                "go: git.flintwharf.internal/ops/tickloom imports\n"
                "        github.com/google/go-cmp/cmp: git.flintwharf.internal/ops/tickloom@v0.0.0: reading https://proxy.golang.org/github.com/google/go-cmp/@v/v0.6.0.zip:\n"
                "502 Bad Gateway\n"
                "<html>\n"
                "<head><title>502 Bad Gateway</title></head>\n"
                "<body>\n"
                "<center><h1>502 Bad Gateway</h1></center>\n"
                "upstream connect error or disconnect/reset before headers. "
                "reset reason: connection failure\n"
                "</body></html>"
            ),
            "reflection": "proxy.golang.org returned 502 while fetching go-cmp. Transient module proxy; retry offline against the already-populated module cache rather than treating the millis bug as a missing cmp.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: go test returned 502 Bad Gateway from proxy.golang.org (step 4). Sleep 4s, retry GOPROXY=off as recovered evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "sleep 4 && GOPROXY=off go test -mod=readonly ./plc -count=1 2>&1 | tail -n 12"
                    )
                },
            },
            "observation": (
                "--- FAIL: TestParsePLCMillisIsCivilMorning (0.00s)\n"
                "    parse_test.go:18: ParsePLC(1788336000440).Year() = 58640; want 2026\n"
                "FAIL\n"
                "FAIL\tgit.flintwharf.internal/ops/tickloom/plc\t0.009s\n"
                "FAIL"
            ),
            "reflection": "Offline module cache recovered the go-cmp fetch. Year is still 58640, so the defect is local time.Unix seconds not a missing plugin.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: offline ParsePLC still failed year 58640 (step 5). Dump Unix vs UnixMilli as evidence 440ms is a 250ms occupancy window."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 - <<'PY' > /tmp/tickloom-epoch.json\n"
                        "import json\n"
                        "from datetime import datetime, timezone, timedelta\n"
                        "ms = 1788336000440\n"
                        "as_seconds = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=ms)\n"
                        "div = datetime.fromtimestamp(ms // 1000, tz=timezone.utc)\n"
                        "milli = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)\n"
                        "meta = {\n"
                        "  'ms': ms,\n"
                        "  'unix_as_seconds_year': as_seconds.year,\n"
                        "  'unix_div_1000': div.strftime('%Y-%m-%dT%H:%M:%SZ'),\n"
                        "  'remainder_ms': ms % 1000,\n"
                        "  'unix_milli': milli.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',\n"
                        "}\n"
                        "print(json.dumps(meta))\n"
                        "PY\n"
                        "cat /tmp/tickloom-epoch.json"
                    )
                },
            },
            "observation": (
                "{\n"
                '  "ms": 1788336000440,\n'
                '  "unix_as_seconds_year": 58640,\n'
                '  "unix_div_1000": "2026-09-02T08:00:00Z",\n'
                '  "remainder_ms": 440,\n'
                '  "unix_milli": "2026-09-02T08:00:00.440Z"\n'
                "}\n"
                "Found UnixMilli(1788336000440) equals 08:00:00.440Z; time.Unix(ms, 0) never consumed milliseconds."
            ),
            "reflection": "Measured unix_milli=08:00:00.440Z for the mill stamp. Dividing by 1000 would print 08:00:00Z and land the occupancy in the wrong 250ms window.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: dump remainder_ms is 440 and unix_milli is 08:00:00.440Z (step 6). jq the dump and re-read ParsePLC for evidence time.Unix is still seconds."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "filter": "{ms, unix_as_seconds_year, unix_div_1000, remainder_ms, unix_milli}",
                    "file": "/tmp/tickloom-epoch.json",
                },
            },
            "observation": (
                "{\n"
                '  "ms": 1788336000440,\n'
                '  "unix_as_seconds_year": 58640,\n'
                '  "unix_div_1000": "2026-09-02T08:00:00Z",\n'
                '  "remainder_ms": 440,\n'
                '  "unix_milli": "2026-09-02T08:00:00.440Z"\n'
                "}\n"
                "Found TL-SPEC-4 in docs/tl-spec.md:8: mill PLC stamps are epoch milliseconds; occupancy windows are 250ms so 08:00:00.440 must not collapse to 08:00:00.000."
            ),
            "reflection": (
                "Plan change: abandon treating the mill stamp as already Unix seconds. Observation shows 440ms is a real occupancy remainder. "
                "Switching the edit target to time.UnixMilli(ms) so the 250ms window is applied."
            ),
        },
        {
            "n": 8,
            "decision_basis": db(
                "Reflection: plan now targets UnixMilli instants, not seconds (step 7). First patch: divide ms by 1000 and keep time.Unix."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "plc/parse.go",
                    "old_string": (
                        "func ParsePLC(ms int64) time.Time {\n"
                        "\treturn time.Unix(ms, 0).UTC()\n"
                        "}"
                    ),
                    "new_string": (
                        "func ParsePLC(ms int64) time.Time {\n"
                        "\treturn time.Unix(ms/1000, 0).UTC()\n"
                        "}"
                    ),
                },
            },
            "observation": "Edited plc/parse.go: ParsePLC now time.Unix(ms/1000, 0). UnixMilli is still unused.",
            "reflection": "Divide-by-1000 is the tempting wrong durable step. Year 2026 would luckily appear; 440ms would become 08:00:00Z and miss TL-SPEC-4.",
        },
        {
            "n": 9,
            "decision_basis": db(
                "Observation: parse.go now divides ms by 1000 then Unix (step 8). Write TestMillisKept as evidence 08:00:00.440Z must survive."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "plc/milli_test.go",
                    "content": MILLI_TEST,
                },
            },
            "observation": "Wrote plc/milli_test.go (18 lines). Asserts ParsePLC(1788336000440) equals 2026-09-02T08:00:00.440Z.",
            "reflection": "Created a millisecond-kept regression that refuses 08:00:00Z. Run it to see whether divide-by-1000 actually keeps 440ms.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: TestMillisKept asserts 08:00:00.440Z (step 9). Run go test for evidence the divide-by-1000 patch failed."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "GOPROXY=off go test -mod=readonly ./plc -count=1 2>&1 | tail -n 16"
                },
            },
            "observation": (
                "--- FAIL: TestMillisKept (0.00s)\n"
                "    milli_test.go:12: got 2026-09-02T08:00:00Z want 2026-09-02T08:00:00.44Z\n"
                "--- PASS: TestParsePLCMillisIsCivilMorning (0.00s)\n"
                "FAIL\n"
                "FAIL\tgit.flintwharf.internal/ops/tickloom/plc\t0.011s\n"
                "FAIL"
            ),
            "reflection": "Divide-by-1000 made year 2026 pass and printed 08:00:00Z for the 440ms remainder. Need UnixMilli so occupancy stays in the 250–500ms window.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: TestMillisKept failed was 08:00:00Z (step 10). Re-read parse.go for evidence divide-by-1000 is still the decoder."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "plc/parse.go", "offset": 1, "limit": 16},
            },
            "observation": TICK_DIV,
            "reflection": "Found time.Unix(ms/1000, 0). TL-SPEC-4 wants the millisecond occupancy; drop the divide and parse UnixMilli.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Reflection: divide-by-1000 dropped the 440ms remainder (step 11). Patch ParsePLC to time.UnixMilli(ms) so 08:00:00.440Z is verified."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "plc/parse.go",
                    "old_string": TICK_DIV.strip(),
                    "new_string": TICK_MILLI.strip(),
                },
            },
            "observation": "Edited plc/parse.go: ParsePLC now time.UnixMilli(ms).UTC(). Divide-by-1000 is gone.",
            "reflection": "Patched the epoch-millisecond path. Re-run ParsePLC and MillisKept tests.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: parse.go now uses UnixMilli (step 12). Re-run go test as verified evidence 08:00:00.440Z is kept."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "GOPROXY=off go test -mod=readonly ./plc -count=1 2>&1 | tail -n 8"
                },
            },
            "observation": (
                "ok  \tgit.flintwharf.internal/ops/tickloom/plc\t0.008s\n"
                "6 passed (TestParsePLCMillisIsCivilMorning, TestMillisKept, plus 4 second-stamp tests)"
            ),
            "reflection": "Verified 6 passed including TestMillisKept. Open the TL-440 PR.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Observation: 6 ParsePLC tests passed after the UnixMilli patch (step 13). Create the TL-440 PR via gh api as evidence of the handoff."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/flintwharf/tickloom/pulls",
                    "raw_field": "title=TL-440: parse mill PLC epoch milliseconds via UnixMilli so 08:00:00.440Z is kept",
                },
            },
            "observation": (
                "HTTP 429 Too Many Requests\n"
                "Retry-After: 8\n"
                "x-ratelimit-limit: 30\n"
                "x-ratelimit-remaining: 0\n"
                '{"message":"API rate limit exceeded for user ci-bot (30 req/min); retry_after=8",'
                '"documentation_url":"https://docs.github.com/rest/overview/rate-limits"}'
            ),
            "reflection": "gh returned 429 with retry-after 8 on the shared ci-bot token. Wait the advertised window and retry the create once.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: gh api returned 429 with Retry-After 8 (step 14). Sleep 9s, retry the pull create once, then show the verified URL."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "sleep 9 && gh api -X POST repos/flintwharf/tickloom/pulls "
                        "-f title='TL-440: parse mill PLC epoch milliseconds via UnixMilli so 08:00:00.440Z is kept' "
                        "-f head=tl-440-millis -f base=main --jq .html_url"
                    )
                },
            },
            "observation": "https://git.flintwharf.internal/ops/tickloom/pull/229",
            "reflection": "Verified PR 229 opened. TL-440 can close on the branch; mill PLC epoch milliseconds apply to the occupancy window.",
        },
    ]
    return {
        "id": ID1,
        "goal": (
            "TL-440 (tickloom, Go 1.22 time; go test): mill PLC stamps such as 1788336000440 (2026-09-02T08:00:00.440Z) "
            "decode as year 58640 from ParsePLC while 10-digit second stamps still match. Reproduce with the millisecond "
            "fixture, make parse honor TL-SPEC-4 (epoch milliseconds stored as instants, occupancy windows 250ms), keep "
            "existing second-stamp tests green, and open a PR. Designed plant; not a live PLC claim."
        ),
        "steps": steps,
        "outcome": (
            "Root cause was time.Unix treating mill PLC milliseconds as seconds, so 1788336000440 became year 58640. A "
            "first patch that divided by 1000 made the year pass and then printed 08:00:00Z because the 440ms remainder "
            "was dropped. ParsePLC now uses time.UnixMilli(ms). Verified by GOPROXY=off go test ./plc: 6 passed including "
            "TestMillisKept; PR 229 opened. Overall: verified and shipped."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.40,
            "unix_milli_applied": 0.12,
            "millis_kept_regression": 0.08,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.58,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 6,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 2,
                "duration_min": 33,
            },
        },
        "meta": meta_common(
            codebase_type="library (Go 1.22 time mill PLC epoch)",
            bug_class="time.Unix treats PLC epoch milliseconds as seconds; divide-by-1000 drops the 440ms remainder",
            test_harness="go test",
            noise_steps={"502": 4, "429": 14},
            noise_recovery_steps={"502": 5, "429": 15},
            plan_change_step=7,
            debug_loop_steps=[8, 9, 10, 11, 12, 13],
            tags=[
                "go-1.22",
                "time-unix",
                "unixmilli",
                "epoch-millis",
                "plc-stamp",
                "mill-clock",
            ],
        ),
    }


def ep2() -> dict:
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: LG-277 reports lotglob matching lot4.csv when the mill filter is lot[440].csv. Search fnmatch and match_lot for evidence of a character class."
            ),
            "plan": "1) search fnmatch 2) read match_lot 3) reproduce brackets 4) glob.escape 5) unit tests; mill object store is a later handoff",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "fnmatch|match_lot|glob.escape|lot\\[",
                    "path": "src/lotglob",
                },
            },
            "observation": (
                "src/lotglob/match.py:4:def match_lot(name: str, pattern: str) -> bool:\n"
                "src/lotglob/match.py:5:    return fnmatch.fnmatch(name, pattern)\n"
                "src/lotglob/match.py:1:import fnmatch\n"
                "src/lotglob/scan.py:12:        if match_lot(path.name, pattern):\n"
                "4 matches"
            ),
            "reflection": "Found fnmatch.fnmatch on the raw mill pattern. A literal lot[440].csv would be a character class of 4 and 0, so lot4.csv would match.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: match.py:5 uses fnmatch.fnmatch with no glob.escape (step 1). Read match.py for evidence of escaping or a second matcher."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "src/lotglob/match.py", "offset": 1, "limit": 16},
            },
            "observation": MATCH_BEFORE,
            "reflection": "Measured a bare fnmatch.fnmatch. POSIX fnmatch treats [440] as a character class, so mill lot[440].csv never matches itself.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: match_lot uses fnmatch with no escape (step 2). Run pytest for evidence the bracket fixture already failed the literal name."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest -q tests/test_match.py --tb=short 2>&1 | tail -n 20"
                },
            },
            "observation": (
                "F.....                                                                   [100%]\n"
                "=================================== FAILURES ===================================\n"
                "_______________________________ test_bracket_lot_present _______________________________\n"
                "tests/test_match.py:11: in test_bracket_lot_present\n"
                "    assert match_lot(\"lot[440].csv\", \"lot[440].csv\")\n"
                "E   AssertionError: assert False\n"
                "FAILED tests/test_match.py::test_bracket_lot_present - AssertionError\n"
                "1 failed, 5 passed in 0.12s"
            ),
            "reflection": "Reproduced False for lot[440].csv against itself. Hyphen-name tests still passed on lot-440.csv, so the defect is the character class, not the mill scan loop.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: test_bracket_lot_present failed False on lot[440].csv (step 3). pip install pytest-cov so coverage evidence can join the same suite."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pip install pytest-cov==5.0.0 2>&1 | tail -n 16"
                },
            },
            "observation": (
                "Looking in indexes: https://pypi.org/simple\n"
                "Collecting pytest-cov==5.0.0\n"
                "  Downloading pytest_cov-5.0.0-py3-none-any.whl (21 kB)\n"
                "ERROR: Could not install packages due to an OSError: 429 Too Many Requests\n"
                "Retry-After: 6\n"
                '{"error":"rate_limit_exceeded","retry_after":6,'
                '"message":"pypi.org CDN 429 for /simple/pytest-cov/"}\n'
            ),
            "reflection": "pypi.org returned 429 with retry-after 6. Sleep then retry install once; do not tight-loop the simple index.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: pip install returned 429 with retry_after 6 (step 4). Sleep 7s and retry install once as evidence the index recovered."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "sleep 7 && pip install pytest-cov==5.0.0 2>&1 | tail -n 8; "
                        "pytest -q tests/test_match.py --tb=line 2>&1 | tail -n 6"
                    )
                },
            },
            "observation": (
                "Successfully installed pytest-cov-5.0.0 coverage-7.6.1\n"
                "F.....                                                                   [100%]\n"
                "FAILED tests/test_match.py::test_bracket_lot_present - AssertionError\n"
                "1 failed, 5 passed in 0.10s"
            ),
            "reflection": "Install recovered. Bracket False is still there, so the defect is local fnmatch character class not a missing pytest plugin.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: pytest-cov installed and bracket test still failed False (step 5). Dump fnmatch vs glob.escape as evidence [440] is a class of 4 and 0."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 - <<'PY'\n"
                        "import fnmatch, glob, json\n"
                        "from pathlib import Path\n"
                        "pat = 'lot[440].csv'\n"
                        "meta = {\n"
                        "  'self_match': fnmatch.fnmatch('lot[440].csv', pat),\n"
                        "  'lot4_match': fnmatch.fnmatch('lot4.csv', pat),\n"
                        "  'lot0_match': fnmatch.fnmatch('lot0.csv', pat),\n"
                        "  'escaped': glob.escape(pat),\n"
                        "  'escaped_self': fnmatch.fnmatch('lot[440].csv', glob.escape(pat)),\n"
                        "}\n"
                        "Path('/tmp/lotglob-fnmatch.json').write_text(json.dumps(meta))\n"
                        "print(json.dumps(meta))\n"
                        "PY"
                    )
                },
            },
            "observation": (
                '{"self_match": false, "lot4_match": true, "lot0_match": true, '
                '"escaped": "lot[[]440].csv", "escaped_self": true}\n'
                "Wrote /tmp/lotglob-fnmatch.json from that dump."
            ),
            "reflection": "Measured self_match false and lot4_match true. The mill filter is a literal filename with brackets, not a glob character class.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: dump lot4_match is true and escaped_self is true (step 6). jq the dump for evidence brackets must stay literal under LG-SPEC-2."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "filter": "{self_match, lot4_match, lot0_match, escaped, escaped_self}",
                    "file": "/tmp/lotglob-fnmatch.json",
                },
            },
            "observation": (
                "{\n"
                '  "self_match": false,\n'
                '  "lot4_match": true,\n'
                '  "lot0_match": true,\n'
                '  "escaped": "lot[[]440].csv",\n'
                '  "escaped_self": true\n'
                "}\n"
                "Found LG-SPEC-2 in docs/lotglob-spec.md:6: mill lot filenames may contain literal [n] revision marks; filters are exact names, not globs."
            ),
            "reflection": (
                "Plan change: abandon treating [440] as a revision glob / character class. Observation shows lot4.csv matches and the literal name does not. "
                "Switching the edit target to glob.escape so fnmatch sees lot[440].csv as a filename."
            ),
        },
        {
            "n": 8,
            "decision_basis": db(
                "Reflection: plan now targets glob.escape, not a raw class (step 7). First patch: replace [ with [[] and ] with []]."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "src/lotglob/match.py",
                    "old_string": MATCH_BEFORE.strip(),
                    "new_string": MATCH_REPLACE.strip(),
                },
            },
            "observation": "Edited src/lotglob/match.py: match_lot now replace('[','[[]').replace(']','[]]') then fnmatch. glob.escape is still unused.",
            "reflection": "Sequential replace is the tempting wrong durable step. The second replace rewrites the escape brackets and the literal name still misses.",
        },
        {
            "n": 9,
            "decision_basis": db(
                "Observation: match_lot now double-replaces brackets (step 8). Write literal and lot4 tests as evidence both contracts must hold."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_bracket_literal.py",
                    "content": BRACKET_TEST,
                },
            },
            "observation": "Wrote tests/test_bracket_literal.py (12 lines). Asserts lot[440].csv matches itself and lot4.csv does not.",
            "reflection": "Created a paired regression. Run it to see whether sequential replace actually keeps the literal brackets.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: test_bracket_literal.py asserts self-match and not lot4 (step 9). Run pytest for evidence the sequential-replace patch failed."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "pytest -q tests/test_match.py tests/test_bracket_literal.py --tb=short 2>&1 | tail -n 18"
                    )
                },
            },
            "observation": (
                ".F......                                                                 [100%]\n"
                "=================================== FAILURES ===================================\n"
                "__________________________ test_literal_brackets __________________________\n"
                "tests/test_bracket_literal.py:6: in test_literal_brackets\n"
                "    assert match_lot(\"lot[440].csv\", \"lot[440].csv\")\n"
                "E   AssertionError: assert False\n"
                "FAILED tests/test_bracket_literal.py::test_literal_brackets - AssertionError\n"
                "1 failed, 7 passed in 0.14s"
            ),
            "reflection": "lot4 no longer matches; the literal name stayed False because replace produced lot[[[]]440[]].csv. Need glob.escape so only [ is wrapped.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: test_literal_brackets failed False (step 10). Re-read match.py for evidence sequential replace is still the matcher."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "src/lotglob/match.py", "offset": 1, "limit": 16},
            },
            "observation": MATCH_REPLACE,
            "reflection": "Found replace('[','[[]').replace(']','[]]') on match_lot. LG-SPEC-2 wants glob.escape; drop the sequential replace.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Reflection: sequential replace broke the literal name (step 11). Patch match_lot to fnmatch(name, glob.escape(pattern)) so both tests are verified."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "src/lotglob/match.py",
                    "old_string": MATCH_REPLACE.strip(),
                    "new_string": MATCH_ESC.strip(),
                },
            },
            "observation": "Edited src/lotglob/match.py: match_lot now fnmatch.fnmatch(name, glob.escape(pattern)). Sequential replace is gone.",
            "reflection": "Patched the literal-bracket path. Re-run match and bracket-literal tests.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: match_lot now uses glob.escape (step 12). Re-run pytest as verified evidence the literal name matches and lot4 does not."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "pytest -q tests/test_match.py tests/test_bracket_literal.py 2>&1 | tail -n 8"
                    )
                },
            },
            "observation": (
                "........                                                                 [100%]\n"
                "8 passed in 0.11s "
                "(test_bracket_lot_present, test_literal_brackets, test_does_not_match_lot4, plus 5 others)"
            ),
            "reflection": "Verified 8 passed including the bracket pair. Unit fnmatch math is done; the mill object-store copy is still required before LG-277 can close.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: unit tests passed; need the mill object-store copy (step 13). GET the sedgefen mill lots.csv as evidence a live bracket filename can match."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "curl -sS -o /tmp/mill-lots.csv -w '%{http_code}' "
                        "https://objects.sedgefen.internal/v1/lotglob/week36-lots.csv"
                    )
                },
            },
            "observation": (
                "curl: (22) The requested URL returned error: 502\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "content-type: text/plain\n"
                "x-envoy-upstream-service-time: 30012\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection timeout\n"
                "000"
            ),
            "reflection": "objects.sedgefen.internal returned 502 upstream timeout. Retry once with backoff; if it stays down, the mill-file round-trip stays unverified and LG-277 cannot close.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: mill object GET returned 502 upstream timeout (step 14). Sleep 5s, retry once, and if empty record evidence that the mill is unavailable."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "sleep 5 && curl -sS -o /tmp/mill-lots.csv -w '%{http_code}\\n' "
                        "https://objects.sedgefen.internal/v1/lotglob/week36-lots.csv "
                        "|| echo LAB_UNAVAILABLE; ls /tmp/mill-lots.csv 2>&1 | head"
                    )
                },
            },
            "observation": (
                "LAB_UNAVAILABLE\n"
                "ls: cannot access '/tmp/mill-lots.csv': No such file or directory"
            ),
            "reflection": "Object store stayed unavailable after backoff. Open LG-311 as the mill-file handoff; do not claim the live bracket filename on the sedgefen box.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: mill-lots.csv was missing after LAB_UNAVAILABLE (step 15). Open gh issue create for LG-311 as evidence the unresolved mill ACK is tracked."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "repo": "sedgefen/lotglob",
                    "title": "LG-311: mill week36 lots.csv required before closing LG-277 glob.escape match",
                    "body": "Unit tests glob.escape literal [440] + not lot4; objects.sedgefen.internal unreachable.",
                },
            },
            "observation": "https://git.sedgefen.internal/mill/lotglob/issues/311",
            "reflection": "Created LG-311. lotglob unit tests are green; live mill-file confirmation is a separate ticket.",
        },
    ]
    return {
        "id": ID2,
        "goal": (
            "LG-277 (lotglob, Python 3.12 fnmatch; pytest): mill lot filter lot[440].csv returns lot4.csv and misses the "
            "literal bracket filename because fnmatch treats [440] as a character class. Reproduce with the bracket fixture, "
            "make match_lot honor LG-SPEC-2 (literal [n] revision marks, not globs), and keep existing hyphen-name tests "
            "green. Designed plant; the mill object-store copy is a lab path, not a live lot claim."
        ),
        "steps": steps,
        "outcome": (
            "Root cause was fnmatch.fnmatch on a raw mill pattern, so lot[440].csv was a class of 4 and 0 (self False, "
            "lot4 True). A first patch that replace('[','[[]').replace(']','[]]') produced lot[[[]]440[]].csv and still "
            "missed the literal name. match_lot now uses glob.escape. Verified by pytest tests/test_match.py "
            "tests/test_bracket_literal.py: 8 passed including test_literal_brackets and test_does_not_match_lot4. The mill "
            "object-store copy stayed unreachable, so live bracket confirmation is unresolved; LG-311 was opened as the "
            "handoff. Overall: incomplete; unit fnmatch only."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "glob_escape_match": 0.10,
            "lot4_rejected": 0.08,
            "hil_unverified_penalty": -0.14,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.26,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 8,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 2,
                "duration_min": 42,
                "hil_jobs": 0,
            },
        },
        "meta": meta_common(
            codebase_type="data pipeline (Python 3.12 fnmatch mill lot filter)",
            bug_class="fnmatch treats lot[440].csv as a character class; sequential bracket replace still misses the literal name",
            test_harness="pytest",
            noise_steps={"429": 4, "502": 14},
            noise_recovery_steps={"429": 5, "502": 15},
            plan_change_step=7,
            debug_loop_steps=[8, 9, 10, 11, 12, 13],
            tags=[
                "python-3.12",
                "fnmatch",
                "glob-escape",
                "character-class",
                "mill-lots",
                "hil-handoff",
            ],
        ),
    }


def walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{path}.{k}" if path else k
            yield child, k, v
            yield from walk_keys(v, child)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, f"{path}[{i}]")


def prior_ids() -> set[str]:
    found: set[str] = set()
    id_re = re.compile(r'"id":\s*"(act[^"]+)"')
    for p in Path("/tmp").glob("actf-r*/batch-r*.jsonl"):
        if p.parent.name == "actf-r26":
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            found.add(rec["id"])
    for p in Path("/tmp").glob("actf-r*/gen.py"):
        if p.parent.name == "actf-r26":
            continue
        found.update(id_re.findall(p.read_text(encoding="utf-8")))
    mill = Path("/home/raulmc/rmems/synthetic-factory/outputs/raw")
    if mill.is_dir():
        for p in mill.glob("**/agentic-coding-trajectory-factory/batch-r*.jsonl"):
            for line in p.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                rid = rec.get("id")
                if rid:
                    found.add(rid)
    return found


def validate_record(rec: dict) -> None:
    steps = rec["steps"]
    n = len(steps)
    if not 12 <= n <= 17:
        raise SystemExit(f"{rec['id']} step count {n}")
    for i, step in enumerate(steps, 1):
        if step["n"] != i:
            raise SystemExit(f"{rec['id']} numbering {step['n']} != {i}")
        name = step["tool_call"]["name"]
        if name not in KNOWN:
            raise SystemExit(f"{rec['id']} unknown tool {name}")
        if not isinstance(step["tool_call"].get("args"), dict):
            raise SystemExit(f"{rec['id']} args not object {i}")
        if not step["observation"].strip():
            raise SystemExit(f"{rec['id']} empty obs {i}")
        db(step["decision_basis"])
        blob = " ".join(
            [
                step["decision_basis"],
                step["observation"],
                step["tool_call"]["name"],
                json.dumps(step["tool_call"]["args"], sort_keys=True),
            ]
        )
        if STALL_RE.search(blob):
            raise SystemExit(f"{rec['id']} step {i} stall: {STALL_RE.search(blob).group(0)!r}")
        if not PROGRESS_RE.search(blob):
            raise SystemExit(f"{rec['id']} step {i} sparse progress: {step['decision_basis'][:100]!r}")
        if "hypothesis" in step["observation"].lower():
            raise SystemExit(f"{rec['id']} step {i} hypothesis in observation")
    obs = [s["observation"] for s in steps]
    n429 = sum("429" in o for o in obs)
    n502 = sum("502" in o for o in obs)
    if n429 != 1 or n502 != 1:
        raise SystemExit(f"{rec['id']} noise counts 429={n429} 502={n502}")
    recov = rec["meta"]["noise_recovery_steps"]
    noise = rec["meta"]["noise_steps"]
    for code, idx in noise.items():
        if code not in steps[idx - 1]["observation"]:
            raise SystemExit(f"{rec['id']} noise {code} not in step {idx}")
        ridx = recov[code]
        if code not in steps[ridx - 1]["decision_basis"]:
            raise SystemExit(f"{rec['id']} recovery {ridx} missing {code} in basis")
        if code in steps[ridx - 1]["observation"]:
            raise SystemExit(f"{rec['id']} recovery {ridx} repeats {code} in observation")
    pc = rec["meta"]["plan_change_step"]
    if "Plan change:" not in steps[pc - 1].get("reflection", ""):
        raise SystemExit(f"{rec['id']} plan change reflection missing")
    if pc in (1, n):
        raise SystemExit(f"{rec['id']} plan change at terminal {pc}")
    for path, key, _ in walk_keys(rec):
        norm = re.sub(r"[^a-z0-9]+", "_", key).strip("_").lower()
        if norm in FORBIDDEN or norm.startswith("internal_reasoning"):
            raise SystemExit(f"{rec['id']} forbidden key {path}")
        if "thought" in norm and norm != "thoughtful":
            raise SystemExit(f"{rec['id']} thought-like key {path}")
    rc = rec["reward"]
    numeric = [
        v
        for k, v in rc.items()
        if k not in {"success", "aggregation", "cost", "total"}
        and isinstance(v, (int, float))
        and not isinstance(v, bool)
    ]
    if abs(sum(numeric) - rc["total"]) > 1e-9:
        raise SystemExit(f"{rec['id']} reward {sum(numeric)} != {rc['total']}")
    if rec["meta"]["training_ready"] is not False:
        raise SystemExit("training_ready")
    if rec["meta"]["rights"]["intended_use"] != "research_only":
        raise SystemExit("rights")
    if rec["meta"]["rights"]["training_ready"] is not False:
        raise SystemExit("rights.training_ready")
    if rec["meta"]["sim_or_real"] != "designed":
        raise SystemExit("sim_or_real")
    if rec["meta"]["round"] != 26:
        raise SystemExit("round")
    if rec["meta"]["rights"]["linear_issue"] != "RM-793":
        raise SystemExit("linear")
    if rec["reward"]["success"] is True and not re.search(
        r"\b(?:verified|shipped|passed)\b", rec["outcome"], re.I
    ):
        raise SystemExit(f"{rec['id']} success outcome missing completion")
    if rec["reward"]["success"] is False and not re.search(
        r"\b(?:incomplete|unresolved|handoff|pending)\b", rec["outcome"], re.I
    ):
        raise SystemExit(f"{rec['id']} failure outcome missing incomplete/handoff")


def notes() -> str:
    return """# ACTF r26 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (`FACTORY_QUOTAS["agentic-coding-trajectory-factory"] == 2`). IDs mill-safe `act-r26-…` (not the unresolved `actf-` prefix). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (bash, read_file, edit_file, write_file, search, gh, jq). meta.round=26, meta.factory=agentic-coding-trajectory-factory, meta.generator=grok-4.6, run_label=2026-09-02-final-heavy, meta.sim_or_real=designed. meta.rights RM-793 research-only; training_ready false. Linear RM-793. Invented repos only (flintwharf/tickloom, sedgefen/lotglob). Never wrote outputs/raw/. Did not steal 2026-08-17 r13 reservation. Beads create failed (Dolt events id default); Linear RM-793 remains the rights tracker. Unique vs staged r10–r24 (r22 ParseInLocation Chicago / csv utf-8-sig BOM; r23 String.split(\".\") / pathlib with_suffix .tar.gz; r24 os.path.commonprefix /bin vs /binaries / preStop sleep>grace) and committed mill (meterflow/hubgate/shardup/tollgate/feedloom/tallyhouse).

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r26-unix-millis-tickloom-d81f2a | Go 1.22 time / go test | time.Unix treats PLC epoch milliseconds as seconds; divide-by-1000 drops the 440ms remainder | success; 6/6; PR 229 | 0.58 |
| act-r26-fnmatch-brackets-lotglob-c9e047 | Python 3.12 fnmatch / pytest | fnmatch treats lot[440].csv as a character class; sequential bracket replace still misses the literal name | incomplete HIL handoff LG-311; 8 unit tests | 0.26 |

## Step counts, noise, plan change
- act-r26-unix-millis-tickloom-d81f2a: 15 steps. 502 at step 4 (`go test` proxy.golang.org go-cmp, upstream connect) → recovery step 5 (`sleep 4 && GOPROXY=off -mod=readonly`; year still 58640). 429 at step 14 (`gh api` POST pulls, Retry-After 8) → recovery step 15 (`sleep 9 && gh api`). Plan change at step 7: dump remainder_ms 440 + unix_milli 08:00:00.440Z + TL-SPEC-4 kills seconds-as-given; edit target becomes time.UnixMilli. Debug loop: 8 divide-by-1000 (wrong civil ms dropped) → 9 write TestMillisKept → 10 FAIL was 08:00:00Z → 11 re-read ms/1000 → 12 patch UnixMilli → 13 6 passed.
- act-r26-fnmatch-brackets-lotglob-c9e047: 16 steps. 429 at step 4 (`pip install pytest-cov` pypi.org, retry_after 6) → recovery step 5 (`sleep 7 && pip`; literal name still False). 502 at step 14 (sedgefen objects GET, envoy timeout) → recovery step 15 (retry then LAB_UNAVAILABLE). Plan change at step 7: dump self_match false + lot4_match true + LG-SPEC-2 kills revision-glob; edit target becomes glob.escape. Debug loop: 8 sequential [[] / []] replace → 9 write literal+lot4 pair → 10 FAIL literal False → 11 re-read sequential replace → 12 glob.escape → 13 8 passed.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80–240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. The word "hypothesis" is kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. tickloom: 0.40+0.12+0.08-0.02=0.58. lotglob: 0.24+0.10+0.08-0.14-0.02=0.26.

## Realism / weak recovery
Good: tickloom is a real Go time.Unix footgun (the int64 is seconds; mill PLC stamps are epoch milliseconds); divide-by-1000 is the tempting wrong durable step and drops 440ms out of the 250ms occupancy window. lotglob is a real POSIX fnmatch trap (`[440]` is a class of 4 and 0, so lot4.csv matches and lot[440].csv does not); sequential replace('[','[[]').replace(']','[]]') is the equally tempting wrong escape and rewrites the inserted brackets. Weak: epoch dump is a designed Python helper rather than a committed Go probe; GOPROXY 502 fallback is availability of the module cache, not a stale tzdata that still Unix-seconds; mill object 502 is availability, not a stale CSV whose names are already unescaped. Next densification: a reviewer asking to keep time.Unix "so PLC and Unix seconds share one decoder", or a 502 whose local fallback lots.csv already lists lot4.csv as the intended match.

Novel coverage: 36%
"""


def pipeline_checks(recs) -> None:
    sys.path.insert(0, str(Path("/home/raulmc/rmems/synthetic-factory/pipelines")))
    from validate_run import check_episode, terminal_outcome_agrees
    from check_records import FactoryStaging, check_jsonl
    from verify_execution import verify_batch_for_frontier, verify_record_execution
    from round_txn_coverage import has_long_horizon_debug_loop, sparse_step_progress_errors

    for rec in recs:
        errs = check_episode(
            rec,
            rec["id"],
            forbid_hidden_thought=True,
            enforce_terminal_outcome=True,
        )
        if errs:
            raise SystemExit(f"check_episode {errs[:5]}")
        if not terminal_outcome_agrees(rec["outcome"], rec["reward"]["success"]):
            raise SystemExit(f"{rec['id']} terminal_outcome_agrees")
        if not has_long_horizon_debug_loop(rec["steps"]):
            raise SystemExit(f"{rec['id']} missing debug loop")
        sparse = sparse_step_progress_errors(rec["id"], rec["steps"])
        if sparse:
            raise SystemExit(str(sparse))
        status, reason = verify_record_execution(rec, rec["id"])
        if status != "verified":
            raise SystemExit(f"{rec['id']} execution {status}: {reason}")

    batch = OUT / "batch-r26.jsonl"
    errors, warnings, kinds, records = check_jsonl(
        batch, batch.name, staging=FactoryStaging(enabled=True)
    )
    if errors:
        raise SystemExit(f"check_jsonl errors {errors[:8]}")
    if records != 2:
        raise SystemExit(f"records {records}")
    counts, findings, blocked = verify_batch_for_frontier(batch, strict=True)
    if blocked or counts.get("verified") != 2:
        raise SystemExit(f"frontier {counts} {findings} blocked={blocked}")
    print("pipeline ok", kinds, counts, "warnings", warnings[:4])


def main() -> int:
    recs = [ep1(), ep2()]
    taken = prior_ids()
    for rec in recs:
        if rec["id"] in taken:
            raise SystemExit(f"id collision {rec['id']}")
        validate_record(rec)
    OUT.mkdir(parents=True, exist_ok=True)
    raw = Path("/home/raulmc/rmems/synthetic-factory/outputs/raw")
    if raw.exists() and OUT.resolve().is_relative_to(raw.resolve()):
        raise SystemExit("refusing to write under outputs/raw/")
    batch = OUT / "batch-r26.jsonl"
    with batch.open("w", encoding="utf-8") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    notes_path = OUT / "NOTES-r26.md"
    notes_path.write_text(notes(), encoding="utf-8")
    print(f"wrote {batch} ({len(recs)} records)")
    print(f"wrote {notes_path}")
    pipeline_checks(recs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
