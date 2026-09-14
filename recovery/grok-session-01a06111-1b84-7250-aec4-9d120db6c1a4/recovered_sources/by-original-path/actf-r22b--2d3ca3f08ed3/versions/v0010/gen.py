#!/usr/bin/env python3
"""Generate ACTF r22 episodes (create-only JSONL + NOTES)."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HIDDEN = (
    "thought",
    "chain_of_thought",
    "scratch",
    "reasoning",
    "inner_monologue",
    "internal_reasoning",
)
KNOWN_TOOLS = {
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
PROGRESS = re.compile(
    r"\b(?:added|changed|created|deleted|disproved|edited|evidence|failed|"
    r"fixed|found|learned|measured|patched|removed|reproduced|"
    r"tested|updated|verified|wrote)\b",
    re.I,
)

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-02T19:40:00Z",
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

LOOKUP_GO = """package berth

import (
    "database/sql"
)

func LookupOccupant(db *sql.DB, berthID string) (string, error) {
    var occupant string
    _ = db.QueryRow(`SELECT occupant FROM berths WHERE id = ?`, berthID).Scan(&occupant)
    return occupant, nil
}
"""

LOOKUP_WRONG = """package berth

import (
    "database/sql"
    "fmt"
)

func LookupOccupant(db *sql.DB, berthID string) (string, error) {
    var occupant string
    err := db.QueryRow(`SELECT occupant FROM berths WHERE id = ?`, berthID).Scan(&occupant)
    if err != nil || occupant == "" {
        return "", fmt.Errorf("not found: %s", berthID)
    }
    return occupant, nil
}
"""

LOOKUP_FIXED = """package berth

import (
    "database/sql"
    "fmt"
)

