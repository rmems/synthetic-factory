#!/usr/bin/env python3
"""Generate designed ACTF r44 episodes (Q=2). Never writes outputs/raw/."""
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

OUT = Path("/tmp/actf-r44")
GENERATED_AT = "2026-09-03T00:22:00Z"
ROUND = 44
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
ID1 = "act-r44-mktime-local-ruddtime-b4e81a"
ID2 = "act-r44-readiness-tcp-avocetready-c7d214"
PLANT_TOKENS = ("ruddtime", "ruddfen", "avocetready", "avocetfen")


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
    self_batch = (OUT / "batch-r44.jsonl").resolve()
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


EPOCH_BEFORE = '''from datetime import datetime
import time


def lot_epoch(ts: str) -> int:
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
    return int(time.mktime(dt.timetuple()))
'''

EPOCH_MINUS5 = '''from datetime import datetime
import time


def lot_epoch(ts: str) -> int:
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
    return int(time.mktime(dt.timetuple())) - 18000
'''

EPOCH_TIMEGM = '''from datetime import datetime
import calendar


def lot_epoch(ts: str) -> int:
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
    return calendar.timegm(dt.timetuple())
'''

EPOCH_TEST = '''from ruddtime.lotepoch import lot_epoch

ROWS = [
    {"lot": "dace.json", "ts": "2026-09-02T00:00:00"},
    {"lot": "mid-rill.json", "ts": "2026-01-14T00:00:00"},
    {"lot": "eddy.JSON", "ts": "2026-09-02T00:00:00"},
]
WANT = {
    "dace.json": 1788307200,
    "mid-rill.json": 1768348800,
    "eddy.JSON": 1788307200,
}


def test_lot_epoch_is_utc_not_local():
    got = {row["lot"]: lot_epoch(row["ts"]) for row in ROWS}
    assert got == WANT, f"got={got} want={WANT}"
'''

READY_BEFORE = '''# Ported from a mill harvest chart. tcpSocket treated an open port as Ready.
API_VERSION = "apps/v1"
KIND = "Deployment"
LIVENESS_PATH = "/healthz"
READINESS = {"tcpSocket": {"port": 8443}}


def render_deploy() -> dict:
    return {
        "apiVersion": API_VERSION,
        "kind": KIND,
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "avocetready-harvest",
                            "livenessProbe": {
                                "httpGet": {"path": LIVENESS_PATH, "port": 8443},
                                "periodSeconds": 10,
                            },
                            "readinessProbe": dict(READINESS),
                        }
                    ]
                }
            }
        },
    }
'''

READY_HEALTHZ = '''# Ported from a mill harvest chart. tcpSocket treated an open port as Ready.
API_VERSION = "apps/v1"
KIND = "Deployment"
LIVENESS_PATH = "/healthz"
READINESS = {"httpGet": {"path": "/healthz", "port": 8443}}


def render_deploy() -> dict:
    return {
        "apiVersion": API_VERSION,
        "kind": KIND,
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "avocetready-harvest",
                            "livenessProbe": {
                                "httpGet": {"path": LIVENESS_PATH, "port": 8443},
                                "periodSeconds": 10,
                            },
                            "readinessProbe": dict(READINESS),
                        }
                    ]
                }
            }
        },
    }
'''

READY_READYZ = '''# Ported from a mill harvest chart. tcpSocket treated an open port as Ready.
API_VERSION = "apps/v1"
KIND = "Deployment"
LIVENESS_PATH = "/healthz"
READINESS = {"httpGet": {"path": "/readyz", "port": 8443}}


def render_deploy() -> dict:
    return {
        "apiVersion": API_VERSION,
        "kind": KIND,
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "avocetready-harvest",
                            "livenessProbe": {
                                "httpGet": {"path": LIVENESS_PATH, "port": 8443},
                                "periodSeconds": 10,
                            },
                            "readinessProbe": dict(READINESS),
                        }
                    ]
                }
            }
        },
    }
'''

READY_TEST = '''from avocetready.harvest import render_deploy


def test_readiness_is_readyz_not_tcp():
    spec = render_deploy()["spec"]["template"]["spec"]["containers"][0]
    ready = spec["readinessProbe"]
    got = ready.get("httpGet", {}).get("path")
    assert got == "/readyz", f"got path={got} probe={ready}"
    assert "tcpSocket" not in ready
    assert spec["livenessProbe"]["httpGet"]["path"] == "/healthz"
'''


