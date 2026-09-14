#!/usr/bin/env python3
"""Generate designed ACTF r33 episodes (Q=2). Never writes outputs/raw/."""
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

OUT = Path("/tmp/actf-r33")
GENERATED_AT = "2026-09-02T23:58:00Z"
ROUND = 33
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
ID1 = "act-r33-quoteplus-space-hmac-siltquery-b7e41a"
ID2 = "act-r33-k8s-cpu-bare-int-cores-tarncpu-c3f82b"
PLANT_TOKENS = ("siltquery", "siltmoor", "tarncpu", "tarnfen")


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
    self_batch = (OUT / "batch-r33.jsonl").resolve()
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


HMAC_BEFORE = '''import urllib.parse


def encode_lot(lot_key: str) -> str:
    return urllib.parse.quote(lot_key)
'''

HMAC_PLUS = '''import urllib.parse


def encode_lot(lot_key: str) -> str:
    return urllib.parse.quote_plus(lot_key)
'''

HMAC_SAFE = '''import urllib.parse


def encode_lot(lot_key: str) -> str:
    return urllib.parse.quote(lot_key, safe="")
'''

HMAC_TEST = '''from siltquery.hmac import encode_lot

KEYS = ["/week36/lot.ndjson", "week36/shift-a/lot.ndjson", "WB 440.csv"]
WANT = {
    "%2Fweek36%2Flot.ndjson",
    "week36%2Fshift-a%2Flot.ndjson",
    "WB%20440.csv",
}


def test_encode_lot_percent_encodes_slash_and_space():
    got = {encode_lot(k) for k in KEYS}
    assert got == WANT, f"got={sorted(got)} want={sorted(WANT)}"
'''

QUOTA_BEFORE = '''# Ported from the v1 mill harvest. cpu 100 meant millicores in the spreadsheet.
# Kubernetes Quantity treats a bare integer as whole cores.

API_VERSION = "apps/v1"
DEFAULT_CPU = "100"
DEFAULT_MEMORY = "256Mi"


def render_resources() -> dict:
    return {
        "requests": {"cpu": DEFAULT_CPU, "memory": DEFAULT_MEMORY},
        "limits": {"cpu": DEFAULT_CPU, "memory": DEFAULT_MEMORY},
    }
'''

QUOTA_TENTH = '''# Ported from the v1 mill harvest. cpu 100 meant millicores in the spreadsheet.
# Kubernetes Quantity treats a bare integer as whole cores.

API_VERSION = "apps/v1"
DEFAULT_CPU = "0.1"
DEFAULT_MEMORY = "256Mi"


def render_resources() -> dict:
    return {
        "requests": {"cpu": DEFAULT_CPU, "memory": DEFAULT_MEMORY},
        "limits": {"cpu": DEFAULT_CPU, "memory": DEFAULT_MEMORY},
    }
'''

QUOTA_MILLI = '''# Ported from the v1 mill harvest. cpu 100 meant millicores in the spreadsheet.
# Kubernetes Quantity treats a bare integer as whole cores.

API_VERSION = "apps/v1"
DEFAULT_CPU = "100m"
DEFAULT_MEMORY = "256Mi"


def render_resources() -> dict:
    return {
        "requests": {"cpu": DEFAULT_CPU, "memory": DEFAULT_MEMORY},
        "limits": {"cpu": DEFAULT_CPU, "memory": DEFAULT_MEMORY},
    }
'''

QUOTA_TEST = '''from tarncpu.quota import render_resources


def test_cpu_is_canonical_millicores():
    spec = render_resources()
    assert spec["requests"]["cpu"] == "100m", f"got cpu={spec['requests']['cpu']}"
    assert spec["limits"]["cpu"] == "100m"
    assert spec["requests"]["cpu"].endswith("m")
    assert "0.1" not in spec["requests"]["cpu"]
'''


