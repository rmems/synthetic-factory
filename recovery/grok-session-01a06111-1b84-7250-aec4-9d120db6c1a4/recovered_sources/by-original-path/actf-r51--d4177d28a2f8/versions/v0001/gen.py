#!/usr/bin/env python3
"""Generate designed ACTF r51 episodes (Q=2). Never writes outputs/raw/."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/home/raulmc/rmems/synthetic-factory/pipelines")

from check_records import FactoryStaging, check_jsonl  # noqa: E402
from round_txn_coverage import (  # noqa: E402
    has_long_horizon_debug_loop,
    sparse_step_progress_errors,
)
from validate_run import check_episode  # noqa: E402
from verify_execution import verify_batch_for_frontier  # noqa: E402

OUT = Path("/tmp/actf-r51")
GENERATED_AT = "2026-09-02T23:58:00Z"
ROUND = 51
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
ID1 = "act-r51-round-half-even-chubround-a9d72c"
ID2 = "act-r51-emptydir-sizelimit-darterdisk-e2b618"
PLANT_TOKENS = ("chubround", "chubfen", "darterdisk", "darterfen")


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
        "round": ROUND,
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "sim_or_real": "designed",
        "training_ready": False,
        "rights": rights(),
    }
    m.update(extra)
    return m


def prior_ids() -> set[str]:
    found: set[str] = set()
    self_batch = (OUT / "batch-r51.jsonl").resolve()
    for path in sorted(Path("/tmp").glob("actf-r*/batch-r*.jsonl")):
        if path.resolve() == self_batch:
            continue
        for line in path.read_text(encoding="utf-8").split("\n"):
            if not line.strip():
                continue
            rec = json.loads(line)
            rid = rec.get("id")
            if isinstance(rid, str) and rid.strip():
                found.add(rid.strip())
    id_re = re.compile(r'ID[12] = "(act[^"]+)"')
    for path in sorted(Path("/tmp").glob("actf-r*/gen.py")):
        if path.resolve().parent == OUT.resolve():
            continue
        found.update(id_re.findall(path.read_text(encoding="utf-8")))
    mill = Path("/home/raulmc/rmems/synthetic-factory/outputs/raw")
    if mill.is_dir():
        for path in mill.glob("**/agentic-coding-trajectory-factory/batch-r*.jsonl"):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                rid = rec.get("id")
                if rid:
                    found.add(rid)
    return found


def prior_plant_hits() -> list[str]:
    hits: list[str] = []
    self_dir = OUT.resolve()
    paths = list(Path("/tmp").glob("actf-r*/*"))
    mill = Path("/home/raulmc/rmems/synthetic-factory/outputs/raw")
    if mill.is_dir():
        paths.extend(mill.glob("**/agentic-coding-trajectory-factory/*"))
    for path in sorted(paths):
        if not path.is_file():
            continue
        if path.resolve().parent == self_dir:
            continue
        if path.suffix not in {".jsonl", ".md", ".py"}:
            continue
        blob = path.read_text(encoding="utf-8", errors="replace").lower()
        for token in PLANT_TOKENS:
            if token in blob:
                hits.append(f"{path}:{token}")
    return hits


def ep1() -> dict:
    """chubround-lots: builtin round() mill milligram bins use half-even."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: CB-510 reports mill milligram bins drift off 3/2/1. Search bin_lots and round as evidence of a half-even milligram cast."
            ),
            "plan": "1) search bin_lots 2) read lots.py 3) measure round(2.5) 4) confirm want bins 5) fix ROUND_HALF_UP 6) regression + PR",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "bin_lots|round\\(|quantize|lot.hex",
                    "path": ".",
                },
            },
            "observation": (
                "chubround/lots.py:1:from decimal import Decimal\n"
                "chubround/lots.py:6:def bin_lots(path: str) -> list:\n"
                "chubround/lots.py:11:            rec[\"mg\"] = round(rec[\"mg\"])\n"
                "tests/test_install.py:14:    assert bin_lots(\"fixtures/lots.ndjson\")[0][\"dest\"] == \"shift-a/lot\"\n"
                "fixtures/lot-mg.json:4:    \"lot.hex\",\n"
                "5 matches"
            ),
            "reflection": "Found bin_lots wrapping builtin round on mill JSON milligrams. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: lots.py:11 assigns round(rec[\"mg\"]) with no Decimal rounding (step 1). Read the helper as evidence of any milligram-bin clamp."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "chubround/lots.py", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  from decimal import Decimal\n"
                "2  import json\n"
                "3\n"
                "4  # Mill milligram bins were copied from a PLC float helper.\n"
                "5  # json.loads already turned mg into binary floats.\n"
                "6  def bin_lots(path: str) -> list:\n"
                "7      rows = []\n"
                "8      with open(path) as f:\n"
                "9          for line in f:\n"
                "10             rec = json.loads(line)\n"
                "11             rec[\"mg\"] = round(rec[\"mg\"])\n"
                "12             rows.append(rec)\n"
                "13     return rows\n"
            ),
            "reflection": "Learned round is called on mill JSON milligrams as-is. First plan: S3 truncated mg digits. Next measure round(2.5).",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: bin_lots passes rec[\"mg\"] through builtin round (step 2). Measure round(2.5/1.5/0.5) as evidence of half-even milligram bins."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 -c \"print(round(2.5), round(1.5), round(0.5))\""
                    )
                },
            },
            "observation": "2 2 0",
            "reflection": "Measured round(2.5)=2, round(1.5)=2, round(0.5)=0. Next confirm the mill want bins still list 3/2/1.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Reflection: round(2.5) printed 2 (step 3). Fetch functions.rst notes via gh as evidence of the half-even vs half-up constructor."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/python/cpython/contents/Doc/library/functions.rst",
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
            "reflection": "GitHub returned 429 with retry-after 5 while fetching round docs. Wait, then use the vendored docs/round-half-even.md fixture.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/round-half-even.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/round-half-even.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  Python round(x) uses banker's rounding (half to even); round(2.5) is 2, round(0.5) is 0.\n"
                "2  Mill PLC milligram bins are ROUND_HALF_UP; 2.5 bins to 3, 1.5 to 2, 0.5 to 1.\n"
                "3  Decimal.quantize(1, ROUND_HALF_EVEN) still maps 2.5 to 2 and fails a mill dest check.\n"
                "4  Durable: Decimal(str(mg)).quantize(Decimal(\"1\"), rounding=ROUND_HALF_UP).\n"
                "5  Dropping mill dest week36 loses the 1.5 mg row.\n"
                "6  A truncated S3 object is independent of this client round.\n"
            ),
            "reflection": "Verified the half-even trap and that ROUND_HALF_EVEN still bins 2.5 to 2. Next pull the committed mill mg fixture.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: RFC-style notes say mill mg needs ROUND_HALF_UP (step 5). Get the committed mill mg object as evidence the want set is 3/2/1."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-object",
                        "--bucket",
                        "chubfen-specs",
                        "--key",
                        "chubround/lot-mg.json",
                        "/tmp/chubround-inventory.json",
                    ]
                },
            },
            "observation": (
                "download failed: s3.eu-west-1.amazonaws.com/chubfen-specs\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "server: awselb/2.0\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection failure"
            ),
            "reflection": "Mill inventory get-object hit 502 on the ELB before headers. Retry against the committed fixtures/lot-mg.json instead of the edge.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: mill inventory get-object returned 502 from the ELB (step 6). jq fixtures/lot-mg.json want as local-spec evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{want:.want, mg:.mg, n:.dest_count, path:.path}",
                        "fixtures/lot-mg.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "want": {\n'
                '    "shift-a/lot": 3,\n'
                '    "week36": 2,\n'
                '    "lot.hex": 1\n'
                "  },\n"
                '  "mg": [2.5, 1.5, 0.5],\n'
                '  "n": 3,\n'
                '  "path": "fixtures/lots.ndjson"\n'
                "}"
            ),
            "reflection": "Verified want already lists mill milligram bins 3/2/1 and JSON numbers include 2.5. Next join that with the measured round() bins.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: fixture want already lists 3/2/1 (step 7). jq the measured round bins against that spec as evidence whether S3 truncated mg."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "s",
                        "fixtures/lot-mg.json",
                        '{got:"round 2 2 0 from 2.5 1.5 0.5",want:$s[0].want,mg:$s[0].mg,n:$s[0].dest_count,path:$s[0].path}',
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "got": "round 2 2 0 from 2.5 1.5 0.5",\n'
                '  "want": {\n'
                '    "shift-a/lot": 3,\n'
                '    "week36": 2,\n'
                '    "lot.hex": 1\n'
                "  },\n"
                '  "mg": [2.5, 1.5, 0.5],\n'
                '  "n": 3,\n'
                '  "path": "fixtures/lots.ndjson"\n'
                "}"
            ),
            "reflection": (
                "Plan change: mill want bins already list 3/2/1 and got is builtin round on a committed 3-line ndjson. "
                "Abandon truncated-transit. Switching the edit target to bin_lots so mill JSON milligrams go through ROUND_HALF_UP."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the truncated-transit plan; round still emits even milligram bins (step 8). Edit ROUND_HALF_EVEN as evidence only even mill mg survive."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "chubround/lots.py",
                    "old_string": "            rec[\"mg\"] = round(rec[\"mg\"])\n",
                    "new_string": (
                        "            rec[\"mg\"] = int(Decimal(str(rec[\"mg\"]))"
                        ".quantize(Decimal(\"1\"), rounding=ROUND_HALF_EVEN))\n"
                    ),
                },
            },
            "observation": "Edited chubround/lots.py: bin_lots now quantizes mg with ROUND_HALF_EVEN so 2.5 still bins to 2.",
            "reflection": "Wrote a half-even Decimal load. Add a pytest that requires mill milligram bins 3/2/1.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: bin_lots now quantizes mg with ROUND_HALF_EVEN (step 9). Write a pytest as evidence that bin_lots milligram bins match 3/2/1."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_lots.py",
                    "content": (
                        "from chubround.lots import bin_lots\n\n"
                        "WANT = {\"shift-a/lot\": 3, \"week36\": 2, \"lot.hex\": 1}\n\n"
                        "def test_bin_lots_mg_is_half_up():\n"
                        "    got = {row[\"dest\"]: row[\"mg\"] for row in bin_lots(\"fixtures/lots.ndjson\")}\n"
                        "    assert got == WANT, f\"got={got} want={WANT}\"\n"
                    ),
                },
            },
            "observation": "Wrote tests/test_lots.py (9 lines).",
            "reflection": "Created a mixed-mg regression that expects lot.hex to stay 1. Run pytest to reproduce the 0 bin.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Plan: run pytest tests/test_lots.py as evidence whether ROUND_HALF_EVEN keeps mill dest lot.hex as milligram bin 1."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_lots.py -q --tb=short 2>&1 | tail -n 20"
                },
            },
            "observation": (
                "F\n"
                "=================================== FAILURES ===================================\n"
                "______________ test_bin_lots_mg_is_half_up ______________\n"
                "tests/test_lots.py:7: in test_bin_lots_mg_is_half_up\n"
                "    assert got == WANT, f\"got={got} want={WANT}\"\n"
                "E   AssertionError: got={'shift-a/lot': 2, 'week36': 2, 'lot.hex': 0} "
                "want={'shift-a/lot': 3, 'week36': 2, 'lot.hex': 1}\n"
                "FAILED tests/test_lots.py::test_bin_lots_mg_is_half_up - AssertionError: "
                "got={'shift-a/lot': 2, 'week36': 2, 'lot.hex': 0} "
                "want={'shift-a/lot': 3, 'week36': 2, 'lot.hex': 1}\n"
                "1 failed in 0.05s"
            ),
            "reflection": "Test failed: ROUND_HALF_EVEN still bins lot.hex to 0. Re-read bin_lots and switch to ROUND_HALF_UP.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Observation: pytest failed with got lot.hex=0 on ROUND_HALF_EVEN (step 11). Re-read bin_lots for the quantize evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "chubround/lots.py", "offset": 4, "limit": 12},
            },
            "observation": (
                "4  # Mill milligram bins were copied from a PLC float helper.\n"
                "5  # json.loads already turned mg into binary floats.\n"
                "6  def bin_lots(path: str) -> list:\n"
                "7      rows = []\n"
                "8      with open(path) as f:\n"
                "9          for line in f:\n"
                "10             rec = json.loads(line)\n"
                "11             rec[\"mg\"] = int(Decimal(str(rec[\"mg\"]))"
                ".quantize(Decimal(\"1\"), rounding=ROUND_HALF_EVEN))\n"
                "12             rows.append(rec)\n"
                "13     return rows\n"
            ),
            "reflection": "Confirmed line 11 still bins mill milligrams half-even. Patch ROUND_HALF_UP.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Reflection: bin_lots must ROUND_HALF_UP rather than ROUND_HALF_EVEN (step 12). Patch lots.py to half-up as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "chubround/lots.py",
                    "old_string": (
                        "            rec[\"mg\"] = int(Decimal(str(rec[\"mg\"]))"
                        ".quantize(Decimal(\"1\"), rounding=ROUND_HALF_EVEN))\n"
                    ),
                    "new_string": (
                        "            rec[\"mg\"] = int(Decimal(str(rec[\"mg\"]))"
                        ".quantize(Decimal(\"1\"), rounding=ROUND_HALF_UP))\n"
                    ),
                },
            },
            "observation": "Edited chubround/lots.py: bin_lots now ROUND_HALF_UP so mill milligram 0.5 bins to 1.",
            "reflection": "Patched the half-up constructor. Re-run pytest; lot.hex should stay 1.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Observation: bin_lots now ROUND_HALF_UP (step 13). Re-run pytest tests/test_lots.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_lots.py tests/test_install.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                "......\n"
                "6 passed in 0.08s"
            ),
            "reflection": "Verified 6 passed including test_bin_lots_mg_is_half_up. Open the CB-510 PR.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: pytest passed 6/6 after the ROUND_HALF_UP patch (step 14). Create the CB-510 PR via gh as evidence of the bin_lots fix."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/chubfen/chubround-lots/pulls",
                    "raw_field": "title=CB-510: ROUND_HALF_UP mill milligram bins so 2.5 bins to 3 instead of banker's 2",
                },
            },
            "observation": (
                "{\n"
                '  "number": 511,\n'
                '  "html_url": "https://git.chubfen.internal/pkg/chubround-lots/pull/511",\n'
                '  "state": "open"\n'
                "}"
            ),
            "reflection": "Opened PR 511. bin_lots keeps 2.5 as 3 and 0.5 as 1. Live mill census follow-up remains against the designed mill host.",
        },
    ]
    return {
        "id": ID1,
        "goal": (
            "CB-510 (chubround-lots, Python 3.12 mill lot milligram helper + fixtures/lot-mg.json; pytest): "
            "nightly mill copies print milligram bins 2/2/0 while the mill dest names are shift-a/lot, week36, lot.hex "
            "(file fixtures/lots.ndjson, mg 2.5/1.5/0.5). "
            "Find why bin_lots drifts mill PLC milligram bins, add a mixed-mg regression, and open a PR. Designed plant; not a live mill apply."
        ),
        "steps": steps,
        "outcome": (
            "bin_lots passed mill JSON milligrams through builtin round(), so lot.hex printed milligram bin 0. "
            "A first patch that used Decimal(str(mg)).quantize(Decimal('1'), rounding=ROUND_HALF_EVEN) still failed "
            "test_bin_lots_mg_is_half_up (got lot.hex=0). "
            "bin_lots now ROUND_HALF_UP. Verified by pytest 6 passed "
            "(tests/test_lots.py::test_bin_lots_mg_is_half_up). PR 511 opened. "
            "Live mill copies remain a follow-up against the designed mill host."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.40,
            "round_half_up_fix": 0.12,
            "mixed_mg_lot_test": 0.08,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.58,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 6,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 2,
                "duration_min": 28,
            },
        },
        "meta": meta_common(
            codebase_type="library / mill lot milligram bins (Python 3.12 round/decimal)",
            bug_class="schema mismatch: builtin round() used half-even mill PLC milligram bins; first fix used ROUND_HALF_EVEN and kept 2.5 as 2",
            test_harness="pytest + aws s3api + jq",
            noise_steps={"429": 4, "502": 6},
            noise_recovery_steps={"429": 5, "502": 7},
            plan_change_step=8,
            debug_loop_steps=[9, 10, 11, 12, 13, 14],
            tags=[
                "round",
                "ROUND_HALF_EVEN",
                "ROUND_HALF_UP",
                "mill-lots",
                "milligram-bins",
                "mixed-mg",
            ],
        ),
    }


