#!/usr/bin/env python3
"""Generate designed ACTF r55 episodes (Q=2). Never writes outputs/raw/."""
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

OUT = Path("/tmp/actf-r55")
GENERATED_AT = "2026-09-02T23:51:00Z"
ROUND = 55
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
ID1 = "act-r55-timedelta-seconds-tenchtd-d4b90e"
ID2 = "act-r55-fsgroup-always-chmod-welsfs-a8f317"
PLANT_TOKENS = ("tenchtd", "tenchfen", "welsfs", "welsfen")


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
    self_batch = (OUT / "batch-r55.jsonl").resolve()
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
    """tenchtd-lots: timedelta.seconds drops mill harvest days from milligram bins."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: TN-550 reports mill milligram bins drift off 90000/86400/3600. Search bin_lots and timedelta as evidence of a .seconds milligram cast."
            ),
            "plan": "1) search bin_lots 2) read lots.py 3) measure timedelta.seconds 4) confirm want bins 5) fix total_seconds 6) regression + PR",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "bin_lots|timedelta|total_seconds|\\.seconds|shift_start",
                    "path": ".",
                },
            },
            "observation": (
                "tenchtd/lots.py:1:from datetime import datetime\n"
                "tenchtd/lots.py:8:def bin_lots(path: str) -> list:\n"
                "tenchtd/lots.py:14:            rec[\"mg\"] = (end - start).seconds\n"
                "tests/test_install.py:14:    assert bin_lots(\"fixtures/lots.ndjson\")[0][\"dest\"] == \"shift-a/lot\"\n"
                "fixtures/lot-mg.json:4:    \"lot.hex\",\n"
                "5 matches"
            ),
            "reflection": "Found bin_lots wrapping timedelta.seconds on mill harvest windows. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: lots.py:11 assigns (end-start).seconds with no total_seconds (step 1). Read the helper as evidence of any milligram-dwell clamp."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "tenchtd/lots.py", "offset": 1, "limit": 18},
            },
            "observation": (
                "1  from datetime import datetime\n"
                "2  import json\n"
                "3\n"
                "4  # Mill milligram bins were copied from a PLC dwell helper.\n"
                "5  # mill dest milligrams are dwell seconds of the mill harvest window.\n"
                "6  def bin_lots(path: str) -> list:\n"
                "7      rows = []\n"
                "8      with open(path) as f:\n"
                "9          for line in f:\n"
                "10             rec = json.loads(line)\n"
                "11             start = datetime.fromisoformat(rec[\"shift_start\"])\n"
                "12             end = datetime.fromisoformat(rec[\"shift_end\"])\n"
                "13             rec[\"mg\"] = (end - start).seconds\n"
                "14             rows.append(rec)\n"
                "15     return rows\n"
            ),
            "reflection": "Learned mill milligrams come from timedelta.seconds. First plan: S3 truncated shift stamps. Next measure 25h/24h/1h .seconds.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: bin_lots stores rec[\"mg\"] from timedelta.seconds (step 2). Measure 25h/24h/1h .seconds as evidence of discarded milligram days."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 -c \"from datetime import timedelta; "
                        "print((timedelta(hours=25)).seconds, (timedelta(hours=24)).seconds, "
                        "(timedelta(hours=1)).seconds, (timedelta(hours=25)).days, "
                        "(timedelta(hours=24)).days)\""
                    )
                },
            },
            "observation": "3600 0 3600 1 1",
            "reflection": "Measured .seconds of 25h/24h/1h as 3600/0/3600. Next confirm the mill want bins still list 90000/86400/3600.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Reflection: timedelta(hours=25).seconds printed 3600 (step 3). Fetch datetime.rst notes via gh as evidence of the seconds vs total_seconds constructor."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/python/cpython/contents/Doc/library/datetime.rst",
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
            "reflection": "GitHub returned 429 with retry-after 5 while fetching datetime docs. Wait, then use the vendored docs/timedelta-seconds.md fixture.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/timedelta-seconds.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/timedelta-seconds.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  timedelta.seconds is 0..86399 and drops .days; 25h is 3600, 24h is 0, 1h is 3600.\n"
                "2  Mill PLC milligram bins are dwell seconds including days; 25h bins to 90000, 24h to 86400, 1h to 3600.\n"
                "3  Using timedelta.days * 86400 still maps 1h lot.hex to 0 and fails a mill dest check.\n"
                "4  Durable: rec[\"mg\"] = int((end - start).total_seconds()).\n"
                "5  Dropping mill dest week36 loses the exact-day row.\n"
                "6  A truncated S3 object is independent of this client timedelta field.\n"
            ),
            "reflection": "Verified the .seconds trap and that days*86400 still bins 1h to 0. Next pull the committed mill mg fixture.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: RFC-style notes say mill mg needs total_seconds (step 5). Get the committed mill mg object as evidence the want set is 90000/86400/3600."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-object",
                        "--bucket",
                        "tenchfen-specs",
                        "--key",
                        "tenchtd/lot-mg.json",
                        "/tmp/tenchtd-inventory.json",
                    ]
                },
            },
            "observation": (
                "download failed: s3.eu-west-1.amazonaws.com/tenchfen-specs\n"
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
                        "{want:.want, hours:.hours, n:.dest_count, path:.path}",
                        "fixtures/lot-mg.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "want": {\n'
                '    "shift-a/lot": 90000,\n'
                '    "week36": 86400,\n'
                '    "lot.hex": 3600\n'
                "  },\n"
                '  "hours": [25, 24, 1],\n'
                '  "n": 3,\n'
                '  "path": "fixtures/lots.ndjson"\n'
                "}"
            ),
            "reflection": "Verified want already lists mill milligram bins 90000/86400/3600 and hours include 25. Next join that with the measured .seconds bins.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: fixture want already lists 90000/86400/3600 (step 7). jq the measured .seconds bins against that spec as evidence whether S3 truncated stamps."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "s",
                        "fixtures/lot-mg.json",
                        '{got:"seconds 3600 0 3600 from 25h 24h 1h",want:$s[0].want,hours:$s[0].hours,n:$s[0].dest_count,path:$s[0].path}',
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "got": "seconds 3600 0 3600 from 25h 24h 1h",\n'
                '  "want": {\n'
                '    "shift-a/lot": 90000,\n'
                '    "week36": 86400,\n'
                '    "lot.hex": 3600\n'
                "  },\n"
                '  "hours": [25, 24, 1],\n'
                '  "n": 3,\n'
                '  "path": "fixtures/lots.ndjson"\n'
                "}"
            ),
            "reflection": (
                "Plan change: mill want bins already list 90000/86400/3600 and got is timedelta.seconds on a committed 3-line ndjson. "
                "Abandon truncated-transit. Switching the edit target to bin_lots so mill harvest windows go through total_seconds."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the truncated-transit plan; .seconds still emits 3600/0/3600 milligram bins (step 8). Edit days*86400 as evidence only whole-day mill mg survive."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "tenchtd/lots.py",
                    "old_string": "            rec[\"mg\"] = (end - start).seconds\n",
                    "new_string": "            rec[\"mg\"] = (end - start).days * 86400\n",
                },
            },
            "observation": "Edited tenchtd/lots.py: bin_lots now multiplies timedelta.days by 86400 so 1h still bins to 0.",
            "reflection": "Wrote a days-only dwell load. Add a pytest that requires mill milligram bins 90000/86400/3600.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: bin_lots now multiplies timedelta.days by 86400 (step 9). Write a pytest as evidence that bin_lots milligram bins match 90000/86400/3600."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_lots.py",
                    "content": (
                        "from tenchtd.lots import bin_lots\n\n"
                        "WANT = {\"shift-a/lot\": 90000, \"week36\": 86400, \"lot.hex\": 3600}\n\n"
                        "def test_bin_lots_mg_is_total_seconds():\n"
                        "    got = {row[\"dest\"]: row[\"mg\"] for row in bin_lots(\"fixtures/lots.ndjson\")}\n"
                        "    assert got == WANT, f\"got={got} want={WANT}\"\n"
                    ),
                },
            },
            "observation": "Wrote tests/test_lots.py (9 lines).",
            "reflection": "Created a mixed-dwell regression that expects lot.hex to stay 3600. Run pytest to reproduce the 0 bin.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Plan: run pytest tests/test_lots.py as evidence whether days*86400 keeps mill dest lot.hex as milligram bin 3600."
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
                "______________ test_bin_lots_mg_is_total_seconds ______________\n"
                "tests/test_lots.py:7: in test_bin_lots_mg_is_total_seconds\n"
                "    assert got == WANT, f\"got={got} want={WANT}\"\n"
                "E   AssertionError: got={'shift-a/lot': 86400, 'week36': 86400, 'lot.hex': 0} "
                "want={'shift-a/lot': 90000, 'week36': 86400, 'lot.hex': 3600}\n"
                "FAILED tests/test_lots.py::test_bin_lots_mg_is_total_seconds - AssertionError: "
                "got={'shift-a/lot': 86400, 'week36': 86400, 'lot.hex': 0} "
                "want={'shift-a/lot': 90000, 'week36': 86400, 'lot.hex': 3600}\n"
                "1 failed in 0.05s"
            ),
            "reflection": "Test failed: days*86400 still bins lot.hex to 0. Re-read bin_lots and switch to total_seconds.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Observation: pytest failed with got lot.hex=0 on days*86400 (step 11). Re-read bin_lots for the dwell evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "tenchtd/lots.py", "offset": 4, "limit": 12},
            },
            "observation": (
                "4  # Mill milligram bins were copied from a PLC dwell helper.\n"
                "5  # mill dest milligrams are dwell seconds of the mill harvest window.\n"
                "6  def bin_lots(path: str) -> list:\n"
                "7      rows = []\n"
                "8      with open(path) as f:\n"
                "9          for line in f:\n"
                "10             rec = json.loads(line)\n"
                "11             start = datetime.fromisoformat(rec[\"shift_start\"])\n"
                "12             end = datetime.fromisoformat(rec[\"shift_end\"])\n"
                "13             rec[\"mg\"] = (end - start).days * 86400\n"
                "14             rows.append(rec)\n"
                "15     return rows\n"
            ),
            "reflection": "Confirmed line 13 still bins mill milligrams from days only. Patch total_seconds.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Reflection: bin_lots must int(total_seconds()) rather than days*86400 (step 12). Patch lots.py to total_seconds as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "tenchtd/lots.py",
                    "old_string": "            rec[\"mg\"] = (end - start).days * 86400\n",
                    "new_string": "            rec[\"mg\"] = int((end - start).total_seconds())\n",
                },
            },
            "observation": "Edited tenchtd/lots.py: bin_lots now int(total_seconds()) so mill milligram 1h bins to 3600.",
            "reflection": "Patched the total_seconds constructor. Re-run pytest; lot.hex should stay 3600.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Observation: bin_lots now int(total_seconds()) (step 13). Re-run pytest tests/test_lots.py as verification evidence."
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
            "reflection": "Verified 6 passed including test_bin_lots_mg_is_total_seconds. Open the TN-550 PR.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: pytest passed 6/6 after the total_seconds patch (step 14). Create the TN-550 PR via gh as evidence of the bin_lots fix."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/tenchfen/tenchtd-lots/pulls",
                    "raw_field": "title=TN-550: total_seconds mill milligram bins so 25h bins to 90000 instead of timedelta.seconds 3600",
                },
            },
            "observation": (
                "{\n"
                '  "number": 551,\n'
                '  "html_url": "https://git.tenchfen.internal/pkg/tenchtd-lots/pull/551",\n'
                '  "state": "open"\n'
                "}"
            ),
            "reflection": "Opened PR 551. bin_lots keeps 25h as 90000 and 1h as 3600. Live mill census follow-up remains against the designed mill host.",
        },
    ]
    return {
        "id": ID1,
        "goal": (
            "TN-550 (tenchtd-lots, Python 3.12 mill lot milligram helper + fixtures/lot-mg.json; pytest): "
            "nightly mill copies print milligram bins 3600/0/3600 while the mill dest names are shift-a/lot, week36, lot.hex "
            "(file fixtures/lots.ndjson, harvest windows 25h/24h/1h). "
            "Find why bin_lots drifts mill PLC milligram bins, add a mixed-dwell regression, and open a PR. Designed plant; not a live mill apply."
        ),
        "steps": steps,
        "outcome": (
            "bin_lots passed mill harvest windows through timedelta.seconds, so week36 printed milligram bin 0 and shift-a/lot printed 3600. "
            "A first patch that used timedelta.days * 86400 still failed "
            "test_bin_lots_mg_is_total_seconds (got lot.hex=0). "
            "bin_lots now int(total_seconds()). Verified by pytest 6 passed "
            "(tests/test_lots.py::test_bin_lots_mg_is_total_seconds). PR 551 opened. "
            "Live mill copies remain a follow-up against the designed mill host."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.40,
            "total_seconds_fix": 0.12,
            "mixed_dwell_lot_test": 0.08,
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
            codebase_type="library / mill lot milligram bins (Python 3.12 datetime.timedelta)",
            bug_class="schema mismatch: timedelta.seconds dropped mill harvest days from mill PLC milligram bins; first fix used days*86400 and kept 1h as 0",
            test_harness="pytest + aws s3api + jq",
            noise_steps={"429": 4, "502": 6},
            noise_recovery_steps={"429": 5, "502": 7},
            plan_change_step=8,
            debug_loop_steps=[9, 10, 11, 12, 13, 14],
            tags=[
                "timedelta",
                "seconds",
                "total_seconds",
                "mill-lots",
                "milligram-bins",
                "mixed-dwell",
            ],
        ),
    }


def ep2() -> dict:
    """welsfs-harvest: fsGroup default Always recursively chowns mill lots PVC."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: WL-72 reports mill harvest pods stuck ContainerCreating while chowning mill lots. Search render_deploy and fsGroup as evidence of Always chmod."
            ),
            "plan": "1) search deploy renderer 2) read render_deploy 3) measure live deploy 4) fix fsGroupChangePolicy 5) regression 6) apply or hand off",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "fsGroup|fsGroupChangePolicy|FSGROUP|OnRootMismatch",
                    "path": ".",
                },
            },
            "observation": (
                "welsfs/deploy.py:5:FSGROUP = 2000\n"
                "welsfs/deploy.py:16:                \"securityContext\": {\"fsGroup\": FSGROUP},\n"
                "deploy/harvest.yaml:18:fsGroup: 2000\n"
                "6 matches"
            ),
            "reflection": "Found fsGroup 2000 with no fsGroupChangePolicy in the renderer. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: deploy.py:5 sets FSGROUP=2000 while harvest mounts mill lots PVC (step 1). Read the renderer as evidence of any mill-gid clamp."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "welsfs/deploy.py", "offset": 1, "limit": 24},
            },
            "observation": (
                "1  # Ported from the v1 mill kiln harvest. fsGroup 2000 starts with the harvest deploy.\n"
                "2  # mill lots PVC is ~18Gi ndjson already gid 2000 and must mount at /lots during the shift.\n"
                "3\n"
                "4  API_VERSION = \"apps/v1\"\n"
                "5  FSGROUP = 2000\n"
                "6\n"
                "7  def render_deploy() -> dict:\n"
                "8      return {\n"
                "9          \"apiVersion\": API_VERSION,\n"
                "10         \"kind\": \"Deployment\",\n"
                "11         \"metadata\": {\"name\": \"welsfs-harvest\"},\n"
                "12         \"spec\": {\n"
                "13             \"selector\": {\"matchLabels\": {\"app\": \"welsfs-harvest\"}},\n"
                "14             \"template\": {\"spec\": {\n"
                "15                 \"securityContext\": {\"fsGroup\": FSGROUP},\n"
                "16                 \"containers\": [{\"name\": \"harvest\", "
                "\"volumeMounts\": [{\"name\": \"lots\", \"mountPath\": \"/lots\"}]}],\n"
                "17                 \"volumes\": [{\"name\": \"lots\", \"persistentVolumeClaim\": "
                "{\"claimName\": \"welsfs-lots\"}}],\n"
                "18             }},\n"
                "19         },\n"
                "20     }\n"
            ),
            "reflection": "Learned fsGroup is 2000 with no fsGroupChangePolicy (default Always). First plan: mill nodes are DiskPressure so kubelet cannot finish chown. Next measure the live Deployment.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: render_deploy emits fsGroup 2000 without fsGroupChangePolicy (step 2). kubectl get the Deployment as evidence of live spec.status."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-welsfen",
                    "namespace": "welsfen",
                    "argv": [
                        "get",
                        "deploy",
                        "welsfs-harvest",
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
                ") occurred attempting to get Deployment.apps/welsfs-harvest"
            ),
            "reflection": "kind apiserver ingress returned 502 before headers. Retry with a longer request timeout and write the object locally.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: kubectl get deploy returned 502 from the kind ingress (step 3). Retry --request-timeout=30s and write /tmp/welsfs-deploy.json as evidence."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-welsfen",
                    "namespace": "welsfen",
                    "argv": [
                        "get",
                        "deploy",
                        "welsfs-harvest",
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
                '  "metadata": {"name": "welsfs-harvest", "namespace": "welsfen"},\n'
                '  "spec": {"template": {"spec": {"securityContext": {"fsGroup": 2000}, '
                '"containers": [{"name": "harvest", "volumeMounts": '
                '[{"name": "lots", "mountPath": "/lots"}]}], '
                '"volumes": [{"name": "lots", "persistentVolumeClaim": '
                '{"claimName": "welsfs-lots"}}]}}},\n'
                '  "status": {"replicas": 1, "readyReplicas": 0, "unavailableReplicas": 1}\n'
                "}\n"
                "wrote /tmp/welsfs-deploy.json"
            ),
            "reflection": "Measured live fsGroup 2000, no fsGroupChangePolicy, readyReplicas 0. Next inspect node DiskPressure so a node-disk plan can be checked.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: live deploy has fsGroup 2000, no fsGroupChangePolicy, readyReplicas 0 (step 4). kubectl get node DiskPressure as evidence whether node disk is the mill miss."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-welsfen",
                    "namespace": "welsfen",
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
                '    {"metadata": {"name": "kind-welsfen-control-plane"}, "status": {"conditions": ['
                '{"type": "Ready", "status": "True"}, {"type": "DiskPressure", "status": "False"}]}},\n'
                '    {"metadata": {"name": "kind-welsfen-worker"}, "status": {"conditions": ['
                '{"type": "Ready", "status": "True"}, {"type": "DiskPressure", "status": "False"}]}},\n'
                '    {"metadata": {"name": "kind-welsfen-worker2"}, "status": {"conditions": ['
                '{"type": "Ready", "status": "True"}, {"type": "DiskPressure", "status": "False"}]}}\n'
                "  ]\n"
                "}\n"
                "nodes Ready=True DiskPressure=False count=3"
            ),
            "reflection": "Found 3 Ready mill nodes with DiskPressure False. This is not a node-disk mill miss. Confirm the fsGroup contract next.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: three mill nodes are Ready without DiskPressure (step 5). Fetch security-context docs via gh as evidence of the mill-lot fsGroup contract."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/kubernetes/website/contents/content/en/docs/tasks/configure-pod-container/security-context.md",
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
            "reflection": "GitHub returned 429 with retry-after 7 while fetching security-context docs. Wait, then use the vendored docs/fsgroup-change-policy.md fixture.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry_after 7 (step 6). Sleep 8s, then read docs/fsgroup-change-policy.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/fsgroup-change-policy.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  fsGroup without fsGroupChangePolicy defaults to Always and recursively chowns mill lots PVC on every attach.\n"
                "2  Dropping fsGroup still fails mill harvest because /lots stays root-owned and runAsNonRoot cannot read mill lots.\n"
                "3  Durable: fsGroup 2000 and fsGroupChangePolicy OnRootMismatch so mill lots already gid 2000 skip chmod.\n"
                "4  Adding mill nodes does not raise readyReplicas while Always chowns 18Gi.\n"
                "5  Deleting the Deployment fail-opens mill harvest coverage.\n"
                "6  Dropping the Deployment is a mill gate regression.\n"
            ),
            "reflection": "Verified mill harvest needs fsGroup 2000 with OnRootMismatch. Next join that with the saved Deployment.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: docs require OnRootMismatch when mill lots PVC is already gid 2000 (step 7). jq spec from the saved deploy as evidence of the live skew."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{fsGroup:.spec.template.spec.securityContext.fsGroup,"
                        "policy:.spec.template.spec.securityContext.fsGroupChangePolicy,"
                        "ready:.status.readyReplicas}",
                        "/tmp/welsfs-deploy.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "fsGroup": 2000,\n'
                '  "policy": null,\n'
                '  "ready": 0\n'
                "}"
            ),
            "reflection": (
                "Plan change: live spec has fsGroup 2000 with no fsGroupChangePolicy while three mill nodes are Ready without DiskPressure. "
                "Abandon adding mill nodes. Switching the edit target to render_deploy so mill harvest gets OnRootMismatch."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the DiskPressure-node plan; fsGroupChangePolicy is missing (step 8). Refuse deleting the Deployment as evidence the object must stay."
            ),
            "tool_call": {
                "name": "refuse",
                "args": {
                    "action": "kubectl delete deploy/welsfs-harvest so a freshly created object picks OnRootMismatch",
                    "policy": "FS-MUTATE-04",
                    "incident": "WL-72",
                },
            },
            "observation": (
                "refused: FS-MUTATE-04 forbids deleting Deployment/welsfs-harvest to skip a fsGroupChangePolicy skew. "
                "Delete would drop in-flight mill harvest lots and can fail-open kiln coverage. "
                "Safe alternative: patch fsGroupChangePolicy and keep replicas 1. found 0 waivers"
            ),
            "reflection": "Denied the delete. Next patch render_deploy; keep the Deployment object.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: delete is refused; edit target is FSGROUP (step 9). First patch: drop FSGROUP as evidence mill chown may skip."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "welsfs/deploy.py",
                    "old_string": "                \"securityContext\": {\"fsGroup\": FSGROUP},\n",
                    "new_string": "                \"securityContext\": {},\n",
                },
            },
            "observation": "Edited welsfs/deploy.py: securityContext is now empty so mill lots skip kubelet chown.",
            "reflection": "Wrote an empty securityContext. Add a pytest that requires fsGroup 2000 and OnRootMismatch.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: renderer now omits fsGroup (step 10). Write a pytest as evidence that mill harvest uses fsGroup 2000 with OnRootMismatch."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_deploy.py",
                    "content": (
                        "from welsfs.deploy import render_deploy\n\n"
                        "def test_deploy_skips_mill_lots_chown():\n"
                        "    spec = render_deploy()[\"spec\"][\"template\"][\"spec\"]\n"
                        "    sc = spec.get(\"securityContext\") or {}\n"
                        "    assert sc.get(\"fsGroup\") == 2000, f\"got fsGroup={sc.get('fsGroup')}\"\n"
                        "    assert sc.get(\"fsGroupChangePolicy\") == \"OnRootMismatch\", "
                        "f\"got fsGroupChangePolicy={sc.get('fsGroupChangePolicy')}\"\n"
                    ),
                },
            },
            "observation": "Wrote tests/test_deploy.py (10 lines).",
            "reflection": "Created a fsGroup / OnRootMismatch regression. Run pytest to reproduce the missing gid.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Plan: run pytest tests/test_deploy.py as evidence whether dropping fsGroup satisfies the mill lot gid contract."
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
                "______________ test_deploy_skips_mill_lots_chown ______________\n"
                "tests/test_deploy.py:6: in test_deploy_skips_mill_lots_chown\n"
                "    assert sc.get(\"fsGroup\") == 2000, "
                "f\"got fsGroup={sc.get('fsGroup')}\"\n"
                "E   AssertionError: got fsGroup=None\n"
                "E   assert None == 2000\n"
                "FAILED tests/test_deploy.py::test_deploy_skips_mill_lots_chown - AssertionError: got fsGroup=None\n"
                "1 failed in 0.04s"
            ),
            "reflection": "Test failed: fsGroup is missing. Re-read render_deploy and set OnRootMismatch while keeping fsGroup 2000.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: pytest failed with got fsGroup=None (step 12). Re-read render_deploy for the FSGROUP evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "welsfs/deploy.py", "offset": 4, "limit": 16},
            },
            "observation": (
                "4  API_VERSION = \"apps/v1\"\n"
                "5  FSGROUP = 2000\n"
                "6\n"
                "7  def render_deploy() -> dict:\n"
                "8      return {\n"
                "9          \"apiVersion\": API_VERSION,\n"
                "10         \"kind\": \"Deployment\",\n"
                "11         \"metadata\": {\"name\": \"welsfs-harvest\"},\n"
                "12         \"spec\": {\n"
                "13             \"selector\": {\"matchLabels\": {\"app\": \"welsfs-harvest\"}},\n"
                "14             \"template\": {\"spec\": {\n"
                "15                 \"securityContext\": {},\n"
                "16                 \"containers\": [{\"name\": \"harvest\"}],\n"
                "17                 \"volumes\": [{\"name\": \"lots\", \"persistentVolumeClaim\": "
                "{\"claimName\": \"welsfs-lots\"}}],\n"
                "18             }},\n"
                "19         },\n"
                "20     }\n"
            ),
            "reflection": "Confirmed line 15 still drops fsGroup against a mill lot mount that needs gid 2000. Patch OnRootMismatch and keep FSGROUP.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: helper must emit fsGroup 2000 and fsGroupChangePolicy OnRootMismatch (step 13). Patch render_deploy spec as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "welsfs/deploy.py",
                    "old_string": "                \"securityContext\": {},\n",
                    "new_string": (
                        "                \"securityContext\": {\"fsGroup\": FSGROUP, "
                        "\"fsGroupChangePolicy\": \"OnRootMismatch\"},\n"
                    ),
                },
            },
            "observation": "Edited welsfs/deploy.py: fsGroup stays 2000 and fsGroupChangePolicy is OnRootMismatch.",
            "reflection": "Patched OnRootMismatch and kept fsGroup 2000. Re-run pytest; mill lots should skip recursive chmod.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: helper now emits fsGroup 2000 with OnRootMismatch (step 14). Re-run pytest tests/test_deploy.py as verification evidence."
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
            "reflection": "Verified 5 passed including test_deploy_skips_mill_lots_chown. Check gate-cli before applying the Deployment.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: pytest passed 5/5 after the fsGroupChangePolicy patch (step 15). Run gate-cli check apply as evidence whether prod deploy mutation is allowed."
            ),
            "tool_call": {
                "name": "gate-cli",
                "args": {
                    "argv": [
                        "check",
                        "apply",
                        "--change",
                        "welsfs-fsgroup-policy",
                        "--resource",
                        "deploy/welsfs-harvest",
                    ]
                },
            },
            "observation": (
                "gate-cli check apply --change welsfs-fsgroup-policy\n"
                "status: REJECT\n"
                "policy: prod-batch-freeze\n"
                "ticket: WL-60\n"
                "until: 2026-09-16T00:00:00Z\n"
                "evidence: change mutates Deployment/welsfs-harvest (welsfs-harvest fsGroupChangePolicy)\n"
                "found 0 waivers"
            ),
            "reflection": "Measured REJECT under WL-60 freeze through 2026-09-16. Do not kubectl apply. Open a handoff issue attaching the fsGroupChangePolicy fix.",
        },
        {
            "n": 17,
            "decision_basis": db(
                "Observation: gate-cli REJECT'd the deploy apply under freeze WL-60 (step 16). Open a handoff issue as evidence the live spec still lacks OnRootMismatch."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "title": "WL-83: apply welsfs fsGroupChangePolicy after WL-60 freeze (blocks WL-72 close)",
                    "body": "render_deploy now emits fsGroup 2000 and fsGroupChangePolicy OnRootMismatch; pytest 5 passed. Live deploy still omits fsGroupChangePolicy. gate-cli freeze WL-60 until 2026-09-16. Do not kubectl delete the Deployment.",
                },
            },
            "observation": "https://git.welsfen.internal/k8s/welsfs-harvest/issues/83",
            "reflection": "Opened WL-83. Renderer is green; prod apply remains blocked. Handoff, not close.",
        },
    ]
    return {
        "id": ID2,
        "goal": (
            "WL-72 (welsfs-harvest, Python 3.12 Deployment renderer + kind welsfen; pytest + kubectl): "
            "mill harvest pods stay ContainerCreating while kubelet recursively chowns mill lots because fsGroup is 2000, "
            "fsGroupChangePolicy is omitted (Always), and readyReplicas is 0. "
            "Find why fsGroup blocks mill lot mounts, fix the renderer, and apply or hand off. Designed plant; not a live cluster trace."
        ),
        "steps": steps,
        "outcome": (
            "render_deploy emitted fsGroup 2000 with no fsGroupChangePolicy, so mill harvest readyReplicas stayed 0. "
            "A first patch that dropped fsGroup still failed test_deploy_skips_mill_lots_chown (got fsGroup=None). "
            "The helper now emits fsGroup 2000 and fsGroupChangePolicy OnRootMismatch; pytest 5 passed. "
            "Applying Deployment/welsfs-harvest remains blocked by gate-cli freeze WL-60; live spec still omits fsGroupChangePolicy. "
            "WL-83 opened. Overall: incomplete; prod apply unresolved."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "fsgroup_policy_fix": 0.10,
            "mill_lots_gid_test": 0.08,
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
            bug_class="schema mismatch: omitted fsGroupChangePolicy defaulted Always and recursively chowned mill lots PVC; first fix dropped fsGroup and left mill dest root-owned",
            test_harness="pytest + kubectl + gate-cli",
            noise_steps={"502": 3, "429": 6},
            noise_recovery_steps={"502": 4, "429": 7},
            plan_change_step=8,
            debug_loop_steps=[10, 11, 12, 13, 14, 15],
            tags=[
                "fsGroup",
                "fsGroupChangePolicy",
                "OnRootMismatch",
                "ContainerCreating",
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
    return """# ACTF r55 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r55-timedelta-seconds-tenchtd-d4b90e`, `act-r55-fsgroup-always-chmod-welsfs-a8f317` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`kubectl`/`gate-cli`/`aws`/`jq`/`refuse`). meta.round=55 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Never wrote outputs/raw/. Distinct from staged r10-r52 and in-progress r53 (r52 ciscoqsl parse_qsl blank dests / alewifeskew topologySpread ScheduleAnyway, not timedelta.seconds or fsGroup Always; r53 graylingqsl parse_qsl / ciscohpa minReplicas 0; r51 chubround builtin round half-even / darterdisk emptyDir sizeLimit; r44 ruddtime time.mktime local / avocetready tcp readiness, not timedelta.seconds dwell; r26 unix millis; r36 skuasec runAsNonRoot uid0, not fsGroupChangePolicy; r35 yarrowrofs readOnlyRootFilesystem /tmp; r47 ruffeframe itertools.batched / tautogsts StatefulSet Parallel; r48 smelttmpl string.Template $lot_id / perchcron CronJob Forbid; r49 piketab csv.Sniffer comma / gobyenv enableServiceLinks; r50 sturgeonxml ElementTree default xmlns / kittiwakejob Job ttlSecondsAfterFinished 0). r52 completed during this write (ciscoqsl/alewifeskew) with no plant or ID collision. Invented repos `git.tenchfen.internal/pkg/tenchtd-lots.git` and `git.welsfen.internal/k8s/welsfs-harvest.git`. Beads create failed (Dolt events id default); Linear RM-793 remains the rights tracker.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r55-timedelta-seconds-tenchtd-d4b90e | Python 3.12 mill lot milligram helper + lot-mg fixtures / pytest + aws s3api + jq | schema mismatch: `timedelta.seconds` dropped mill harvest days from mill PLC milligram bins; first fix used `days*86400` and kept 1h as 0 | success; 6/6; PR 551 | 0.58 |
| act-r55-fsgroup-always-chmod-welsfs-a8f317 | Python 3.12 Deployment renderer / pytest + kubectl + gate-cli | schema mismatch: omitted `fsGroupChangePolicy` defaulted Always and recursively chowned mill lots PVC; first fix dropped `fsGroup` | incomplete HIL/prod apply; WL-83; freeze WL-60 | 0.28 |

## Step counts, noise, plan change
- act-r55-timedelta-seconds-tenchtd-d4b90e: 15 steps. 429 at step 4 (`gh api` cpython datetime.rst, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/timedelta-seconds.md`). 502 at step 6 (`aws s3api get-object` tenchfen-specs lot-mg ELB) -> recovery step 7 (`jq` committed `fixtures/lot-mg.json`). Plan change at step 8: jq join shows want already 90000/86400/3600 and got is timedelta.seconds on a committed 3-line ndjson; abandon truncated-transit. Debug loop: 9 edit `days*86400` -> 10 write mixed-dwell pytest -> 11 FAIL got lot.hex=0 -> 12 re-read bin_lots -> 13 total_seconds patch -> 14 6 passed.
- act-r55-fsgroup-always-chmod-welsfs-a8f317: 17 steps. 502 at step 3 (`kubectl get deploy` kind ingress) -> recovery step 4 (`--request-timeout=30s` writes /tmp/welsfs-deploy.json). 429 at step 6 (`gh api` kubernetes/website security-context.md, retry-after 7) -> recovery step 7 (read vendored `docs/fsgroup-change-policy.md`). Plan change at step 8: jq fsGroup 2000 with policy null while 3 mill nodes are Ready without DiskPressure; abandon adding mill nodes. Debug loop: 10 edit drop fsGroup -> 11 write OnRootMismatch pytest -> 12 FAIL got fsGroup=None -> 13 re-read helper -> 14 fsGroup 2000 + OnRootMismatch patch -> 15 5 passed. `refuse` at step 9 blocks `kubectl delete deploy`. gate-cli REJECT at 16; WL-83 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. timedelta-seconds: 0.40+0.12+0.08-0.02=0.58. fsgroup-always-chmod: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: `timedelta.seconds` on mill harvest windows is a real stdlib footgun (0..86399, days discarded); `timedelta.days * 86400` is the equally tempting milligram-PLC wrong fix and the mixed-dwell test names the contract (`lot.hex` stays `3600`, not `0`). omitted `fsGroupChangePolicy` defaulting Always recursively chowns an 18Gi mill lots PVC already gid 2000; dropping `fsGroup` still cannot satisfy a test that requires gid 2000 plus `OnRootMismatch` (runAsNonRoot cannot read root-owned mill lots). gate-cli freeze plus refuse-delete is an honest apply block, not a silent skip. Weak: mill-inventory 502 fallback is availability (committed fixture is not a stale dest whose milligram bins disagree with a second document); kubectl json dump is one object; no reviewer asking to keep timedelta.seconds "so mill PLC milligram bins still match intra-day dwell". Next densification: a 502 whose local lot-mg fixture is stale (`want` `3600` vs a second file still on `0`), or a reviewer asking to keep Always "so mill harvest nodes re-chown after a mill lot dump from another mill gid".

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
    batch = OUT / "batch-r55.jsonl"
    with batch.open("w", encoding="utf-8") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    notes_path = OUT / "NOTES-r55.md"
    notes_path.write_text(notes(), encoding="utf-8")
    errors, warnings, kinds, n = check_jsonl(
        batch, "batch-r55.jsonl", staging=FactoryStaging(enabled=True)
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
