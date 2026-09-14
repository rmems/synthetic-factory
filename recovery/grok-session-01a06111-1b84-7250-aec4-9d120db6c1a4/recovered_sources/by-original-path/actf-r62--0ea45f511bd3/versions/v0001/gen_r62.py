#!/usr/bin/env python3
"""Create-only ACTF r62 batch + NOTES. Does not touch existing raw files."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

DEST_DIR = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "agentic-coding-trajectory-factory"
)
WINDOW_DIR = Path(
    "/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/"
    "agentic-coding-trajectory-factory"
)
STAGE = Path("/tmp/actf-r62")

LABELS = ("Plan: ", "Reflection: ", "Observation: ", "Tool call: ")
PROGRESS = re.compile(
    r"\b(?:added|changed|created|deleted|disproved|edited|evidence|failed|"
    r"fixed|found|hypothesis|learned|measured|patched|removed|reproduced|"
    r"tested|updated|verified|wrote)\b",
    re.I,
)
HIDDEN = {"thought", "chain_of_thought", "scratch", "reasoning", "inner_monologue"}
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

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-02T20:40:00Z",
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

META_BASE = {
    "factory": "agentic-coding-trajectory-factory",
    "round": 62,
    "generator": "grok-4.6",
    "run_label": "2026-09-02-final-heavy",
    "sim_or_real": "designed",
    "training_ready": False,
    "rights": RIGHTS,
}


def basis(text: str) -> str:
    if not any(text.startswith(label) for label in LABELS):
        raise SystemExit(f"basis prefix: {text!r}")
    n = len(text)
    if n < 80 or n > 240:
        raise SystemExit(f"basis len {n}: {text}")
    return text


def walk_keys(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path + "." + str(k), k, v
            yield from walk_keys(v, path + "." + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, f"{path}[{i}]")


def count_status(text: str, code: str) -> int:
    return len(re.findall(rf"\b{code}\b", text))


def validate_episode(ep: dict) -> None:
    steps = ep["steps"]
    n = len(steps)
    if not 12 <= n <= 17:
        raise SystemExit(f"{ep['id']}: step count {n}")
    nums = [s["n"] for s in steps]
    if nums != list(range(1, n + 1)):
        raise SystemExit(f"{ep['id']}: step numbers {nums}")
    for p, k, _v in walk_keys(ep):
        if str(k).casefold() in HIDDEN or str(k).casefold().startswith("internal_reasoning"):
            raise SystemExit(f"{ep['id']}: hidden key {p}")
    noise_429 = []
    noise_502 = []
    for s in steps:
        db = s["decision_basis"]
        basis(db)
        tool = s["tool_call"]["name"]
        if tool not in KNOWN:
            raise SystemExit(f"{ep['id']} step {s['n']}: unknown tool {tool}")
        obs = s["observation"]
        if not isinstance(obs, str) or not obs.strip():
            raise SystemExit(f"{ep['id']} step {s['n']}: empty obs")
        if "hypothesis" in obs.casefold():
            raise SystemExit(f"{ep['id']} step {s['n']}: hypothesis in observation")
        blob = " ".join(
            [
                db,
                s.get("plan") or "",
                json.dumps(s["tool_call"]),
                obs,
                s.get("reflection") or "",
            ]
        )
        if PROGRESS.search(blob) is None:
            raise SystemExit(f"{ep['id']} step {s['n']}: no progress term")
        if re.search(r"\b(?:no[ -]?op|no change|nothing changed|unchanged)\b", blob, re.I):
            raise SystemExit(f"{ep['id']} step {s['n']}: stall term")
        c429 = count_status(obs, "429")
        c502 = count_status(obs, "502")
        if c429:
            noise_429.append(s["n"])
        if c502:
            noise_502.append(s["n"])
    if len(noise_429) != 1 or len(noise_502) != 1:
        raise SystemExit(f"{ep['id']}: noise 429={noise_429} 502={noise_502}")
    rec_429 = noise_429[0] + 1
    rec_502 = noise_502[0] + 1
    if rec_429 > n or rec_502 > n:
        raise SystemExit(f"{ep['id']}: recovery out of range")
    b429 = steps[rec_429 - 1]["decision_basis"]
    b502 = steps[rec_502 - 1]["decision_basis"]
    if "429" not in b429:
        raise SystemExit(f"{ep['id']}: recovery {rec_429} must cite 429")
    if "502" not in b502:
        raise SystemExit(f"{ep['id']}: recovery {rec_502} must cite 502")
    if count_status(steps[rec_429 - 1]["observation"], "429"):
        raise SystemExit(f"{ep['id']}: recovery obs repeats 429")
    if count_status(steps[rec_502 - 1]["observation"], "502"):
        raise SystemExit(f"{ep['id']}: recovery obs repeats 502")
    pivots = [
        s["n"]
        for s in steps
        if "plan change:" in (s.get("reflection") or "").casefold()
        or "pivoting:" in (s.get("reflection") or "").casefold()
    ]
    if len(pivots) != 1 or pivots[0] in (1, n):
        raise SystemExit(f"{ep['id']}: plan-change steps {pivots}")
    nxt = steps[pivots[0]]
    if "pivot" not in nxt["decision_basis"].casefold() and "abandon" not in nxt[
        "decision_basis"
    ].casefold():
        raise SystemExit(f"{ep['id']}: next basis after plan-change must cite pivot")
    reward = ep["reward"]
    numeric = [
        v
        for k, v in reward.items()
        if k not in {"success", "aggregation", "cost", "total"} and isinstance(v, (int, float))
    ]
    total = sum(numeric)
    if abs(total - reward["total"]) > 1e-9:
        raise SystemExit(f"{ep['id']}: reward {total} != {reward['total']}")
    if not isinstance(reward["success"], bool):
        raise SystemExit("success not bool")


def ep1() -> dict:
    steps = [
        {
            "n": 1,
            "decision_basis": basis(
                "Plan: OG-620 reports partner B -0000 stamps compare False against partner A GMT. Search ParseTide and parsedate_to_datetime as evidence of a dropped UTC zone."
            ),
            "plan": "1) search ParseTide 2) read tide.py 3) measure GMT vs -0000 4) confirm want 13:15+00:00 5) fix naive -0000 6) regression + PR",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "ParseTide|parsedate_to_datetime|-0000|TideUTC",
                    "path": ".",
                },
            },
            "observation": (
                "oystergauge/tide.py:1:import email.utils\n"
                "oystergauge/tide.py:4:def ParseTide(stamp: str):\n"
                "oystergauge/tide.py:6:    return email.utils.parsedate_to_datetime(stamp)\n"
                "oystergauge/tide.py:8:def TideUTC(stamp: str):\n"
                "oystergauge/tide.py:9:    return ParseTide(stamp)\n"
                "tests/test_install.py:11:    assert ParseTide(s) is not None\n"
                "5 matches"
            ),
            "reflection": "Found ParseTide wrapping parsedate_to_datetime with no tzinfo guard. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": basis(
                "Observation: tide.py:6 returns parsedate_to_datetime(stamp) with no tzinfo guard (step 1). Read the helper as evidence of any UTC normalize."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "oystergauge/tide.py", "offset": 1, "limit": 18},
            },
            "observation": (
                "1  import email.utils\n"
                "2  from datetime import datetime, timezone\n"
                "3\n"
                "4  # Harbor RFC822 tide stamps must compare as UTC for partner A GMT and partner B -0000.\n"
                "5  def ParseTide(stamp: str) -> datetime:\n"
                "6      return email.utils.parsedate_to_datetime(stamp)\n"
                "7\n"
                "8  def TideUTC(stamp: str) -> datetime:\n"
                "9      return ParseTide(stamp)\n"
                "10\n"
                "11 WANT = datetime(2026, 9, 2, 13, 15, tzinfo=timezone.utc)\n"
            ),
            "reflection": "Learned TideUTC is a passthrough. First plan: S3 truncated RFC822 stamps. Next measure GMT vs -0000.",
        },
        {
            "n": 3,
            "decision_basis": basis(
                "Observation: TideUTC is a passthrough of parsedate_to_datetime (step 2). Measure GMT vs -0000 as evidence of a naive UTC stamp."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 - <<'EOF'\n"
                        "import email.utils\n"
                        "from datetime import timezone\n"
                        "for s in [\n"
                        "  'Wed, 02 Sep 2026 13:15:00 GMT',\n"
                        "  'Wed, 02 Sep 2026 13:15:00 -0000',\n"
                        "  'Wed, 02 Sep 2026 15:15:00 +0200',\n"
                        "]:\n"
                        "    d = email.utils.parsedate_to_datetime(s)\n"
                        "    print(s, 'tz', d.tzinfo, 'as_utc', d.astimezone(timezone.utc))\n"
                        "EOF"
                    )
                },
            },
            "observation": (
                "Wed, 02 Sep 2026 13:15:00 GMT tz UTC as_utc 2026-09-02 13:15:00+00:00\n"
                "Wed, 02 Sep 2026 13:15:00 -0000 tz None as_utc 2026-09-02 18:15:00+00:00\n"
                "Wed, 02 Sep 2026 15:15:00 +0200 tz UTC+02:00 as_utc 2026-09-02 13:15:00+00:00"
            ),
            "reflection": "Measured -0000 as naive; astimezone(utc) on the helper host (CDT) yields 18:15+00:00. Next confirm dest want is 13:15+00:00.",
        },
        {
            "n": 4,
            "decision_basis": basis(
                "Reflection: -0000 printed tz None and astimezone 18:15+00:00 (step 3). Fetch parsedate notes via gh as evidence of the naive -0000 contract."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/python/cpython/contents/Doc/library/email.utils.rst",
                },
            },
            "observation": (
                "HTTP/2 429\n"
                "retry-after: 5\n"
                "x-ratelimit-limit: 60\n"
                "x-ratelimit-remaining: 0\n"
                '{"message":"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=5",'
                '"documentation_url":"https://docs.github.com/rest/overview/rate-limits"}'
            ),
            "reflection": "GitHub returned 429 with retry-after 5 while fetching parsedate docs. Wait, then use the vendored docs/parsedate-minus0000.md fixture.",
        },
        {
            "n": 5,
            "decision_basis": basis(
                "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/parsedate-minus0000.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/parsedate-minus0000.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  email.utils.parsedate_to_datetime treats RFC2822 -0000 as naive (UTC unknown).\n"
                "2  GMT and +0000 become aware UTC; naive == aware is False even at 13:15.\n"
                "3  astimezone(timezone.utc) on naive stamps uses the helper host offset (CDT → 18:15Z).\n"
                "4  Durable: if tzinfo is None, replace(tzinfo=timezone.utc); else astimezone(utc).\n"
                "5  Partner B +0200 must still fold to 13:15+00:00.\n"
                "6  A truncated S3 object is independent of this client tz attach.\n"
            ),
            "reflection": "Verified the naive -0000 trap and that astimezone still emits 18:15Z. Next pull the committed tide stamp fixture.",
        },
        {
            "n": 6,
            "decision_basis": basis(
                "Observation: RFC-style notes say -0000 must attach UTC without a local shift (step 5). Get the committed tide stamp object as evidence the want set is 13:15+00:00."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-object",
                        "--bucket",
                        "oysterfen-specs",
                        "--key",
                        "oystergauge/tide-stamps.json",
                        "/tmp/oystergauge-inventory.json",
                    ]
                },
            },
            "observation": (
                "download failed: s3.us-east-2.amazonaws.com/oysterfen-specs\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "server: awselb/2.0\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection failure"
            ),
            "reflection": "Tide inventory get-object hit 502 on the ELB before headers. Retry against the committed fixtures/tide-stamps.json instead of the edge.",
        },
        {
            "n": 7,
            "decision_basis": basis(
                "Observation: tide inventory get-object returned 502 from the ELB (step 6). jq fixtures/tide-stamps.json want as local-spec evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{want:.want, utc:.utc, n:.dest_count, path:.path, stale_note:.stale}",
                        "fixtures/tide-stamps.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "want": {\n'
                '    "partner-a/gmt": "2026-09-02T13:15:00+00:00",\n'
                '    "partner-b/minus0000": "2026-09-02T13:15:00+00:00",\n'
                '    "partner-c/plus0200": "2026-09-02T13:15:00+00:00"\n'
                "  },\n"
                '  "utc": "2026-09-02T13:15:00+00:00",\n'
                '  "n": 3,\n'
                '  "path": "fixtures/tide.ndjson",\n'
                '  "stale": "fixtures/tide-stamps.stale.json"\n'
                "}"
            ),
            "reflection": "Verified want already lists 13:15+00:00 for GMT, -0000, and +0200. Next join that with the stale fixture and the measured naive stamp.",
        },
        {
            "n": 8,
            "decision_basis": basis(
                "Observation: fixture want already lists 13:15+00:00 (step 7). jq the measured naive stamp against that spec and the stale file as evidence whether S3 truncated stamps."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "s",
                        "fixtures/tide-stamps.json",
                        "--slurpfile",
                        "k",
                        "fixtures/tide-stamps.stale.json",
                        '{got:"ParseTide -0000 naive; astimezone 18:15+00:00",want:$s[0].want,stale:$k[0].want,n:$s[0].dest_count,path:$s[0].path}',
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "got": "ParseTide -0000 naive; astimezone 18:15+00:00",\n'
                '  "want": {\n'
                '    "partner-a/gmt": "2026-09-02T13:15:00+00:00",\n'
                '    "partner-b/minus0000": "2026-09-02T13:15:00+00:00",\n'
                '    "partner-c/plus0200": "2026-09-02T13:15:00+00:00"\n'
                "  },\n"
                '  "stale": {\n'
                '    "partner-a/gmt": "2026-09-02T13:15:00",\n'
                '    "partner-b/minus0000": "2026-09-02T13:15:00",\n'
                '    "partner-c/plus0200": "2026-09-02T15:15:00"\n'
                "  },\n"
                '  "n": 3,\n'
                '  "path": "fixtures/tide.ndjson"\n'
                "}"
            ),
            "reflection": "Plan change: tide want stamps already list 13:15+00:00 and got is naive -0000 plus astimezone local shift on a committed 3-line ndjson. Abandon truncated-transit. Switching the edit target to TideUTC so -0000 attaches UTC without a host offset.",
        },
        {
            "n": 9,
            "decision_basis": basis(
                "Reflection: pivoting off the truncated-transit plan; TideUTC still emits naive -0000 (step 8). Edit astimezone(utc) as evidence only the host offset shifts."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "oystergauge/tide.py",
                    "old_string": "def TideUTC(stamp: str) -> datetime:\n    return ParseTide(stamp)\n",
                    "new_string": "def TideUTC(stamp: str) -> datetime:\n    return ParseTide(stamp).astimezone(timezone.utc)\n",
                },
            },
            "observation": "Edited oystergauge/tide.py: TideUTC now astimezone(utc) so naive -0000 becomes 18:15+00:00 on the CDT helper host.",
            "reflection": "Wrote an astimezone clock shift. Add a pytest that requires 13:15+00:00 for GMT, -0000, and +0200.",
        },
        {
            "n": 10,
            "decision_basis": basis(
                "Observation: TideUTC now astimezone(utc) on every stamp (step 9). Write a pytest as evidence that RFC822 dest stamps keep 13:15+00:00."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_tide_minus0000.py",
                    "content": (
                        "from datetime import datetime, timezone\n"
                        "from oystergauge.tide import TideUTC\n"
                        "\n"
                        "WANT = datetime(2026, 9, 2, 13, 15, tzinfo=timezone.utc)\n"
                        "\n"
                        "def test_parse_tide_minus0000_gmt_plus0200():\n"
                        "    gmt = TideUTC('Wed, 02 Sep 2026 13:15:00 GMT')\n"
                        "    minus = TideUTC('Wed, 02 Sep 2026 13:15:00 -0000')\n"
                        "    plus2 = TideUTC('Wed, 02 Sep 2026 15:15:00 +0200')\n"
                        "    assert gmt == WANT\n"
                        "    assert minus == WANT\n"
                        "    assert plus2 == WANT\n"
                        "    assert minus.tzinfo is not None\n"
                    ),
                },
            },
            "observation": "Wrote tests/test_tide_minus0000.py (14 lines).",
            "reflection": "Created a mixed-tz regression that expects partner-b/minus0000 to stay 13:15+00:00. Run pytest to reproduce the 18:15 stamp.",
        },
        {
            "n": 11,
            "decision_basis": basis(
                "Plan: run pytest tests/test_tide_minus0000.py as evidence whether astimezone(utc) keeps dest stamps as 13:15+00:00."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_tide_minus0000.py tests/test_install.py -q 2>&1 | tail -n 24"
                },
            },
            "observation": (
                "F.\n"
                "=================================== FAILURES ===================================\n"
                "_________________ test_parse_tide_minus0000_gmt_plus0200 _________________\n"
                "tests/test_tide_minus0000.py:11: in test_parse_tide_minus0000_gmt_plus0200\n"
                "    assert minus == WANT\n"
                "E   AssertionError: assert datetime.datetime(2026, 9, 2, 18, 15, tzinfo=datetime.timezone.utc) == datetime.datetime(2026, 9, 2, 13, 15, tzinfo=datetime.timezone.utc)\n"
                "=========================== 1 failed, 1 passed in 0.04s ==========================="
            ),
            "reflection": "Test failed: astimezone(utc) still emits 18:15+00:00 on naive -0000. Re-read TideUTC and reject a keep-astimezone review.",
        },
        {
            "n": 12,
            "decision_basis": basis(
                "Observation: pytest failed with got 18:15+00:00 on astimezone(utc) (step 11). Read the keep-astimezone review as evidence whether dest may stay on host offset."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/review-keep-astimezone.md", "offset": 1, "limit": 12},
            },
            "observation": (
                "1  Reviewer (OG-620 comment 4): keep TideUTC astimezone(utc) so harbor clocks stay in local CDT.\n"
                "2  Claim: 18:15Z matches the helper host wall clock and Excel CSV still parses.\n"
                "3  Dest contract named in fixtures/tide-stamps.json is 13:15+00:00 for GMT, -0000, and +0200.\n"
                "4  Reject keep-astimezone: partner-c +0200 already folds correctly only if naive stamps attach UTC, not local.\n"
            ),
            "reflection": "Rejected the keep-astimezone review; dest want is 13:15+00:00 not 18:15. Re-read TideUTC and attach UTC only when tzinfo is missing.",
        },
        {
            "n": 13,
            "decision_basis": basis(
                "Observation: keep-astimezone review was rejected; dest want stays 13:15+00:00 (step 12). Re-read TideUTC for the astimezone evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "oystergauge/tide.py", "offset": 4, "limit": 10},
            },
            "observation": (
                "4  # Harbor RFC822 tide stamps must compare as UTC for partner A GMT and partner B -0000.\n"
                "5  def ParseTide(stamp: str) -> datetime:\n"
                "6      return email.utils.parsedate_to_datetime(stamp)\n"
                "7\n"
                "8  def TideUTC(stamp: str) -> datetime:\n"
                "9      return ParseTide(stamp).astimezone(timezone.utc)\n"
                "10\n"
                "11 WANT = datetime(2026, 9, 2, 13, 15, tzinfo=timezone.utc)\n"
            ),
            "reflection": "Confirmed line 9 still astimezone-shifts naive -0000. Patch replace(tzinfo=utc) when tzinfo is None.",
        },
        {
            "n": 14,
            "decision_basis": basis(
                "Reflection: TideUTC must replace naive -0000 with UTC rather than astimezone (step 13). Patch tide.py as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "oystergauge/tide.py",
                    "old_string": "def TideUTC(stamp: str) -> datetime:\n    return ParseTide(stamp).astimezone(timezone.utc)\n",
                    "new_string": (
                        "def TideUTC(stamp: str) -> datetime:\n"
                        "    dt = ParseTide(stamp)\n"
                        "    if dt.tzinfo is None:\n"
                        "        return dt.replace(tzinfo=timezone.utc)\n"
                        "    return dt.astimezone(timezone.utc)\n"
                    ),
                },
            },
            "observation": "Edited oystergauge/tide.py: TideUTC now replace(tzinfo=utc) on naive -0000 and astimezone on aware GMT/+0200 so 13:15 stays +00:00.",
            "reflection": "Patched the naive-UTC constructor. Re-run pytest; stamps should stay 13:15+00:00.",
        },
        {
            "n": 15,
            "decision_basis": basis(
                "Observation: TideUTC now replace(tzinfo=utc) on naive -0000 (step 14). Re-run pytest as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_tide_minus0000.py tests/test_install.py -q 2>&1 | tail -n 12"
                },
            },
            "observation": (
                "......\n"
                "6 passed in 0.05s"
            ),
            "reflection": "Verified 6 passed including test_parse_tide_minus0000_gmt_plus0200. Open the OG-620 PR.",
        },
        {
            "n": 16,
            "decision_basis": basis(
                "Observation: pytest passed 6/6 after the naive-UTC patch (step 15). Create the OG-620 PR via gh as evidence of the TideUTC fix."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/oysterfen/oystergauge-tide/pulls",
                    "raw_field": "title=OG-620: attach UTC on parsedate -0000 so TideUTC keeps 13:15+00:00 instead of naive/local 18:15",
                },
            },
            "observation": (
                "{\n"
                '  "number": 621,\n'
                '  "html_url": "https://git.oysterfen.internal/pkg/oystergauge-tide/pull/621",\n'
                '  "state": "open"\n'
                "}"
            ),
            "reflection": "Opened PR 621. TideUTC keeps 13:15+00:00 for GMT, -0000, and +0200. Live tide copies remain a follow-up against the designed harbor host.",
        },
    ]
    return {
        "id": "act-r62-parsedate-minus0000-oystergauge-a4c91b",
        "goal": (
            "OG-620 (oystergauge-tide, Python 3.12 RFC822 tide stamp helper + fixtures/tide-stamps.json; pytest): "
            "nightly dest copies print naive 13:15 while partner A GMT stamps compare False against partner B -0000 "
            "(file fixtures/tide.ndjson, UTC 13:15). Find why TideUTC drifts UTC stamps, add a mixed-tz regression, "
            "and open a PR. Designed plant; not a live harbor apply."
        ),
        "steps": steps,
        "outcome": (
            "TideUTC passed through email.utils.parsedate_to_datetime, so partner B -0000 stayed naive and compared False to partner A GMT. "
            "A first patch that used astimezone(timezone.utc) still failed tests/test_tide_minus0000.py (got 18:15+00:00 on the CDT helper host). "
            "TideUTC now replace(tzinfo=utc) when tzinfo is None and astimezone otherwise. Verified by pytest 6 passed "
            "(tests/test_tide_minus0000.py::test_parse_tide_minus0000_gmt_plus0200). PR 621 opened. Live tide copies remain a follow-up against the designed harbor host."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.4,
            "parsedate_minus0000_fix": 0.12,
            "mixed_tz_tide_test": 0.08,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.58,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 6,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 2,
                "duration_min": 29,
            },
        },
        "meta": {
            **META_BASE,
            "codebase_type": "library / harbor RFC822 tide stamps (Python 3.12 email.utils)",
            "bug_class": "schema mismatch: parsedate_to_datetime -0000 stayed naive; first fix astimezone(utc) emitted 18:15Z on CDT",
            "test_harness": "pytest + aws s3api + jq",
            "noise_steps": {"429": 4, "502": 6},
            "noise_recovery_steps": {"429": 5, "502": 7},
            "plan_change_step": 8,
            "debug_loop_steps": [9, 10, 11, 12, 13, 14, 15],
            "tags": [
                "email.utils.parsedate_to_datetime",
                "-0000",
                "naive-datetime",
                "astimezone",
                "harbor-tide",
                "mixed-tz",
            ],
        },
    }


def ep2() -> dict:
    steps = [
        {
            "n": 1,
            "decision_basis": basis(
                "Plan: DN-72 reports crane serial A still listed twice after unique_serials. Search dedup and unique_serials as evidence of a consecutive-only collapse."
            ),
            "plan": "1) search unique_serials 2) read lib.rs 3) measure unsorted dupes 4) fix first-seen unique 5) regression 6) apply or hand off",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "unique_serials|dedup|HashSet|crane serial",
                    "path": ".",
                },
            },
            "observation": (
                "src/lib.rs:1:pub fn unique_serials(xs: &[String]) -> Vec<String> {\n"
                "src/lib.rs:3:    v.dedup();\n"
                "src/lib.rs:4:    v\n"
                "tests/install.rs:8:    assert!(!unique_serials(&xs).is_empty());\n"
                "4 matches"
            ),
            "reflection": "Found unique_serials calling Vec::dedup with no sort and no seen-set. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": basis(
                "Observation: lib.rs:3 calls Vec::dedup with no sort (step 1). Read the helper as evidence of any first-seen unique."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "src/lib.rs", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  /// Harbor crane load-cell serials must keep first-seen order and drop later repeats.\n"
                "2  pub fn unique_serials(xs: &[String]) -> Vec<String> {\n"
                "3      let mut v = xs.to_vec();\n"
                "4      v.dedup();\n"
                "5      v\n"
                "6  }\n"
                "7\n"
                "8  pub fn load_serials(raw: &str) -> Vec<String> {\n"
                "9      raw.split_whitespace().map(|s| s.to_string()).collect()\n"
                "10 }\n"
            ),
            "reflection": "Learned dedup only collapses consecutive repeats. First plan: S3 truncated serial lists. Next measure unsorted input.",
        },
        {
            "n": 3,
            "decision_basis": basis(
                "Observation: unique_serials is Vec::dedup on an unsorted clone (step 2). Measure [A,C,A,B] as evidence of a leftover second A."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 - <<'EOF'\n"
                        "xs=['A','C','A','B']\n"
                        "consec=[]\n"
                        "for x in xs:\n"
                        "    if not consec or consec[-1]!=x: consec.append(x)\n"
                        "print('input', xs)\n"
                        "print('dedup_consecutive', consec)\n"
                        "print('sort_dedup', sorted(set(xs)))\n"
                        "seen=[]; out=[]\n"
                        "for x in xs:\n"
                        "    if x not in seen:\n"
                        "        seen.append(x); out.append(x)\n"
                        "print('first_seen', out)\n"
                        "EOF"
                    )
                },
            },
            "observation": (
                "input ['A', 'C', 'A', 'B']\n"
                "dedup_consecutive ['A', 'C', 'A', 'B']\n"
                "sort_dedup ['A', 'B', 'C']\n"
                "first_seen ['A', 'C', 'B']"
            ),
            "reflection": "Measured consecutive dedup leaving A twice while dest first-seen is A,C,B. Next confirm the committed serial fixture.",
        },
        {
            "n": 4,
            "decision_basis": basis(
                "Observation: consecutive dedup left ['A','C','A','B'] (step 3). Get the committed serial object as evidence the want set is first-seen A,C,B."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-object",
                        "--bucket",
                        "dunlinfen-specs",
                        "--key",
                        "dunlincut/serials.json",
                        "/tmp/dunlincut-inventory.json",
                    ]
                },
            },
            "observation": (
                "download failed: s3.eu-north-1.amazonaws.com/dunlinfen-specs\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "server: awselb/2.0\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection failure"
            ),
            "reflection": "Serial inventory get-object hit 502 on the ELB before headers. Retry against the committed fixtures/serials.json and write it locally.",
        },
        {
            "n": 5,
            "decision_basis": basis(
                "Observation: serial inventory get-object returned 502 from the ELB (step 4). jq fixtures/serials.json and write /tmp/dunlincut-serials.json as evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{want:.want, input:.input, n:.dest_count, path:.path, stale:.stale}",
                        "fixtures/serials.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "want": ["A", "C", "B"],\n'
                '  "input": ["A", "C", "A", "B"],\n'
                '  "n": 3,\n'
                '  "path": "fixtures/serials.ndjson",\n'
                '  "stale": "fixtures/serials.stale.json"\n'
                "}\n"
                "wrote /tmp/dunlincut-serials.json"
            ),
            "reflection": "Measured dest want as first-seen A,C,B. Next fetch Vec::dedup notes so a consecutive-only plan can be checked.",
        },
        {
            "n": 6,
            "decision_basis": basis(
                "Observation: dest want is first-seen A,C,B on input A,C,A,B (step 5). Fetch Vec::dedup docs via gh as evidence of the consecutive-only contract."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/rust-lang/rust/contents/library/alloc/src/vec/mod.rs",
                },
            },
            "observation": (
                "HTTP/2 429\n"
                "retry-after: 7\n"
                "x-ratelimit-limit: 60\n"
                "x-ratelimit-remaining: 0\n"
                '{"message":"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=7",'
                '"documentation_url":"https://docs.github.com/rest/overview/rate-limits"}'
            ),
            "reflection": "GitHub returned 429 with retry-after 7 while fetching Vec::dedup docs. Wait, then use the vendored docs/dedup-unsorted.md fixture.",
        },
        {
            "n": 7,
            "decision_basis": basis(
                "Observation: gh api returned 429 with retry_after 7 (step 6). Sleep 8s, then read docs/dedup-unsorted.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/dedup-unsorted.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  Vec::dedup only drops consecutive repeats; unsorted [A,C,A,B] keeps the second A.\n"
                "2  sort then dedup yields [A,B,C] and breaks dest first-seen order [A,C,B].\n"
                "3  Durable: HashSet seen, push when insert succeeds, keep input order.\n"
                "4  cargo clean of the serial cache fail-opens in-flight crane flashes.\n"
                "5  A dummy consecutive-only fixture is independent of this client unique.\n"
                "6  Remote S3 lag is independent of this Vec::dedup addressing.\n"
            ),
            "reflection": "Verified harbor serials need first-seen unique, not sort+dedup. Next join that with the saved fixture.",
        },
        {
            "n": 8,
            "decision_basis": basis(
                "Observation: docs require first-seen unique keyed by serial (step 7). jq spec from the saved fixture as evidence of the live skew."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "s",
                        "/tmp/dunlincut-serials.json",
                        "--slurpfile",
                        "k",
                        "fixtures/serials.stale.json",
                        "{got:\"unique_serials [A,C,A,B]\",want:$s[0].want,stale:$k[0].want,input:$s[0].input,n:$s[0].dest_count}",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "got": "unique_serials [A,C,A,B]",\n'
                '  "want": ["A", "C", "B"],\n'
                '  "stale": ["A", "C", "A", "B"],\n'
                '  "input": ["A", "C", "A", "B"],\n'
                '  "n": 3\n'
                "}"
            ),
            "reflection": "Plan change: dest want already lists first-seen A,C,B and got is consecutive-only leftover on a committed 4-row ndjson. Abandon remounting the serial prefix. Switching the edit target to unique_serials so a seen-set keeps order.",
        },
        {
            "n": 9,
            "decision_basis": basis(
                "Reflection: pivoting off the stale-prefix plan; unique_serials still leaves the second A (step 8). Refuse deleting the serial cache as evidence the objects must stay."
            ),
            "tool_call": {
                "name": "refuse",
                "args": {
                    "action": "cargo clean && rm -rf /var/lib/dunlincut/serial-cache so a freshly built cutter picks HashSet keys",
                    "policy": "FS-MUTATE-04",
                    "incident": "DN-72",
                },
            },
            "observation": (
                "refused: FS-MUTATE-04 forbids deleting /var/lib/dunlincut/serial-cache to skip a consecutive-dedup skew. "
                "Destroy would drop in-flight harbor crane flashes and can fail-open serial coverage. "
                "Safe alternative: patch unique_serials and keep the cache objects. found 0 waivers"
            ),
            "reflection": "Denied the cache wipe. Next patch src/lib.rs; keep the serial objects.",
        },
        {
            "n": 10,
            "decision_basis": basis(
                "Observation: cache wipe is refused; edit target is Vec::dedup (step 9). First patch: sort then dedup as evidence later repeats may drop."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "src/lib.rs",
                    "old_string": "    let mut v = xs.to_vec();\n    v.dedup();\n    v\n",
                    "new_string": "    let mut v = xs.to_vec();\n    v.sort();\n    v.dedup();\n    v\n",
                },
            },
            "observation": "Edited src/lib.rs: unique_serials now sort then dedup so later A cannot survive as a consecutive repeat.",
            "reflection": "Wrote a sort+dedup collapse. Add a cargo test that requires first-seen keys A,C,B.",
        },
        {
            "n": 11,
            "decision_basis": basis(
                "Observation: helper now emits sort then dedup (step 10). Write a cargo test as evidence that harbor serials keep first-seen order without leaving a second A."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/first_seen.rs",
                    "content": (
                        "use dunlincut::unique_serials;\n"
                        "\n"
                        "#[test]\n"
                        "fn first_seen_keeps_acb() {\n"
                        "    let xs = [\"A\", \"C\", \"A\", \"B\"].map(|s| s.to_string());\n"
                        "    let got = unique_serials(&xs);\n"
                        "    let want = [\"A\", \"C\", \"B\"].map(|s| s.to_string());\n"
                        "    assert_eq!(got, want, \"got keys={:?} want A,C,B\", got);\n"
                        "}\n"
                    ),
                },
            },
            "observation": "Wrote tests/first_seen.rs (11 lines).",
            "reflection": "Created a first-seen regression. Run cargo test to reproduce the sort-order miss.",
        },
        {
            "n": 12,
            "decision_basis": basis(
                "Plan: run cargo test as evidence whether sort then dedup satisfies the first-seen A,C,B contract."
            ),
            "tool_call": {
                "name": "bash",
                "args": {"command": "cargo test --tests -q -- --nocapture 2>&1 | tail -n 24"},
            },
            "observation": (
                "running 2 tests\n"
                "test tests::install::nonempty ... ok\n"
                "test first_seen::first_seen_keeps_acb ... FAILED\n"
                "\n"
                "---- first_seen::first_seen_keeps_acb stdout ----\n"
                "got keys=[\"A\", \"B\", \"C\"] want A,C,B\n"
                "\n"
                "failures:\n"
                "    first_seen::first_seen_keeps_acb\n"
                "\n"
                "test result: FAILED. 1 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.02s"
            ),
            "reflection": "Test failed: keys are still A,B,C. Re-read lib.rs and switch to a seen HashSet.",
        },
        {
            "n": 13,
            "decision_basis": basis(
                "Observation: cargo test failed with got keys=[A, B, C] on sort+dedup (step 12). Re-read src/lib.rs for the sort evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "src/lib.rs", "offset": 1, "limit": 12},
            },
            "observation": (
                "1  /// Harbor crane load-cell serials must keep first-seen order and drop later repeats.\n"
                "2  pub fn unique_serials(xs: &[String]) -> Vec<String> {\n"
                "3      let mut v = xs.to_vec();\n"
                "4      v.sort();\n"
                "5      v.dedup();\n"
                "6      v\n"
                "7  }\n"
                "8\n"
                "9  pub fn load_serials(raw: &str) -> Vec<String> {\n"
                "10     raw.split_whitespace().map(|s| s.to_string()).collect()\n"
                "11 }\n"
            ),
            "reflection": "Confirmed lines 4-5 still sort the harbor serial list that must stay first-seen. Patch HashSet and keep three keys.",
        },
        {
            "n": 14,
            "decision_basis": basis(
                "Reflection: helper must emit first-seen unique keyed by serial (step 13). Patch src/lib.rs spec as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "src/lib.rs",
                    "old_string": (
                        "    let mut v = xs.to_vec();\n"
                        "    v.sort();\n"
                        "    v.dedup();\n"
                        "    v\n"
                    ),
                    "new_string": (
                        "    let mut out = Vec::new();\n"
                        "    let mut seen = std::collections::HashSet::new();\n"
                        "    for x in xs {\n"
                        "        if seen.insert(x.clone()) {\n"
                        "            out.push(x.clone());\n"
                        "        }\n"
                        "    }\n"
                        "    out\n"
                    ),
                },
            },
            "observation": "Edited src/lib.rs: unique_serials is a seen HashSet keyed by serial and sort/dedup is gone.",
            "reflection": "Patched first-seen unique and kept three serial objects. Re-run cargo test; C should keep its place before B.",
        },
        {
            "n": 15,
            "decision_basis": basis(
                "Observation: helper now emits first-seen unique keyed by serial (step 14). Re-run cargo test as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {"command": "cargo test --tests -q -- --nocapture 2>&1 | tail -n 12"},
            },
            "observation": (
                "running 5 tests\n"
                "test tests::install::nonempty ... ok\n"
                "test first_seen::first_seen_keeps_acb ... ok\n"
                "test first_seen::plus0200_unused ... ok\n"
                "test load_serials::whitespace ... ok\n"
                "test unique_serials::empty ... ok\n"
                "test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.03s"
            ),
            "reflection": "Verified 5 passed including first_seen_keeps_acb. Check gate-cli before flashing the cutter.",
        },
        {
            "n": 16,
            "decision_basis": basis(
                "Observation: cargo test passed 5/5 after the HashSet patch (step 15). Run gate-cli check apply as evidence whether prod cutter mutation is allowed."
            ),
            "tool_call": {
                "name": "gate-cli",
                "args": {
                    "argv": [
                        "check",
                        "apply",
                        "--change",
                        "dunlincut-dedup-first-seen",
                        "--resource",
                        "unique_serials",
                    ]
                },
            },
            "observation": (
                "gate-cli check apply --change dunlincut-dedup-first-seen\n"
                "status: REJECT\n"
                "policy: prod-batch-freeze\n"
                "ticket: DN-60\n"
                "until: 2026-09-16T00:00:00Z\n"
                "evidence: change mutates unique_serials (dunlincut-serial consecutive dedup to HashSet)\n"
                "found 0 waivers"
            ),
            "reflection": "Measured REJECT under DN-60 freeze through 2026-09-16. Do not flash the cutter. Open a handoff issue attaching the HashSet fix.",
        },
        {
            "n": 17,
            "decision_basis": basis(
                "Observation: gate-cli REJECT'd the cutter apply under freeze DN-60 (step 16). Open a handoff issue as evidence live flashes still have consecutive-only serials."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "title": "DN-83: apply dunlincut first-seen unique after DN-60 freeze (blocks DN-72 close)",
                    "body": (
                        "src/lib.rs now emits HashSet first-seen unique; cargo test 5 passed. "
                        "Live flashes still have consecutive-only serials. gate-cli freeze DN-60 until 2026-09-16. "
                        "Do not cargo clean the serial cache."
                    ),
                },
            },
            "observation": "https://git.dunlinfen.internal/cli/dunlincut-serial/issues/83",
            "reflection": "Opened DN-83. Cutter tests are green; prod flash remains blocked. Handoff, not close.",
        },
    ]
    return {
        "id": "act-r62-dedup-unsorted-dunlincut-b7e305",
        "goal": (
            "DN-72 (dunlincut-serial, Rust 1.78 crane serial cutter + fixtures/serials.json; cargo test): "
            "harbor crane load-cell serial A was still listed twice after unique_serials because Vec::dedup "
            "only drops consecutive repeats on unsorted runs. Find why unique_serials leaves later A, fix the cutter, "
            "and apply or hand off. Designed plant; not a live crane flash."
        ),
        "steps": steps,
        "outcome": (
            "unique_serials emitted Vec::dedup on an unsorted clone, so input [A,C,A,B] kept a second A. "
            "A first patch that sorted then deduped still failed tests/first_seen.rs (got keys=[A, B, C]). "
            "The cutter now emits a HashSet first-seen unique; cargo test 5 passed. "
            "Applying unique_serials remains blocked by gate-cli freeze DN-60; live flashes still have consecutive-only serials. "
            "DN-83 opened. Overall: incomplete; prod apply unresolved."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "first_seen_hashset_fix": 0.1,
            "first_seen_serial_test": 0.08,
            "prod_apply_blocked_penalty": -0.12,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.28,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 5,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 3,
                "duration_min": 36,
                "prod_apply": 0,
            },
        },
        "meta": {
            **META_BASE,
            "codebase_type": "CLI / harbor crane serial cutter (Rust 1.78 Vec::dedup)",
            "bug_class": "silent consecutive-only unique: Vec::dedup left unsorted later A; first fix sort+dedup reordered dest to A,B,C",
            "test_harness": "cargo test + aws s3api + jq + gate-cli",
            "noise_steps": {"502": 4, "429": 6},
            "noise_recovery_steps": {"502": 5, "429": 7},
            "plan_change_step": 8,
            "debug_loop_steps": [10, 11, 12, 13, 14, 15],
            "tags": [
                "Vec::dedup",
                "first-seen",
                "HashSet",
                "crane-serial",
                "gate-cli-freeze",
                "refuse-destroy",
            ],
        },
    }


NOTES = """# ACTF r62 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r62-parsedate-minus0000-oystergauge-a4c91b`, `act-r62-dedup-unsorted-dunlincut-b7e305` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`kubectl`/`gate-cli`/`aws`/`jq`/`refuse`). meta.round=62 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Window write is create-only (`batch-r62.jsonl`); never clobbered `batch-r01.jsonl` / `NOTES-r01.md` / r21 / r41 / r61. Distinct from window r01 (sanderling inclusive-after Rust pager / whimbrel Node inflight Map race), r21 (turnlease Duration JSON ns / stiltmig sqlite execute), r41 (saugermg struct.unpack endian / godwitvol PVC RWO), r61 (knotberth time/tzdata LoadLocation / curlewberth tofu count-index), and from mill+k8s plateau. Invented repos `git.oysterfen.internal/pkg/oystergauge-tide.git` and `git.dunlinfen.internal/cli/dunlincut-serial.git`. Linear RM-793 remains the rights tracker.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r62-parsedate-minus0000-oystergauge-a4c91b | Python 3.12 RFC822 tide helper + tide-stamps fixtures / pytest + aws s3api + jq | schema mismatch: `parsedate_to_datetime` left RFC2822 `-0000` naive; first fix `astimezone(utc)` emitted 18:15Z on CDT | success; 6/6; PR 621 | 0.58 |
| act-r62-dedup-unsorted-dunlincut-b7e305 | Rust 1.78 crane serial cutter / cargo test + gate-cli | silent consecutive-only unique: `Vec::dedup` left later A; first fix `sort`+`dedup` reordered dest to A,B,C | incomplete HIL/prod apply; DN-83; freeze DN-60 | 0.28 |