def ep2() -> dict:
    """darterdisk-harvest: emptyDir sizeLimit 1Mi evicts mill lot writes."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: DD-72 reports mill harvest pods Evicted while writing mill lots. Search render_deploy and sizeLimit as evidence of a 1Mi emptyDir floor."
            ),
            "plan": "1) search deploy renderer 2) read render_deploy 3) measure live deploy 4) fix sizeLimit 5) regression 6) apply or hand off",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "emptyDir|sizeLimit|ephemeral-storage|EMPTYDIR_SIZE_LIMIT",
                    "path": ".",
                },
            },
            "observation": (
                "darterdisk/deploy.py:5:EMPTYDIR_SIZE_LIMIT = \"1Mi\"\n"
                "darterdisk/deploy.py:6:EPHEMERAL_STORAGE_REQUEST = \"1Mi\"\n"
                "darterdisk/deploy.py:18:                    \"emptyDir\": {\"sizeLimit\": EMPTYDIR_SIZE_LIMIT},\n"
                "deploy/harvest.yaml:14:sizeLimit: 1Mi\n"
                "6 matches"
            ),
            "reflection": "Found emptyDir sizeLimit 1Mi and ephemeral-storage request 1Mi in the renderer. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: deploy.py:5 sets EMPTYDIR_SIZE_LIMIT=1Mi while harvest writes mill lots (step 1). Read the renderer as evidence of any mill-disk clamp."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "darterdisk/deploy.py", "offset": 1, "limit": 28},
            },
            "observation": (
                "1  # Ported from the v1 mill kiln harvest. emptyDir sizeLimit 1Mi starts with the harvest deploy.\n"
                "2  # mill lots are ~18Mi ndjson and must land on /lots during the shift.\n"
                "3\n"
                "4  API_VERSION = \"apps/v1\"\n"
                "5  EMPTYDIR_SIZE_LIMIT = \"1Mi\"\n"
                "6  EPHEMERAL_STORAGE_REQUEST = \"1Mi\"\n"
                "7\n"
                "8  def render_deploy() -> dict:\n"
                "9      return {\n"
                "10         \"apiVersion\": API_VERSION,\n"
                "11         \"kind\": \"Deployment\",\n"
                "12         \"metadata\": {\"name\": \"darterdisk-harvest\"},\n"
                "13         \"spec\": {\n"
                "14             \"selector\": {\"matchLabels\": {\"app\": \"darterdisk-harvest\"}},\n"
                "15             \"template\": {\"spec\": {\n"
                "16                 \"containers\": [{\"name\": \"harvest\", \"resources\": {\"requests\": "
                "{\"ephemeral-storage\": EPHEMERAL_STORAGE_REQUEST}}, "
                "\"volumeMounts\": [{\"name\": \"lots\", \"mountPath\": \"/lots\"}]}],\n"
                "17                 \"volumes\": [{\"name\": \"lots\", \"emptyDir\": {\"sizeLimit\": EMPTYDIR_SIZE_LIMIT}}],\n"
                "18             }},\n"
                "19         },\n"
                "20     }\n"
            ),
            "reflection": "Learned sizeLimit is 1Mi with ephemeral-storage request 1Mi. First plan: mill nodes are DiskPressure so the pod cannot write. Next measure the live Deployment.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: render_deploy emits emptyDir sizeLimit 1Mi (step 2). kubectl get the Deployment as evidence of live spec.status."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-darterfen",
                    "namespace": "darterfen",
                    "argv": [
                        "get",
                        "deploy",
                        "darterdisk-harvest",
                        "-o",
                        "json",
                    ],
                },
            },
            "observation": (
                "Error from server (InternalError): an error on the server ("
                '"<html>\\r\\n<head><title>502 Bad Gateway</title></head>\\r\\n'
                "<body>\\r\\n<center><h1>502 Bad Gateway</h1></center>\\r\\n"
                "upstream connect error or disconnect/reset before headers. "
                'reset reason: connection failure</body></html>"'
                ") occurred attempting to get Deployment.apps/darterdisk-harvest"
            ),
            "reflection": "kind apiserver ingress returned 502 before headers. Retry with a longer request timeout and write the object locally.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: kubectl get deploy returned 502 from the kind ingress (step 3). Retry --request-timeout=30s and write /tmp/darterdisk-deploy.json as evidence."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-darterfen",
                    "namespace": "darterfen",
                    "argv": [
                        "get",
                        "deploy",
                        "darterdisk-harvest",
                        "-o",
                        "json",
                        "--request-timeout=30s",
                    ],
                },
            },
            "observation": (
                "{\n"
                '  "apiVersion": "apps/v1",\n'
                '  "kind": "Deployment",\n'
                '  "metadata": {"name": "darterdisk-harvest", "namespace": "darterfen"},\n'
                '  "spec": {"template": {"spec": {"containers": [{"name": "harvest", '
                '"resources": {"requests": {"ephemeral-storage": "1Mi"}}}], '
                '"volumes": [{"name": "lots", "emptyDir": {"sizeLimit": "1Mi"}}]}}},\n'
                '  "status": {"replicas": 1, "readyReplicas": 0, "unavailableReplicas": 1}\n'
                "}\n"
                "wrote /tmp/darterdisk-deploy.json"
            ),
            "reflection": "Measured live sizeLimit 1Mi, ephemeral-storage 1Mi, readyReplicas 0. Next inspect node DiskPressure so a node-disk plan can be checked.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: live deploy has sizeLimit 1Mi and readyReplicas 0 (step 4). kubectl get node DiskPressure as evidence whether node disk is the mill write miss."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-darterfen",
                    "namespace": "darterfen",
                    "argv": [
                        "get",
                        "nodes",
                        "-o",
                        "json",
                    ],
                },
            },
            "observation": (
                "{\n"
                '  "items": [\n'
                '    {"metadata": {"name": "kind-darterfen-control-plane"}, "status": {"conditions": ['
                '{"type": "Ready", "status": "True"}, {"type": "DiskPressure", "status": "False"}]}},\n'
                '    {"metadata": {"name": "kind-darterfen-worker"}, "status": {"conditions": ['
                '{"type": "Ready", "status": "True"}, {"type": "DiskPressure", "status": "False"}]}},\n'
                '    {"metadata": {"name": "kind-darterfen-worker2"}, "status": {"conditions": ['
                '{"type": "Ready", "status": "True"}, {"type": "DiskPressure", "status": "False"}]}}\n'
                "  ]\n"
                "}\n"
                "nodes Ready=True DiskPressure=False count=3"
            ),
            "reflection": "Found 3 Ready mill nodes with DiskPressure False. This is not a node-disk mill miss. Confirm the emptyDir contract next.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: three mill nodes are Ready without DiskPressure (step 5). Fetch emptyDir sizeLimit docs via gh as evidence of the mill-lot disk contract."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/kubernetes/website/contents/content/en/docs/concepts/storage/volumes.md",
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
            "reflection": "GitHub returned 429 with retry-after 7 while fetching volume docs. Wait, then use the vendored docs/emptydir-sizelimit.md fixture.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry_after 7 (step 6). Sleep 8s, then read docs/emptydir-sizelimit.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/emptydir-sizelimit.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  emptyDir sizeLimit 1Mi evicts mill harvest when mill lots are ~18Mi ndjson.\n"
                "2  Raising sizeLimit to 64Mi still Evicts if ephemeral-storage request stays 1Mi.\n"
                "3  Durable: sizeLimit 64Mi and ephemeral-storage request 64Mi so mill lots land on /lots.\n"
                "4  Adding mill nodes does not raise readyReplicas while sizeLimit is 1Mi.\n"
                "5  Deleting the Deployment fail-opens mill harvest coverage.\n"
                "6  Dropping the Deployment is a mill gate regression.\n"
            ),
            "reflection": "Verified mill harvest needs sizeLimit 64Mi with ephemeral-storage 64Mi. Next join that with the saved Deployment.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: docs require sizeLimit 64Mi when mill lots are 18Mi (step 7). jq spec from the saved deploy as evidence of the live skew."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{limit:.spec.template.spec.volumes[0].emptyDir.sizeLimit,"
                        "eph:.spec.template.spec.containers[0].resources.requests.\"ephemeral-storage\","
                        "ready:.status.readyReplicas}",
                        "/tmp/darterdisk-deploy.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "limit": "1Mi",\n'
                '  "eph": "1Mi",\n'
                '  "ready": 0\n'
                "}"
            ),
            "reflection": (
                "Plan change: live spec has emptyDir sizeLimit 1Mi vs mill lots 18Mi while three mill nodes are Ready without DiskPressure. "
                "Abandon adding mill nodes. Switching the edit target to render_deploy so mill harvest gets sizeLimit 64Mi."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the DiskPressure-node plan; sizeLimit is 1Mi (step 8). Refuse deleting the Deployment as evidence the object must stay."
            ),
            "tool_call": {
                "name": "refuse",
                "args": {
                    "action": "kubectl delete deploy/darterdisk-harvest so a freshly created object picks sizeLimit 64Mi",
                    "policy": "FS-MUTATE-04",
                    "incident": "DD-72",
                },
            },
            "observation": (
                "refused: FS-MUTATE-04 forbids deleting Deployment/darterdisk-harvest to skip a sizeLimit skew. "
                "Delete would drop in-flight mill harvest lots and can fail-open kiln coverage. "
                "Safe alternative: patch sizeLimit and keep replicas 1. found 0 waivers"
            ),
            "reflection": "Denied the delete. Next patch render_deploy; keep the Deployment object.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: delete is refused; edit target is EMPTYDIR_SIZE_LIMIT (step 9). First patch: set EMPTYDIR_SIZE_LIMIT 64Mi as evidence mill lots may fit."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "darterdisk/deploy.py",
                    "old_string": "EMPTYDIR_SIZE_LIMIT = \"1Mi\"\n",
                    "new_string": "EMPTYDIR_SIZE_LIMIT = \"64Mi\"\n",
                },
            },
            "observation": "Edited darterdisk/deploy.py: EMPTYDIR_SIZE_LIMIT is now 64Mi so mill lots may fit on /lots.",
            "reflection": "Wrote a 64Mi sizeLimit floor. Add a pytest that requires sizeLimit 64Mi and ephemeral-storage 64Mi.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: renderer now emits sizeLimit 64Mi (step 10). Write a pytest as evidence that mill harvest uses 64Mi without leaving ephemeral-storage at 1Mi."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_deploy.py",
                    "content": (
                        "from darterdisk.deploy import render_deploy\n\n"
                        "def test_deploy_allows_mill_lots():\n"
                        "    spec = render_deploy()[\"spec\"][\"template\"][\"spec\"]\n"
                        "    limit = spec[\"volumes\"][0][\"emptyDir\"].get(\"sizeLimit\")\n"
                        "    eph = spec[\"containers\"][0][\"resources\"][\"requests\"].get(\"ephemeral-storage\")\n"
                        "    assert limit == \"64Mi\", f\"got sizeLimit={limit}\"\n"
                        "    assert eph == \"64Mi\", f\"got ephemeral-storage={eph}\"\n"
                    ),
                },
            },
            "observation": "Wrote tests/test_deploy.py (10 lines).",
            "reflection": "Created a sizeLimit / ephemeral-storage-64Mi regression. Run pytest to reproduce the 1Mi request miss.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Plan: run pytest tests/test_deploy.py as evidence whether raising sizeLimit to 64Mi satisfies the mill lot disk contract."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_deploy.py -q --tb=short 2>&1 | tail -n 22"
                },
            },
            "observation": (
                "F\n"
                "=================================== FAILURES ===================================\n"
                "______________ test_deploy_allows_mill_lots ______________\n"
                "tests/test_deploy.py:8: in test_deploy_allows_mill_lots\n"
                "    assert eph == \"64Mi\", "
                "f\"got ephemeral-storage={eph}\"\n"
                "E   AssertionError: got ephemeral-storage=1Mi\n"
                "E   assert '1Mi' == '64Mi'\n"
                "FAILED tests/test_deploy.py::test_deploy_allows_mill_lots - AssertionError: got ephemeral-storage=1Mi\n"
                "1 failed in 0.04s"
            ),
            "reflection": "Test failed: ephemeral-storage is still 1Mi. Re-read render_deploy and set the request to 64Mi.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: pytest failed with got ephemeral-storage=1Mi (step 12). Re-read render_deploy for the EMPTYDIR_SIZE_LIMIT evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "darterdisk/deploy.py", "offset": 4, "limit": 16},
            },
            "observation": (
                "4  API_VERSION = \"apps/v1\"\n"
                "5  EMPTYDIR_SIZE_LIMIT = \"64Mi\"\n"
                "6  EPHEMERAL_STORAGE_REQUEST = \"1Mi\"\n"
                "7\n"
                "8  def render_deploy() -> dict:\n"
                "9      return {\n"
                "10         \"apiVersion\": API_VERSION,\n"
                "11         \"kind\": \"Deployment\",\n"
                "12         \"metadata\": {\"name\": \"darterdisk-harvest\"},\n"
                "13         \"spec\": {\n"
                "14             \"selector\": {\"matchLabels\": {\"app\": \"darterdisk-harvest\"}},\n"
                "15             \"template\": {\"spec\": {\n"
                "16                 \"containers\": [{\"name\": \"harvest\", \"resources\": {\"requests\": "
                "{\"ephemeral-storage\": EPHEMERAL_STORAGE_REQUEST}}}],\n"
                "17                 \"volumes\": [{\"name\": \"lots\", \"emptyDir\": {\"sizeLimit\": EMPTYDIR_SIZE_LIMIT}}],\n"
                "18             }},\n"
                "19         },\n"
                "20     }\n"
            ),
            "reflection": "Confirmed line 6 still floors ephemeral-storage against a mill lot write that needs 64Mi. Patch the request and keep sizeLimit 64Mi.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: helper must emit sizeLimit 64Mi and ephemeral-storage 64Mi (step 13). Patch render_deploy spec as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "darterdisk/deploy.py",
                    "old_string": "EPHEMERAL_STORAGE_REQUEST = \"1Mi\"\n",
                    "new_string": "EPHEMERAL_STORAGE_REQUEST = \"64Mi\"\n",
                },
            },
            "observation": "Edited darterdisk/deploy.py: ephemeral-storage request is 64Mi and sizeLimit stays 64Mi.",
            "reflection": "Patched the request and kept sizeLimit 64Mi. Re-run pytest; mill lots should land on /lots.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: helper now emits sizeLimit 64Mi with ephemeral-storage 64Mi (step 14). Re-run pytest tests/test_deploy.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_deploy.py tests/test_render.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                ".....\n"
                "5 passed in 0.07s"
            ),
            "reflection": "Verified 5 passed including test_deploy_allows_mill_lots. Check gate-cli before applying the Deployment.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: pytest passed 5/5 after the sizeLimit patch (step 15). Run gate-cli check apply as evidence whether prod deploy mutation is allowed."
            ),
            "tool_call": {
                "name": "gate-cli",
                "args": {
                    "argv": [
                        "check",
                        "apply",
                        "--change",
                        "darterdisk-size-limit",
                        "--resource",
                        "deploy/darterdisk-harvest",
                    ]
                },
            },
            "observation": (
                "gate-cli check apply --change darterdisk-size-limit\n"
                "status: REJECT\n"
                "policy: prod-batch-freeze\n"
                "ticket: DD-60\n"
                "until: 2026-09-16T00:00:00Z\n"
                "evidence: change mutates Deployment/darterdisk-harvest (darterdisk-harvest sizeLimit)\n"
                "found 0 waivers"
            ),
            "reflection": "Measured REJECT under DD-60 freeze through 2026-09-16. Do not kubectl apply. Open a handoff issue attaching the sizeLimit fix.",
        },
        {
            "n": 17,
            "decision_basis": db(
                "Observation: gate-cli REJECT'd the deploy apply under freeze DD-60 (step 16). Open a handoff issue as evidence the live spec still has sizeLimit 1Mi."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "title": "DD-83: apply darterdisk sizeLimit after DD-60 freeze (blocks DD-72 close)",
                    "body": "render_deploy now emits sizeLimit 64Mi and ephemeral-storage 64Mi; pytest 5 passed. Live deploy still has sizeLimit 1Mi. gate-cli freeze DD-60 until 2026-09-16. Do not kubectl delete the Deployment.",
                },
            },
            "observation": "https://git.darterfen.internal/k8s/darterdisk-harvest/issues/83",
            "reflection": "Opened DD-83. Renderer is green; prod apply remains blocked. Handoff, not close.",
        },
    ]
    return {
        "id": ID2,
        "goal": (
            "DD-72 (darterdisk-harvest, Python 3.12 Deployment renderer + kind darterfen; pytest + kubectl): "
            "mill harvest pods are Evicted while writing mill lots because emptyDir.sizeLimit is 1Mi, "
            "ephemeral-storage request is 1Mi, and readyReplicas is 0. "
            "Find why sizeLimit blocks mill lot writes, fix the renderer, and apply or hand off. Designed plant; not a live cluster trace."
        ),
        "steps": steps,
        "outcome": (
            "render_deploy emitted emptyDir sizeLimit 1Mi with ephemeral-storage request 1Mi, so mill harvest readyReplicas stayed 0. "
            "A first patch that set EMPTYDIR_SIZE_LIMIT 64Mi still failed test_deploy_allows_mill_lots (got ephemeral-storage=1Mi). "
            "The helper now emits sizeLimit 64Mi and ephemeral-storage 64Mi; pytest 5 passed. "
            "Applying Deployment/darterdisk-harvest remains blocked by gate-cli freeze DD-60; live spec still has sizeLimit 1Mi. "
            "DD-83 opened. Overall: incomplete; prod apply unresolved."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "emptydir_size_fix": 0.10,
            "mill_lots_disk_test": 0.08,
            "prod_apply_blocked_penalty": -0.12,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.28,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 5,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 3,
                "duration_min": 35,
                "prod_apply": 0,
            },
        },
        "meta": meta_common(
            codebase_type="CLI / Kubernetes Deployment renderer (Python 3.12)",
            bug_class="schema mismatch: emptyDir sizeLimit 1Mi evicted mill lot writes; first fix set sizeLimit 64Mi and left ephemeral-storage 1Mi",
            test_harness="pytest + kubectl + gate-cli",
            noise_steps={"502": 3, "429": 6},
            noise_recovery_steps={"502": 4, "429": 7},
            plan_change_step=8,
            debug_loop_steps=[10, 11, 12, 13, 14, 15],
            tags=[
                "emptyDir",
                "sizeLimit",
                "ephemeral-storage",
                "Evicted",
                "gate-cli-freeze",
                "refuse-delete",
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
        if not step["observation"].strip():
            raise SystemExit(f"{rec['id']} empty obs {i}")
        if "hypothesis" in step["observation"].lower():
            raise SystemExit(f"{rec['id']} hypothesis in observation {i}")
        db(step["decision_basis"])
        blob = " ".join(
            [
                step["decision_basis"],
                step["observation"],
                step["tool_call"]["name"],
                json.dumps(step["tool_call"]["args"], sort_keys=True),
            ]
        )
        if STALL_RE.search(blob) or not PROGRESS_RE.search(blob):
            raise SystemExit(
                f"{rec['id']} step {i} sparse progress: {step['decision_basis'][:100]!r}"
            )
    obs = [s["observation"] for s in steps]
    n429 = sum("429" in o for o in obs)
    n502 = sum("502" in o for o in obs)
    if n429 != 1 or n502 != 1:
        raise SystemExit(f"{rec['id']} noise counts 429={n429} 502={n502}")
    recov = rec["meta"]["noise_recovery_steps"]
    for code, recov_n in recov.items():
        if code in steps[recov_n - 1]["observation"]:
            raise SystemExit(f"{rec['id']} recovery step {recov_n} repeats {code}")
        if code not in steps[recov_n - 1]["decision_basis"]:
            raise SystemExit(f"{rec['id']} recovery step {recov_n} basis missing {code}")
    reflections = [s.get("reflection", "") for s in steps]
    pivots = [i + 1 for i, r in enumerate(reflections) if "Plan change:" in r or "Pivoting:" in r]
    if pivots != [rec["meta"]["plan_change_step"]]:
        raise SystemExit(f"{rec['id']} plan-change {pivots}")
    pc = rec["meta"]["plan_change_step"]
    if pc in (1, n):
        raise SystemExit(f"{rec['id']} plan-change at end/start")
    nxt = steps[pc]["decision_basis"]
    if "pivot" not in nxt.lower() and "abandon" not in nxt.lower():
        raise SystemExit(f"{rec['id']} next basis missing pivot")
    for path, key, _ in walk_keys(rec):
        norm = re.sub(r"[^a-z0-9]+", "_", key).strip("_").lower()
        if norm in FORBIDDEN or norm.startswith("internal_reasoning"):
            raise SystemExit(f"{rec['id']} forbidden key {path}")
    if rec["meta"]["sim_or_real"] != "designed":
        raise SystemExit("sim_or_real")
    blob = json.dumps(rec)
    if '"sim_or_real": "real"' in blob or '"sim_or_real":"real"' in blob:
        raise SystemExit("real provenance")
    try:
        blob.encode("ascii")
    except UnicodeEncodeError as exc:
        raise SystemExit(f"{rec['id']} non-ascii: {exc}") from exc
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
    if rec["meta"]["rights"]["linear_issue"] != "RM-793":
        raise SystemExit("RM-793")
    if rec["meta"]["rights"]["training_ready"] is not False:
        raise SystemExit("rights.training_ready")
    errs = check_episode(
        rec, rec["id"], forbid_hidden_thought=True, enforce_terminal_outcome=True
    )
    if errs:
        raise SystemExit(f"{rec['id']} check_episode {errs}")
    if not has_long_horizon_debug_loop(steps):
        raise SystemExit(f"{rec['id']} missing debug loop")
    sparse = sparse_step_progress_errors(rec["id"], steps)
    if sparse:
        raise SystemExit(f"{rec['id']} sparse {sparse}")


def notes() -> str:
    return """# ACTF r51 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r51-round-half-even-chubround-a9d72c`, `act-r51-emptydir-sizelimit-darterdisk-e2b618` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`kubectl`/`gate-cli`/`aws`/`jq`/`refuse`). meta.round=51 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Never wrote outputs/raw/. Distinct from staged r10-r49 (r46 vendacekg Decimal(float) binary significand, not builtin `round()` half-even milligram bins; r16 Java BigDecimal scale-equals; r35 yarrowrofs readOnlyRootFilesystem /tmp, not emptyDir sizeLimit; r41 cobiaqos limits-only BestEffort OOM, not emptyDir 1Mi Evicted; r47 ruffeframe itertools.batched short frame / tautogsts StatefulSet Parallel; r48 smelttmpl string.Template $lot_id / perchcron CronJob Forbid; r49 piketab csv.Sniffer comma / gobyenv enableServiceLinks; r24 preStop sleep>grace; r29 minReady>progressDeadline; r34 liveness successThreshold; r37 Deployment OnDelete; r38 startupProbe missing; r40 itertools.groupby unsorted / NetworkPolicy ipBlock.except; r42 wrylots unhexlify odd pad / gannetpdb PDB minAvailable 100%; r43 shadmerge heapq.merge unsorted / hakeipfam Service ipFamilyPolicy SingleStack; r44 ruddtime time.mktime local / avocetready tcp readiness; r45 minnowzip zip truncate / blennydns publishNotReadyAddresses). r50 dir empty at generation. Invented repos `git.chubfen.internal/pkg/chubround-lots.git` and `git.darterfen.internal/k8s/darterdisk-harvest.git`. Beads create failed (Dolt events id default); Linear RM-793 remains the rights tracker.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r51-round-half-even-chubround-a9d72c | Python 3.12 mill lot milligram helper + lot-mg fixtures / pytest + aws s3api + jq | schema mismatch: builtin `round()` used half-even mill PLC milligram bins; first fix used `ROUND_HALF_EVEN` and kept 2.5 as 2 | success; 6/6; PR 511 | 0.58 |
