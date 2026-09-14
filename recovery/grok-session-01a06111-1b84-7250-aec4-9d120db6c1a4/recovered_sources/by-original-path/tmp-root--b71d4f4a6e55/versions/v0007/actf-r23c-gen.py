#!/usr/bin/env python3
"""Create-only ACTF r23c episodes. Never overwrite factory files."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

FACTORY = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "agentic-coding-trajectory-factory"
)
BATCH = FACTORY / "batch-r23c.jsonl"
NOTES = FACTORY / "NOTES-r23c.md"
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
HIDDEN = {
    "thought",
    "chain_of_thought",
    "scratch",
    "reasoning",
    "inner_monologue",
    "internal_reasoning",
}
VISIBLE = ("Plan: ", "Observation: ", "Reflection: ", "Tool call: ")
PROGRESS = (
    "found",
    "measured",
    "reproduced",
    "failed",
    "edited",
    "tested",
    "verified",
    "patched",
)
RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-02T20:10:00Z",
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


def db(text: str) -> str:
    text = text.strip()
    if not text.startswith(VISIBLE):
        raise SystemExit(f"decision_basis prefix: {text[:80]!r}")
    n = len(text)
    if n < 80 or n > 240:
        raise SystemExit(f"decision_basis len {n}: {text}")
    return text


def step(n, decision_basis, tool_call, observation, reflection=None, plan=None):
    out = {
        "n": n,
        "decision_basis": db(decision_basis),
        "tool_call": tool_call,
        "observation": observation,
    }
    if reflection is not None:
        out["reflection"] = reflection
    if plan is not None:
        out["plan"] = plan
    blob = (reflection or "") + " " + observation
    if not any(p in blob.lower() for p in PROGRESS):
        raise SystemExit(f"step {n} missing progress term")
    if "hypothesis" in observation.lower():
        raise SystemExit(f"step {n} observation contains hypothesis")
    return out


def walk_keys(obj, acc):
    if isinstance(obj, dict):
        for k, v in obj.items():
            acc.add(k)
            walk_keys(v, acc)
    elif isinstance(obj, list):
        for item in obj:
            walk_keys(item, acc)


META_BASE = {
    "factory": "agentic-coding-trajectory-factory",
    "round": 23,
    "generator": "grok-4.6",
    "run_label": "2026-09-02-final-heavy",
    "sim_or_real": "designed",
    "training_ready": False,
    "rights": RIGHTS,
}


PATH_GO = """package radar

import "net/url"

func DestPath(dest string) string {
    return "/radar/dest/" + url.QueryEscape(dest)
}
"""

PATH_GO_WRONG = """package radar

import (
    "net/url"
    "strings"
)

func DestPath(dest string) string {
    return "/radar/dest/" + strings.ReplaceAll(url.QueryEscape(dest), "+", "%20")
}
"""

PATH_GO_FIX = """package radar

import "net/url"

func DestPath(dest string) string {
    return "/radar/dest/" + url.PathEscape(dest)
}
"""

PATH_TEST = """package radar

import "testing"

func TestDestPathMixedSpaceAndPlus(t *testing.T) {
    got := DestPath("berth a")
    if got != "/radar/dest/berth%20a" {
        t.Fatalf("space got=%q want=/radar/dest/berth%%20a", got)
    }
    got = DestPath("radar+hex")
    if got != "/radar/dest/radar+hex" {
        t.Fatalf("plus got=%q want=/radar/dest/radar+hex", got)
    }
    got = DestPath("radar.hex")
    if got != "/radar/dest/radar.hex" {
        t.Fatalf("dot got=%q", got)
    }
}
"""

RENDER_PY = """from string import Template


def render_dest(row: dict) -> str:
    body = Template("$berth/$quay/$slip").safe_substitute(row)
    note = row.get("note", "")
    return f"{body} {note}".rstrip()
"""

RENDER_PY_WRONG = """from string import Template


def render_dest(row: dict) -> str:
    body = Template("$berth/$quay/$slip").safe_substitute(row)
    note = row.get("note", "")
    text = f"{body} {note}".rstrip()
    return text.replace("$slip", row.get("slip", ""))
"""

RENDER_PY_FIX = """from string import Template

REQUIRED = ("berth", "quay", "slip")


def render_dest(row: dict) -> str:
    for key in REQUIRED:
        if key not in row:
            raise KeyError(key)
    body = Template("$berth/$quay/$slip").substitute(row)
    note = row.get("note", "")
    return f"{body} {note}".rstrip()
"""

RENDER_TEST = """from merganser.tpl import render_dest
import pytest


def test_render_dest_complete():
    assert render_dest({"berth": "A01", "quay": "north", "slip": "12"}) == "A01/north/12"


def test_render_dest_missing_slip_raises():
    with pytest.raises(KeyError):
        render_dest({"berth": "A01", "quay": "north"})


def test_render_dest_keeps_dollar_note():
    got = render_dest({"berth": "A01", "quay": "north", "slip": "12", "note": "$slipway"})
    assert got == "A01/north/12 $slipway"