def ep1() -> dict:
    """ruddtime-lots: time.mktime treats mill UTC stamps as local Chicago time."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: RT-241 reports mill lot epochs are five hours high versus UTC dest want. Search lot_epoch and mktime as evidence of a local-time fold."
            ),
            "plan": "1) search lot_epoch 2) read lotepoch.py 3) measure mktime 4) confirm UTC want 5) fix timegm 6) regression + PR",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "lot_epoch|mktime|timegm|strptime",
                    "path": ".",
                },
            },
            "observation": (
                "ruddtime/lotepoch.py:1:from datetime import datetime\n"
                "ruddtime/lotepoch.py:6:def lot_epoch(ts: str) -> int:\n"
                "ruddtime/lotepoch.py:8:    return int(time.mktime(dt.timetuple()))\n"
                "tests/test_install.py:11:    assert lot_epoch(\"2026-09-02T00:00:00\") > 0\n"
                "5 matches"
            ),
            "reflection": "Found lot_epoch wrapping time.mktime with no UTC clamp. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: lotepoch.py:9 uses time.mktime on naive mill stamps (step 1). Read the helper as evidence of any UTC clamp before mktime."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "ruddtime/lotepoch.py", "offset": 1, "limit": 16},
            },
            "observation": EPOCH_BEFORE,
            "reflection": "Learned mktime walks naive mill stamps as local time. First plan: mill S3 prefix missing. Next measure Chicago vs UTC.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: lot_epoch mktime's naive mill timestamps (step 2). Measure Chicago local vs UTC epochs on Sep vs Jan mill lots as evidence of DST skew."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "TZ=America/Chicago python3 -c \"from datetime import datetime; "
                        "import time, calendar; "
                        "rows=['2026-09-02T00:00:00','2026-01-14T00:00:00',"
                        "'2026-09-02T00:00:00']; "
                        "fmt='%Y-%m-%dT%H:%M:%S'; "
                        "print([(ts, int(time.mktime(datetime.strptime(ts, fmt).timetuple())), "
                        "calendar.timegm(datetime.strptime(ts, fmt).timetuple())) for ts in rows])\""
                    )
                },
            },
            "observation": (
                "[('2026-09-02T00:00:00', 1788325200, 1788307200), "
                "('2026-01-14T00:00:00', 1768370400, 1768348800), "
                "('2026-09-02T00:00:00', 1788325200, 1788307200)]"
            ),
            "reflection": "Measured Chicago mktime 18000 high in September and 21600 high in January. Next confirm the mill UTC want epochs.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Reflection: mktime treated mill UTC stamps as Chicago local (step 3). Fetch time.mktime notes via gh as evidence of the local-naive contract."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/python/cpython/contents/Doc/library/time.rst",
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
            "reflection": "GitHub returned a rate-limit with retry-after 5 while fetching mktime docs. Wait, then use the vendored docs/mktime-local.md fixture.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/mktime-local.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/mktime-local.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  time.mktime interprets naive struct_time as the host local zone; it is not UTC.\n"
                "2  Mill stamps 2026-09-02T00:00:00 mean UTC midnight, not Chicago midnight.\n"
                "3  TZ=America/Chicago mktime is 1788325200 in September (CDT, plus 18000) and 1768370400 in January (CST, plus 21600).\n"
                "4  Subtracting 18000 still leaves January mill lots 3600 high versus UTC want.\n"
                "5  Durable: calendar.timegm(dt.timetuple()). A missing mill prefix is independent of this client fold.\n"
            ),
            "reflection": "Verified naive mktime is local and that a hardcoded 18000 offset still splits January mill lots. Next pull the committed mill epoch fixture.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: RFC-style notes say mktime is local for naive stamps (step 5). Get the committed mill epoch inventory as evidence the want set is UTC."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-object",
                        "--bucket",
                        "ruddfen-specs",
                        "--key",
                        "ruddtime/lot-epochs.json",
                        "/tmp/ruddtime-inventory.json",
                    ]
                },
            },
            "observation": (
                "download failed: s3.eu-west-1.amazonaws.com/ruddfen-specs\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "server: awselb/2.0\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection failure"
            ),
            "reflection": "Mill inventory get-object hit a bad gateway on the ELB before headers. Retry against the committed fixtures/lot-epochs.json instead of the edge.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: mill inventory get-object returned 502 from the ELB (step 6). jq fixtures/lot-epochs.json want and rows as local-spec evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{want:.want, n:.key_count, lots:(.want|keys)}",
                        "fixtures/lot-epochs.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "want": {"dace.json": 1788307200, '
                '"mid-rill.json": 1768348800, "eddy.JSON": 1788307200},\n'
                '  "n": 3,\n'
                '  "lots": ["dace.json", "eddy.JSON", "mid-rill.json"]\n'
                "}"
            ),
            "reflection": "Verified want already lists UTC mill epochs. Next join that with the measured Chicago mktime values.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: fixture want already lists UTC mill epochs (step 7). jq the measured mktime epochs against that spec as evidence whether folds are wrong."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "s",
                        "fixtures/lot-epochs.json",
                        "{got:{\"dace.json\":1788325200,\"mid-rill.json\":1768370400,"
                        "\"eddy.JSON\":1788325200},want:$s[0].want,n:$s[0].key_count}",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "got": {"dace.json": 1788325200, "mid-rill.json": 1768370400, '
                '"eddy.JSON": 1788325200},\n'
                '  "want": {"dace.json": 1788307200, "mid-rill.json": 1768348800, '
                '"eddy.JSON": 1788307200},\n'
                '  "n": 3\n'
                "}"
            ),
            "reflection": (
                "Plan change: mill want inventory already lists UTC epochs and got is Chicago-local mktime. "
                "Abandon remounting the mill S3 prefix. Switching the edit target to lot_epoch so naive stamps fold as UTC."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the missing-prefix plan; mktime kept Chicago-local mill epochs (step 8). Edit subtract-18000 as evidence CDT mill lots cluster."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "ruddtime/lotepoch.py",
                    "old_string": EPOCH_BEFORE.strip(),
                    "new_string": EPOCH_MINUS5.strip(),
                },
            },
            "observation": "Edited ruddtime/lotepoch.py: lot_epoch now subtracts 18000 after mktime so September CDT mill lots land on UTC midnight.",
            "reflection": "Wrote a hardcoded CDT offset. Add a pytest that requires January CST mill lots to match UTC want too.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: lot_epoch now subtracts 18000 after mktime (step 9). Write a pytest as evidence that mill Jan CST lots still match UTC want."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_epoch.py",
                    "content": EPOCH_TEST,
                },
            },
            "observation": "Wrote tests/test_epoch.py (22 lines).",
            "reflection": "Created a mixed-DST regression that expects UTC mill epochs. Run pytest to reproduce the January CST miss.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Plan: run pytest tests/test_epoch.py as evidence whether subtracting 18000 maps mill Jan CST lots onto UTC want."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "TZ=America/Chicago pytest tests/test_epoch.py -q --tb=short 2>&1 | tail -n 20"
                },
            },
            "observation": (
                "F\n"
                "=================================== FAILURES ===================================\n"
                "______ test_lot_epoch_is_utc_not_local ______\n"
                "tests/test_epoch.py:20: in test_lot_epoch_is_utc_not_local\n"
                "    assert got == WANT, f\"got={got} want={WANT}\"\n"
                "E   AssertionError: got={'dace.json': 1788307200, 'eddy.JSON': 1788307200, "
                "'mid-rill.json': 1768352400} want={'dace.json': 1788307200, "
                "'eddy.JSON': 1788307200, 'mid-rill.json': 1768348800}\n"
                "FAILED tests/test_epoch.py::test_lot_epoch_is_utc_not_local - AssertionError: got mid-rill.json 1768352400\n"
                "1 failed in 0.05s"
            ),
            "reflection": "Test failed: subtract-18000 still left January mill lots 3600 high. Re-read lot_epoch and switch to calendar.timegm.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Observation: pytest failed with got mid-rill.json=1768352400 want 1768348800 (step 11). Re-read lot_epoch for the subtract-18000 evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "ruddtime/lotepoch.py", "offset": 1, "limit": 16},
            },
            "observation": EPOCH_MINUS5,
            "reflection": "Confirmed line 8 still subtracts 18000 so mill January CST lots stay high. Patch calendar.timegm(dt.timetuple()).",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Reflection: lot_epoch must use calendar.timegm rather than mktime-18000 (step 12). Patch lotepoch.py to timegm as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "ruddtime/lotepoch.py",
                    "old_string": EPOCH_MINUS5.strip(),
                    "new_string": EPOCH_TIMEGM.strip(),
                },
            },
            "observation": "Edited ruddtime/lotepoch.py: lot_epoch now uses calendar.timegm so naive mill stamps fold as UTC.",
            "reflection": "Patched the epoch fold. Re-run pytest; September and January mill lots should both match UTC want.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Observation: lot_epoch now uses calendar.timegm (step 13). Re-run pytest tests/test_epoch.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "TZ=America/Chicago pytest tests/test_epoch.py tests/test_install.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                "......\n"
                "6 passed in 0.08s"
            ),
            "reflection": "Verified 6 passed including test_lot_epoch_is_utc_not_local. Open the RT-241 PR.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: pytest passed 6/6 after the timegm patch (step 14). Create the RT-241 PR via gh as evidence of the lot_epoch fix."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/ruddfen/ruddtime-lots/pulls",
                    "raw_field": "title=RT-241: fold mill UTC stamps with calendar.timegm so Chicago DST cannot skew lot epochs",
                },
            },
            "observation": (
                "{\n"
                '  "number": 441,\n'
                '  "html_url": "https://git.ruddfen.internal/pkg/ruddtime-lots/pull/441",\n'
                '  "state": "open"\n'
                "}"
            ),
            "reflection": "Opened PR 441. lot_epoch matches UTC mill epochs. Live mill catalog follow-up remains against the designed mill host.",
        },
    ]
    return {
        "id": ID1,
        "goal": (
            "RT-241 (ruddtime-lots, Python 3.12 mill lot epoch helper + fixtures/lot-epochs.json; pytest): "
            "nightly mill kiln catalog stores dace.json five hours high versus UTC dest want while January lots drift by six. "
            "Find why lot_epoch keeps local mktime folds, add a mixed-DST regression, and open a PR. Designed plant; not a live mill apply."
        ),
        "steps": steps,
        "outcome": (
            "lot_epoch passed mill UTC stamps through time.mktime, so naive Chicago-local epochs put dace.json five hours high. "
            "A first patch that subtracted 18000 still failed test_lot_epoch_is_utc_not_local (got mid-rill.json=1768352400). "
            "lot_epoch now uses calendar.timegm. Verified by pytest 6 passed "
            "(tests/test_epoch.py::test_lot_epoch_is_utc_not_local). PR 441 opened. "
            "Live mill catalog copies remain a follow-up against the designed mill host."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.40,
            "mktime_utc_fix": 0.12,
            "mixed_dst_epoch_test": 0.08,
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
            codebase_type="library / mill lot epoch (Python 3.12 time.mktime)",
            bug_class="schema mismatch: time.mktime treats mill UTC stamps as local; first fix subtracted 18000",
            test_harness="pytest + aws s3api + jq",
            noise_steps={"429": 4, "502": 6},
            noise_recovery_steps={"429": 5, "502": 7},
            plan_change_step=8,
            debug_loop_steps=[9, 10, 11, 12, 13, 14],
            tags=[
                "time.mktime",
                "calendar.timegm",
                "naive-datetime",
                "mill-lot-epoch",
                "dst-offset",
                "chicago-local",
            ],
        ),
    }


def ep2() -> dict:
    """avocetready-harvest: readinessProbe tcpSocket marks mill harvest Ready during lot load."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: AV-72 reports mill harvest pods Ready while lots still load. Search READINESS and tcpSocket as evidence of a silent Ready."
            ),
            "plan": "1) search harvest renderer 2) read render_deploy 3) measure live deploy 4) fix /readyz 5) regression 6) apply or hand off",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "READINESS|tcpSocket|readyz|readinessProbe",
                    "path": ".",
                },
            },
            "observation": (
                "avocetready/harvest.py:5:READINESS = {\"tcpSocket\": {\"port\": 8443}}\n"
                "avocetready/harvest.py:22:                            \"readinessProbe\": dict(READINESS),\n"
                "deploy/harvest-deploy.yaml:31:readinessProbe:\n"
                "deploy/harvest-deploy.yaml:32:  tcpSocket:\n"
                "6 matches"
            ),
            "reflection": "Found READINESS filled with mill harvest tcpSocket on a Deployment. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: harvest.py:5 sets READINESS tcpSocket port 8443 while mill lots still load (step 1). Read the renderer as evidence of any readyz clamp."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "avocetready/harvest.py", "offset": 1, "limit": 40},
            },
            "observation": READY_BEFORE,
            "reflection": "Learned there is no /readyz clamp. First plan: mill Deployment missing. Next measure the live object.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: render_deploy emits readinessProbe tcpSocket 8443 (step 2). kubectl get the Deployment as evidence of live liveness vs readiness."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-avocetfen",
                    "namespace": "avocetfen",
                    "argv": [
                        "get",
                        "deploy",
                        "avocetready-harvest",
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
                ") occurred attempting to get Deployment.apps/avocetready-harvest"
            ),
            "reflection": "kind apiserver ingress returned a bad gateway before headers. Retry with a longer request timeout and write the object locally.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: kubectl get deploy returned 502 from the kind ingress (step 3). Retry --request-timeout=30s and write /tmp/avocetready-deploy.json as evidence."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-avocetfen",
                    "namespace": "avocetfen",
                    "argv": [
                        "get",
                        "deploy",
                        "avocetready-harvest",
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
                '  "metadata": {"name": "avocetready-harvest", "namespace": "avocetfen"},\n'
                '  "spec": {\n'
                '    "template": {"spec": {"containers": [{\n'
                '      "name": "avocetready-harvest",\n'
                '      "livenessProbe": {"httpGet": {"path": "/healthz", "port": 8443}},\n'
                '      "readinessProbe": {"tcpSocket": {"port": 8443}}\n'
                "    }]}}\n"
                "  }\n"
                "}\n"
                "wrote /tmp/avocetready-deploy.json"
            ),
            "reflection": "Measured live liveness /healthz with readiness tcpSocket 8443. Next inspect mill harvest pod Ready status.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: live readiness is tcpSocket 8443 (step 4). kubectl get pods as evidence whether mill harvest is Ready during lot load."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-avocetfen",
                    "namespace": "avocetfen",
                    "argv": [
                        "get",
                        "pods",
                        "-l",
                        "app=avocetready-harvest",
                        "-o",
                        "json",
                    ],
                },
            },
            "observation": (
                "{\n"
                '  "items": [{\n'
                '    "metadata": {"name": "avocetready-harvest-7b9c"},\n'
                '    "status": {"phase": "Running", "containerStatuses": [{\n'
                '      "ready": true, "started": true, "restartCount": 0\n'
                "    }]}\n"
                "  }]\n"
                "}\n"
                "found mill harvest Ready 1/1 while logs still say loading lots"
            ),
            "reflection": "Found mill harvest Ready while lots still load because tcpSocket sees port 8443. This is not a missing Deployment. Confirm the readiness contract next.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: pods are Ready 1/1 while mill lots still load (step 5). Fetch Pod readinessProbe docs via gh as evidence of the tcpSocket contract."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/kubernetes/website/contents/content/en/docs/concepts/workloads/pods/pod-lifecycle.md",
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
            "reflection": "GitHub returned a rate-limit with retry-after 7 while fetching Pod lifecycle docs. Wait, then use the vendored docs/readiness-tcp.md fixture.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry_after 7 (step 6). Sleep 8s, then read docs/readiness-tcp.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/readiness-tcp.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  readinessProbe.tcpSocket succeeds as soon as the mill harvest port accepts TCP.\n"
                "2  mill harvest listens on 8443 during lot load; tcpSocket marks Ready before /readyz.\n"
                "3  Copying liveness /healthz still reports Ready while lots load; /healthz is process-up not mill-ready.\n"
                "4  Durable: render_deploy must readinessProbe httpGet /readyz and keep liveness /healthz.\n"
                "5  Recreating the Deployment is not required and drops in-flight mill harvest Ready.\n"
                "6  Kind does not rewrite readinessProbe; the renderer must.\n"
            ),
            "reflection": "Verified tcpSocket marks mill harvest Ready too early. Next join that with the saved Deployment.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: docs require readiness httpGet /readyz not tcpSocket (step 7). jq spec from the saved deploy as evidence of the live skew."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{ready:.spec.template.spec.containers[0].readinessProbe,"
                        "live:.spec.template.spec.containers[0].livenessProbe.httpGet.path,"
                        "app:.spec.template.spec.containers[0].name}",
                        "/tmp/avocetready-deploy.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "ready": {"tcpSocket": {"port": 8443}},\n'
                '  "live": "/healthz",\n'
                '  "app": "avocetready-harvest"\n'
                "}"
            ),
            "reflection": (
                "Plan change: live spec already has a Deployment whose readinessProbe is mill tcpSocket 8443. "
                "Abandon adding mill nodes. Switching the edit target to render_deploy so readiness is httpGet /readyz."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the missing-probe plan; readiness is mill tcpSocket (step 8). Refuse deleting the Deployment as evidence the object must stay."
            ),
            "tool_call": {
                "name": "refuse",
                "args": {
                    "action": "kubectl delete deploy/avocetready-harvest so a freshly created object picks /readyz",
                    "policy": "READY-MUTATE-04",
                    "incident": "AV-72",
                },
            },
            "observation": (
                "refused: READY-MUTATE-04 forbids deleting Deployment/avocetready-harvest to skip a readinessProbe skew. "
                "Delete would drop in-flight mill harvest Ready endpoints and can fail-open kiln traffic. "
                "Safe alternative: patch readinessProbe to httpGet /readyz and keep liveness /healthz. found 0 waivers"
            ),
            "reflection": "Denied the delete. Next patch render_deploy; keep the Deployment object.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: delete is refused; edit target is READINESS (step 9). First patch: copy liveness /healthz as evidence mill harvest will wait."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "avocetready/harvest.py",
                    "old_string": READY_BEFORE.strip(),
                    "new_string": READY_HEALTHZ.strip(),
                },
            },
            "observation": "Edited avocetready/harvest.py: READINESS is now httpGet /healthz so mill harvest matches liveness.",
            "reflection": "Wrote a /healthz-as-readiness swap. Add a pytest that requires readiness httpGet /readyz.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: renderer now emits readiness httpGet /healthz (step 10). Write a pytest as evidence that mill /readyz stays the readiness path."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_harvest.py",
                    "content": READY_TEST,
                },
            },
            "observation": "Wrote tests/test_harvest.py (14 lines).",
            "reflection": "Created a /readyz regression. Run pytest to reproduce the /healthz miss.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Plan: run pytest tests/test_harvest.py as evidence whether copying /healthz satisfies the mill /readyz contract."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_harvest.py -q --tb=short 2>&1 | tail -n 22"
                },
            },
            "observation": (
                "F\n"
                "=================================== FAILURES ===================================\n"
                "______________ test_readiness_is_readyz_not_tcp ______________\n"
                "tests/test_harvest.py:9: in test_readiness_is_readyz_not_tcp\n"
                "    assert got == \"/readyz\", f\"got path={got} probe={ready}\"\n"
                "E   AssertionError: got path=/healthz probe={'httpGet': {'path': '/healthz', 'port': 8443}}\n"
                "E   assert '/healthz' == '/readyz'\n"
                "FAILED tests/test_harvest.py::test_readiness_is_readyz_not_tcp - AssertionError: got path=/healthz\n"
                "1 failed in 0.04s"
            ),
            "reflection": "Test failed: readiness is /healthz and mill gate wants /readyz. Re-read render_deploy and set READINESS to httpGet /readyz.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: pytest failed with got path=/healthz want /readyz (step 12). Re-read render_deploy for the READINESS evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "avocetready/harvest.py", "offset": 1, "limit": 40},
            },
            "observation": READY_HEALTHZ,
            "reflection": "Confirmed line 5 still copies /healthz against mill lot-load Ready. Patch READINESS to httpGet /readyz.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: helper must readinessProbe httpGet /readyz not copy /healthz (step 13). Patch READINESS to /readyz as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "avocetready/harvest.py",
                    "old_string": READY_HEALTHZ.strip(),
                    "new_string": READY_READYZ.strip(),
                },
            },
            "observation": "Edited avocetready/harvest.py: READINESS is httpGet /readyz (mill lots loaded).",
            "reflection": "Patched /readyz readiness. Re-run pytest; mill harvest should no longer use tcpSocket.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: helper now emits readiness httpGet /readyz (step 14). Re-run pytest tests/test_harvest.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_harvest.py tests/test_render.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                ".....\n"
                "5 passed in 0.07s"
            ),
            "reflection": "Verified 5 passed including test_readiness_is_readyz_not_tcp. Check gate-cli before applying the Deployment.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: pytest passed 5/5 after the /readyz patch (step 15). Run gate-cli check apply as evidence whether prod Deployment mutation is allowed."
            ),
            "tool_call": {
                "name": "gate-cli",
                "args": {
                    "argv": [
                        "check",
                        "apply",
                        "--change",
                        "avocetready-readyz",
                        "--resource",
                        "deploy/avocetready-harvest",
                    ]
                },
            },
            "observation": (
                "gate-cli check apply --change avocetready-readyz\n"
                "status: REJECT\n"
                "policy: prod-batch-freeze\n"
                "ticket: AV-60\n"
                "until: 2026-09-16T00:00:00Z\n"
                "evidence: change mutates Deployment/avocetready-harvest (avocetready-harvest readinessProbe tcpSocket 8443)\n"
                "found 0 waivers"
            ),
            "reflection": "Measured REJECT under AV-60 freeze through 2026-09-16. Do not kubectl apply. Open a handoff issue attaching the /readyz fix.",
        },
        {
            "n": 17,
            "decision_basis": db(
                "Observation: gate-cli REJECT'd the Deployment apply under freeze AV-60 (step 16). Open a handoff issue as evidence live readiness is still tcpSocket."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "title": "AV-83: apply avocetready /readyz after AV-60 freeze (blocks AV-72 close)",
                    "body": "render_deploy now emits readinessProbe httpGet /readyz; pytest 5 passed. Live Deployment still uses tcpSocket 8443. gate-cli freeze AV-60 until 2026-09-16. Do not kubectl delete the Deployment.",
                },
            },
            "observation": "https://git.avocetfen.internal/k8s/avocetready-harvest/issues/83",
            "reflection": "Opened AV-83. Renderer is green; prod apply remains blocked. Handoff, not close.",
        },
    ]
    return {
        "id": ID2,
        "goal": (
            "AV-72 (avocetready-harvest, Python 3.12 resource renderer + kind avocetfen; pytest + kubectl): "
            "mill harvest pods are Ready while lots still load and a Deployment already exists. "
            "Find why readinessProbe tcpSocket marks Ready, fix the renderer, and apply or hand off. Designed plant; not a live cluster trace."
        ),
        "steps": steps,
        "outcome": (
            "render_deploy emitted readinessProbe tcpSocket port 8443, so mill harvest was Ready while lots still loaded. "
            "A first patch that copied liveness /healthz still failed test_readiness_is_readyz_not_tcp (got path=/healthz). "
            "The helper now readinessProbe httpGet /readyz; pytest 5 passed. "
            "Applying Deployment/avocetready-harvest remains blocked by gate-cli freeze AV-60; live spec still uses tcpSocket 8443. "
            "AV-83 opened. Overall: incomplete; prod apply unresolved."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "readiness_readyz_fix": 0.10,
            "readyz_probe_test": 0.08,
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
            codebase_type="CLI / Kubernetes resource renderer (Python 3.12)",
            bug_class="silent no-op: readinessProbe tcpSocket marks mill harvest Ready during lot load; first fix copied /healthz",
            test_harness="pytest + kubectl + gate-cli",
            noise_steps={"502": 3, "429": 6},
            noise_recovery_steps={"502": 4, "429": 7},
            plan_change_step=8,
            debug_loop_steps=[10, 11, 12, 13, 14, 15],
            tags=[
                "readinessProbe",
                "tcpSocket",
                "readyz",
                "mill-harvest-ready",
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
    return """# ACTF r44 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r44-mktime-local-ruddtime-b4e81a`, `act-r44-readiness-tcp-avocetready-c7d214` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`kubectl`/`gate-cli`/`aws`/`jq`/`refuse`). meta.round=44 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Never wrote outputs/raw/. Distinct from staged r10-r43 (r40 itertools.groupby unsorted / NetworkPolicy ipBlock.except; r41 json.dumps allow_nan / QoS limits-only; r42 binascii.unhexlify odd pad / PDB minAvailable 100%; r43 heapq.merge unsorted / ipFamily single-stack; r38 json.load NDJSON Extra data / liveness without startupProbe; r37 `str.rstrip('.json')` charset / Deployment OnDelete; r36 uuid5 vs uuid3 / runAsNonRoot uid0; r34 filecmp.cmp shallow / liveness successThreshold; r32 os.path.join absolute / hostNetwork ClusterFirst; r24 os.path.commonprefix / preStop sleep>grace). Invented repos `git.ruddfen.internal/pkg/ruddtime-lots.git` and `git.avocetfen.internal/k8s/avocetready-harvest.git`. Beads create failed (Dolt events id default); Linear RM-793 remains the rights tracker.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r44-mktime-local-ruddtime-b4e81a | Python 3.12 mill lot epoch helper + lot-epochs fixtures / pytest + aws s3api + jq | schema mismatch: `time.mktime` treats mill UTC stamps as local; first fix subtracted 18000 | success; 6/6; PR 441 | 0.58 |
| act-r44-readiness-tcp-avocetready-c7d214 | Python 3.12 resource renderer / pytest + kubectl + gate-cli | silent no-op: readinessProbe `tcpSocket` marks mill harvest Ready during lot load; first fix copied `/healthz` | incomplete HIL/prod apply; AV-83; freeze AV-60 | 0.28 |

## Step counts, noise, plan change
- act-r44-mktime-local-ruddtime-b4e81a: 15 steps. 429 at step 4 (`gh api` cpython time.rst, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/mktime-local.md`). 502 at step 6 (`aws s3api get-object` ruddfen-specs lot-epochs ELB) -> recovery step 7 (`jq` committed `fixtures/lot-epochs.json`). Plan change at step 8: jq join shows want already UTC epochs and got is Chicago-local mktime; abandon remounting mill S3 prefix. Debug loop: 9 edit subtract-18000 -> 10 write mixed-DST pytest -> 11 FAIL got mid-rill.json=1768352400 -> 12 re-read lot_epoch -> 13 calendar.timegm patch -> 14 6 passed.
- act-r44-readiness-tcp-avocetready-c7d214: 17 steps. 502 at step 3 (`kubectl get deploy` kind ingress) -> recovery step 4 (`--request-timeout=30s` writes /tmp/avocetready-deploy.json). 429 at step 6 (`gh api` kubernetes/website pod-lifecycle.md, retry-after 7) -> recovery step 7 (read vendored `docs/readiness-tcp.md`). Plan change at step 8: jq readiness tcpSocket 8443 vs liveness /healthz while pods Ready 1/1 during lot load; abandon adding mill nodes. Debug loop: 10 edit copy /healthz -> 11 write /readyz pytest -> 12 FAIL got path=/healthz -> 13 re-read helper -> 14 httpGet /readyz patch -> 15 5 passed. `refuse` at step 9 blocks `kubectl delete deploy`. gate-cli REJECT at 16; AV-83 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. mktime-local: 0.40+0.12+0.08-0.02=0.58. readiness-tcp: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: `time.mktime` on naive mill UTC stamps is a real stdlib footgun (host local zone); subtracting 18000 is the equally tempting CDT-shaped wrong fix and the mixed-DST test names the contract (`mid-rill.json` January CST stays 3600 high). readinessProbe `tcpSocket` treating an open mill harvest port as Ready is the usual silent Ready-during-boot; copying liveness `/healthz` still fails the mill contract that requires `/readyz`. gate-cli freeze plus refuse-delete is an honest apply block, not a silent skip. Weak: mill-inventory 502 fallback is availability (committed fixture is not a stale dest whose UTC epochs disagree with a second document); kubectl json dump is one object; no reviewer asking to keep mktime "so mill PLC wall clocks still fold". Next densification: a 502 whose local lot-epochs fixture is stale (`want` UTC vs a second file still on Chicago mktime), or a reviewer asking to keep tcpSocket 8443 "so mill harvest sidecars can skip /readyz".

Novel coverage: 42%
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
    batch = OUT / "batch-r44.jsonl"
    with batch.open("w", encoding="utf-8") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    notes_path = OUT / "NOTES-r44.md"
    notes_path.write_text(notes(), encoding="utf-8")
    errors, warnings, kinds, n = check_jsonl(
        batch, "batch-r44.jsonl", staging=FactoryStaging(enabled=True)
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
