#!/usr/bin/env python3
"""Generate ACTF r68 episodes into a reserved round_txn staging dir."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STAGE = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/staging/"
    "2026-09-02-final-heavy/agentic-coding-trajectory-factory/"
    "r68-317a0728ec0f41a9b4850c97c4568d3b"
)

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-03T00:52:00Z",
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

PROGRESS = re.compile(
    r"\b(?:found|measured|reproduced|failed|edited|tested|verified|patched)\b",
    re.I,
)
HIDDEN = {"thought", "chain_of_thought", "scratch", "inner_monologue", "reasoning"}


def db(text: str) -> str:
    text = " ".join(text.split())
    if not (80 <= len(text) <= 240):
        raise SystemExit(f"decision_basis len {len(text)}: {text}")
    if not text.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")):
        raise SystemExit(f"bad prefix: {text}")
    return text


def walk_hidden(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            nk = re.sub(r"[^a-z0-9]+", "_", str(k)).casefold().strip("_")
            if nk in HIDDEN or nk.startswith("internal_reasoning"):
                raise SystemExit(f"hidden key {k} at {path}")
            walk_hidden(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk_hidden(v, f"{path}[{i}]")


def audit(ep: dict) -> None:
    steps = ep["steps"]
    if not 12 <= len(steps) <= 17:
        raise SystemExit(f"{ep['id']} step count {len(steps)}")
    ns = [s["n"] for s in steps]
    if ns != list(range(1, len(steps) + 1)):
        raise SystemExit(f"{ep['id']} bad n {ns}")
    blob_429 = blob_502 = 0
    for s in steps:
        walk_hidden(s)
        db(s["decision_basis"])
        obs = s["observation"]
        ref = s.get("reflection", "")
        if "hypothesis" in obs.lower():
            raise SystemExit(f"{ep['id']} hypothesis in obs n={s['n']}")
        if not PROGRESS.search(obs + " " + ref):
            raise SystemExit(f"{ep['id']} missing progress n={s['n']}: {obs[:80]!r} {ref[:80]!r}")
        blob_429 += len(re.findall(r"429", obs))
        blob_502 += len(re.findall(r"502", obs))
        if s["tool_call"]["name"] not in {
            "bash", "read_file", "edit_file", "write_file", "search",
            "gh", "kubectl", "gate-cli", "tofu", "tenv", "tflint", "aws", "jq",
            "hcl2json", "block", "decline", "deny", "refuse",
        }:
            raise SystemExit(f"unknown tool {s['tool_call']['name']}")
    if blob_429 != 1 or blob_502 != 1:
        raise SystemExit(f"{ep['id']} noise counts 429={blob_429} 502={blob_502}")
    rec = ep["reward"]
    nums = [v for k, v in rec.items() if k not in {"success", "aggregation", "cost"} and isinstance(v, (int, float))]
    if abs(sum(nums) - rec["total"]) > 1e-9:
        raise SystemExit(f"{ep['id']} reward {sum(nums)} != {rec['total']}")
    walk_hidden(ep)


def ep1() -> dict:
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: PH-680 reports radio dest lists pick up X after a caller mutates week36. Search load_catalog as evidence of copy.copy on nested dest lists."
            ),
            "plan": "1) search load_catalog 2) read catalog.py 3) measure copy.copy alias 4) confirm want ['A'] 5) fix deepcopy 6) regression + PR",
            "tool_call": {
                "name": "search",
                "args": {"pattern": "load_catalog|copy.copy|deepcopy|CATALOG", "path": "."},
            },
            "observation": (
                "phalaropecopy/catalog.py:1:import copy\n"
                "phalaropecopy/catalog.py:8:def load_catalog() -> dict:\n"
                "phalaropecopy/catalog.py:9:    return copy.copy(CATALOG)\n"
                "tests/test_install.py:12:    assert 'week36' in load_catalog()\n"
                "5 matches"
            ),
            "reflection": "Found load_catalog calling copy.copy(CATALOG) on nested dest lists. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: catalog.py:9 calls copy.copy(CATALOG) on nested dest lists (step 1). Read the helper as evidence of any deepcopy."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "phalaropecopy/catalog.py", "offset": 1, "limit": 18},
            },
            "observation": (
                "1  import copy\n"
                "2\n"
                "3  # Harbor radio dest lists must stay ['A'] after a caller mutates its copy.\n"
                "4  # Nested lists are the dest occupancy for week36 / shift-a/berth / radio.hex.\n"
                "5\n"
                "6  CATALOG = {\"week36\": [\"A\"], \"shift-a/berth\": [\"B\"], \"radio.hex\": [\"C\"]}\n"
                "7\n"
                "8  def load_catalog() -> dict:\n"
                "9      return copy.copy(CATALOG)\n"
                "10\n"
                "11 def load_week36() -> list:\n"
                "12     return load_catalog()[\"week36\"]\n"
            ),
            "reflection": "Found copy.copy is the only clone and nested lists are shared. First plan: S3 truncated the dest catalog. Next measure the alias.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: load_catalog runs copy.copy without deepcopy (step 2). Measure a mutated week36 list as evidence of the alias."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 -c \"import copy; C={'week36':['A'],'radio.hex':['C']}; "
                        "d=copy.copy(C); d['week36'].append('X'); print('copy', C); "
                        "e=dict(C); e['week36'].append('Y'); print('dict', C); "
                        "f=copy.deepcopy(C); f['week36'].append('Z'); print('deep', C)\""
                    )
                },
            },
            "observation": "copy {'week36': ['A', 'X'], 'radio.hex': ['C']}\ndict {'week36': ['A', 'X', 'Y'], 'radio.hex': ['C']}\ndeep {'week36': ['A', 'X', 'Y'], 'radio.hex': ['C']}",
            "reflection": "Measured copy.copy and dict() both alias week36 so X/Y leak; deepcopy leaves the source list. Next confirm dest want still lists ['A'].",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Reflection: copy.copy leaked X into CATALOG week36 (step 3). Fetch copy notes via gh as evidence of copy.copy vs deepcopy."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/python/cpython/contents/Doc/library/copy.rst",
                },
            },
            "observation": (
                "HTTP/2 429\n"
                "retry-after: 5\n"
                "x-ratelimit-limit: 60\n"
                "x-ratelimit-remaining: 0\n"
                "{\"message\":\"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=5\","
                "\"documentation_url\":\"https://docs.github.com/rest/overview/rate-limits\"}"
            ),
            "reflection": "GitHub fetch failed: 429 with retry-after 5 while fetching copy docs. Wait, then use the vendored docs/copy-copy-nested.md fixture.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/copy-copy-nested.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/copy-copy-nested.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  copy.copy is a shallow clone; nested dest lists stay shared.\n"
                "2  dict(CATALOG) is also shallow and still aliases week36.\n"
                "3  Durable: copy.deepcopy so a caller append cannot leak into CATALOG.\n"
                "4  Mixed catalog: week36, shift-a/berth, and radio.hex must stay one-letter lists.\n"
                "5  Skipping deepcopy drops radio.hex identity instead of keeping dest lists.\n"
                "6  A truncated S3 object is independent of this client clone.\n"
            ),
            "reflection": "Verified the shallow-copy trap and that dict() still aliases week36. Next pull the committed radio dest fixture.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: RFC-style notes say radio dest lists need deepcopy (step 5). Get the committed radio dest object as evidence the want set is ['A']."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-object",
                        "--bucket",
                        "phalaropefen-specs",
                        "--key",
                        "phalaropecopy/radio-dests.json",
                        "/tmp/phalaropecopy-inventory.json",
                    ]
                },
            },
            "observation": (
                "download failed: s3.eu-north-1.amazonaws.com/phalaropefen-specs\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "server: awselb/2.0\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection failure"
            ),
            "reflection": "Radio dest get-object hit 502 on the ELB before headers. Retry against the committed fixtures/radio-dests.json instead of the edge.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: radio dest get-object returned 502 from the ELB (step 6). jq fixtures/radio-dests.json want as local-spec evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": ["-r", "{want:.want, stale:.stale, n:.dest_count, path:.path}", "fixtures/radio-dests.json"]
                },
            },
            "observation": (
                "{\n"
                "  \"want\": {\n"
                "    \"week36\": [\"A\"],\n"
                "    \"shift-a/berth\": [\"B\"],\n"
                "    \"radio.hex\": [\"C\"]\n"
                "  },\n"
                "  \"stale\": [\"A\", \"X\"],\n"
                "  \"n\": 3,\n"
                "  \"path\": \"fixtures/radio-dests.stale.json\"\n"
                "}"
            ),
            "reflection": "Verified want already lists week36=['A'] and the stale file still lists ['A','X']. Next join that with the measured copy.copy alias.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: fixture want already lists week36=['A'] (step 7). jq the measured ['A','X'] against that spec as evidence whether S3 truncated dests."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "s",
                        "fixtures/radio-dests.json",
                        "--slurpfile",
                        "k",
                        "fixtures/radio-dests.stale.json",
                        '{got:"load_catalog week36 [A, X]",want:$s[0].want,stale:$k[0].week36,n:$s[0].dest_count,path:$s[0].path}',
                    ]
                },
            },
            "observation": (
                "{\n"
                "  \"got\": \"load_catalog week36 [A, X]\",\n"
                "  \"want\": {\n"
                "    \"week36\": [\"A\"],\n"
                "    \"shift-a/berth\": [\"B\"],\n"
                "    \"radio.hex\": [\"C\"]\n"
                "  },\n"
                "  \"stale\": [\"A\", \"X\"],\n"
                "  \"n\": 3,\n"
                "  \"path\": \"fixtures/radio-dests.stale.json\"\n"
                "}"
            ),
            "reflection": "Plan change: radio want dests already list week36=['A'] and got is copy.copy aliasing on a committed 3-key catalog. Abandon truncated-catalog. Switching the edit target to load_catalog so nested dest lists deepcopy.",
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the truncated-catalog plan; load_catalog still aliases week36 (step 8). Edit dict() as evidence only the mapping is cloned."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "phalaropecopy/catalog.py",
                    "old_string": "def load_catalog() -> dict:\n    return copy.copy(CATALOG)\n",
                    "new_string": "def load_catalog() -> dict:\n    return dict(CATALOG)\n",
                },
            },
            "observation": "Edited phalaropecopy/catalog.py: load_catalog now returns dict(CATALOG) so the outer mapping is a new dict.",
            "reflection": "Wrote a shallow dict() clone. Add a pytest that requires week36 to stay ['A'] after a caller append.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: load_catalog now returns dict(CATALOG) (step 9). Write a pytest as evidence that week36 stays ['A'] after a caller mutates."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_catalog.py",
                    "content": (
                        "from phalaropecopy.catalog import load_catalog, load_week36\n\n"
                        "def test_week36_isolated():\n"
                        "    got = load_catalog()\n"
                        "    got['week36'].append('X')\n"
                        "    assert load_catalog()['week36'] == ['A']\n"
                        "    assert load_week36() == ['A']\n\n"
                        "def test_radio_hex_isolated():\n"
                        "    got = load_catalog()\n"
                        "    got['radio.hex'].append('X')\n"
                        "    assert load_catalog()['radio.hex'] == ['C']\n"
                    ),
                },
            },
            "observation": "Wrote tests/test_catalog.py (14 lines).",
            "reflection": "Wrote a mixed-dest isolation regression that expects week36 to stay ['A']. Next pytest should reproduce the dict() alias.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Plan: run pytest tests/test_catalog.py as evidence whether dict(CATALOG) keeps week36 as ['A'] after a caller append."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_catalog.py tests/test_install.py -q --tb=short 2>&1 | tail -n 24"
                },
            },
            "observation": (
                "_________________ test_week36_isolated _________________\n"
                "tests/test_catalog.py:7: AssertionError: assert ['A', 'X'] == ['A']\n"
                "_________________ test_radio_hex_isolated _________________\n"
                "tests/test_catalog.py:13: AssertionError: assert ['C', 'X'] == ['C']\n"
                "FAILED tests/test_catalog.py::test_week36_isolated\n"
                "FAILED tests/test_catalog.py::test_radio_hex_isolated\n"
                "2 failed, 4 passed in 0.04s"
            ),
            "reflection": "Test failed: dict() still aliases nested dest lists. Re-read load_catalog and patch deepcopy.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Observation: pytest failed with got ['A','X'] on dict() week36 (step 11). Rewrite fixtures/radio-dests.stale.json as evidence the local spec still disagrees after that patch."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "fixtures/radio-dests.stale.json",
                    "content": (
                        "{\n"
                        "  \"week36\": [\"A\", \"X\"],\n"
                        "  \"shift-a/berth\": [\"B\"],\n"
                        "  \"radio.hex\": [\"C\", \"X\"]\n"
                        "}\n"
                    ),
                },
            },
            "observation": "Wrote fixtures/radio-dests.stale.json (6 lines) from the dict() catalog after the caller append.",
            "reflection": "Edited the local stale dest file after the dict() patch; it still lists leaked X. Next join it with want ['A'].",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: rewritten stale dest file still lists week36=['A','X'] (step 12). jq want vs stale, then re-read load_catalog for the copy.copy evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "s",
                        "fixtures/radio-dests.json",
                        "--slurpfile",
                        "k",
                        "fixtures/radio-dests.stale.json",
                        "{want:$s[0].want.week36,stale:$k[0].week36,got:\"dict() still [A, X]\"}",
                    ]
                },
            },
            "observation": (
                "{\n"
                "  \"want\": [\"A\"],\n"
                "  \"stale\": [\"A\", \"X\"],\n"
                "  \"got\": \"dict() still [A, X]\"\n"
                "}\n"
                "phalaropecopy/catalog.py:8: def load_catalog() -> dict:\n"
                "phalaropecopy/catalog.py:9:     return dict(CATALOG)\n"
            ),
            "reflection": "Verified rewritten stale still disagrees with want ['A'] and line 9 still returns dict(CATALOG). Patch deepcopy.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: load_catalog must deepcopy nested dest lists rather than dict() (step 13). Patch catalog.py as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "phalaropecopy/catalog.py",
                    "old_string": "def load_catalog() -> dict:\n    return dict(CATALOG)\n",
                    "new_string": "def load_catalog() -> dict:\n    return copy.deepcopy(CATALOG)\n",
                },
            },
            "observation": "Edited phalaropecopy/catalog.py: load_catalog now returns copy.deepcopy(CATALOG) so nested dest lists are isolated.",
            "reflection": "Patched the deepcopy clone. Re-run pytest; week36 should stay ['A'].",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: load_catalog now deepcopy's nested dest lists (step 14). Re-run pytest as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_catalog.py tests/test_install.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                "tests/test_catalog.py::test_week36_isolated PASSED\n"
                "tests/test_catalog.py::test_radio_hex_isolated PASSED\n"
                "6 passed in 0.05s"
            ),
            "reflection": "Verified 6 passed including test_week36_isolated. Open the PH-680 PR.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: pytest passed 6/6 after the deepcopy patch (step 15). Create the PH-680 PR via gh as evidence of the load_catalog fix."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/phalaropefen/phalaropecopy-radio/pulls",
                    "raw_field": "title=PH-680: deepcopy radio dest lists instead of copy.copy aliasing week36",
                },
            },
            "observation": (
                "{\n"
                "  \"number\": 681,\n"
                "  \"html_url\": \"https://git.phalaropefen.internal/pkg/phalaropecopy-radio/pull/681\",\n"
                "  \"state\": \"open\"\n"
                "}"
            ),
            "reflection": "Verified PR 681 opened. load_catalog keeps week36=['A'] after a caller mutates. Live radio copies remain a follow-up against the designed harbor host.",
        },
    ]
    return {
        "id": "act-r68-copy-copy-nested-phalaropecopy-a6e81c",
        "goal": (
            "PH-680 (phalaropecopy-radio, Python 3.12 harbor radio dest helper + fixtures/radio-dests.json; pytest): "
            "nightly radio copies print week36=['A','X'] after a caller mutates its catalog while dest names are "
            "week36, shift-a/berth, radio.hex (file fixtures/radio.ndjson, occupancy ['A']). Find why load_catalog "
            "aliases nested dest lists, add a mixed-dest isolation regression, and open a PR. Designed plant; not a live harbor apply."
        ),
        "steps": steps,
        "outcome": (
            "load_catalog ran copy.copy(CATALOG) so nested dest lists were shared and week36 printed ['A','X'] after a caller append. "
            "A first patch that returned dict(CATALOG) still failed tests/test_catalog.py::test_week36_isolated (got ['A','X']). "
            "The rewritten local stale fixture still listed leaked X. load_catalog now returns copy.deepcopy(CATALOG). "
            "Verified by pytest 6 passed (tests/test_catalog.py::test_week36_isolated). PR 681 opened. "
            "Live radio copies remain a follow-up against the designed harbor host."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.4,
            "copy_copy_nested_fix": 0.12,
            "mixed_dest_isolation_test": 0.08,
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
            "factory": "agentic-coding-trajectory-factory",
            "round": 68,
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "sim_or_real": "designed",
            "training_ready": False,
            "rights": RIGHTS,
            "codebase_type": "library / harbor radio dest lists (Python 3.12 copy.copy)",
            "bug_class": "silent no-op: copy.copy aliased nested dest lists so week36 leaked X; first fix dict() stayed shallow",
            "test_harness": "pytest + aws s3api + jq",
            "noise_steps": {"429": 4, "502": 6},
            "noise_recovery_steps": {"429": 5, "502": 7},
            "plan_change_step": 8,
            "debug_loop_steps": [9, 10, 11, 12, 13, 14, 15],
            "tags": ["copy.copy", "copy.deepcopy", "shallow-copy", "nested-list", "radio-dest", "rewritten-stale"],
        },
    }


def ep2() -> dict:
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: SR-72 reports berth dest splits fail on unbracketed IPv6 host:port. Search SplitDest as evidence of net.SplitHostPort."
            ),
            "plan": "1) search SplitDest 2) read host.go 3) measure SplitHostPort 4) confirm want 2001:db8::1 5) fix JoinHostPort wrap 6) regression 7) apply or hand off",
            "tool_call": {
                "name": "search",
                "args": {"pattern": "SplitDest|SplitHostPort|JoinHostPort|LastIndex", "path": "."},
            },
            "observation": (
                "soraaddr/host.go:1:package soraaddr\n"
                "soraaddr/host.go:8:func SplitDest(raw string) (string, string, error) {\n"
                "soraaddr/host.go:9:    return net.SplitHostPort(raw)\n"
                "soraaddr/host_test.go:12:func TestHostnamePort(t *testing.T)\n"
                "5 matches"
            ),
            "reflection": "Found SplitDest calling net.SplitHostPort on raw dests. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: host.go:9 calls net.SplitHostPort(raw) on dests (step 1). Read the helper as evidence of any JoinHostPort wrap."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "soraaddr/host.go", "offset": 1, "limit": 18},
            },
            "observation": (
                "1  package soraaddr\n"
                "2\n"
                "3  import \"net\"\n"
                "4\n"
                "5  // Harbor berth dests arrive as host:port. PLC IPv6 omits brackets.\n"
                "6  // SplitDest must return host 2001:db8::1 and port 443.\n"
                "7\n"
                "8  func SplitDest(raw string) (string, string, error) {\n"
                "9      return net.SplitHostPort(raw)\n"
                "10 }\n"
                "11\n"
                "12 func LoadCatalog() map[string]string {\n"
                "13     h, _, _ := SplitDest(\"2001:db8::1:443\")\n"
                "14     return map[string]string{\"radio.hex\": h}\n"
                "15 }\n"
            ),
            "reflection": "Found SplitHostPort is the only parser and there is no IPv6 wrap. First plan: S3 truncated the dest catalog. Next measure SplitHostPort.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: SplitDest runs SplitHostPort without an IPv6 wrap (step 2). Measure unbracketed IPv6 as evidence of too many colons."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 -c \""
                        "raw='2001:db8::1:443'; i=raw.rfind(':'); print('last', raw[:i], raw[i+1:]); "
                        "b='[2001:db8::1]:443'; j=b.rfind(':'); print('brack', b[:j], b[j+1:]); "
                        "print('hostport harbor.fen:443'.rsplit(':',1))"
                        "\""
                    )
                },
            },
            "observation": "last 2001:db8::1 443\nbrack [2001:db8::1] 443\n['hostport harbor.fen', '443']",
            "reflection": "Measured last-colon split keeps 2001:db8::1 but leaves brackets on the already-wrapped form. Next confirm dest want still lists 2001:db8::1.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: last-colon split printed 2001:db8::1 for the PLC dest (step 3). Get the committed berth dest object as evidence the want host is unbracketed."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-object",
                        "--bucket",
                        "sorafen-specs",
                        "--key",
                        "soraaddr/berth-dests.json",
                        "/tmp/soraaddr-inventory.json",
                    ]
                },
            },
            "observation": (
                "download failed: s3.eu-north-1.amazonaws.com/sorafen-specs\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "server: awselb/2.0\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection failure"
            ),
            "reflection": "Berth dest get-object hit 502 on the ELB before headers. Retry against the committed fixtures/berth-dests.json instead of the edge.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: berth dest get-object returned 502 from the ELB (step 4). jq fixtures/berth-dests.json want as local-spec evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": ["-r", "{want:.want, stale:.stale, n:.dest_count, path:.path}", "fixtures/berth-dests.json"]
                },
            },
            "observation": (
                "{\n"
                "  \"want\": {\n"
                "    \"radio.hex\": \"2001:db8::1\",\n"
                "    \"week36\": \"harbor.fen\",\n"
                "    \"shift-a/berth\": \"2001:db8::1\"\n"
                "  },\n"
                "  \"stale\": \"too many colons\",\n"
                "  \"n\": 3,\n"
                "  \"path\": \"fixtures/berth-dests.stale.json\"\n"
                "}"
            ),
            "reflection": "Verified want already lists 2001:db8::1 and the stale file still lists too many colons. Next confirm SplitHostPort notes.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: fixture want already lists host 2001:db8::1 (step 5). Fetch net docs via gh as evidence of SplitHostPort vs JoinHostPort."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/golang/go/contents/src/net/ipsock.go",
                },
            },
            "observation": (
                "HTTP/2 429\n"
                "retry-after: 7\n"
                "x-ratelimit-limit: 60\n"
                "x-ratelimit-remaining: 0\n"
                "{\"message\":\"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=7\","
                "\"documentation_url\":\"https://docs.github.com/rest/overview/rate-limits\"}"
            ),
            "reflection": "GitHub returned 429 with retry-after 7 while fetching net docs. Wait, then use the vendored docs/splithostport-ipv6.md fixture.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry_after 7 (step 6). Sleep 8s, then read docs/splithostport-ipv6.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/splithostport-ipv6.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  net.SplitHostPort requires [IPv6]:port; 2001:db8::1:443 is too many colons.\n"
                "2  strings.LastIndex colon leaves brackets on [2001:db8::1]:443.\n"
                "3  Durable: JoinHostPort wrap for unbracketed IPv6, then SplitHostPort.\n"
                "4  Mixed catalog: radio.hex PLC IPv6, week36 hostname, shift-a/berth already bracketed.\n"
                "5  Deleting dest.lock fail-opens harbor berth copies.\n"
                "6  A truncated S3 object is independent of this client parse.\n"
            ),
            "reflection": "Verified harbor berth dests need a JoinHostPort wrap before SplitHostPort. Next join that with the saved want host.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: docs require JoinHostPort wrap plus unbracketed host (step 7). jq the measured too-many-colons against want as evidence whether S3 truncated dests."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "s",
                        "fixtures/berth-dests.json",
                        "--slurpfile",
                        "k",
                        "fixtures/berth-dests.stale.json",
                        '{got:"SplitHostPort too many colons",want:$s[0].want,stale:$k[0].radio,n:$s[0].dest_count,path:$s[0].path}',
                    ]
                },
            },
            "observation": (
                "{\n"
                "  \"got\": \"SplitHostPort too many colons\",\n"
                "  \"want\": {\n"
                "    \"radio.hex\": \"2001:db8::1\",\n"
                "    \"week36\": \"harbor.fen\",\n"
                "    \"shift-a/berth\": \"2001:db8::1\"\n"
                "  },\n"
                "  \"stale\": \"too many colons\",\n"
                "  \"n\": 3,\n"
                "  \"path\": \"fixtures/berth-dests.stale.json\"\n"
                "}"
            ),
            "reflection": "Plan change: berth want dests already list 2001:db8::1 and got is SplitHostPort too many colons on a committed PLC IPv6 catalog. Abandon truncated-catalog. Switching the edit target to SplitDest so unbracketed IPv6 wraps then splits.",
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the truncated-catalog plan; SplitHostPort still errors on PLC IPv6 (step 8). Refuse deleting dest.lock as evidence the object must stay."
            ),
            "tool_call": {
                "name": "refuse",
                "args": {
                    "action": "rm dest.lock so a freshly created object picks JoinHostPort wrap",
                    "policy": "DEST-MUTATE-04",
                    "incident": "SR-72",
                },
            },
            "observation": (
                "refused: DEST-MUTATE-04 forbids deleting dest.lock to skip a SplitHostPort parse. "
                "Delete would drop in-flight harbor berth copies and can fail-open radio.hex. "
                "Safe alternative: wrap unbracketed IPv6 with net.JoinHostPort then SplitHostPort. found 0 waivers"
            ),
            "reflection": "Denied the delete. Next patch host.go; keep dest.lock.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: delete is refused; edit target is SplitDest (step 9). First patch: LastIndex colon as evidence only the last colon is port."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "soraaddr/host.go",
                    "old_string": (
                        "func SplitDest(raw string) (string, string, error) {\n"
                        "    return net.SplitHostPort(raw)\n"
                        "}\n"
                    ),
                    "new_string": (
                        "func SplitDest(raw string) (string, string, error) {\n"
                        "    i := strings.LastIndex(raw, \":\")\n"
                        "    if i < 0 {\n"
                        "        return \"\", \"\", errNoPort\n"
                        "    }\n"
                        "    return raw[:i], raw[i+1:], nil\n"
                        "}\n"
                    ),
                },
            },
            "observation": "Edited soraaddr/host.go: SplitDest now uses strings.LastIndex colon so unbracketed IPv6 keeps 2001:db8::1.",
            "reflection": "Wrote a last-colon splitter. Add a go test that requires unbracketed and bracketed IPv6 plus harbor.fen.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: SplitDest now splits on the last colon (step 10). Write a go test as evidence that radio.hex stays 2001:db8::1 without brackets."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "soraaddr/host_split_test.go",
                    "content": (
                        "package soraaddr\n\n"
                        "import \"testing\"\n\n"
                        "func TestUnbracketedIPv6(t *testing.T) {\n"
                        "    h, p, err := SplitDest(\"2001:db8::1:443\")\n"
                        "    if err != nil || h != \"2001:db8::1\" || p != \"443\" {\n"
                        "        t.Fatalf(\"got %q %q %v\", h, p, err)\n"
                        "    }\n"
                        "}\n\n"
                        "func TestBracketedIPv6(t *testing.T) {\n"
                        "    h, p, err := SplitDest(\"[2001:db8::1]:443\")\n"
                        "    if err != nil || h != \"2001:db8::1\" || p != \"443\" {\n"
                        "        t.Fatalf(\"got %q %q %v\", h, p, err)\n"
                        "    }\n"
                        "}\n\n"
                        "func TestHostnamePort(t *testing.T) {\n"
                        "    h, p, err := SplitDest(\"harbor.fen:443\")\n"
                        "    if err != nil || h != \"harbor.fen\" || p != \"443\" {\n"
                        "        t.Fatalf(\"got %q %q %v\", h, p, err)\n"
                        "    }\n"
                        "}\n"
                    ),
                },
            },
            "observation": "Wrote soraaddr/host_split_test.go (28 lines).",
            "reflection": "Created a mixed-dest regression that expects radio.hex to stay 2001:db8::1. Run go test to reproduce the bracket leftover.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Plan: run go test ./soraaddr as evidence whether LastIndex colon keeps bracketed IPv6 as 2001:db8::1."
            ),
            "tool_call": {
                "name": "bash",
                "args": {"command": "go test ./soraaddr -count=1 2>&1 | tail -n 24"},
            },
            "observation": (
                "--- FAIL: TestBracketedIPv6 (0.00s)\n"
                "    host_split_test.go:16: got \"[2001:db8::1]\" \"443\" <nil>\n"
                "FAIL\n"
                "FAIL    git.sorafen.internal/cli/soraaddr-harbor/soraaddr    0.03s\n"
                "ok      git.sorafen.internal/cli/soraaddr-harbor/soraaddr/install    0.01s"
            ),
            "reflection": "Test failed: LastIndex leaves brackets on [2001:db8::1]:443. Re-read SplitDest and wrap with JoinHostPort.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: go test failed with got [2001:db8::1] on bracketed dest (step 12). Re-read SplitDest; a reviewer asked to keep LastIndex so runbooks still grep host:port."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "soraaddr/host.go", "offset": 1, "limit": 20},
            },
            "observation": (
                "1  package soraaddr\n"
                "2\n"
                "3  import (\n"
                "4      \"net\"\n"
                "5      \"strings\"\n"
                "6  )\n"
                "7\n"
                "8  func SplitDest(raw string) (string, string, error) {\n"
                "9      i := strings.LastIndex(raw, \":\")\n"
                "10     if i < 0 {\n"
                "11         return \"\", \"\", errNoPort\n"
                "12     }\n"
                "13     return raw[:i], raw[i+1:], nil\n"
                "14 }\n"
                "reviewer PH-keep-lastindex: keep LastIndex so operators can grep host:port from runbooks without JoinHostPort. status: rejected\n"
            ),
            "reflection": "Confirmed line 13 still returns bracketed host. Reviewer keep-LastIndex rejected. Patch JoinHostPort wrap then SplitHostPort.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: SplitDest must JoinHostPort-wrap unbracketed IPv6 rather than LastIndex (step 13). Patch host.go as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "soraaddr/host.go",
                    "old_string": (
                        "func SplitDest(raw string) (string, string, error) {\n"
                        "    i := strings.LastIndex(raw, \":\")\n"
                        "    if i < 0 {\n"
                        "        return \"\", \"\", errNoPort\n"
                        "    }\n"
                        "    return raw[:i], raw[i+1:], nil\n"
                        "}\n"
                    ),
                    "new_string": (
                        "func SplitDest(raw string) (string, string, error) {\n"
                        "    if strings.Count(raw, \":\") >= 2 && !strings.HasPrefix(raw, \"[\") {\n"
                        "        i := strings.LastIndex(raw, \":\")\n"
                        "        raw = net.JoinHostPort(raw[:i], raw[i+1:])\n"
                        "    }\n"
                        "    return net.SplitHostPort(raw)\n"
                        "}\n"
                    ),
                },
            },
            "observation": "Edited soraaddr/host.go: SplitDest now JoinHostPort-wraps unbracketed IPv6 then calls SplitHostPort so bracketed dests stay 2001:db8::1.",
            "reflection": "Patched the JoinHostPort wrap. Re-run go test; radio.hex should stay 2001:db8::1.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: SplitDest now wraps unbracketed IPv6 then SplitHostPort (step 14). Re-run go test ./soraaddr as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {"command": "go test ./soraaddr -count=1 2>&1 | tail -n 12"},
            },
            "observation": (
                "ok      git.sorafen.internal/cli/soraaddr-harbor/soraaddr    0.04s\n"
                "ok      git.sorafen.internal/cli/soraaddr-harbor/soraaddr/install    0.01s"
            ),
            "reflection": "Verified 2 packages passed including TestBracketedIPv6. Check gate-cli before applying dest.lock.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: go test passed 2 packages after the JoinHostPort wrap (step 15). Run gate-cli check apply as evidence whether prod dest mutation is allowed."
            ),
            "tool_call": {
                "name": "gate-cli",
                "args": {
                    "argv": ["check", "apply", "--change", "soraaddr-ipv6-wrap", "--resource", "dest.lock"]
                },
            },
            "observation": (
                "gate-cli check apply --change soraaddr-ipv6-wrap\n"
                "status: REJECT\n"
                "policy: prod-batch-freeze\n"
                "ticket: SR-60\n"
                "until: 2026-09-16T00:00:00Z\n"
                "evidence: change mutates dest.lock (soraaddr-harbor SplitHostPort to JoinHostPort wrap)\n"
                "found 0 waivers"
            ),
            "reflection": "Measured REJECT under SR-60 freeze through 2026-09-16. Do not apply dest.lock. Open a handoff issue attaching the JoinHostPort wrap.",
        },
        {
            "n": 17,
            "decision_basis": db(
                "Observation: gate-cli REJECT'd the dest apply under freeze SR-60 (step 16). Open a handoff issue as evidence live SplitDest still errors on PLC IPv6."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "title": "SR-83: apply soraaddr JoinHostPort wrap after SR-60 freeze (blocks SR-72 close)",
                    "body": "host.go now JoinHostPort-wraps unbracketed IPv6 then SplitHostPort; go test 2 packages passed. Live dest.lock still SplitHostPort-only. gate-cli freeze SR-60 until 2026-09-16. Do not delete dest.lock.",
                },
            },
            "observation": "https://git.sorafen.internal/cli/soraaddr-harbor/issues/83",
            "reflection": "Opened SR-83. Stack tests are green; prod apply remains blocked. Handoff, not close.",
        },
    ]
    return {
        "id": "act-r68-splithostport-ipv6-soraaddr-d3f914",
        "goal": (
            "SR-72 (soraaddr-harbor, Go 1.22 berth dest helper + kind-less sorafen; go test + gate-cli): "
            "nightly berth copies fail net.SplitHostPort on PLC dest 2001:db8::1:443 (too many colons) while dest names are "
            "radio.hex, week36, shift-a/berth (file fixtures/berth-dests.json, want host 2001:db8::1). Find why SplitDest "
            "rejects unbracketed IPv6, fix the helper, and apply or hand off. Designed plant; not a live harbor apply."
        ),
        "steps": steps,
        "outcome": (
            "SplitDest ran net.SplitHostPort on unbracketed PLC IPv6, so radio.hex failed with too many colons. "
            "A first patch that split on strings.LastIndex colon still failed TestBracketedIPv6 (got [2001:db8::1]). "
            "Reviewer keep-LastIndex was rejected. SplitDest now JoinHostPort-wraps unbracketed IPv6 then SplitHostPort; go test 2 packages passed. "
            "Applying dest.lock remains blocked by gate-cli freeze SR-60; live helper still SplitHostPort-only. SR-83 opened. "
            "Overall: incomplete; prod apply unresolved."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "splithostport_ipv6_fix": 0.1,
            "mixed_hostport_test": 0.08,
            "prod_apply_blocked_penalty": -0.12,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.28,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 2,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 3,
                "duration_min": 36,
                "prod_apply": 0,
            },
        },
        "meta": {
            "factory": "agentic-coding-trajectory-factory",
            "round": 68,
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "sim_or_real": "designed",
            "training_ready": False,
            "rights": RIGHTS,
            "codebase_type": "CLI / harbor berth dests (Go 1.22 net.SplitHostPort)",
            "bug_class": "schema mismatch: net.SplitHostPort rejected unbracketed IPv6; first fix LastIndex left brackets on wrapped dests",
            "test_harness": "go test + aws s3api + jq + gate-cli",
            "noise_steps": {"502": 4, "429": 6},
            "noise_recovery_steps": {"502": 5, "429": 7},
            "plan_change_step": 8,
            "debug_loop_steps": [10, 11, 12, 13, 14, 15],
            "tags": ["net.SplitHostPort", "net.JoinHostPort", "ipv6", "host-port", "gate-cli-freeze", "refuse-delete"],
        },
    }


NOTES = """# ACTF r68 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r68-copy-copy-nested-phalaropecopy-a6e81c`, `act-r68-splithostport-ipv6-soraaddr-d3f914` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`gate-cli`/`aws`/`jq`/`refuse`). meta.round=68 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Live-tree write is create-only via round_txn (`batch-r68.jsonl`); never clobbered `batch-r01.jsonl` / `NOTES-r01.md` / r02 / r03 / r04 / r21 / r22 / r41 / r42 / r61 / r62 / r63 / r64 / r65 / r66 / r67. Distinct from window r01 (sanderling inclusive-after / whimbrel inflight Map), r02 jacanasub re.sub count-vs-flags / tattlerbool argparse bool, r03 path.Clean scheme / scauphmac UTF-16 length, r04 json float64 id / csv quoted comma, r21 duration-json / executescript, r22 sql.ErrNoRows / SameSite, r41 unpack-be-le / pvc-rwo, r42 re.sub group10 / json omitempty, r61 tzdata / tofu count-index, r62 parsedate -0000 / dunlincut unsorted dedup, r63 pem.Decode rest / tofu moved, r64 inet_aton / WaitForFirstConsumer, r65 uuid bytes_le / sg inline, r66 commonprefix lib64 / s3 ACL, r67 zip strict / tofu removed, leftover mill r50 ElementTree default xmlns, r23 Path.with_suffix .tar.gz, r19 configparser percent, r53 shlex comments, and r37 rstrip charset. Addresses r67 NOTES gap (rewritten stale dest file after the first patch still disagrees; reviewer keep-LastIndex rejected) while leaving mill lots, Kubernetes YAML, and OpenTofu. Invented repos `git.phalaropefen.internal/pkg/phalaropecopy-radio.git` and `git.sorafen.internal/cli/soraaddr-harbor.git`. Linear RM-793 remains the rights tracker.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r68-copy-copy-nested-phalaropecopy-a6e81c | Python 3.12 harbor radio dest helper + radio-dests fixtures / pytest + aws s3api + jq | silent no-op: `copy.copy` aliased nested dest lists so week36 leaked X; first fix `dict()` stayed shallow | success; 6/6; PR 681 | 0.58 |
| act-r68-splithostport-ipv6-soraaddr-d3f914 | Go 1.22 berth dest helper / go test + aws s3api + jq + gate-cli | schema mismatch: `net.SplitHostPort` rejected unbracketed IPv6; first fix `LastIndex` left brackets | incomplete HIL/prod apply; SR-83; freeze SR-60 | 0.28 |