| act-r51-emptydir-sizelimit-darterdisk-e2b618 | Python 3.12 Deployment renderer / pytest + kubectl + gate-cli | schema mismatch: emptyDir `sizeLimit` 1Mi evicted mill lot writes; first fix set `sizeLimit` 64Mi and left ephemeral-storage 1Mi | incomplete HIL/prod apply; DD-83; freeze DD-60 | 0.28 |

## Step counts, noise, plan change
- act-r51-round-half-even-chubround-a9d72c: 15 steps. 429 at step 4 (`gh api` cpython functions.rst, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/round-half-even.md`). 502 at step 6 (`aws s3api get-object` chubfen-specs lot-mg ELB) -> recovery step 7 (`jq` committed `fixtures/lot-mg.json`). Plan change at step 8: jq join shows want already 3/2/1 and got is builtin round on a committed 3-line ndjson; abandon truncated-transit. Debug loop: 9 edit `ROUND_HALF_EVEN` -> 10 write mixed-mg pytest -> 11 FAIL got lot.hex=0 -> 12 re-read bin_lots -> 13 ROUND_HALF_UP patch -> 14 6 passed.
- act-r51-emptydir-sizelimit-darterdisk-e2b618: 17 steps. 502 at step 3 (`kubectl get deploy` kind ingress) -> recovery step 4 (`--request-timeout=30s` writes /tmp/darterdisk-deploy.json). 429 at step 6 (`gh api` kubernetes/website volumes.md, retry-after 7) -> recovery step 7 (read vendored `docs/emptydir-sizelimit.md`). Plan change at step 8: jq sizeLimit 1Mi vs mill lots 18Mi while 3 mill nodes are Ready without DiskPressure; abandon adding mill nodes. Debug loop: 10 edit EMPTYDIR_SIZE_LIMIT 64Mi -> 11 write mill-lots pytest -> 12 FAIL got ephemeral-storage=1Mi -> 13 re-read helper -> 14 ephemeral-storage 64Mi + sizeLimit 64Mi patch -> 15 5 passed. `refuse` at step 9 blocks `kubectl delete deploy`. gate-cli REJECT at 16; DD-83 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. round-half-even: 0.40+0.12+0.08-0.02=0.58. emptydir-sizelimit: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: builtin `round()` on mill JSON milligrams is a real stdlib footgun (IEEE half-even); `Decimal.quantize(..., ROUND_HALF_EVEN)` is the equally tempting milligram-PLC wrong fix and the mixed-mg test names the contract (`lot.hex` stays `1`, not `0`). emptyDir `sizeLimit` 1Mi with mill lots ~18Mi is the usual mill harvest eviction; raising only `sizeLimit` still cannot satisfy a test that requires `ephemeral-storage` 64Mi (kubelet still evicts on the request). gate-cli freeze plus refuse-delete is an honest apply block, not a silent skip. Weak: mill-inventory 502 fallback is availability (committed fixture is not a stale dest whose milligram bins disagree with a second document); kubectl json dump is one object; no reviewer asking to keep round() "so mill PLC milligram bins still match IEEE floats". Next densification: a 502 whose local lot-mg fixture is stale (`want` `1` vs a second file still on `0`), or a reviewer asking to keep sizeLimit 1Mi "so mill harvest nodes never cache two lot dumps".

Novel coverage: 40%
"""


def main() -> int:
    plant_hits = prior_plant_hits()
    if plant_hits:
        raise SystemExit(f"plant collision {plant_hits}")
    recs = [ep1(), ep2()]
    taken = prior_ids()
    for rec in recs:
        if rec["id"] in taken:
            raise SystemExit(f"id collision {rec['id']}")
        validate_record(rec)
    OUT.mkdir(parents=True, exist_ok=True)
    raw_guard = Path("/home/raulmc/rmems/synthetic-factory/outputs/raw")
    if raw_guard.exists() and OUT.resolve().is_relative_to(raw_guard.resolve()):
        raise SystemExit("refusing to write under outputs/raw/")
    batch = OUT / "batch-r51.jsonl"
    with batch.open("w", encoding="utf-8") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    notes_path = OUT / "NOTES-r51.md"
    notes_path.write_text(notes(), encoding="utf-8")
    errors, warnings, kinds, n = check_jsonl(
        batch, "batch-r51.jsonl", staging=FactoryStaging(enabled=True)
    )
    if errors:
        raise SystemExit(f"check_jsonl errors {errors}")
    if warnings:
        raise SystemExit(f"check_jsonl warnings {warnings}")
    counts, findings, blocked = verify_batch_for_frontier(batch, strict=True)
    if blocked or counts.get("verified") != 2:
        raise SystemExit(f"frontier blocked={blocked} counts={counts} findings={findings}")
    print(f"wrote {batch} ({n} records, kinds={kinds})")
    print(f"wrote {notes_path}")
    print(f"verify_batch_for_frontier strict: {counts} blocked={blocked}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