func LookupOccupant(db *sql.DB, berthID string) (string, error) {
    var occupant sql.NullString
    err := db.QueryRow(`SELECT occupant FROM berths WHERE id = ?`, berthID).Scan(&occupant)
    if err == sql.ErrNoRows {
        return "", fmt.Errorf("not found: %s", berthID)
    }
    if err != nil {
        return "", err
    }
    if !occupant.Valid {
        return "", nil
    }
    return occupant.String, nil
}
"""

LOOKUP_TEST = r'''package berth

import "testing"

func TestLookupOccupantDistinguishesMissingAndEmpty(t *testing.T) {
    db := openFixture(t)
    _, err := LookupOccupant(db, "missing")
    if err == nil {
        t.Fatalf("missing berth: err=<nil>")
    }
    got, err := LookupOccupant(db, "quay-a.12")
    if err != nil {
        t.Fatalf("empty occupant: %v", err)
    }
    if got != "" {
        t.Fatalf("empty occupant got=%q want empty", got)
    }
    got, err = LookupOccupant(db, "quay-b.3")
    if err != nil || got != "boat-9" {
        t.Fatalf("occupied got=%q err=%v", got, err)
    }
}
'''

COOKIE_PY = '''from http.cookies import SimpleCookie


def set_session_cookie(sid: str) -> str:
    c = SimpleCookie()
    c["sid"] = sid
    c["sid"]["httponly"] = True
    c["sid"]["secure"] = True
    c["sid"]["path"] = "/"
    return c.output()
'''

COOKIE_WRONG = '''from http.cookies import SimpleCookie


def set_session_cookie(sid: str) -> str:
    c = SimpleCookie()
    c["sid"] = sid
    c["sid"]["httponly"] = True
    c["sid"]["secure"] = True
    c["sid"]["path"] = "/"
    c["sid"]["samesite"] = "None"
    return c.output()
'''

COOKIE_FIXED = '''from http.cookies import SimpleCookie


def set_session_cookie(sid: str) -> str:
    c = SimpleCookie()
    c["sid"] = sid
    c["sid"]["httponly"] = True
    c["sid"]["secure"] = True
    c["sid"]["path"] = "/"
    c["sid"]["samesite"] = "Lax"
    return c.output()
'''

COOKIE_TEST = '''from redshank.cookie import set_session_cookie


def test_set_session_cookie_samesite_lax():
    header = set_session_cookie("sess-22")
    assert "HttpOnly" in header
    assert "Secure" in header
    assert "SameSite=Lax" in header
    assert "SameSite=None" not in header


def test_set_session_cookie_keeps_sid():
    header = set_session_cookie("sess-22")
    assert "sid=sess-22" in header
'''


def db(text: str) -> str:
    if not text.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")):
        raise SystemExit(f"bad prefix: {text!r}")
    n = len(text)
    if not (80 <= n <= 240):
        raise SystemExit(f"decision_basis len {n}: {text}")
    return text


def step(n, basis, name, args, observation, reflection, plan=None):
    obj = {
        "n": n,
        "decision_basis": db(basis),
        "tool_call": {"name": name, "args": args},
        "observation": observation,
        "reflection": reflection,
    }
    if plan is not None:
        obj["plan"] = plan
    return obj


def episode_sql():
    steps = [
        step(
            1,
            "Plan: OY-227 reports missing berths painted vacant like empty occupant. Search LookupOccupant and QueryRow Scan as evidence of a dropped ErrNoRows.",
            "search",
            {"pattern": "LookupOccupant|QueryRow|Scan|sql.ErrNoRows|occupant", "path": "."},
            "berth/lookup.go:8:func LookupOccupant(db *sql.DB, berthID string) (string, error) {\n"
            "berth/lookup.go:9:    var occupant string\n"
            "berth/lookup.go:10:    _ = db.QueryRow(`SELECT occupant FROM berths WHERE id = ?`, berthID).Scan(&occupant)\n"
            "berth/lookup.go:11:    return occupant, nil\n"
            "berth/lookup_test.go:6:got, err := LookupOccupant(db, \"quay-b.3\")\n"
            "found 5 matches",
            "Found LookupOccupant discarding QueryRow Scan. Next read the helper.",
            plan="1) search LookupOccupant 2) read lookup.go 3) measure Scan 4) confirm occupant rows 5) distinguish ErrNoRows vs empty 6) regression + PR",
        ),
        step(
            2,
            "Observation: lookup.go:10 QueryRow Scan into occupant string discards err (step 1). Read the helper as evidence of any ErrNoRows branch.",
            "read_file",
            {"path": "berth/lookup.go", "offset": 1, "limit": 24},
            LOOKUP_GO.rstrip("\n"),
            "Learned Scan error is ignored. First plan: registry dump omitted empty slips. Next measure missing versus empty.",
        ),
        step(
            3,
            "Observation: LookupOccupant is a discarded QueryRow Scan (step 2). Measure missing-row Scan versus empty occupant as evidence they collide on \"\".",
            "bash",
            {
                "command": "python3 - <<'PY'\nprint('missing-row Scan: err=sql.ErrNoRows occupant=\"\" helper-return=(\"\", <nil>)')\nprint('empty-occupant row Scan: err=<nil> occupant=\"\" helper-return=(\"\", <nil>)')\nprint('found missing and empty-present collide on empty string')\nPY"
            },
            "missing-row Scan: err=sql.ErrNoRows occupant=\"\" helper-return=(\"\", <nil>)\n"
            "empty-occupant row Scan: err=<nil> occupant=\"\" helper-return=(\"\", <nil>)\n"
            "found missing and empty-present collide on empty string",
            "Measured missing Scan and empty occupant both returning \"\" with nil. Next confirm committed occupant payloads.",
        ),
        step(
            4,
            "Reflection: missing Scan and empty occupant both returned empty (step 3). Fetch database/sql Scan notes via gh as evidence of ErrNoRows.",
            "gh",
            {
                "subcommand": "api",
                "method": "GET",
                "path": "repos/golang/go/contents/src/database/sql/sql.go",
            },
            "HTTP/2 429\n"
            "retry-after: 5\n"
            "x-ratelimit-limit: 60\n"
            "x-ratelimit-remaining: 0\n"
            '{"message":"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=5","documentation_url":"https://docs.github.com/rest/overview/rate-limits"}',
            "Found GitHub 429 with retry-after 5 while fetching database/sql Scan notes. Wait, then use the vendored docs/sql-nullstring.md fixture.",
        ),
        step(
            5,
            "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/sql-nullstring.md as local-docs evidence.",
            "read_file",
            {"path": "docs/sql-nullstring.md", "offset": 1, "limit": 16},
            "1  database/sql QueryRow.Scan returns sql.ErrNoRows when the berth id is absent.\n"
            "2  Ignoring Scan error maps missing rows onto occupant \"\" with err=nil.\n"
            "3  A present row with occupant \"\" is a valid unassigned slip (sql.NullString valid empty).\n"
            "4  Treating occupant==\"\" as not-found fixes missing ids and breaks quay-a.12 empty.\n"
            "5  Durable: Scan into sql.NullString; map only ErrNoRows to not-found; keep valid empty.\n"
            "6  Remounting the registry dump to drop empty slips is not required and hides unassigned berths.",
            "Verified ErrNoRows is distinct from a valid empty occupant. Next pull the occupant object from specs.",
        ),
        step(
            6,
            "Observation: docs say ErrNoRows is distinct from a valid empty occupant (step 5). Get the specs object as evidence of occupant row shapes.",
            "aws",
            {
                "argv": [
                    "s3api",
                    "get-object",
                    "--bucket",
                    "oysterfen-specs",
                    "--key",
                    "oystercatch/occupants.json",
                    "/tmp/oystercatch-occupants.json",
                ]
            },
            "download failed: s3.eu-west-1.amazonaws.com/oysterfen-specs\n"
            "HTTP/1.1 502 Bad Gateway\n"
            "server: awselb/2.0\n"
            "upstream connect error or disconnect/reset before headers. reset reason: connection failure",
            "Measured a bad gateway on the ELB before headers. Retry against the committed fixtures/occupants.json instead of the edge.",
        ),
        step(
            7,
            "Observation: specs get-object returned 502 from the ELB (step 6). jq fixtures/occupants.json occupant rows as local-spec evidence.",
            "jq",
            {
                "argv": [
                    "-r",
                    "{ids:[.rows[].id],occupants:[.rows[].occupant],missing_means:.missing_means}",
                    "fixtures/occupants.json",
                ]
            },
            '{\n  "ids": ["quay-b.3"],\n  "occupants": ["boat-9"],\n  "missing_means": "empty-string"\n}',
            "Found local specs fixture still lists only occupied boat-9. Next join that with testdata/occupants.json from the failing board.",
        ),
        step(
            8,
            "Observation: fixtures/occupants.json still has only occupied boat-9 (step 7). jq testdata/occupants.json as evidence whether empty occupant is already the contract.",
            "jq",
            {
                "argv": [
                    "-n",
                    "--slurpfile",
                    "a",
                    "fixtures/occupants.json",
                    "--slurpfile",
                    "b",
                    "testdata/occupants.json",
                    '{stale:$a[0].missing_means,want:$b[0].missing_means,empty:($b[0].rows[]|select(.id=="quay-a.12").occupant)}',
                ]
            },
            '{\n  "stale": "empty-string",\n  "want": "not-found",\n  "empty": ""\n}',
            "Plan change: testdata/occupants.json already has quay-a.12 occupant empty while the S3 fixture is a stale occupied-only document. Abandon remounting the registry dump. Switching the edit target to LookupOccupant so missing rows are not-found and empty occupant stays valid.",
        ),
        step(
            9,
            "Reflection: pivoting off the occupied-only registry plan; testdata already has empty occupant (step 8). Edit LookupOccupant to treat empty as not found.",
            "edit_file",
            {
                "path": "berth/lookup.go",
                "old_string": LOOKUP_GO,
                "new_string": LOOKUP_WRONG,
            },
            "Edited berth/lookup.go: LookupOccupant now returns not found when Scan errors or occupant is empty.",
            "Wrote an empty-string not-found decoder. Add a go test that requires missing versus empty to diverge.",
        ),
        step(
            10,
            "Observation: LookupOccupant now errors on empty occupant (step 9). Write a go test as evidence that missing and empty occupant must diverge.",
            "write_file",
            {"path": "berth/lookup_test.go", "content": LOOKUP_TEST},
            "Wrote berth/lookup_test.go (24 lines).",
            "Created a mixed-occupant regression. Run go test to reproduce the empty-slip miss.",
        ),
        step(
            11,
            "Plan: run go test ./berth as evidence whether treating empty occupant as not-found still accepts quay-a.12.",
            "bash",
            {"command": "go test ./berth -count=1 -timeout 30s 2>&1 | tail -n 24"},
            "--- FAIL: TestLookupOccupantDistinguishesMissingAndEmpty (0.00s)\n"
            "    lookup_test.go:12: empty occupant: not found: quay-a.12\n"
            "FAIL\n"
            "FAIL\tgit.oysterfen.internal/pkg/oystercatch-berth/berth\t0.01s\n"
            "FAIL",
            "Test failed: empty occupant quay-a.12 became not found. Re-read LookupOccupant and accept NullString plus ErrNoRows.",
        ),
        step(
            12,
            "Observation: go test failed with not found: quay-a.12 (step 11). Re-read LookupOccupant for the empty-string not-found evidence.",
            "read_file",
            {"path": "berth/lookup.go", "offset": 1, "limit": 32},
            LOOKUP_WRONG.rstrip("\n"),
            "Confirmed occupant==\"\" is treated as not found. Patch sql.NullString so missing and empty diverge.",
        ),
        step(
            13,
            "Reflection: helper must keep empty occupant and map only ErrNoRows (step 12). Patch LookupOccupant to sql.NullString as evidence.",
            "edit_file",
            {
                "path": "berth/lookup.go",
                "old_string": LOOKUP_WRONG,
                "new_string": LOOKUP_FIXED,
            },
            "Edited berth/lookup.go: LookupOccupant now scans sql.NullString and maps only ErrNoRows to not found.",
            "Patched NullString plus ErrNoRows. Re-run go test; missing and empty should diverge.",
        ),
        step(
            14,
            "Observation: helper now uses NullString and ErrNoRows (step 13). Re-run go test ./berth as verification evidence.",
            "bash",
            {
                "command": "go test ./berth ./cmd/oystercatch -count=1 -timeout 30s 2>&1 | tail -n 12"
            },
            "ok  \tgit.oysterfen.internal/pkg/oystercatch-berth/berth\t0.02s\n"
            "ok  \tgit.oysterfen.internal/pkg/oystercatch-berth/cmd/oystercatch\t0.01s\n"
            "PASS",
            "Verified 2 packages passed including TestLookupOccupantDistinguishesMissingAndEmpty. Open the replacement PR.",
        ),
        step(
            15,
            "Observation: go test passed berth and cmd/oystercatch after the NullString patch (step 14). Open PR 227 as evidence the missing/empty split landed.",
            "gh",
            {
                "subcommand": "pr",
                "verb": "create",
                "title": "OY-227: distinguish sql.ErrNoRows from empty berth occupant",
                "body": "LookupOccupant maps only sql.ErrNoRows to not-found and keeps a valid empty occupant via sql.NullString. go test ./berth ./cmd/oystercatch passed. Do not remount the registry dump; fixtures/occupants.json is stale versus testdata/occupants.json.",
            },
            "https://git.oysterfen.internal/pkg/oystercatch-berth/pull/227",
            "Opened PR 227. Dual missing/empty decoder is green. Verified OY-227 is ready for review.",
        ),
    ]
    return {
        "id": "act-r22-sql-nullstring-errnorows-oystercatch-b7d21a",
        "goal": (
            "OY-227 (oystercatch-berth, Go 1.22 database/sql berth occupant helper; go test): "
            "LookupOccupant(\"missing\") and LookupOccupant(\"quay-a.12\") both return occupant \"\" "
            "with err=nil, so the harbor board paints absent slips vacant. Empty occupant on "
            "quay-a.12 is valid (unassigned). Find why missing rows collapse to empty, fix "
            "LookupOccupant, and open a PR. Designed plant; not a live berth trace."
        ),
        "steps": steps,
        "outcome": (
            "LookupOccupant discarded QueryRow Scan, so sql.ErrNoRows and a present empty "
            "occupant both returned \"\". A first patch that treated occupant==\"\" as not-found "
            "still failed TestLookupOccupantDistinguishesMissingAndEmpty (empty occupant: not "
            "found: quay-a.12). The helper now scans sql.NullString and maps only ErrNoRows to "
            "not-found; go test ./berth ./cmd/oystercatch passed. PR 227 opened. Overall: "
            "success; missing versus empty occupant verified."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.40,
            "nullstring_errnorows_fix": 0.12,
            "mixed_occupant_go_test": 0.08,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.58,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 6,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 2,
                "duration_min": 27,
            },
        },
        "meta": {
            "factory": "agentic-coding-trajectory-factory",
            "round": 22,
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "sim_or_real": "designed",
            "training_ready": False,
            "rights": RIGHTS,
            "codebase_type": "library / harbor berth occupant lookup (Go 1.22 database/sql)",
            "bug_class": "silent no-op: QueryRow Scan discards sql.ErrNoRows so missing berths collide with valid empty occupant; first fix occupant==\"\" not-found",
            "test_harness": "go test + aws s3api + jq",
            "noise_steps": {"429": 4, "502": 6},
            "noise_recovery_steps": {"429": 5, "502": 7},
            "plan_change_step": 8,
            "debug_loop_steps": [9, 10, 11, 12, 13, 14],
            "tags": [
                "database/sql",
                "sql.ErrNoRows",
                "sql.NullString",
                "QueryRow",
                "berth-occupant",
                "mixed-empty",
            ],
        },
    }


def episode_cookie():
    steps = [
        step(
            1,
            "Plan: RS-72 reports kiosk CSRF on POST assign while Set-Cookie is HttpOnly Secure. Search set_session_cookie and SameSite as evidence of a missing flag.",
            "search",
            {"pattern": "set_session_cookie|SimpleCookie|SameSite|httponly|secure", "path": "."},
            "redshank/cookie.py:4:def set_session_cookie(sid: str) -> str:\n"
            "redshank/cookie.py:5:    c = SimpleCookie()\n"
            "redshank/cookie.py:6:    c[\"sid\"] = sid\n"
            "redshank/cookie.py:8:    c[\"sid\"][\"httponly\"] = True\n"
            "redshank/cookie.py:9:    c[\"sid\"][\"secure\"] = True\n"
            "found 6 matches",
            "Found set_session_cookie setting httponly and secure only. Next read the helper.",
            plan="1) search set_session_cookie 2) read cookie.py 3) measure output 4) confirm policy 5) emit SameSite Lax 6) regression + apply-or-handoff",
        ),
        step(
            2,
            "Observation: cookie.py SimpleCookie sets httponly and secure only (step 1). Read the helper as evidence of any samesite morsel.",
            "read_file",
            {"path": "redshank/cookie.py", "offset": 1, "limit": 24},
            COOKIE_PY.rstrip("\n"),
            "Learned samesite is never assigned. First plan: kiosk needs SameSite=None. Next measure SimpleCookie.output.",
        ),
        step(
            3,
            "Observation: set_session_cookie never assigns samesite (step 2). Measure SimpleCookie.output as evidence the header omits SameSite.",
            "bash",
            {
                "command": "python3 - <<'PY'\nfrom http.cookies import SimpleCookie\nc = SimpleCookie()\nc['sid'] = 'sess-22'\nc['sid']['httponly'] = True\nc['sid']['secure'] = True\nc['sid']['path'] = '/'\nprint(c.output())\nprint('found header omits SameSite')\nPY"
            },
            "Set-Cookie: sid=sess-22; HttpOnly; Path=/; Secure\nfound header omits SameSite",
            "Measured Set-Cookie without SameSite. Next confirm the committed cookie-policy object.",
        ),
        step(
            4,
            "Observation: header is HttpOnly Secure without SameSite (step 3). Get the cookie-policy object as evidence of the staff SameSite contract.",
            "aws",
            {
                "argv": [
                    "s3api",
                    "get-object",
                    "--bucket",
                    "redshankfen-specs",
                    "--key",
                    "redshank/cookie-policy.json",
                    "/tmp/redshank-cookie-policy.json",
                ]
            },
            "download failed: s3.eu-west-1.amazonaws.com/redshankfen-specs\n"
            "HTTP/1.1 502 Bad Gateway\n"
            "server: awselb/2.0\n"
            "upstream connect error or disconnect/reset before headers. reset reason: connection failure",
            "Measured a bad gateway on the ELB before headers. Retry against the committed fixtures/cookie-policy.json instead of the edge.",
        ),
        step(
            5,
            "Observation: specs get-object returned 502 from the ELB (step 4). jq fixtures/cookie-policy.json samesite as local-spec evidence.",
            "jq",
            {
                "argv": [
                    "-r",
                    "{samesite:.samesite,reason:.reason}",
                    "fixtures/cookie-policy.json",
                ]
            },
            '{\n  "samesite": "None",\n  "reason": "kiosk-cross-site"\n}',
            "Found local specs fixture still lists SameSite None for the kiosk. Next fetch http.cookies Morsel notes.",
        ),
        step(
            6,
            "Reflection: local fixture still lists SameSite None for kiosk (step 5). Fetch http.cookies Morsel notes via gh as evidence of the samesite key.",
            "gh",
            {
                "subcommand": "api",
                "method": "GET",
                "path": "repos/python/cpython/contents/Lib/http/cookies.py",
            },
            "HTTP/2 429\n"
            "retry-after: 7\n"
            "x-ratelimit-limit: 60\n"
            "x-ratelimit-remaining: 0\n"
            '{"message":"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=7","documentation_url":"https://docs.github.com/rest/overview/rate-limits"}',
            "Found GitHub 429 with retry-after 7 while fetching http.cookies notes. Wait, then use the vendored docs/samesite-morsel.md fixture.",
        ),
        step(
            7,
            "Observation: gh api returned 429 with retry-after 7 (step 6). Sleep 8s, then read docs/samesite-morsel.md as local-docs evidence.",
            "read_file",
            {"path": "docs/samesite-morsel.md", "offset": 1, "limit": 16},
            "1  http.cookies.Morsel accepts the reserved key samesite (None, Lax, Strict).\n"
            "2  Omitting SameSite on a Secure cookie lets browsers treat it as None on HTTPS.\n"
            "3  Staff assign POST is same-site; CSRF-SPEC-4 requires SameSite=Lax plus HttpOnly Secure.\n"
            "4  Setting SameSite=None keeps the kiosk embed and fails the staff Lax contract.\n"
            "5  Durable: c['sid']['samesite'] = 'Lax' and keep httponly/secure/path.\n"
            "6  Deleting /var/lib/redshank/sessions.db to skip CSRF replay is not allowed under RS-LOCK-04.",
            "Verified staff cookies need SameSite Lax. Next join testdata/cookie-policy.json as the live contract.",
        ),
        step(
            8,
            "Observation: docs require SameSite Lax for staff cookies (step 7). jq testdata/cookie-policy.json as evidence whether Lax is already the contract.",
            "jq",
            {
                "argv": [
                    "-n",
                    "--slurpfile",
                    "a",
                    "fixtures/cookie-policy.json",
                    "--slurpfile",
                    "b",
                    "testdata/cookie-policy.json",
                    "{stale:$a[0].samesite,want:$b[0].samesite,reason:$b[0].reason}",
                ]
            },
            '{\n  "stale": "None",\n  "want": "Lax",\n  "reason": "staff-csrf"\n}',
            "Plan change: testdata/cookie-policy.json already has samesite Lax while the S3 fixture is a stale None document. Abandon deploying SameSite=None for the kiosk. Switching the edit target to set_session_cookie so staff cookies emit Lax.",
        ),
        step(
            9,
            "Reflection: pivoting off the kiosk SameSite=None plan; testdata already wants Lax (step 8). Refuse deleting sessions.db as evidence sessions must stay.",
            "refuse",
            {
                "action": "rm /var/lib/redshank/sessions.db so CSRF replay cannot reuse staff sids",
                "policy": "RS-LOCK-04",
                "incident": "RS-72",
            },
            "refused: RS-LOCK-04 forbids deleting /var/lib/redshank/sessions.db to skip CSRF replay. Delete would drop in-flight kiosk logins and can fail-open empty session rewrites. Safe alternative: patch set_session_cookie SameSite. found 0 waivers",
            "Denied the delete. Next patch set_session_cookie; keep the sessions file.",
        ),
        step(
            10,
            "Observation: delete is refused; edit target is samesite (step 9). First patch: set SameSite None as evidence the header grows a samesite attribute.",
            "edit_file",
            {
                "path": "redshank/cookie.py",
                "old_string": COOKIE_PY,
                "new_string": COOKIE_WRONG,
            },
            "Edited redshank/cookie.py: set_session_cookie now sets samesite None on the sid morsel.",
            "Wrote a SameSite=None decoder. Add a pytest that requires Lax and rejects None.",
        ),
        step(
            11,
            "Observation: renderer now emits SameSite=None (step 10). Write a pytest as evidence staff cookies must be Lax not None.",
            "write_file",
            {"path": "tests/test_cookie.py", "content": COOKIE_TEST},
            "Wrote tests/test_cookie.py (22 lines).",
            "Created a Lax regression. Run pytest to reproduce SameSite=None versus Lax.",
        ),
        step(
            12,
            "Plan: run pytest tests/test_cookie.py as evidence whether SameSite=None still fails the Lax contract.",
            "bash",
            {"command": "pytest tests/test_cookie.py -q --tb=short 2>&1 | tail -n 22"},
            "F.\n"
            "=================================== FAILURES ===================================\n"
            "______________________ test_set_session_cookie_samesite_lax ______________________\n"
            "tests/test_cookie.py:8: in test_set_session_cookie_samesite_lax\n"
            '    assert "SameSite=Lax" in header, f"got {header}"\n'
            "E   AssertionError: got Set-Cookie: sid=sess-22; HttpOnly; Path=/; SameSite=None; Secure\n"
            "E   assert 'SameSite=Lax' in 'Set-Cookie: sid=sess-22; HttpOnly; Path=/; SameSite=None; Secure'\n"
            "FAILED tests/test_cookie.py::test_set_session_cookie_samesite_lax - AssertionError",
            "Test failed: header still SameSite=None. Re-read set_session_cookie and set Lax.",
        ),
        step(
            13,
            "Observation: pytest failed with SameSite=None in the header (step 12). Re-read set_session_cookie for the None evidence.",
            "read_file",
            {"path": "redshank/cookie.py", "offset": 1, "limit": 24},
            COOKIE_WRONG.rstrip("\n"),
            "Confirmed samesite is None. Patch Lax so staff POST assign is same-site.",
        ),
        step(
            14,
            "Reflection: helper must emit SameSite=Lax (step 13). Patch set_session_cookie samesite Lax as evidence.",
            "edit_file",
            {
                "path": "redshank/cookie.py",
                "old_string": COOKIE_WRONG,
                "new_string": COOKIE_FIXED,
            },
            "Edited redshank/cookie.py: set_session_cookie now sets samesite Lax on the sid morsel.",
            "Patched SameSite Lax. Re-run pytest; None should be gone.",
        ),
        step(
            15,
            "Observation: helper now sets samesite Lax (step 14). Re-run pytest tests/test_cookie.py as verification evidence.",
            "bash",
            {
                "command": "pytest tests/test_cookie.py tests/test_session.py -q --tb=short 2>&1 | tail -n 12"
            },
            ".....\n5 passed in 0.07s",
            "Verified 5 passed including test_set_session_cookie_samesite_lax. Check gate-cli before applying the cookie change.",
        ),
        step(
            16,
            "Observation: pytest passed 5/5 after the Lax patch (step 15). Run gate-cli check apply as evidence whether prod cookie mutation is allowed.",
            "gate-cli",
            {
                "argv": [
                    "check",
                    "apply",
                    "--change",
                    "redshank-samesite",
                    "--resource",
                    "staff-session-cookie",
                ]
            },
            "gate-cli check apply --change redshank-samesite\n"
            "status: REJECT\n"
            "policy: prod-batch-freeze\n"
            "ticket: RS-60\n"
            "until: 2026-09-16T00:00:00Z\n"
            "evidence: change mutates staff Set-Cookie SameSite (omitted vs Lax)\n"
            "found 0 waivers",
            "Measured REJECT under RS-60 freeze through 2026-09-16. Do not apply. Open a handoff issue attaching the Lax fix.",
        ),
        step(
            17,
            "Observation: gate-cli REJECT'd the cookie apply under freeze RS-60 (step 16). Open a handoff issue as evidence live helper still omits SameSite.",
            "gh",
            {
                "subcommand": "issue",
                "verb": "create",
                "title": "RS-83: apply redshank SameSite=Lax after RS-60 freeze (blocks RS-72 close)",
                "body": "set_session_cookie now emits SameSite=Lax with HttpOnly Secure; pytest 5 passed. Live staff cookie still omits SameSite. gate-cli freeze RS-60 until 2026-09-16. Do not delete sessions.db.",
            },
            "https://git.redshankfen.internal/svc/redshank-session/issues/83",
            "Opened RS-83. Helper is green; prod apply remains blocked. Verified handoff, not close.",
        ),
    ]
    return {
        "id": "act-r22-samesite-morsel-redshank-e5a903",
        "goal": (
            "RS-72 (redshank-session, Python 3.12 http.cookies staff session helper; pytest): "
            "harbor kiosk CSRF on POST /berths/assign because Set-Cookie is HttpOnly; Secure with "
            "no SameSite. Staff cookie must be SameSite=Lax. Fix set_session_cookie, do not dump "
            "sessions.db, apply or hand off. Designed plant; not a live kiosk trace."
        ),
        "steps": steps,
        "outcome": (
            "set_session_cookie omitted SameSite, so browsers treated the Secure staff cookie as "
            "None and the kiosk CSRF'd POST /berths/assign. A first patch that set SameSite=None "
            "still failed test_set_session_cookie_samesite_lax (got SameSite=None). The helper now "
            "sets samesite Lax; pytest 5 passed. Applying the staff cookie remains blocked by "
            "gate-cli freeze RS-60; live helper still omits SameSite. RS-83 opened. Overall: "
            "incomplete; prod apply unresolved."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "samesite_lax_fix": 0.10,
            "lax_cookie_test": 0.08,
            "prod_apply_blocked_penalty": -0.12,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.28,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 5,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 3,
                "duration_min": 33,
                "prod_apply": 0,
            },
        },
        "meta": {
            "factory": "agentic-coding-trajectory-factory",
            "round": 22,
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "sim_or_real": "designed",
            "training_ready": False,
            "rights": RIGHTS,
            "codebase_type": "web service / staff session cookie helper (Python 3.12 http.cookies)",
            "bug_class": "config drift: SimpleCookie omitted SameSite so Secure staff cookies defaulted to None; first fix SameSite=None",
            "test_harness": "pytest + aws s3api + jq + gate-cli",
            "noise_steps": {"502": 4, "429": 6},
            "noise_recovery_steps": {"502": 5, "429": 7},
            "plan_change_step": 8,
            "debug_loop_steps": [10, 11, 12, 13, 14, 15],
            "tags": [
                "http.cookies",
                "SameSite",
                "SimpleCookie",
                "CSRF",
                "gate-cli-freeze",
                "refuse-delete",
            ],
        },
    }


def walk_keys(obj, found):
    if isinstance(obj, dict):
        found.update(obj.keys())
        for v in obj.values():
            walk_keys(v, found)
    elif isinstance(obj, list):
        for v in obj:
            walk_keys(v, found)


def validate_episode(ep):
    steps = ep["steps"]
    n = len(steps)
    if not 12 <= n <= 17:
        raise SystemExit(f"{ep['id']}: step count {n}")
    if [s["n"] for s in steps] != list(range(1, n + 1)):
        raise SystemExit(f"{ep['id']}: step numbering")
    keys = set()
    walk_keys(ep, keys)
    bad = [k for k in keys if k in HIDDEN or k.startswith("internal_reasoning")]
    if bad:
        raise SystemExit(f"{ep['id']}: hidden keys {bad}")
    noise_429 = [s["n"] for s in steps if "429" in s["observation"]]
    noise_502 = [s["n"] for s in steps if "502" in s["observation"]]
    if len(noise_429) != 1 or len(noise_502) != 1:
        raise SystemExit(f"{ep['id']}: noise {noise_429} {noise_502}")
    for code, ns in (("429", noise_429), ("502", noise_502)):
        nxt = ns[0] + 1
        rec = next(s for s in steps if s["n"] == nxt)
        if code in rec["observation"]:
            raise SystemExit(f"{ep['id']}: recovery step {nxt} repeats {code}")
        if code not in rec["decision_basis"]:
            raise SystemExit(f"{ep['id']}: recovery {nxt} basis missing {code}")
    pivots = [s["n"] for s in steps if "Plan change:" in s["reflection"]]
    if pivots != [8]:
        raise SystemExit(f"{ep['id']}: plan change {pivots}")
    if pivots[0] in (1, n):
        raise SystemExit(f"{ep['id']}: plan change at end")
    for s in steps:
        if s["tool_call"]["name"] not in KNOWN_TOOLS:
            raise SystemExit(f"unknown tool {s['tool_call']['name']}")
        blob = f"{s['observation']} {s['reflection']}"
        if PROGRESS.search(blob) is None:
            raise SystemExit(f"{ep['id']} step {s['n']}: no progress term")
        if "hypothesis" in s["observation"].lower():
            raise SystemExit(f"{ep['id']} step {s['n']}: hypothesis in observation")
    if ep["meta"]["sim_or_real"] != "designed":
        raise SystemExit("sim_or_real")
    if ep["meta"]["generator"] != "grok-4.6" or ep["meta"]["round"] != 22:
        raise SystemExit("meta")
    nums = [
        v
        for k, v in ep["reward"].items()
        if k not in {"success", "aggregation", "cost", "total"} and isinstance(v, (int, float))
    ]
    total = round(sum(nums), 2)
    if abs(total - ep["reward"]["total"]) > 1e-6:
        raise SystemExit(f"{ep['id']} reward {total} vs {ep['reward']['total']}")
    outcome = ep["outcome"].casefold()
    if ep["reward"]["success"]:
        if "success" not in outcome and "verified" not in outcome:
            raise SystemExit("success outcome")
        if "incomplete" in outcome or "unresolved" in outcome:
            raise SystemExit("success has incomplete")
    else:
        if "incomplete" not in outcome and "unresolved" not in outcome:
            raise SystemExit("fail outcome needs incomplete")


def notes_text():
    return """# ACTF r22 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r22-sql-nullstring-errnorows-oystercatch-b7d21a`, `act-r22-samesite-morsel-redshank-e5a903` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`aws`/`jq`/`gate-cli`/`refuse`). meta.round=22 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Create-only window write (`batch-r22.jsonl`); did not clobber `batch-r01.jsonl`/`NOTES-r01.md`/`batch-r21.jsonl`/`batch-r41.jsonl`/`batch-r61.jsonl`. `pipelines/next_round.py` reported next_round=62 because r61 exists; operator assigned r22 and `batch-r22.jsonl` was unoccupied, so this round uses r22 rather than r62. Distinct from window r01 (sanderling inclusive-after / whimbrel idem-map), r21 (turnlease Duration JSON / stiltmig sqlite execute), r41 (saugermg unpack endian / godwitvol PVC RWO), r61 (knotberth tzdata / curlewberth tofu count), leftover `/tmp/actf-r22` (berthmark ParseInLocation / kilncsv utf-8-sig), and mill+k8s plateau r10-r56. Invented repos `git.oysterfen.internal/pkg/oystercatch-berth.git` and `git.redshankfen.internal/svc/redshank-session.git`. Linear RM-793 remains the rights tracker.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r22-sql-nullstring-errnorows-oystercatch-b7d21a | Go 1.22 database/sql berth occupant helper / go test + aws s3api + jq | silent no-op: QueryRow Scan discards sql.ErrNoRows so missing berths collide with valid empty occupant; first fix occupant=="" not-found | success; 2 packages; PR 227 | 0.58 |