"""


ep1_steps = [
    step(
        1,
        "Plan: SP-230 reports DestPath emitting berth+a while dest want is berth%20a. Search DestPath and QueryEscape as evidence of plus encoding.",
        {"name": "search", "args": {"pattern": "DestPath|QueryEscape|PathEscape|url.Query", "path": "."}},
        "dest/path.go:6:func DestPath(dest string) string {\ndest/path.go:7:    return \"/radar/dest/\" + url.QueryEscape(dest)\ndest/path_test.go:8:got := DestPath(\"berth a\")\nfound 5 matches",
        "Found DestPath wrapping QueryEscape. Next read the helper.",
        "1) search DestPath 2) read path.go 3) measure QueryEscape 4) confirm dest-paths 5) PathEscape mixed dests 6) regression + PR",
    ),
    step(
        2,
        "Observation: path.go:7 DestPath concatenates url.QueryEscape (step 1). Read the helper as evidence of any PathEscape branch.",
        {"name": "read_file", "args": {"path": "dest/path.go", "offset": 1, "limit": 24}},
        PATH_GO.rstrip("\n"),
        "Found QueryEscape is the only encoder. First plan: dest catalog stored plus-for-space. Next measure encodings.",
    ),
    step(
        3,
        "Observation: DestPath is QueryEscape only (step 2). Measure QueryEscape versus PathEscape as evidence plus-for-space and plus-dest diverge.",
        {
            "name": "bash",
            "args": {
                "command": "python3 - <<'PY'\nprint('QueryEscape berth a -> berth+a')\nprint('QueryEscape radar+hex -> radar%2Bhex')\nprint('PathEscape berth a -> berth%20a')\nprint('PathEscape radar+hex -> radar+hex')\nprint('found QueryEscape plus-for-space and %2B on literal plus')\nPY"
            },
        },
        "QueryEscape berth a -> berth+a\nQueryEscape radar+hex -> radar%2Bhex\nPathEscape berth a -> berth%20a\nPathEscape radar+hex -> radar+hex\nfound QueryEscape plus-for-space and %2B on literal plus",
        "Measured QueryEscape mapping space to plus and plus to %2B. Next confirm committed dest-paths.",
    ),
    step(
        4,
        "Reflection: QueryEscape mapped space to plus and plus to %2B (step 3). Fetch net/url QueryEscape notes via gh as evidence of plus encoding.",
        {
            "name": "gh",
            "args": {
                "subcommand": "api",
                "method": "GET",
                "path": "repos/golang/go/contents/src/net/url/url.go",
            },
        },
        "HTTP/2 429\nretry-after: 5\nx-ratelimit-limit: 60\nx-ratelimit-remaining: 0\n{\"message\":\"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=5\",\"documentation_url\":\"https://docs.github.com/rest/overview/rate-limits\"}",
        "Found GitHub 429 with retry-after 5 while fetching net/url notes. Wait, then use the vendored docs/queryescape-path.md fixture.",
    ),
    step(
        5,
        "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/queryescape-path.md as local-docs evidence.",
        {"name": "read_file", "args": {"path": "docs/queryescape-path.md", "offset": 1, "limit": 16}},
        "1  net/url QueryEscape encodes space as plus and plus as %2B (query form).\n2  PathEscape encodes space as %20 and leaves plus unescaped in a path segment.\n3  Dest paths are path segments, not query strings; plus-for-space 404s radar.hex lookups.\n4  strings.ReplaceAll(QueryEscape(dest), \"+\", \"%20\") fixes berth a and leaves radar+hex as %2B.\n5  Durable: url.PathEscape(dest) so space is %20 and dest plus stays plus.\n6  Remounting the dest catalog to store plus-for-space is not required and hides radar+hex.",
        "Verified PathEscape is the dest-path encoder. Next pull dest-paths from specs.",
    ),
    step(
        6,
        "Observation: docs say PathEscape keeps dest plus and encodes space as %20 (step 5). Get the specs object as evidence of dest path shapes.",
        {
            "name": "aws",
            "args": {
                "argv": [
                    "s3api",
                    "get-object",
                    "--bucket",
                    "snipefen-specs",
                    "--key",
                    "snipepath/dest-paths.json",
                    "/tmp/snipepath-dest-paths.json",
                ]
            },
        },
        "download failed: s3.eu-west-1.amazonaws.com/snipefen-specs\nHTTP/1.1 502 Bad Gateway\nserver: awselb/2.0\nupstream connect error or disconnect/reset before headers. reset reason: connection failure",
        "Measured a bad gateway on the ELB before headers. Retry against the committed fixtures/dest-paths.json instead of the edge.",
    ),
    step(
        7,
        "Observation: specs get-object returned 502 from the ELB (step 6). jq fixtures/dest-paths.json dest rows as local-spec evidence.",
        {
            "name": "jq",
            "args": {
                "argv": [
                    "-r",
                    "{space:.rows.space,plus:.rows.plus,encoder:.encoder}",
                    "fixtures/dest-paths.json",
                ]
            },
        },
        "{\n  \"space\": \"/radar/dest/berth+a\",\n  \"plus\": \"/radar/dest/radar%2Bhex\",\n  \"encoder\": \"query-escape\"\n}",
        "Found local specs fixture still lists plus-for-space paths. Next join testdata/dest-paths.json from the failing radar.",
    ),
    step(
        8,
        "Observation: fixtures/dest-paths.json still has plus-for-space berth+a (step 7). jq testdata/dest-paths.json as evidence whether %20 and literal plus are already the contract.",
        {
            "name": "jq",
            "args": {
                "argv": [
                    "-n",
                    "--slurpfile",
                    "a",
                    "fixtures/dest-paths.json",
                    "--slurpfile",
                    "b",
                    "testdata/dest-paths.json",
                    "{stale:$a[0].rows.space,want:$b[0].rows.space,plus:$b[0].rows.plus}",
                ]
            },
        },
        "{\n  \"stale\": \"/radar/dest/berth+a\",\n  \"want\": \"/radar/dest/berth%20a\",\n  \"plus\": \"/radar/dest/radar+hex\"\n}",
        "Plan change: testdata/dest-paths.json already has berth%20a and radar+hex while the S3 fixture is a stale QueryEscape document. Found PathEscape is the live contract. Abandon remounting the dest catalog. Switching the edit target to DestPath so space is %20 and plus stays plus.",
    ),
    step(
        9,
        "Reflection: pivoting off the remount-catalog plan; testdata already wants %20 and literal plus (step 8). Edit DestPath to rewrite plus as %20.",
        {
            "name": "edit_file",
            "args": {
                "path": "dest/path.go",
                "old_string": PATH_GO,
                "new_string": PATH_GO_WRONG,
            },
        },
        "Edited dest/path.go: DestPath now rewrites QueryEscape plus tokens to %20.",
        "Wrote a plus-to-%20 rewrite on QueryEscape. Add a go test that requires mixed dests.",
    ),
    step(
        10,
        "Observation: DestPath now rewrites QueryEscape plus to %20 (step 9). Write a go test as evidence that space and literal plus must diverge.",
        {
            "name": "write_file",
            "args": {"path": "dest/path_test.go", "content": PATH_TEST},
        },
        "Wrote dest/path_test.go (24 lines).",
        "Found a mixed-dest regression file. Run go test to reproduce radar+hex still %2B.",
    ),
    step(
        11,
        "Plan: run go test ./dest as evidence whether plus-to-%20 rewrite still encodes radar+hex as %2B.",
        {
            "name": "bash",
            "args": {"command": "go test ./dest -count=1 -timeout 30s 2>&1 | tail -n 24"},
        },
        "--- FAIL: TestDestPathMixedSpaceAndPlus (0.00s)\n    path_test.go:12: plus got=\"/radar/dest/radar%2Bhex\" want=/radar/dest/radar+hex\nFAIL\nFAIL\tgit.snipefen.internal/pkg/snipepath-radar/dest\t0.01s\nFAIL",
        "Test failed: radar+hex became %2B. Re-read DestPath and reject a keep-Replace review.",
    ),
    step(
        12,
        "Observation: go test failed with radar%2Bhex on plus rewrite (step 11). Read the keep-Replace review as evidence whether dest may stay QueryEscape-shaped.",
        {"name": "read_file", "args": {"path": "docs/review-keep-plus.md", "offset": 1, "limit": 16}},
        "1  Reviewer (SP-230 comment 4): keep strings.ReplaceAll plus-to-%20 so operators can grep berth+a from runbooks.\n2  Claim: radar+hex partners are legacy and bookmarks still match on %2Bhex.\n3  Dest contract named in testdata/dest-paths.json is berth%20a and radar+hex.\n4  Reject keep-Replace; PathEscape is the dest-path encoder.\n5  Do not remount the catalog to store QueryEscape output.",
        "Verified keep-Replace is rejected; dest want is PathEscape. Re-read DestPath and switch encoders.",
    ),
    step(
        13,
        "Observation: keep-Replace review was rejected; dest want stays PathEscape (step 12). Re-read DestPath for the QueryEscape rewrite evidence.",
        {"name": "read_file", "args": {"path": "dest/path.go", "offset": 1, "limit": 32}},
        PATH_GO_WRONG.rstrip("\n"),
        "Found DestPath still QueryEscape-rewrites plus. Patch url.PathEscape so space and plus diverge.",
    ),
    step(
        14,
        "Reflection: DestPath must PathEscape dest segments (step 13). Patch dest/path.go as evidence.",
        {
            "name": "edit_file",
            "args": {
                "path": "dest/path.go",
                "old_string": PATH_GO_WRONG,
                "new_string": PATH_GO_FIX,
            },
        },
        "Edited dest/path.go: DestPath now uses url.PathEscape on the dest segment.",
        "Patched PathEscape. Re-run go test; berth a should be %20 and radar+hex should stay plus.",
    ),
    step(
        15,
        "Observation: helper now uses PathEscape (step 14). Re-run go test ./dest as verification evidence.",
        {
            "name": "bash",
            "args": {
                "command": "go test ./dest ./cmd/snipepath -count=1 -timeout 30s 2>&1 | tail -n 12"
            },
        },
        "ok  \tgit.snipefen.internal/pkg/snipepath-radar/dest\t0.02s\nok  \tgit.snipefen.internal/pkg/snipepath-radar/cmd/snipepath\t0.01s\nPASS",
        "Verified 2 packages passed including TestDestPathMixedSpaceAndPlus. Open the replacement PR.",
    ),
    step(
        16,
        "Observation: go test passed dest and cmd/snipepath after the PathEscape patch (step 15). Open PR 230 as evidence the mixed dest split landed.",
        {
            "name": "gh",
            "args": {
                "subcommand": "pr",
                "verb": "create",
                "title": "SP-230: PathEscape dest segments (space %20, plus stays plus)",
                "body": "DestPath uses url.PathEscape so berth a is /radar/dest/berth%20a and radar+hex stays plus. go test ./dest ./cmd/snipepath passed. Do not remount the dest catalog; fixtures/dest-paths.json is stale versus testdata/dest-paths.json.",
            },
        },
        "https://git.snipefen.internal/pkg/snipepath-radar/pull/230",
        "Opened PR 230. Mixed space/plus encoder is green. Verified SP-230 is ready for review.",
    ),
]

ep2_steps = [
    step(
        1,
        "Plan: MG-72 reports dest labels printing leftover $slip when slip is omitted. Search render_dest and Template as evidence of safe_substitute.",
        {
            "name": "search",
            "args": {"pattern": "render_dest|safe_substitute|Template\\(|\\$slip", "path": "."},
        },
        "merganser/tpl.py:4:def render_dest(row: dict) -> str:\nmerganser/tpl.py:5:    body = Template(\"$berth/$quay/$slip\").safe_substitute(row)\nmerganser/tpl.py:6:    note = row.get(\"note\", \"\")\nfound 6 matches",
        "Found render_dest using Template.safe_substitute. Next read the helper.",
        "1) search render_dest 2) read tpl.py 3) measure leftover $slip 4) confirm traces 5) required-key substitute 6) regression + apply-or-handoff",
    ),
    step(
        2,
        "Observation: tpl.py:5 render_dest calls Template.safe_substitute (step 1). Read the helper as evidence of any required-key check.",
        {"name": "read_file", "args": {"path": "merganser/tpl.py", "offset": 1, "limit": 24}},
        RENDER_PY.rstrip("\n"),
        "Found missing identifiers stay as $slip. First plan: dest INI stored optional slip. Next measure leftover tokens.",
    ),
    step(
        3,
        "Observation: render_dest never requires slip (step 2). Measure safe_substitute as evidence a missing slip leaves $slip in the dest label.",
        {
            "name": "bash",
            "args": {
                "command": "python3 - <<'PY'\nfrom string import Template\nprint(Template('$berth/$quay/$slip').safe_substitute({'berth':'A01','quay':'north'}))\nprint('found leftover $slip on missing key')\nPY"
            },
        },
        "A01/north/$slip\nfound leftover $slip on missing key",
        "Measured leftover $slip when slip is omitted. Next confirm the committed dest-label object.",
    ),
    step(
        4,
        "Observation: missing slip leaves $slip in the label (step 3). Get the dest-labels object as evidence of the required-key contract.",
        {
            "name": "aws",
            "args": {
                "argv": [
                    "s3api",
                    "get-object",
                    "--bucket",
                    "merganserfen-specs",
                    "--key",
                    "mergansertpl/dest-labels.json",
                    "/tmp/mergansertpl-dest-labels.json",
                ]
            },
        },
        "download failed: s3.eu-west-1.amazonaws.com/merganserfen-specs\nHTTP/1.1 502 Bad Gateway\nserver: awselb/2.0\nupstream connect error or disconnect/reset before headers. reset reason: connection failure",
        "Measured a bad gateway on the ELB before headers. Retry against the committed fixtures/dest-labels.json instead of the edge.",
    ),
    step(
        5,
        "Observation: specs get-object returned 502 from the ELB (step 4). jq fixtures/dest-labels.json leftover as local-spec evidence.",
        {
            "name": "jq",
            "args": {
                "argv": [
                    "-r",
                    "{missing_means:.missing_means,note:.note_contract}",
                    "fixtures/dest-labels.json",
                ]
            },
        },
        "{\n  \"missing_means\": \"empty-string\",\n  \"note_contract\": \"strip-dollar\"\n}",
        "Found local specs fixture still lists empty-string for missing slip. Next fetch string.Template notes.",
    ),
    step(
        6,
        "Reflection: local fixture still lists empty-string for missing slip (step 5). Fetch string.Template notes via gh as evidence of safe_substitute leftovers.",
        {
            "name": "gh",
            "args": {
                "subcommand": "api",
                "method": "GET",
                "path": "repos/python/cpython/contents/Lib/string.py",
            },
        },
        "HTTP/2 429\nretry-after: 7\nx-ratelimit-limit: 60\nx-ratelimit-remaining: 0\n{\"message\":\"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=7\",\"documentation_url\":\"https://docs.github.com/rest/overview/rate-limits\"}",
        "Found GitHub 429 with retry-after 7 while fetching string.Template notes. Wait, then use the vendored docs/template-safe.md fixture.",
    ),
    step(
        7,
        "Observation: gh api returned 429 with retry-after 7 (step 6). Sleep 8s, then read docs/template-safe.md as local-docs evidence.",
        {"name": "read_file", "args": {"path": "docs/template-safe.md", "offset": 1, "limit": 16}},
        "1  string.Template.safe_substitute leaves $name when the mapping omits name.\n2  Harbor dest labels require berth, quay, and slip; leftover $slip paints a fake dest.\n3  Notes may contain $slipway as literal text and must not be rewritten.\n4  text.replace(\"$slip\", slip or \"\") blanks missing slip and turns $slipway into {slip}way.\n5  Durable: require keys then Template.substitute; append note as a value (not re-parsed).\n6  Deleting /var/lib/merganser/templates.db to skip leftover labels is not allowed under MG-LOCK-04.",
        "Verified missing slip must raise and $slipway notes stay. Next join testdata/dest-labels.json as the live contract.",
    ),
    step(
        8,
        "Observation: docs require KeyError on missing slip and a literal $slipway note (step 7). jq testdata/dest-labels.json as evidence whether raise is already the contract.",
        {
            "name": "jq",
            "args": {
                "argv": [
                    "-n",
                    "--slurpfile",
                    "a",
                    "fixtures/dest-labels.json",
                    "--slurpfile",
                    "b",
                    "testdata/dest-labels.json",
                    "{stale:$a[0].missing_means,want:$b[0].missing_means,note:$b[0].note_contract}",
                ]
            },
        },
        "{\n  \"stale\": \"empty-string\",\n  \"want\": \"key-error\",\n  \"note\": \"keep-dollar-slipway\"\n}",
        "Plan change: testdata/dest-labels.json already has missing_means key-error and keep-dollar-slipway while the S3 fixture is a stale empty-string document. Found raise-on-missing is the live contract. Abandon stripping leftover $ tokens. Switching the edit target to render_dest so missing slip raises and $slipway stays.",
    ),
    step(
        9,
        "Reflection: pivoting off the empty-string leftover plan; testdata already wants KeyError (step 8). Refuse deleting templates.db as evidence templates must stay.",
        {
            "name": "refuse",
            "args": {
                "action": "rm /var/lib/merganser/templates.db so leftover $slip labels cannot replay",
                "policy": "MG-LOCK-04",
                "incident": "MG-72",
            },
        },
        "refused: MG-LOCK-04 forbids deleting /var/lib/merganser/templates.db to skip leftover dest labels. Delete would drop in-flight harbor templates and can fail-open empty dest rewrites. Safe alternative: patch render_dest required keys. found 0 waivers",
        "Found 0 waivers; denied the delete. Next patch render_dest; keep the templates file.",
    ),
    step(
        10,
        "Observation: delete is refused; edit target is leftover $slip (step 9). First patch: replace $slip as evidence the leftover token leaves the label.",
        {
            "name": "edit_file",
            "args": {
                "path": "merganser/tpl.py",
                "old_string": RENDER_PY,
                "new_string": RENDER_PY_WRONG,
            },
        },
        "Edited merganser/tpl.py: render_dest now replaces leftover $slip with the slip value or empty.",
        "Wrote a $slip replace decoder. Add a pytest that requires KeyError and keeps $slipway.",
    ),
    step(
        11,
        "Observation: renderer now blanks leftover $slip (step 10). Write a pytest as evidence missing slip must raise and $slipway notes stay.",
        {
            "name": "write_file",
            "args": {"path": "tests/test_render.py", "content": RENDER_TEST},
        },
        "Wrote tests/test_render.py (22 lines).",
        "Found a required-key regression file. Run pytest to reproduce empty slip versus $slipway rewrite.",
    ),
    step(
        12,
        "Plan: run pytest tests/test_render.py as evidence whether $slip replace still blanks missing slip and rewrites $slipway.",
        {
            "name": "bash",
            "args": {"command": "pytest tests/test_render.py -q --tb=short 2>&1 | tail -n 22"},
        },
        ".FF\n=================================== FAILURES ===================================\n______________________ test_render_dest_missing_slip_raises ______________________\ntests/test_render.py:10: in test_render_dest_missing_slip_raises\n    render_dest({\"berth\": \"A01\", \"quay\": \"north\"})\nE   Failed: DID NOT RAISE KeyError\n______________________ test_render_dest_keeps_dollar_note ______________________\ntests/test_render.py:16: in test_render_dest_keeps_dollar_note\n    assert got == \"A01/north/12 $slipway\"\nE   AssertionError: assert 'A01/north/12 12way' == 'A01/north/12 $slipway'\nFAILED tests/test_render.py::test_render_dest_missing_slip_raises - Failed: DID NOT RAISE KeyError\nFAILED tests/test_render.py::test_render_dest_keeps_dollar_note - AssertionError",
        "Test failed: missing slip did not raise and $slipway became 12way. Re-read render_dest and require keys.",
    ),
    step(
        13,
        "Observation: pytest failed with DID NOT RAISE and 12way (step 12). Re-read render_dest for the $slip replace evidence.",
        {"name": "read_file", "args": {"path": "merganser/tpl.py", "offset": 1, "limit": 24}},
        RENDER_PY_WRONG.rstrip("\n"),
        "Found $slip is replaced including inside $slipway. Patch required keys plus substitute.",
    ),
    step(
        14,
        "Reflection: helper must KeyError on missing slip and keep $slipway notes (step 13). Patch render_dest as evidence.",
        {
            "name": "edit_file",
            "args": {
                "path": "merganser/tpl.py",
                "old_string": RENDER_PY_WRONG,
                "new_string": RENDER_PY_FIX,
            },
        },
        "Edited merganser/tpl.py: render_dest now requires berth/quay/slip and substitutes only those identifiers.",
        "Patched required-key substitute. Re-run pytest; leftover $slip should raise and $slipway should stay.",
    ),
    step(
        15,
        "Observation: helper now requires keys then substitute (step 14). Re-run pytest tests/test_render.py as verification evidence.",
        {
            "name": "bash",
            "args": {
                "command": "pytest tests/test_render.py tests/test_catalog.py -q --tb=short 2>&1 | tail -n 12"
            },
        },
        ".....\n5 passed in 0.07s",
        "Verified 5 passed including test_render_dest_missing_slip_raises. Check gate-cli before applying the label change.",
    ),
    step(
        16,
        "Observation: pytest passed 5/5 after the required-key patch (step 15). Run gate-cli check apply as evidence whether prod dest-label mutation is allowed.",
        {
            "name": "gate-cli",
            "args": {
                "argv": [
                    "check",
                    "apply",
                    "--change",
                    "merganser-template",
                    "--resource",
                    "harbor-dest-label",
                ]
            },
        },
        "gate-cli check apply --change merganser-template\nstatus: REJECT\npolicy: prod-batch-freeze\nticket: MG-60\nuntil: 2026-09-16T00:00:00Z\nevidence: change mutates dest label rendering (leftover $slip vs KeyError)\nfound 0 waivers",
        "Measured REJECT under MG-60 freeze through 2026-09-16. Do not apply. Open a handoff issue attaching the required-key fix.",
    ),
    step(
        17,
        "Observation: gate-cli REJECT'd the dest-label apply under freeze MG-60 (step 16). Open a handoff issue as evidence live helper still leaves $slip.",
        {
            "name": "gh",
            "args": {
                "subcommand": "issue",
                "verb": "create",
                "title": "MG-83: apply merganser required-key dest labels after MG-60 freeze (blocks MG-72 close)",
                "body": "render_dest now KeyErrors on missing slip and keeps $slipway notes; pytest 5 passed. Live helper still safe_substitutes leftover $slip. gate-cli freeze MG-60 until 2026-09-16. Do not delete templates.db.",
            },
        },
        "https://git.merganserfen.internal/cli/mergansertpl-harbor/issues/83",
        "Opened MG-83. Helper is green; prod apply remains blocked. Verified handoff, not close.",
    ),
]


ep1 = {
    "id": "act-r23c-queryescape-plus-snipepath-b7d41a",
    "goal": (
        "SP-230 (snipepath-radar, Go 1.22 harbor radar dest helper + fixtures/dest-paths.json; go test): "
        "nightly radar copies print /radar/dest/berth+a while dest want is /radar/dest/berth%20a and "
        "/radar/dest/radar+hex. Find why DestPath uses QueryEscape plus-for-space, add a mixed-dest "
        "regression, and open a PR. Designed plant; not a live radar trace."
    ),
    "steps": ep1_steps,
    "outcome": (
        "DestPath used url.QueryEscape, so space became plus and dest plus became %2B. A first patch that "
        "rewrote QueryEscape plus tokens to %20 still failed TestDestPathMixedSpaceAndPlus "
        "(plus got=/radar/dest/radar%2Bhex). The helper now uses url.PathEscape; go test ./dest "
        "./cmd/snipepath passed. PR 230 opened. Overall: success; mixed space/plus dest paths verified."
    ),
    "reward": {
        "success": True,
        "task_completion": 0.4,
        "path_escape_fix": 0.12,
        "mixed_dest_go_test": 0.08,
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
        **META_BASE,
        "codebase_type": "library / harbor radar dest path helper (Go 1.22 net/url)",
        "bug_class": "schema mismatch: url.QueryEscape mapped dest space to plus and dest plus to %2B; first fix plus-to-%20 rewrite left radar+hex as %2B",
        "test_harness": "go test + aws s3api + jq",
        "noise_steps": {"429": 4, "502": 6},
        "noise_recovery_steps": {"429": 5, "502": 7},
        "plan_change_step": 8,
        "debug_loop_steps": [9, 10, 11, 12, 13, 14, 15],
        "tags": [
            "net/url",
            "QueryEscape",
            "PathEscape",
            "plus-for-space",
            "mixed-dest",
            "keep-replace-rejected",
        ],
    },
}

ep2 = {
    "id": "act-r23c-template-safe-mergansertpl-c4e918",
    "goal": (
        "MG-72 (mergansertpl-harbor, Python 3.12 dest label helper; pytest): harbor boards print leftover "
        "$slip when slip is omitted because render_dest uses Template.safe_substitute. Staff dest labels "
        "must KeyError on missing slip and keep $slipway notes. Fix render_dest, do not dump templates.db, "
        "apply or hand off. Designed plant; not a live harbor trace."
    ),
    "steps": ep2_steps,
    "outcome": (
        "render_dest used Template.safe_substitute, so missing slip left $slip on the dest board. A first "
        "patch that replaced $slip with empty or the slip value still failed test_render_dest_missing_slip_raises "
        "(DID NOT RAISE) and test_render_dest_keeps_dollar_note (got 12way). The helper now requires "
        "berth/quay/slip then substitute; pytest 5 passed. Applying dest labels remains blocked by gate-cli "
        "freeze MG-60; live helper still leaves $slip. MG-83 opened. Overall: incomplete; prod apply unresolved."
    ),
    "reward": {
        "success": False,
        "task_completion": 0.24,
        "required_key_substitute_fix": 0.1,
        "dollar_note_test": 0.08,
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
        **META_BASE,
        "codebase_type": "CLI / dest label helper (Python 3.12 string.Template)",
        "bug_class": "silent no-op: Template.safe_substitute left $slip on missing keys; first fix replace $slip blanked notes and $slipway",
        "test_harness": "pytest + aws s3api + jq + gate-cli",
        "noise_steps": {"502": 4, "429": 6},
        "noise_recovery_steps": {"502": 5, "429": 7},
        "plan_change_step": 8,
        "debug_loop_steps": [10, 11, 12, 13, 14, 15],
        "tags": [
            "string.Template",
            "safe_substitute",
            "KeyError",
            "slipway",
            "gate-cli-freeze",
            "refuse-delete",
        ],
    },
}

NOTES_TEXT = """# ACTF r23c - 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r23c-queryescape-plus-snipepath-b7d41a`, `act-r23c-template-safe-mergansertpl-c4e918` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`aws`/`jq`/`gate-cli`/`refuse`). meta.round=23 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Create-only collision write (`batch-r23c.jsonl`); did not clobber occupied `batch-r23.jsonl` / `NOTES-r23.md` (phalarope JoinHostPort / goldeneye redirect-auth) or `ROUND-r68.reserved.json`. `pipelines/next_round.py` reported next_round=68 because marker-mode legacy_baseline=67; operator assigned r23 and `batch-r23.jsonl` was already occupied, so this round uses r23c rather than r68. Distinct from window r01 (sanderling inclusive-after / whimbrel inflight Map), r02 jacanasub re.sub count-vs-flags / tattlerbool argparse bool, r03 willeturl path.Clean scheme (Clean slash-fold, not QueryEscape plus-for-space) / scauphmac utf8 length, r04 bitternid json float64 / avocetsv csv quoted comma, r21 duration-json-ns / sqlite executescript, r22 sql ErrNoRows / SameSite morsel, r23 joinhostport IPv6 brackets / redirect Authorization, r41 unpack-be-le / PVC RWO, r42 bitterncrane re.sub group10 / cormorantflag omitempty, r43 with_suffix tar.gz / csv semicolon, r61 tzdata LoadLocation / tofu count-index, r62 parsedate -0000 / dunlincut unsorted dedup, r63 pem.Decode rest / tofu moved, r63c with_suffix targz / csv semicolon kittiwake, r64 inet_aton classful 3-octet / WaitForFirstConsumer, r65 willetuid uuid bytes le / dowitchersg inline, r66 ploversplit commonprefix / tealcask s3 acl, r67 nuthatchpair zip strict / pintailrm removed, leftover `/tmp/actf-r23` (lotstem split-dot / packloom with_suffix), and mill+k8s plateau r10-r56. Addresses r23 NOTES gap (reviewer keep-wrong-fix; leave mill lots and Kubernetes YAML). Invented repos `git.snipefen.internal/pkg/snipepath-radar.git` and `git.merganserfen.internal/cli/mergansertpl-harbor.git`. Linear RM-793 remains the rights tracker.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r23c-queryescape-plus-snipepath-b7d41a | Go 1.22 harbor radar dest helper + dest-paths fixtures / go test + aws s3api + jq | schema mismatch: `url.QueryEscape` mapped space to plus so `/radar/dest/berth+a`; first fix plus-to-%20 left `radar+hex` as `%2B` | success; 2 packages; PR 230 | 0.58 |
| act-r23c-template-safe-mergansertpl-c4e918 | Python 3.12 dest label helper / pytest + gate-cli | silent no-op: `Template.safe_substitute` left `$slip`; first fix `replace(\"$slip\")` rewrote `$slipway` to `12way` | incomplete HIL/prod apply; MG-83; freeze MG-60 | 0.28 |