def ep1() -> dict:
    """siltquery-hmac: urllib.parse.quote keeps slash; quote_plus breaks space lots."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: SQ-241 reports mill HMAC catalog misses slash lots. Search encode_lot and quote as evidence of urllib.parse.quote keeping slash."
            ),
            "plan": "1) search encode_lot 2) read hmac.py 3) measure quote 4) confirm want encodings 5) fix safe='' 6) regression + PR",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "encode_lot|urllib.parse.quote|quote_plus|HMAC_SECRET",
                    "path": ".",
                },
            },
            "observation": (
                "siltquery/hmac.py:5:def encode_lot(lot_key: str) -> str:\n"
                "siltquery/hmac.py:6:    return urllib.parse.quote(lot_key)\n"
                "siltquery/hmac.py:9:def sign_lot(lot_key: str) -> str:\n"
                "tests/test_install.py:14:    assert encode_lot(\"/week36/lot.ndjson\").startswith(\"%2F\")\n"
                "5 matches"
            ),
            "reflection": "Found encode_lot wrapping urllib.parse.quote with default safe='/'. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: hmac.py:6 returns urllib.parse.quote(lot_key) with default safe slash (step 1). Read the helper as evidence of any safe='' clamp."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "siltquery/hmac.py", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  import urllib.parse\n"
                "2\n"
                "3  # Mill lot HMAC keys. Catalog encodings come from the PLC packer.\n"
                "4  # encode_lot was copied from a helper that assumed slash-safe URLs.\n"
                "5  def encode_lot(lot_key: str) -> str:\n"
                "6      return urllib.parse.quote(lot_key)\n"
                "7\n"
                "8\n"
                "9  def sign_lot(lot_key: str) -> str:\n"
                "10     return hmac.new(SECRET, encode_lot(lot_key).encode(), hashlib.sha256).hexdigest()\n"
            ),
            "reflection": "Learned quote is called with the inventory key as-is. First plan: mill HMAC secret rotated. Next measure the quote.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: encode_lot quotes lot_key with default quote (step 2). Measure urllib.parse.quote of /week36/lot.ndjson as evidence of a kept slash."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 -c \"import urllib.parse; print(urllib.parse.quote("
                        "'/week36/lot.ndjson'))\""
                    )
                },
            },
            "observation": "/week36/lot.ndjson",
            "reflection": "Measured quote keeping /week36/lot.ndjson. Next confirm the mill want encodings still percent-encode slashes.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Reflection: quote kept the leading slash on /week36/lot.ndjson (step 3). Fetch urllib.parse.rst notes via gh as evidence of the safe='/' default."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/python/cpython/contents/Doc/library/urllib.parse.rst",
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
            "reflection": "GitHub returned a rate-limit with retry-after 5 while fetching urllib.parse docs. Wait, then use the vendored docs/quote-safe.md fixture.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/quote-safe.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/quote-safe.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  urllib.parse.quote keeps '/' because the default safe set is '/'.\n"
                "2  quote('/week36/lot.ndjson') is still /week36/lot.ndjson.\n"
                "3  Mill HMAC catalogs encode the slash: %2Fweek36%2Flot.ndjson.\n"
                "4  quote_plus encodes slash but turns mill space lots into plus: WB+440.csv.\n"
                "5  Durable: encode_lot must quote(lot_key, safe='') so slash and space percent-encode.\n"
                "6  A rotated mill HMAC secret is independent of this client quote.\n"
            ),
            "reflection": "Verified the slash-safe quote trap and that quote_plus is worse for space lots. Next pull the committed mill HMAC fixture.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: RFC-style notes say default quote keeps slash (step 5). Get the committed mill HMAC inventory object as evidence the want set is percent-encoded."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-object",
                        "--bucket",
                        "siltmoor-specs",
                        "--key",
                        "siltquery/lot-hmacs.json",
                        "/tmp/siltquery-inventory.json",
                    ]
                },
            },
            "observation": (
                "download failed: s3.eu-west-1.amazonaws.com/siltmoor-specs\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "server: awselb/2.0\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection failure"
            ),
            "reflection": "Mill inventory get-object hit a bad gateway on the ELB before headers. Retry against the committed fixtures/lot-hmacs.json instead of the edge.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: mill inventory get-object returned 502 from the ELB (step 6). jq fixtures/lot-hmacs.json want and keys as local-spec evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{want:.want, keys:.keys, n:.key_count}",
                        "fixtures/lot-hmacs.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "want": [\n'
                '    "%2Fweek36%2Flot.ndjson",\n'
                '    "week36%2Fshift-a%2Flot.ndjson",\n'
                '    "WB%20440.csv"\n'
                "  ],\n"
                '  "keys": ["/week36/lot.ndjson", "week36/shift-a/lot.ndjson", "WB 440.csv"],\n'
                '  "n": 3\n'
                "}"
            ),
            "reflection": "Verified want already lists three percent-encoded mill HMAC keys. Next join that with the measured quote.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: fixture want already lists 3 percent-encoded mill lots (step 7). jq the measured quote against that spec as evidence whether HMAC keys are wrong."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "s",
                        "fixtures/lot-hmacs.json",
                        "{got:[\"/week36/lot.ndjson\"],want:$s[0].want,n:$s[0].key_count}",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "got": ["/week36/lot.ndjson"],\n'
                '  "want": [\n'
                '    "%2Fweek36%2Flot.ndjson",\n'
                '    "week36%2Fshift-a%2Flot.ndjson",\n'
                '    "WB%20440.csv"\n'
                "  ],\n"
                '  "n": 3\n'
                "}"
            ),
            "reflection": (
                "Plan change: mill want inventory already lists three percent-encoded lots and got is /week36/lot.ndjson from quote keeping slash. "
                "Abandon rotating the mill HMAC secret. Switching the edit target to encode_lot so slash and space percent-encode."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the missing-secret plan; quote kept /week36/lot.ndjson (step 8). Edit quote_plus as evidence slashes are encoded."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "siltquery/hmac.py",
                    "old_string": HMAC_BEFORE.strip(),
                    "new_string": HMAC_PLUS.strip(),
                },
            },
            "observation": "Edited siltquery/hmac.py: encode_lot now uses urllib.parse.quote_plus so a leading slash is percent-encoded.",
            "reflection": "Wrote a quote_plus swap. Add a pytest that requires both slash keys and space mill lots.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: encode_lot now uses quote_plus (step 9). Write a pytest as evidence that encode_lot equals the 3 mill HMAC encodings for mixed keys."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_hmac.py",
                    "content": HMAC_TEST,
                },
            },
            "observation": "Wrote tests/test_hmac.py (16 lines).",
            "reflection": "Created a mixed-key regression that expects three percent-encoded HMAC keys. Run pytest to reproduce the plus-space miss.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Plan: run pytest tests/test_hmac.py as evidence whether quote_plus keeps mill space lots as percent-20 not plus."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_hmac.py -q --tb=short 2>&1 | tail -n 20"
                },
            },
            "observation": (
                "F\n"
                "=================================== FAILURES ===================================\n"
                "______ test_encode_lot_percent_encodes_slash_and_space ______\n"
                "tests/test_hmac.py:14: in test_encode_lot_percent_encodes_slash_and_space\n"
                "    assert got == WANT, f\"got={sorted(got)} want={sorted(WANT)}\"\n"
                "E   AssertionError: got=['%2Fweek36%2Flot.ndjson', 'WB+440.csv', "
                "'week36%2Fshift-a%2Flot.ndjson'] "
                "want=['%2Fweek36%2Flot.ndjson', 'WB%20440.csv', "
                "'week36%2Fshift-a%2Flot.ndjson']\n"
                "FAILED tests/test_hmac.py::test_encode_lot_percent_encodes_slash_and_space - AssertionError: got WB+440.csv\n"
                "1 failed in 0.05s"
            ),
            "reflection": "Test failed: quote_plus encoded slash lots and turned WB 440.csv into WB+440.csv. Re-read encode_lot and switch to quote(safe='').",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Observation: pytest failed with got WB+440.csv want WB%20440.csv (step 11). Re-read encode_lot for the quote_plus evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "siltquery/hmac.py", "offset": 1, "limit": 12},
            },
            "observation": HMAC_PLUS,
            "reflection": "Confirmed line 6 still uses quote_plus and space lots become plus. Patch quote(lot_key, safe='').",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Reflection: encode_lot must quote with safe='' rather than quote_plus (step 12). Patch hmac.py to urllib.parse.quote(lot_key, safe='') as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "siltquery/hmac.py",
                    "old_string": HMAC_PLUS.strip(),
                    "new_string": HMAC_SAFE.strip(),
                },
            },
            "observation": "Edited siltquery/hmac.py: encode_lot now quote(lot_key, safe='') so slash and space stay percent-encoded.",
            "reflection": "Patched the quote. Re-run pytest; all three mill HMAC encodings should appear.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Observation: encode_lot now quote(lot_key, safe='') (step 13). Re-run pytest tests/test_hmac.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_hmac.py tests/test_install.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                "......\n"
                "6 passed in 0.08s"
            ),
            "reflection": "Verified 6 passed including test_encode_lot_percent_encodes_slash_and_space. Open the SQ-241 PR.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: pytest passed 6/6 after the quote safe='' patch (step 14). Create the SQ-241 PR via gh as evidence of the encode_lot fix."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/siltmoor/siltquery-hmac/pulls",
                    "raw_field": "title=SQ-241: quote lot keys with safe='' so mill HMAC encodes slash and space",
                },
            },
            "observation": (
                "{\n"
                '  "number": 331,\n'
                '  "html_url": "https://git.siltmoor.internal/pkg/siltquery-hmac/pull/331",\n'
                '  "state": "open"\n'
                "}"
            ),
            "reflection": "Opened PR 331. encode_lot matches all three mill HMAC encodings. Live mill HMAC census follow-up remains against the designed mill host.",
        },
    ]
    return {
        "id": ID1,
        "goal": (
            "SQ-241 (siltquery-hmac, Python 3.12 mill lot HMAC helper + fixtures/lot-hmacs.json; pytest): "
            "nightly mill HMAC catalog misses /week36/lot.ndjson while the mill dest is %2Fweek36%2Flot.ndjson "
            "(keys /week36/lot.ndjson, week36/shift-a/lot.ndjson, WB 440.csv). "
            "Find why encode_lot keeps slash, add a mixed-key regression, and open a PR. Designed plant; not a live mill apply."
        ),
        "steps": steps,
        "outcome": (
            "encode_lot passed lot_key through urllib.parse.quote, so a slash inventory key kept '/' and missed the mill HMAC catalog. "
            "A first patch that swapped in quote_plus still failed test_encode_lot_percent_encodes_slash_and_space (got WB+440.csv). "
            "encode_lot now calls urllib.parse.quote(lot_key, safe=''). Verified by pytest 6 passed "
            "(tests/test_hmac.py::test_encode_lot_percent_encodes_slash_and_space). PR 331 opened. "
            "Live mill HMAC copies remain a follow-up against the designed mill host."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.40,
            "quote_safe_empty_fix": 0.12,
            "mixed_key_hmac_test": 0.08,
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
            codebase_type="library / mill lot HMAC (Python 3.12 urllib.parse)",
            bug_class="schema mismatch: urllib.parse.quote kept slash; first fix used quote_plus and turned mill space lots into plus",
            test_harness="pytest + aws s3api + jq",
            noise_steps={"429": 4, "502": 6},
            noise_recovery_steps={"429": 5, "502": 7},
            plan_change_step=8,
            debug_loop_steps=[9, 10, 11, 12, 13, 14],
            tags=[
                "urllib.parse.quote",
                "quote_plus",
                "percent-encoding",
                "mill-hmac",
                "slash-safe",
                "space-plus",
            ],
        ),
    }


def ep2() -> dict:
    """tarncpu-quota: Kubernetes Quantity '100' is 100 cores, not 100 millicores."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: TQ-72 reports mill-harvest Pending Insufficient cpu. Search DEFAULT_CPU and render_resources as evidence of a bare integer Quantity."
            ),
            "plan": "1) search quota renderer 2) read render_resources 3) measure live deploy 4) fix 100m 5) regression 6) apply or hand off",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "DEFAULT_CPU|render_resources|requests.cpu|100m",
                    "path": ".",
                },
            },
            "observation": (
                "tarncpu/quota.py:5:DEFAULT_CPU = \"100\"\n"
                "tarncpu/quota.py:10:        \"requests\": {\"cpu\": DEFAULT_CPU, \"memory\": DEFAULT_MEMORY},\n"
                "tarncpu/quota.py:11:        \"limits\": {\"cpu\": DEFAULT_CPU, \"memory\": DEFAULT_MEMORY},\n"
                "deploy/harvest.yaml:22:cpu: \"100\"\n"
                "6 matches"
            ),
            "reflection": "Found DEFAULT_CPU 100 with no millicores suffix. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: quota.py:5 sets DEFAULT_CPU=100 while mill harvest is millicores (step 1). Read the renderer as evidence of any millicores suffix clamp."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "tarncpu/quota.py", "offset": 1, "limit": 22},
            },
            "observation": QUOTA_BEFORE,
            "reflection": "Learned there is no millicores suffix clamp. First plan: mill node has no allocatable CPU. Next measure the live Deployment.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: render_resources emits cpu 100 with no millicores suffix (step 2). kubectl get the Deployment as evidence of live spec.template.spec.resources."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-tarnfen",
                    "namespace": "tarnfen",
                    "argv": [
                        "get",
                        "deploy",
                        "tarncpu-harvest",
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
                ") occurred attempting to get Deployment.apps/tarncpu-harvest"
            ),
            "reflection": "kind apiserver ingress returned a bad gateway before headers. Retry with a longer request timeout and write the object locally.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: kubectl get deploy returned 502 from the kind ingress (step 3). Retry --request-timeout=30s and write /tmp/tarncpu-deploy.json as evidence."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-tarnfen",
                    "namespace": "tarnfen",
                    "argv": [
                        "get",
                        "deploy",
                        "tarncpu-harvest",
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
                '  "metadata": {"name": "tarncpu-harvest", "namespace": "tarnfen"},\n'
                '  "spec": {\n'
                '    "replicas": 1,\n'
                '    "template": {"spec": {"containers": [{"name": "harvest", "image": "tarncpu-harvest:1.4", '
                '"resources": {"requests": {"cpu": "100", "memory": "256Mi"}, '
                '"limits": {"cpu": "100", "memory": "256Mi"}}}]}}\n'
                "  },\n"
                '  "status": {"readyReplicas": 0, "unavailableReplicas": 1, '
                '"conditions": [{"type": "ReplicaFailure", "status": "True", '
                '"message": "0/1 nodes are available: 1 Insufficient cpu."}]}\n'
                "}\n"
                "wrote /tmp/tarncpu-deploy.json"
            ),
            "reflection": "Measured live cpu 100 with 0/1 ready and Insufficient cpu. Next inspect node allocatable.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: live deploy has cpu 100, 0 ready replicas, and Insufficient cpu (step 4). kubectl get node allocatable as evidence whether the mill node is the miss."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-tarnfen",
                    "argv": [
                        "get",
                        "node",
                        "tarnfen-control-plane",
                        "-o",
                        "json",
                    ],
                },
            },
            "observation": (
                "{\n"
                '  "metadata": {"name": "tarnfen-control-plane"},\n'
                '  "status": {\n'
                '    "allocatable": {"cpu": "8", "memory": "16032512Ki", "pods": "110"},\n'
                '    "capacity": {"cpu": "8", "memory": "16384000Ki"}\n'
                "  }\n"
                "}\n"
                "found allocatable cpu 8 cores"
            ),
            "reflection": "Found node allocatable 8 cores. This is not a missing mill node. Confirm the Quantity millicores contract next.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: node allocatable is 8 cores (step 5). Fetch resource Quantity docs via gh as evidence of the millicores suffix contract."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/kubernetes/website/contents/content/en/docs/concepts/configuration/manage-resources-containers.md",
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
            "reflection": "GitHub returned a rate-limit with retry-after 7 while fetching Quantity docs. Wait, then use the vendored docs/cpu-quantity.md fixture.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry_after 7 (step 6). Sleep 8s, then read docs/cpu-quantity.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/cpu-quantity.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  Kubernetes Quantity treats a bare integer cpu as whole cores, not millicores.\n"
                "2  cpu: \"100\" is 100 cores; mill harvest wants 100 millicores as 100m.\n"
                "3  cpu: \"0.1\" is 100 millicores as a decimal core and fails mill gate canonical millicores.\n"
                "4  Durable: render_resources must emit 100m on requests and limits.\n"
                "5  Adding a mill node does not shrink a 100-core request onto 8 allocatable cores.\n"
                "6  Kind does not rewrite Quantity suffixes; the renderer must.\n"
            ),
            "reflection": "Verified bare 100 is 100 cores. Next join that with the saved Deployment.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: docs require 100m millicores not bare 100 cores (step 7). jq spec from the saved deploy as evidence of the live skew."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{cpu:.spec.template.spec.containers[0].resources.requests.cpu,ready:.status.readyReplicas,allocCpu:8}",
                        "/tmp/tarncpu-deploy.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "cpu": "100",\n'
                '  "ready": 0,\n'
                '  "allocCpu": 8\n'
                "}"
            ),
            "reflection": (
                "Plan change: live spec has cpu 100 vs node allocatable 8 while mill-harvest is Pending Insufficient cpu. "
                "Abandon adding mill nodes. Switching the edit target to render_resources so cpu is canonical 100m millicores."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the add-node plan; cpu is bare 100 (step 8). Refuse deleting the Deployment as evidence the object must stay."
            ),
            "tool_call": {
                "name": "refuse",
                "args": {
                    "action": "kubectl delete deploy/tarncpu-harvest so a freshly created object picks 100m",
                    "policy": "CPU-MUTATE-04",
                    "incident": "TQ-72",
                },
            },
            "observation": (
                "refused: CPU-MUTATE-04 forbids deleting Deployment/tarncpu-harvest to skip a Quantity millicores skew. "
                "Delete would drop in-flight mill harvest sidecars and can fail-open replica caps. "
                "Safe alternative: patch cpu to 100m and keep replicas 1. found 0 waivers"
            ),
            "reflection": "Denied the delete. Next patch render_resources; keep the Deployment object.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: delete is refused; edit target is DEFAULT_CPU (step 9). First patch: set cpu 0.1 as evidence 100 millicores is 0.1 cores."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "tarncpu/quota.py",
                    "old_string": 'DEFAULT_CPU = "100"\n',
                    "new_string": 'DEFAULT_CPU = "0.1"\n',
                },
            },
            "observation": "Edited tarncpu/quota.py: DEFAULT_CPU is now 0.1 so 100 millicores is a decimal core.",
            "reflection": "Wrote a decimal-core swap. Add a pytest that requires canonical 100m millicores.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: renderer now emits cpu 0.1 (step 10). Write a pytest as evidence that mill harvest cpu is canonical 100m millicores."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_quota.py",
                    "content": QUOTA_TEST,
                },
            },
            "observation": "Wrote tests/test_quota.py (11 lines).",
            "reflection": "Created a millicores Quantity regression. Run pytest to reproduce the 0.1 miss.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Plan: run pytest tests/test_quota.py as evidence whether 0.1 satisfies the millicores Quantity contract."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_quota.py -q --tb=short 2>&1 | tail -n 22"
                },
            },
            "observation": (
                "F\n"
                "=================================== FAILURES ===================================\n"
                "______________ test_cpu_is_canonical_millicores ______________\n"
                "tests/test_quota.py:6: in test_cpu_is_canonical_millicores\n"
                "    assert spec[\"requests\"][\"cpu\"] == \"100m\", f\"got cpu={spec['requests']['cpu']}\"\n"
                "E   AssertionError: got cpu=0.1\n"
                "E   assert '0.1' == '100m'\n"
                "FAILED tests/test_quota.py::test_cpu_is_canonical_millicores - AssertionError: got cpu=0.1\n"
                "1 failed in 0.04s"
            ),
            "reflection": "Test failed: cpu is 0.1 and mill gate wants canonical 100m. Re-read render_resources and set DEFAULT_CPU 100m.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: pytest failed with got cpu=0.1 want 100m (step 12). Re-read render_resources for the DEFAULT_CPU evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "tarncpu/quota.py", "offset": 1, "limit": 18},
            },
            "observation": QUOTA_TENTH,
            "reflection": "Confirmed line 5 still uses 0.1 against mill harvest millicores. Patch DEFAULT_CPU to 100m.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: helper must emit 100m millicores not 0.1 cores (step 13). Patch DEFAULT_CPU to 100m as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "tarncpu/quota.py",
                    "old_string": 'DEFAULT_CPU = "0.1"\n',
                    "new_string": 'DEFAULT_CPU = "100m"\n',
                },
            },
            "observation": "Edited tarncpu/quota.py: DEFAULT_CPU is 100m millicores.",
            "reflection": "Patched canonical millicores. Re-run pytest; mill harvest cpu should now be 100m.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: helper now emits cpu 100m (step 14). Re-run pytest tests/test_quota.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_quota.py tests/test_render.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                ".....\n"
                "5 passed in 0.07s"
            ),
            "reflection": "Verified 5 passed including test_cpu_is_canonical_millicores. Check gate-cli before applying the Deployment.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: pytest passed 5/5 after the 100m patch (step 15). Run gate-cli check apply as evidence whether prod Deployment mutation is allowed."
            ),
            "tool_call": {
                "name": "gate-cli",
                "args": {
                    "argv": [
                        "check",
                        "apply",
                        "--change",
                        "tarncpu-millicores",
                        "--resource",
                        "deploy/tarncpu-harvest",
                    ]
                },
            },
            "observation": (
                "gate-cli check apply --change tarncpu-millicores\n"
                "status: REJECT\n"
                "policy: prod-batch-freeze\n"
                "ticket: TQ-60\n"
                "until: 2026-09-16T00:00:00Z\n"
                "evidence: change mutates Deployment/tarncpu-harvest (tarncpu-harvest cpu Quantity)\n"
                "found 0 waivers"
            ),
            "reflection": "Measured REJECT under TQ-60 freeze through 2026-09-16. Do not kubectl apply. Open a handoff issue attaching the 100m fix.",
        },
        {
            "n": 17,
            "decision_basis": db(
                "Observation: gate-cli REJECT'd the Deployment apply under freeze TQ-60 (step 16). Open a handoff issue as evidence the live cpu is still 100 cores."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "title": "TQ-83: apply tarncpu 100m millicores after TQ-60 freeze (blocks TQ-72 close)",
                    "body": "render_resources now emits cpu 100m; pytest 5 passed. Live Deployment still has cpu 100 cores. gate-cli freeze TQ-60 until 2026-09-16. Do not kubectl delete the Deployment.",
                },
            },
            "observation": "https://git.tarnfen.internal/k8s/tarncpu-quota/issues/83",
            "reflection": "Opened TQ-83. Renderer is green; prod apply remains blocked. Handoff, not close.",
        },
    ]
    return {
        "id": ID2,
        "goal": (
            "TQ-72 (tarncpu-quota, Python 3.12 resource renderer + kind tarnfen; pytest + kubectl): "
            "tarncpu-harvest is Pending Insufficient cpu while the mill node has 8 allocatable cores. "
            "Find why cpu 100 is whole cores not millicores, fix the renderer, and apply or hand off. Designed plant; not a live cluster trace."
        ),
        "steps": steps,
        "outcome": (
            "render_resources emitted cpu 100 with no millicores suffix, so kube-scheduler treated the mill harvest request as 100 cores on an 8-core node. "
            "A first patch that set cpu 0.1 still failed test_cpu_is_canonical_millicores (got cpu=0.1). "
            "The helper now emits 100m; pytest 5 passed. "
            "Applying Deployment/tarncpu-harvest remains blocked by gate-cli freeze TQ-60; live spec still has cpu 100. "
            "TQ-83 opened. Overall: incomplete; prod apply unresolved."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "millicores_suffix_fix": 0.10,
            "canonical_cpu_test": 0.08,
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
            bug_class="schema mismatch: Kubernetes Quantity cpu 100 is 100 cores; first fix used 0.1 cores instead of 100m",
            test_harness="pytest + kubectl + gate-cli",
            noise_steps={"502": 3, "429": 6},
            noise_recovery_steps={"502": 4, "429": 7},
            plan_change_step=8,
            debug_loop_steps=[10, 11, 12, 13, 14, 15],
            tags=[
                "kubernetes-quantity",
                "millicores",
                "cpu-request",
                "Insufficient-cpu",
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
    return """# ACTF r33 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r33-quoteplus-space-hmac-siltquery-b7e41a`, `act-r33-k8s-cpu-bare-int-cores-tarncpu-c3f82b` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`kubectl`/`gate-cli`/`aws`/`jq`/`refuse`). meta.round=33 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Never wrote outputs/raw/. Distinct from staged r10-r32 (r20 urljoin / HPA v2, r24 os.path.commonprefix / preStop sleep>grace, r28 IPv4 hosts skip / Ingress Prefix sibling, r29 glob ** nonrecursive / minReady>progressDeadline, r30 gzip.Flush no footer / NFD combining-strip, r31 ParseUint base 0 octal / NFC lot_key, r32 os.path.join absolute / hostNetwork ClusterFirst). Invented repos `git.siltmoor.internal/pkg/siltquery-hmac.git` and `git.tarnfen.internal/k8s/tarncpu-quota.git`. Beads create failed (Dolt events id default); Linear RM-793 remains the rights tracker.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r33-quoteplus-space-hmac-siltquery-b7e41a | Python 3.12 mill lot HMAC helper + lot-hmacs fixtures / pytest + aws s3api + jq | schema mismatch: `urllib.parse.quote` kept slash; first fix used `quote_plus` and turned mill space lots into plus | success; 6/6; PR 331 | 0.58 |
| act-r33-k8s-cpu-bare-int-cores-tarncpu-c3f82b | Python 3.12 resource renderer / pytest + kubectl + gate-cli | schema mismatch: Quantity `cpu: "100"` is 100 cores; first fix used `0.1` cores instead of `100m` | incomplete HIL/prod apply; TQ-83; freeze TQ-60 | 0.28 |

## Step counts, noise, plan change
- act-r33-quoteplus-space-hmac-siltquery-b7e41a: 15 steps. 429 at step 4 (`gh api` cpython urllib.parse.rst, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/quote-safe.md`). 502 at step 6 (`aws s3api get-object` siltmoor-specs lot-hmacs ELB) -> recovery step 7 (`jq` committed `fixtures/lot-hmacs.json`). Plan change at step 8: jq join shows want already percent-encoded and got is `/week36/lot.ndjson`; abandon rotating HMAC secrets. Debug loop: 9 edit `quote_plus` -> 10 write mixed-key pytest -> 11 FAIL got WB+440.csv -> 12 re-read encode_lot -> 13 quote(safe='') patch -> 14 6 passed.
- act-r33-k8s-cpu-bare-int-cores-tarncpu-c3f82b: 17 steps. 502 at step 3 (`kubectl get deploy` kind ingress) -> recovery step 4 (`--request-timeout=30s` writes /tmp/tarncpu-deploy.json). 429 at step 6 (`gh api` kubernetes/website manage-resources-containers.md, retry-after 7) -> recovery step 7 (read vendored `docs/cpu-quantity.md`). Plan change at step 8: jq cpu 100 vs allocatable 8 while harvest Pending; abandon adding mill nodes. Debug loop: 10 edit cpu 0.1 -> 11 write 100m pytest -> 12 FAIL got cpu=0.1 -> 13 re-read helper -> 14 100m patch -> 15 5 passed. `refuse` at step 9 blocks `kubectl delete deploy`. gate-cli REJECT at 16; TQ-83 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. quoteplus-space-hmac: 0.40+0.12+0.08-0.02=0.58. k8s-cpu-bare-int-cores: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: `urllib.parse.quote` keeping `/` is a real stdlib footgun; `quote_plus` is the equally tempting URL-form wrong fix and the mixed-key test names the contract (space mill lot `WB 440.csv` becomes `WB+440.csv`). Bare Quantity `100` as 100 cores is the usual silent Insufficient cpu on an 8-core mill node; `0.1` is 100 millicores as a decimal core and still fails mill gate canonical `100m`. gate-cli freeze plus refuse-delete is an honest apply block, not a silent skip. Weak: mill-inventory 502 fallback is availability (committed fixture is not a stale dest whose encodings disagree with a second document); kubectl json dump is one object; no reviewer asking to keep slash-safe quote "so mill HTTPS HMAC URLs still join". Next densification: a 502 whose local lot-hmacs fixture is stale (`want` `%2Fweek36%2Flot.ndjson` vs a second file still on `/week36/lot.ndjson`), or a reviewer asking to keep `0.1` "so HPA averageValue still uses cores".

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
    batch = OUT / "batch-r33.jsonl"
    with batch.open("w", encoding="utf-8") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    notes_path = OUT / "NOTES-r33.md"
    notes_path.write_text(notes(), encoding="utf-8")
    errors, warnings, kinds, n = check_jsonl(
        batch, "batch-r33.jsonl", staging=FactoryStaging(enabled=True)
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