## Step counts, noise, plan change
- act-r68-copy-copy-nested-phalaropecopy-a6e81c: 16 steps. 429 at step 4 (`gh api` cpython copy.rst, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/copy-copy-nested.md`). 502 at step 6 (`aws s3api get-object` phalaropefen-specs radio-dests ELB) -> recovery step 7 (`jq` committed `fixtures/radio-dests.json` against stale `fixtures/radio-dests.stale.json`). Plan change at step 8: jq join shows want already week36=['A'] and got is copy.copy alias [A,X] on a committed 3-key catalog; abandon truncated-catalog. Debug loop: 9 edit dict() -> 10 write isolation pytest -> 11 FAIL got ['A','X'] -> 12 rewrite stale fixture after the dict() patch still lists leaked X -> 13 jq want vs rewritten stale + re-read -> 14 deepcopy patch -> 15 6 passed.
- act-r68-splithostport-ipv6-soraaddr-d3f914: 17 steps. 502 at step 4 (`aws s3api get-object` sorafen-specs berth-dests ELB) -> recovery step 5 (`jq` committed `fixtures/berth-dests.json`). 429 at step 6 (`gh api` golang/go ipsock.go, retry-after 7) -> recovery step 7 (read vendored `docs/splithostport-ipv6.md`). Plan change at step 8: jq want already 2001:db8::1 while got is too many colons; abandon remounting remote dests. Debug loop: 10 edit LastIndex -> 11 write mixed-host go test -> 12 FAIL got [2001:db8::1] -> 13 reviewer keep-LastIndex rejected -> 14 JoinHostPort wrap + SplitHostPort -> 15 2 packages passed. `refuse` at step 9 blocks deleting dest.lock. gate-cli REJECT at 16; SR-83 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. copy-copy-nested: 0.40+0.12+0.08-0.02=0.58. splithostport-ipv6: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: `copy.copy` sharing nested dest lists is a real stdlib footgun (`dict()` is equally shallow); the isolation test names the contract (week36 stays `['A']` after a caller append, radio.hex stays `['C']`). `net.SplitHostPort` rejecting unbracketed `2001:db8::1:443` is the usual IPv6 host:port trap; `strings.LastIndex` still cannot satisfy a test that requires bracketed dests to drop the brackets. Addresses r67 densification: the 502 local fixture is rewritten after the dict() patch and still lists leaked X, and a reviewer asking to keep LastIndex "so operators can grep host:port from runbooks" is explicitly rejected. Leave mill lots, Kubernetes YAML, and OpenTofu (r67 already returned `removed`). Weak: deepcopy of the whole mapping copies dest strings that never needed cloning; JoinHostPort wrap still uses `Count(":") >= 2` which would also wrap `harbor.fen:443` if a hostname ever contained a colon. Next densification: a 502 whose local berth-dests fixture is rewritten after the JoinHostPort patch and still lists too many colons, or a reviewer asking to keep `dict()` "so operators can mutate week36 occupancy from runbooks without isolating radio.hex".

Novel coverage: 40%
"""


def main() -> None:
    if not STAGE.is_dir():
        raise SystemExit(f"staging missing: {STAGE}")
    records = [ep1(), ep2()]
    for rec in records:
        audit(rec)
        if rec["meta"]["round"] != 68:
            raise SystemExit("round")
        if rec["meta"]["sim_or_real"] != "designed":
            raise SystemExit("sim")
    batch = STAGE / "batch-r68.jsonl"
    notes = STAGE / "NOTES-r68.md"
    if batch.exists() or notes.exists():
        raise SystemExit("refusing to overwrite staged files")
    lines = [json.dumps(rec, ensure_ascii=False, separators=(",", ":")) for rec in records]
    for i, line in enumerate(lines, 1):
        json.loads(line)
        if "\n" in line:
            raise SystemExit(f"multiline object line {i}")
    batch.write_text("\n".join(lines) + "\n")
    notes.write_text(NOTES)
    print(f"wrote {batch} ({len(lines)} records)")
    print(f"wrote {notes}")
    for rec in records:
        print(rec["id"], "steps", len(rec["steps"]), "success", rec["reward"]["success"])


if __name__ == "__main__":
    main()