## Step counts, noise, plan change
- act-r23c-queryescape-plus-snipepath-b7d41a: 16 steps. 429 at step 4 (`gh api` golang/go url.go, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/queryescape-path.md`). 502 at step 6 (`aws s3api get-object` snipefen-specs dest-paths ELB) -> recovery step 7 (`jq` committed `fixtures/dest-paths.json` against stale plus-for-space). Plan change at step 8: jq join shows testdata already berth%20a / radar+hex while the S3 fixture is QueryEscape output; abandon remounting the dest catalog. Debug loop: 9 edit plus-to-%20 -> 10 write mixed-dest go test -> 11 FAIL radar%2Bhex -> 12 reviewer keep-Replace rejected -> 13 re-read DestPath -> 14 PathEscape patch -> 15 2 packages passed.
- act-r23c-template-safe-mergansertpl-c4e918: 17 steps. 502 at step 4 (`aws s3api get-object` merganserfen-specs dest-labels ELB) -> recovery step 5 (`jq` committed `fixtures/dest-labels.json`, stale empty-string). 429 at step 6 (`gh api` cpython string.py, retry-after 7) -> recovery step 7 (`sleep 8` + read `docs/template-safe.md`). Plan change at step 8: jq join shows testdata already key-error / keep-dollar-slipway while the S3 fixture is empty-string / strip-dollar; abandon stripping leftover $ tokens. Debug loop: 10 edit replace $slip -> 11 write pytest -> 12 FAIL DID NOT RAISE and 12way -> 13 re-read render_dest -> 14 required-key substitute -> 15 5 passed. `refuse` at step 9 blocks deleting templates.db. gate-cli REJECT at 16; MG-83 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. queryescape-plus: 0.40+0.12+0.08-0.02=0.58. template-safe: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: `url.QueryEscape` mapping dest space to plus is a real net/url footgun (`PathEscape` yields `%20` and leaves dest plus); `strings.ReplaceAll(..., "+", "%20")` is the equally tempting board-shaped wrong fix and the mixed-dest test names the contract (`berth a` -> `%20`, `radar+hex` stays plus, not `%2B`). `Template.safe_substitute` leaving `$slip` is the usual missing-key silent leftover; `str.replace("$slip", ...)` still cannot satisfy a test that requires KeyError on missing slip and a literal `$slipway` note. Stale 502 fallback now compares dest want `%20` / key-error against a second file still on plus-for-space / empty-string (r23 densification). Reviewer keep-Replace is an explicit rejected keep-wrong-fix (r23 densification). gate-cli freeze plus refuse-delete is an honest apply block, not a silent skip. Addresses r23 NOTES gap while leaving mill lots and Kubernetes YAML, varying go test vs pytest, and using QueryEscape plus-for-space vs Template leftover `$slip` (not JoinHostPort / redirect Authorization). Weak: the Go measure step still shells a python print as a stand-in before go test; `$slipway` is a designed note token rather than a second document whose dest still disagrees after substitute. Next densification: a 502 whose local dest-paths fixture is rewritten after the PathEscape patch and still lists berth+a, or a reviewer asking to keep safe_substitute "so incomplete dest rows still render berth/quay from runbooks".

Novel coverage: 40%
"""


def noise_hits(obs: str) -> tuple[int, int]:
    return obs.count("429"), obs.count("502")


def validate(rec: dict) -> None:
    keys = set()
    walk_keys(rec, keys)
    bad = keys & HIDDEN
    if bad:
        raise SystemExit(f"{rec['id']} hidden keys {bad}")
    steps = rec["steps"]
    ns = [s["n"] for s in steps]
    if ns != list(range(1, len(steps) + 1)):
        raise SystemExit(f"{rec['id']} step numbers {ns}")
    if not (12 <= len(steps) <= 17):
        raise SystemExit(f"{rec['id']} step count {len(steps)}")
    c429 = c502 = 0
    recovery = rec["meta"]["noise_recovery_steps"]
    noise = rec["meta"]["noise_steps"]
    for s in steps:
        name = s["tool_call"]["name"]
        if name not in KNOWN_TOOLS:
            raise SystemExit(f"{rec['id']} unknown tool {name}")
        a, b = noise_hits(s["observation"])
        if s["n"] == recovery.get("429") or s["n"] == recovery.get("502"):
            if a or b:
                raise SystemExit(f"{rec['id']} recovery step {s['n']} repeats 429/502")
        else:
            c429 += a
            c502 += b
        if len(s["decision_basis"]) > 240:
            raise SystemExit(f"{rec['id']} step {s['n']} db too long")
    if c429 != 1 or c502 != 1:
        raise SystemExit(f"{rec['id']} noise counts 429={c429} 502={c502}")
    if steps[noise["429"] - 1]["observation"].find("429") < 0:
        raise SystemExit(f"{rec['id']} 429 step missing")
    if steps[noise["502"] - 1]["observation"].find("502") < 0:
        raise SystemExit(f"{rec['id']} 502 step missing")
    pc = rec["meta"]["plan_change_step"]
    if "Plan change:" not in steps[pc - 1]["reflection"]:
        raise SystemExit(f"{rec['id']} plan change reflection missing")
    if pc in (1, len(steps)):
        raise SystemExit(f"{rec['id']} plan change at end/start")
    numeric = [
        v
        for k, v in rec["reward"].items()
        if k not in {"success", "aggregation", "cost", "total"} and isinstance(v, (int, float))
    ]
    total = rec["reward"]["total"]
    if abs(sum(numeric) - total) > 1e-9:
        raise SystemExit(f"{rec['id']} reward {sum(numeric)} != {total}")
    line = json.dumps(rec, ensure_ascii=True, separators=(",", ":"))
    json.loads(line)
    if "\n" in line:
        raise SystemExit(f"{rec['id']} multiline json")
    if rec["meta"]["sim_or_real"] not in {"designed", "simulated", "hil"}:
        raise SystemExit("bad sim_or_real")
    if rec["meta"]["sim_or_real"] == "real":
        raise SystemExit("real forbidden")


def exclusive_write(path: Path, data: str) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(data)
            if not data.endswith("\n"):
                fh.write("\n")
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def main() -> None:
    if BATCH.exists() or NOTES.exists():
        raise SystemExit(f"refuse: {BATCH.name if BATCH.exists() else NOTES.name} already exists")
    for rec in (ep1, ep2):
        validate(rec)
    lines = [
        json.dumps(ep1, ensure_ascii=True, separators=(",", ":")),
        json.dumps(ep2, ensure_ascii=True, separators=(",", ":")),
    ]
    for line in lines:
        json.loads(line)
    if "Novel coverage:" not in NOTES_TEXT:
        raise SystemExit("notes missing Novel coverage")
    m = re.search(r"Novel coverage:\s*([0-9]+(?:\.[0-9]+)?)\s*%", NOTES_TEXT)
    if not m or not (0 <= float(m.group(1)) <= 100):
        raise SystemExit("bad novel coverage")
    exclusive_write(BATCH, "\n".join(lines) + "\n")
    exclusive_write(NOTES, NOTES_TEXT if NOTES_TEXT.endswith("\n") else NOTES_TEXT + "\n")
    with BATCH.open() as fh:
        loaded = [json.loads(line) for line in fh if line.strip()]
    assert len(loaded) == 2
    print("wrote", BATCH, "lines", len(loaded))
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)
    for rec in loaded:
        print(rec["id"], "steps", len(rec["steps"]), "success", rec["reward"]["success"])


if __name__ == "__main__":
    main()