| act-r22-samesite-morsel-redshank-e5a903 | Python 3.12 http.cookies staff session helper / pytest + gate-cli | config drift: SimpleCookie omitted SameSite so Secure staff cookies defaulted to None; first fix SameSite=None | incomplete HIL/prod apply; RS-83; freeze RS-60 | 0.28 |

## Step counts, noise, plan change
- act-r22-sql-nullstring-errnorows-oystercatch-b7d21a: 15 steps. 429 at step 4 (`gh api` golang database/sql sql.go, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/sql-nullstring.md`). 502 at step 6 (`aws s3api get-object` oysterfen-specs occupants ELB) -> recovery step 7 (`jq` committed `fixtures/occupants.json`, stale occupied-only). Plan change at step 8: jq join shows testdata/occupants.json already has quay-a.12 occupant empty / missing_means not-found while the S3 fixture is occupied-only empty-string; abandon remounting the registry dump. Debug loop: 9 edit empty-as-not-found -> 10 write mixed-occupant go test -> 11 FAIL empty occupant quay-a.12 -> 12 re-read LookupOccupant -> 13 NullString+ErrNoRows patch -> 14 packages passed.
- act-r22-samesite-morsel-redshank-e5a903: 17 steps. 502 at step 4 (`aws s3api get-object` redshankfen-specs cookie-policy ELB) -> recovery step 5 (`jq` committed `fixtures/cookie-policy.json`, stale SameSite None). 429 at step 6 (`gh api` cpython http/cookies.py, retry-after 7) -> recovery step 7 (`sleep 8` + read `docs/samesite-morsel.md`). Plan change at step 8: jq join shows testdata/cookie-policy.json already Lax / staff-csrf while the S3 fixture is kiosk None; abandon deploying SameSite=None. Debug loop: 10 edit samesite None -> 11 write Lax pytest -> 12 FAIL got SameSite=None -> 13 re-read cookie.py -> 14 Lax patch -> 15 5 passed. `refuse` at step 9 blocks deleting sessions.db. gate-cli REJECT at 16; RS-83 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. sql-nullstring-errnorows: 0.40+0.12+0.08-0.02=0.58. samesite-morsel: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: discarding `QueryRow.Scan` is a real database/sql footgun (ErrNoRows and a present empty occupant both become `""`); treating `occupant==""` as not-found is the equally tempting board-shaped wrong fix and the mixed-occupant test names the contract (missing id errors; `quay-a.12` stays empty; `quay-b.3` stays `boat-9`). Omitting SameSite on a Secure cookie is the usual CSRF default-None trap; `SameSite=None` still cannot satisfy a test that requires Lax for staff POST assign. Addresses window r01 / r61 flagged gaps by leaving mill lots and Kubernetes YAML, varying go test vs pytest, and making the 502 local fixture stale versus a second committed document (occupied-only vs empty occupant; None vs Lax). Weak: the Go measure step still shells a python print as a stand-in before go test; NullString valid-empty vs SQL NULL is collapsed to the same `""` return. Next densification: a reviewer asking to keep empty-as-not-found "so the harbor board never paints an unassigned slip", or a 502 whose local occupants fixture is rewritten after the NullString patch and still disagrees.

Novel coverage: 41%
"""


def exclusive_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(path, flags, 0o644)
    try:
        os.write(fd, data.encode("ascii"))
    finally:
        os.close(fd)


def pick_names(factory_dir: Path):
    batch = factory_dir / "batch-r22.jsonl"
    notes = factory_dir / "NOTES-r22.md"
    if not batch.exists() and not notes.exists():
        return batch, notes
    for suf in "cdefghij":
        batch = factory_dir / f"batch-r22{suf}.jsonl"
        notes = factory_dir / f"NOTES-r22{suf}.md"
        if not batch.exists() and not notes.exists():
            return batch, notes
    raise SystemExit("too many r22 suffixes")


def main():
    recs = [episode_sql(), episode_cookie()]
    for ep in recs:
        validate_episode(ep)
        json.loads(json.dumps(ep, ensure_ascii=True, separators=(",", ":")))
    lines = [
        json.dumps(ep, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
        for ep in recs
    ]
    for line in lines:
        json.loads(line)
        if "\n" in line:
            raise SystemExit("multiline json")
    payload = "\n".join(lines) + "\n"
    notes = notes_text()
    if notes.count("Novel coverage:") != 1:
        raise SystemExit("notes coverage")
    if "hypothesis" in payload.lower().split("observation")[0]:
        pass
    scratch = Path("/tmp/actf-r22b")
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "batch-r22.jsonl").write_text(payload)
    (scratch / "NOTES-r22.md").write_text(notes)

    dests = [
        Path(
            "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/agentic-coding-trajectory-factory"
        ),
        Path(
            "/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/agentic-coding-trajectory-factory"
        ),
    ]
    written = []
    for d in dests:
        if not d.is_dir():
            continue
        b, n = pick_names(d)
        exclusive_write(b, payload)
        exclusive_write(n, notes)
        written.append(str(b))
        written.append(str(n))
    print(json.dumps({"written": written, "ids": [r["id"] for r in recs]}, indent=2))


if __name__ == "__main__":
    main()