## Step counts, noise, plan change
- act-r62-parsedate-minus0000-oystergauge-a4c91b: 16 steps. 429 at step 4 (`gh api` cpython email.utils.rst, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/parsedate-minus0000.md`). 502 at step 6 (`aws s3api get-object` oysterfen-specs tide-stamps ELB) -> recovery step 7 (`jq` committed `fixtures/tide-stamps.json` against stale `fixtures/tide-stamps.stale.json`). Plan change at step 8: jq join shows want already 13:15+00:00 for GMT/-0000/+0200 and got is naive -0000 plus astimezone 18:15Z; abandon truncated-transit. Debug loop: 9 edit astimezone -> 10 write mixed-tz pytest -> 11 FAIL got 18:15+00:00 -> 12 reviewer keep-astimezone rejected -> 13 re-read TideUTC -> 14 replace(tzinfo=utc) on naive -> 15 6 passed.
- act-r62-dedup-unsorted-dunlincut-b7e305: 17 steps. 502 at step 4 (`aws s3api get-object` dunlinfen-specs serials ELB) -> recovery step 5 (`jq` committed `fixtures/serials.json` writes /tmp/dunlincut-serials.json). 429 at step 6 (`gh api` rust-lang vec/mod.rs, retry-after 7) -> recovery step 7 (read vendored `docs/dedup-unsorted.md`). Plan change at step 8: jq join shows want already first-seen A,C,B while stale still lists A,C,A,B; abandon remounting the serial prefix. Debug loop: 10 edit sort+dedup -> 11 write first_seen cargo test -> 12 FAIL got keys=[A, B, C] -> 13 re-read helper -> 14 HashSet first-seen -> 15 5 passed. `refuse` at step 9 blocks `cargo clean` / serial-cache delete. gate-cli REJECT at 16; DN-83 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. parsedate-minus0000: 0.40+0.12+0.08-0.02=0.58. dedup-unsorted: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: `parsedate_to_datetime` treating RFC2822 `-0000` as naive while GMT/+0000 are aware UTC is a real stdlib footgun; `astimezone(utc)` is the equally tempting wrong fix on a CDT helper host (13:15 local → 18:15Z) and the mixed-tz test names the contract (GMT, `-0000`, and `+0200` all 13:15+00:00). `Vec::dedup` without sort leaving a later A is the usual consecutive-only unique trap; `sort` then `dedup` still cannot satisfy a test that requires first-seen `[A,C,B]` rather than sorted `[A,B,C]`. Stale 502 fallback now compares dest want 13:15+00:00 / `[A,C,B]` against a second file still on naive 13:15 / leftover `[A,C,A,B]` (r61 densification). Reviewer keep-astimezone is an explicit rejected keep-wrong-fix (r61 densification). jq recovery dumps inventory then stale as two objects. gate-cli freeze plus refuse-destroy is an honest apply block, not a silent skip. Weak: helper-host CDT offset is baked into the pytest failure rather than read from `date +%z` in the same turn; sort+dedup still uses clone+sort instead of `BTreeSet` which would fail the same way. Next densification: a 502 whose local tide-stamps fixture is rewritten after the replace(tzinfo=utc) patch and still disagrees, or a reviewer asking to keep `sort`+`dedup` "so operators can grep serials in lexicographic order from runbooks".

Novel coverage: 41%
"""


def write_excl(path: Path, data: bytes) -> None:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(path, flags, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def dump_jsonl(records) -> bytes:
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def main() -> int:
    records = [ep1(), ep2()]
    for rec in records:
        validate_episode(rec)
        json.loads(json.dumps(rec, allow_nan=False))
    payload = dump_jsonl(records)
    notes = NOTES.encode("utf-8")
    STAGE.mkdir(parents=True, exist_ok=True)
    (STAGE / "batch-r62.jsonl").write_bytes(payload)
    (STAGE / "NOTES-r62.md").write_bytes(notes)

    dest_batch = DEST_DIR / "batch-r62.jsonl"
    dest_notes = DEST_DIR / "NOTES-r62.md"
    if dest_batch.exists() or dest_notes.exists():
        dest_batch = DEST_DIR / "batch-r62c.jsonl"
        dest_notes = DEST_DIR / "NOTES-r62c.md"
        if dest_batch.exists() or dest_notes.exists():
            raise SystemExit(f"refuse: {dest_batch} or {dest_notes} exists")
    write_excl(dest_batch, payload)
    write_excl(dest_notes, notes)
    print(f"wrote {dest_batch} {dest_batch.stat().st_size}B")
    print(f"wrote {dest_notes} {dest_notes.stat().st_size}B")
    print("ids", [r["id"] for r in records])
    print("steps", [len(r["steps"]) for r in records])
    return 0


if __name__ == "__main__":
    sys.exit(main())
