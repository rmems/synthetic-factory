#!/usr/bin/env python3
"""Generate designed ACTF r36 episodes (Q=2). Never writes outputs/raw/."""
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

OUT = Path("/tmp/actf-r36")
GENERATED_AT = "2026-09-02T23:59:45Z"
ROUND = 36
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
ID1 = "act-r36-uuid5-dns-vs-uuid3-murreuid-a4d81c"
ID2 = "act-r36-runasnonroot-uid0-skuasec-b8e205"
PLANT_TOKENS = ("murreuid", "murrefen", "skuasec", "skuaquay")


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
    self_batch = (OUT / "batch-r36.jsonl").resolve()
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


UUID_BEFORE = '''import uuid


def encode_lot(lot_key: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, lot_key))
'''

UUID_HEX = '''import uuid


def encode_lot(lot_key: str) -> str:
    return uuid.uuid5(uuid.NAMESPACE_DNS, lot_key).hex
'''

UUID_V3 = '''import uuid


def encode_lot(lot_key: str) -> str:
    return uuid.uuid3(uuid.NAMESPACE_DNS, lot_key).hex
'''

UUID_TEST = '''from murreuid.lots import encode_lot

KEYS = ["/week36/lot.ndjson", "week36/shift-a/lot.ndjson", "WB 440.csv"]
WANT = {
    "c8f5d30845363809adb2da8cdf383e13",
    "c7f03f6b138d3824b2d07f25215174bc",
    "c5489e9aa19832d0b21d00d7729a839d",
}


def test_encode_lot_uuid3_dns_hex():
    got = {encode_lot(k) for k in KEYS}
    assert got == WANT, f"got={sorted(got)} want={sorted(WANT)}"
    assert all("-" not in v and len(v) == 32 for v in got)
'''

SCC_BEFORE = '''# Ported from the v1 mill harvest. The image USER is root.
# Kubernetes runAsNonRoot without runAsUser still starts as the image user.

API_VERSION = "apps/v1"
DEFAULT_RUN_AS_NON_ROOT = True


def render_security() -> dict:
    return {
        "runAsNonRoot": DEFAULT_RUN_AS_NON_ROOT,
    }
'''

SCC_UID0 = '''# Ported from the v1 mill harvest. The image USER is root.
# Kubernetes runAsNonRoot without runAsUser still starts as the image user.

API_VERSION = "apps/v1"
DEFAULT_RUN_AS_NON_ROOT = True
DEFAULT_RUN_AS_USER = 0


def render_security() -> dict:
    return {
        "runAsNonRoot": DEFAULT_RUN_AS_NON_ROOT,
        "runAsUser": DEFAULT_RUN_AS_USER,
    }
'''

SCC_NONROOT = '''# Ported from the v1 mill harvest. The image USER is root.
# Kubernetes runAsNonRoot without runAsUser still starts as the image user.

API_VERSION = "apps/v1"
DEFAULT_RUN_AS_NON_ROOT = True
DEFAULT_RUN_AS_USER = 65532


def render_security() -> dict:
    return {
        "runAsNonRoot": DEFAULT_RUN_AS_NON_ROOT,
        "runAsUser": DEFAULT_RUN_AS_USER,
    }
'''

SCC_TEST = '''from skuasec.pod import render_security


def test_run_as_non_root_has_numeric_uid():
    spec = render_security()
    assert spec["runAsNonRoot"] is True, f"got runAsNonRoot={spec.get('runAsNonRoot')}"
    assert spec["runAsUser"] == 65532, f"got runAsUser={spec.get('runAsUser')}"
    assert spec["runAsUser"] != 0
'''


def ep1() -> dict:
    """murreuid-lots: uuid5 DNS hyphenated SHA-1 vs mill uuid3 DNS hex."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: MU-241 reports mill lot UUID catalog misses slash lots. Search encode_lot and uuid.uuid5 as evidence of a SHA-1 name uuid."
            ),
            "plan": "1) search encode_lot 2) read lots.py 3) measure uuid5 4) confirm want hex 5) fix uuid3 .hex 6) regression + PR",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "encode_lot|uuid.uuid5|uuid.uuid3|NAMESPACE_DNS",
                    "path": ".",
                },
            },
            "observation": (
                "murreuid/lots.py:5:def encode_lot(lot_key: str) -> str:\n"
                "murreuid/lots.py:6:    return str(uuid.uuid5(uuid.NAMESPACE_DNS, lot_key))\n"
                "tests/test_install.py:14:    assert \"-\" in encode_lot(\"/week36/lot.ndjson\")\n"
                "5 matches"
            ),
            "reflection": "Found encode_lot wrapping uuid.uuid5 with str() hyphens. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: lots.py:6 returns str(uuid.uuid5(NAMESPACE_DNS, lot_key)) (step 1). Read the helper as evidence of any uuid3 or .hex clamp."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "murreuid/lots.py", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  import uuid\n"
                "2\n"
                "3  # Mill lot UUID keys. Catalog encodings come from the PLC packer.\n"
                "4  # encode_lot was copied from a helper that assumed RFC-4122 hyphen form.\n"
                "5  def encode_lot(lot_key: str) -> str:\n"
                "6      return str(uuid.uuid5(uuid.NAMESPACE_DNS, lot_key))\n"
            ),
            "reflection": "Learned uuid5 DNS is stringified with hyphens. First plan: mill UUID namespace rotated. Next measure uuid5.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: encode_lot stringifies uuid5 DNS (step 2). Measure uuid.uuid5 of /week36/lot.ndjson as evidence of hyphenated SHA-1 form."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 -c \"import uuid; print(uuid.uuid5("
                        "uuid.NAMESPACE_DNS, '/week36/lot.ndjson'))\""
                    )
                },
            },
            "observation": "9eb57b6f-8441-563e-ad1e-5be259b91b4e",
            "reflection": "Measured uuid5 hyphenated 9eb57b6f-8441-563e-ad1e-5be259b91b4e. Next confirm the mill want encodings are 32-hex MD5.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Reflection: uuid5 printed 9eb57b6f-8441-563e-ad1e-5be259b91b4e (step 3). Fetch uuid.rst notes via gh as evidence of uuid3 MD5 vs uuid5 SHA-1."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/python/cpython/contents/Doc/library/uuid.rst",
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
            "reflection": "GitHub returned a rate-limit with retry-after 5 while fetching uuid docs. Wait, then use the vendored docs/uuid3-dns.md fixture.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/uuid3-dns.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/uuid3-dns.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  uuid.uuid5 is SHA-1; mill lot catalogs use uuid.uuid3 (MD5) over NAMESPACE_DNS.\n"
                "2  str(uuid) is 8-4-4-4-12 with hyphens; mill keys are 32-char .hex with no hyphens.\n"
                "3  uuid5('/week36/lot.ndjson') hex is 9eb57b6f8441563ead1e5be259b91b4e.\n"
                "4  Mill want for that key is uuid3 hex c8f5d30845363809adb2da8cdf383e13.\n"
                "5  Durable: encode_lot must uuid.uuid3(NAMESPACE_DNS, lot_key).hex.\n"
                "6  Rotating NAMESPACE_URL is independent of this uuid3/hex contract.\n"
            ),
            "reflection": "Verified uuid5 SHA-1 plus hyphens miss mill uuid3 hex. Next pull the committed mill UUID fixture.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: RFC-style notes say mill catalog is uuid3 DNS hex (step 5). Get the committed mill UUID inventory object as evidence the want set is 32-hex."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-object",
                        "--bucket",
                        "murrefen-specs",
                        "--key",
                        "murreuid/lot-uuids.json",
                        "/tmp/murreuid-inventory.json",
                    ]
                },
            },
            "observation": (
                "download failed: s3.eu-west-1.amazonaws.com/murrefen-specs\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "server: awselb/2.0\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection failure"
            ),
            "reflection": "Mill inventory get-object hit a bad gateway on the ELB before headers. Retry against the committed fixtures/lot-uuids.json instead of the edge.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: mill inventory get-object returned 502 from the ELB (step 6). jq fixtures/lot-uuids.json want and keys as local-spec evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{want:.want, keys:.keys, n:.key_count}",
                        "fixtures/lot-uuids.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "want": [\n'
                '    "c8f5d30845363809adb2da8cdf383e13",\n'
                '    "c7f03f6b138d3824b2d07f25215174bc",\n'
                '    "c5489e9aa19832d0b21d00d7729a839d"\n'
                "  ],\n"
                '  "keys": ["/week36/lot.ndjson", "week36/shift-a/lot.ndjson", "WB 440.csv"],\n'
                '  "n": 3\n'
                "}"
            ),
            "reflection": "Verified want already lists three uuid3 DNS hex mill lots. Next join that with the measured uuid5.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: fixture want already lists 3 uuid3 DNS hex mill lots (step 7). jq the measured uuid5 against that spec as evidence whether UUID keys are wrong."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "s",
                        "fixtures/lot-uuids.json",
                        "{got:[\"9eb57b6f-8441-563e-ad1e-5be259b91b4e\"],want:$s[0].want,n:$s[0].key_count}",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "got": ["9eb57b6f-8441-563e-ad1e-5be259b91b4e"],\n'
                '  "want": [\n'
                '    "c8f5d30845363809adb2da8cdf383e13",\n'
                '    "c7f03f6b138d3824b2d07f25215174bc",\n'
                '    "c5489e9aa19832d0b21d00d7729a839d"\n'
                "  ],\n"
                '  "n": 3\n'
                "}"
            ),
            "reflection": (
                "Plan change: mill want inventory already lists three uuid3 DNS hex lots and got is hyphenated uuid5 SHA-1. "
                "Abandon rotating the mill UUID namespace. Switching the edit target to encode_lot so name UUIDs are uuid3 DNS hex."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the namespace-rotation plan; uuid5 kept hyphens (step 8). Edit uuid5 .hex as evidence hyphens are stripped."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "murreuid/lots.py",
                    "old_string": UUID_BEFORE.strip(),
                    "new_string": UUID_HEX.strip(),
                },
            },
            "observation": "Edited murreuid/lots.py: encode_lot now uses uuid.uuid5(...).hex so hyphens are stripped.",
            "reflection": "Wrote a uuid5 hex swap. Add a pytest that requires uuid3 DNS hex mill lots.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: encode_lot now uses uuid5 .hex (step 9). Write a pytest as evidence that encode_lot equals the 3 mill UUID encodings for mixed keys."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_lots.py",
                    "content": UUID_TEST,
                },
            },
            "observation": "Wrote tests/test_lots.py (16 lines).",
            "reflection": "Created a mixed-key regression that expects three uuid3 DNS hex keys. Run pytest to reproduce the uuid5 miss.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Plan: run pytest tests/test_lots.py as evidence whether uuid5 hex matches mill uuid3 DNS hex not SHA-1."
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
                "______ test_encode_lot_uuid3_dns_hex ______\n"
                "tests/test_lots.py:14: in test_encode_lot_uuid3_dns_hex\n"
                "    assert got == WANT, f\"got={sorted(got)} want={sorted(WANT)}\"\n"
                "E   AssertionError: got=['869b3cb1827c5a06a645d8f245412503', "
                "'9eb57b6f8441563ead1e5be259b91b4e', "
                "'dbe9c1b73c125d6abc8b0a1ba27b769c'] "
                "want=['c5489e9aa19832d0b21d00d7729a839d', "
                "'c7f03f6b138d3824b2d07f25215174bc', "
                "'c8f5d30845363809adb2da8cdf383e13']\n"
                "FAILED tests/test_lots.py::test_encode_lot_uuid3_dns_hex - AssertionError: got uuid5 hex\n"
                "1 failed in 0.05s"
            ),
            "reflection": "Test failed: uuid5 hex is still SHA-1, mill wants uuid3 MD5 hex. Re-read encode_lot and switch to uuid3 .hex.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Observation: pytest failed with got uuid5 hex want uuid3 hex (step 11). Re-read encode_lot for the uuid5 evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "murreuid/lots.py", "offset": 1, "limit": 12},
            },
            "observation": UUID_HEX,
            "reflection": "Confirmed line 6 still uses uuid5 SHA-1 hex. Patch uuid.uuid3(NAMESPACE_DNS, lot_key).hex.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Reflection: encode_lot must uuid3 DNS hex rather than uuid5 SHA-1 (step 12). Patch lots.py to uuid.uuid3(NAMESPACE_DNS, lot_key).hex as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "murreuid/lots.py",
                    "old_string": UUID_HEX.strip(),
                    "new_string": UUID_V3.strip(),
                },
            },
            "observation": "Edited murreuid/lots.py: encode_lot now uuid.uuid3(NAMESPACE_DNS, lot_key).hex so mill MD5 hex matches.",
            "reflection": "Patched uuid3 hex. Re-run pytest; all three mill UUID encodings should appear.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Observation: encode_lot now uuid3 DNS hex (step 13). Re-run pytest tests/test_lots.py as verification evidence."
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
            "reflection": "Verified 6 passed including test_encode_lot_uuid3_dns_hex. Open the MU-241 PR.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: pytest passed 6/6 after the uuid3 hex patch (step 14). Create the MU-241 PR via gh as evidence of the encode_lot fix."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/murrefen/murreuid-lots/pulls",
                    "raw_field": "title=MU-241: encode mill lots as uuid3 DNS hex so catalog keys match MD5 32-hex",
                },
            },
            "observation": (
                "{\n"
                '  "number": 361,\n'
                '  "html_url": "https://git.murrefen.internal/pkg/murreuid-lots/pull/361",\n'
                '  "state": "open"\n'
                "}"
            ),
            "reflection": "Opened PR 361. encode_lot matches all three mill UUID encodings. Live mill UUID census follow-up remains against the designed mill host.",
        },
    ]
    return {
        "id": ID1,
        "goal": (
            "MU-241 (murreuid-lots, Python 3.12 mill lot UUID helper + fixtures/lot-uuids.json; pytest): "
            "nightly mill UUID catalog misses /week36/lot.ndjson while the mill dest is "
            "c8f5d30845363809adb2da8cdf383e13 "
            "(keys /week36/lot.ndjson, week36/shift-a/lot.ndjson, WB 440.csv). "
            "Find why encode_lot emits uuid5 hyphens, add a mixed-key regression, and open a PR. Designed plant; not a live mill apply."
        ),
        "steps": steps,
        "outcome": (
            "encode_lot passed lot_key through uuid.uuid5 then str(), so mill keys were hyphenated SHA-1 and missed the uuid3 DNS hex catalog. "
            "A first patch that swapped in uuid5 .hex still failed test_encode_lot_uuid3_dns_hex (got 9eb57b6f8441563ead1e5be259b91b4e). "
            "encode_lot now calls uuid.uuid3(uuid.NAMESPACE_DNS, lot_key).hex. Verified by pytest 6 passed "
            "(tests/test_lots.py::test_encode_lot_uuid3_dns_hex). PR 361 opened. "
            "Live mill UUID copies remain a follow-up against the designed mill host."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.40,
            "uuid3_dns_hex_fix": 0.12,
            "mixed_key_uuid_test": 0.08,
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
            codebase_type="library / mill lot UUID (Python 3.12 uuid)",
            bug_class="schema mismatch: uuid.uuid5 DNS str() is hyphenated SHA-1; first fix used uuid5 .hex and still missed mill uuid3 MD5 hex",
            test_harness="pytest + aws s3api + jq",
            noise_steps={"429": 4, "502": 6},
            noise_recovery_steps={"429": 5, "502": 7},
            plan_change_step=8,
            debug_loop_steps=[9, 10, 11, 12, 13, 14],
            tags=[
                "uuid.uuid5",
                "uuid.uuid3",
                "NAMESPACE_DNS",
                "mill-uuid",
                "hyphen-hex",
                "md5-vs-sha1",
            ],
        ),
    }


def ep2() -> dict:
    """skuasec-pod: runAsNonRoot true without runAsUser; first fix uid 0."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: SK-72 reports mill-harvest CreateContainerConfigError. Search render_security and runAsNonRoot as evidence of a missing runAsUser."
            ),
            "plan": "1) search security renderer 2) read render_security 3) measure live deploy 4) fix 65532 5) regression 6) apply or hand off",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "runAsNonRoot|runAsUser|render_security|65532",
                    "path": ".",
                },
            },
            "observation": (
                "skuasec/pod.py:5:DEFAULT_RUN_AS_NON_ROOT = True\n"
                "skuasec/pod.py:10:        \"runAsNonRoot\": DEFAULT_RUN_AS_NON_ROOT,\n"
                "deploy/harvest.yaml:22:runAsNonRoot: true\n"
                "6 matches"
            ),
            "reflection": "Found runAsNonRoot true with no runAsUser. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: pod.py sets runAsNonRoot True with no runAsUser (step 1). Read the renderer as evidence of any numeric uid clamp."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "skuasec/pod.py", "offset": 1, "limit": 22},
            },
            "observation": SCC_BEFORE,
            "reflection": "Learned there is no numeric uid clamp. First plan: mill image USER is root so rebuild the image. Next measure the live Deployment.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: render_security emits runAsNonRoot without runAsUser (step 2). kubectl get the Deployment as evidence of live spec.template.spec.securityContext."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-skuaquay",
                    "namespace": "skuaquay",
                    "argv": [
                        "get",
                        "deploy",
                        "skuasec-harvest",
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
                ") occurred attempting to get Deployment.apps/skuasec-harvest"
            ),
            "reflection": "kind apiserver ingress returned a bad gateway before headers. Retry with a longer request timeout and write the object locally.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: kubectl get deploy returned 502 from the kind ingress (step 3). Retry --request-timeout=30s and write /tmp/skuasec-deploy.json as evidence."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-skuaquay",
                    "namespace": "skuaquay",
                    "argv": [
                        "get",
                        "deploy",
                        "skuasec-harvest",
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
                '  "metadata": {"name": "skuasec-harvest", "namespace": "skuaquay"},\n'
                '  "spec": {\n'
                '    "replicas": 1,\n'
                '    "template": {"spec": {"containers": [{"name": "harvest", "image": "skuasec-harvest:1.4", '
                '"securityContext": {"runAsNonRoot": true}}]}}\n'
                "  },\n"
                '  "status": {"readyReplicas": 0, "unavailableReplicas": 1, '
                '"conditions": [{"type": "ReplicaFailure", "status": "True", '
                '"message": "pods skuasec-harvest-7f9c CreateContainerConfigError: container has runAsNonRoot and image will run as root"}]}\n'
                "}\n"
                "wrote /tmp/skuasec-deploy.json"
            ),
            "reflection": "Measured live runAsNonRoot true with no runAsUser and CreateContainerConfigError. Next inspect the mill-harvest pod.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: live deploy has runAsNonRoot true, no runAsUser, and CreateContainerConfigError (step 4). kubectl get pod waiting as evidence whether the mill image USER is the miss."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-skuaquay",
                    "namespace": "skuaquay",
                    "argv": [
                        "get",
                        "pod",
                        "-l",
                        "app=skuasec-harvest",
                        "-o",
                        "json",
                    ],
                },
            },
            "observation": (
                "{\n"
                '  "items": [{\n'
                '    "metadata": {"name": "skuasec-harvest-7f9c"},\n'
                '    "status": {\n'
                '      "phase": "Pending",\n'
                '      "containerStatuses": [{\n'
                '        "name": "harvest",\n'
                '        "image": "skuasec-harvest:1.4",\n'
                '        "state": {"waiting": {"reason": "CreateContainerConfigError", '
                '"message": "container has runAsNonRoot and image will run as root"}}\n'
                "      }]\n"
                "    }\n"
                "  }]\n"
                "}\n"
                "found image USER root; node Ready"
            ),
            "reflection": "Found image USER root on a Ready node. This is not a missing mill node. Confirm the runAsUser numeric contract next.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: mill-harvest pod waits CreateContainerConfigError and image USER is root (step 5). Fetch security-context docs via gh as evidence of the numeric uid contract."
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
            "reflection": "GitHub returned a rate-limit with retry-after 7 while fetching security-context docs. Wait, then use the vendored docs/runasnonroot.md fixture.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry_after 7 (step 6). Sleep 8s, then read docs/runasnonroot.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/runasnonroot.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  runAsNonRoot true without runAsUser still uses the image USER (root here).\n"
                "2  kubelet then fails CreateContainerConfigError: image will run as root.\n"
                "3  runAsUser 0 is numeric but still root and fails mill gate plus runAsNonRoot.\n"
                "4  Durable: render_security must emit runAsNonRoot true and runAsUser 65532.\n"
                "5  Rebuilding the mill image USER does not set pod securityContext.runAsUser.\n"
                "6  Kind does not rewrite missing uids; the renderer must.\n"
            ),
            "reflection": "Verified missing runAsUser is the miss. Next join that with the saved Deployment.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: docs require runAsUser 65532 with runAsNonRoot (step 7). jq spec from the saved deploy as evidence of the live skew."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{ro:.spec.template.spec.containers[0].securityContext.runAsNonRoot,uid:.spec.template.spec.containers[0].securityContext.runAsUser,ready:.status.readyReplicas}",
                        "/tmp/skuasec-deploy.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "ro": true,\n'
                '  "uid": null,\n'
                '  "ready": 0\n'
                "}"
            ),
            "reflection": (
                "Plan change: live spec has runAsNonRoot true and runAsUser null while mill-harvest is CreateContainerConfigError. "
                "Abandon rebuilding mill images. Switching the edit target to render_security so runAsUser is canonical 65532."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the rebuild-image plan; runAsUser is missing (step 8). Refuse deleting the Deployment as evidence the object must stay."
            ),
            "tool_call": {
                "name": "refuse",
                "args": {
                    "action": "kubectl delete deploy/skuasec-harvest so a freshly created object picks runAsUser 65532",
                    "policy": "UID-MUTATE-04",
                    "incident": "SK-72",
                },
            },
            "observation": (
                "refused: UID-MUTATE-04 forbids deleting Deployment/skuasec-harvest to skip a runAsUser skew. "
                "Delete would drop in-flight mill harvest sidecars and can fail-open replica caps. "
                "Safe alternative: patch runAsUser to 65532 and keep replicas 1. found 0 waivers"
            ),
            "reflection": "Denied the delete. Next patch render_security; keep the Deployment object.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: delete is refused; edit target is securityContext (step 9). First patch: set runAsUser 0 as evidence root uid is numeric."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "skuasec/pod.py",
                    "old_string": SCC_BEFORE.strip(),
                    "new_string": SCC_UID0.strip(),
                },
            },
            "observation": "Edited skuasec/pod.py: DEFAULT_RUN_AS_USER is now 0 so the uid is numeric.",
            "reflection": "Wrote a uid-0 swap. Add a pytest that requires runAsNonRoot plus 65532.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: renderer now emits runAsUser 0 (step 10). Write a pytest as evidence that mill harvest uid is 65532 with runAsNonRoot."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_pod.py",
                    "content": SCC_TEST,
                },
            },
            "observation": "Wrote tests/test_pod.py (11 lines).",
            "reflection": "Created a non-root uid regression. Run pytest to reproduce the uid 0 miss.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Plan: run pytest tests/test_pod.py as evidence whether runAsUser 0 satisfies the non-root uid contract."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_pod.py -q --tb=short 2>&1 | tail -n 22"
                },
            },
            "observation": (
                "F\n"
                "=================================== FAILURES ===================================\n"
                "______________ test_run_as_non_root_has_numeric_uid ______________\n"
                "tests/test_pod.py:7: in test_run_as_non_root_has_numeric_uid\n"
                "    assert spec[\"runAsUser\"] == 65532, f\"got runAsUser={spec.get('runAsUser')}\"\n"
                "E   AssertionError: got runAsUser=0\n"
                "E   assert 0 == 65532\n"
                "FAILED tests/test_pod.py::test_run_as_non_root_has_numeric_uid - AssertionError: got runAsUser=0\n"
                "1 failed in 0.04s"
            ),
            "reflection": "Test failed: runAsUser is 0 and mill gate wants 65532. Re-read render_security and set DEFAULT_RUN_AS_USER 65532.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: pytest failed with got runAsUser=0 want 65532 (step 12). Re-read render_security for the DEFAULT_RUN_AS_USER evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "skuasec/pod.py", "offset": 1, "limit": 22},
            },
            "observation": SCC_UID0,
            "reflection": "Confirmed line 6 still uses runAsUser 0 against mill non-root uid. Patch DEFAULT_RUN_AS_USER to 65532.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: helper must emit runAsUser 65532 not 0 (step 13). Patch DEFAULT_RUN_AS_USER to 65532 as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "skuasec/pod.py",
                    "old_string": "DEFAULT_RUN_AS_USER = 0\n",
                    "new_string": "DEFAULT_RUN_AS_USER = 65532\n",
                },
            },
            "observation": "Edited skuasec/pod.py: DEFAULT_RUN_AS_USER is 65532.",
            "reflection": "Patched canonical non-root uid. Re-run pytest; mill harvest uid should now be 65532.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: helper now emits runAsUser 65532 (step 14). Re-run pytest tests/test_pod.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_pod.py tests/test_render.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                ".....\n"
                "5 passed in 0.07s"
            ),
            "reflection": "Verified 5 passed including test_run_as_non_root_has_numeric_uid. Check gate-cli before applying the Deployment.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: pytest passed 5/5 after the 65532 patch (step 15). Run gate-cli check apply as evidence whether prod Deployment mutation is allowed."
            ),
            "tool_call": {
                "name": "gate-cli",
                "args": {
                    "argv": [
                        "check",
                        "apply",
                        "--change",
                        "skuasec-nonroot-uid",
                        "--resource",
                        "deploy/skuasec-harvest",
                    ]
                },
            },
            "observation": (
                "gate-cli check apply --change skuasec-nonroot-uid\n"
                "status: REJECT\n"
                "policy: prod-batch-freeze\n"
                "ticket: SK-60\n"
                "until: 2026-09-16T00:00:00Z\n"
                "evidence: change mutates Deployment/skuasec-harvest (skuasec-harvest runAsUser)\n"
                "found 0 waivers"
            ),
            "reflection": "Measured REJECT under SK-60 freeze through 2026-09-16. Do not kubectl apply. Open a handoff issue attaching the 65532 fix.",
        },
        {
            "n": 17,
            "decision_basis": db(
                "Observation: gate-cli REJECT'd the Deployment apply under freeze SK-60 (step 16). Open a handoff issue as evidence the live uid is still missing."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "title": "SK-83: apply skuasec runAsUser 65532 after SK-60 freeze (blocks SK-72 close)",
                    "body": "render_security now emits runAsNonRoot true and runAsUser 65532; pytest 5 passed. Live Deployment still has no runAsUser. gate-cli freeze SK-60 until 2026-09-16. Do not kubectl delete the Deployment.",
                },
            },
            "observation": "https://git.skuaquay.internal/k8s/skuasec-pod/issues/83",
            "reflection": "Opened SK-83. Renderer is green; prod apply remains blocked. Handoff, not close.",
        },
    ]
    return {
        "id": ID2,
        "goal": (
            "SK-72 (skuasec-pod, Python 3.12 pod renderer + kind skuaquay; pytest + kubectl): "
            "skuasec-harvest is CreateContainerConfigError while the mill node is Ready. "
            "Find why runAsNonRoot true still starts as image root, fix the renderer, and apply or hand off. Designed plant; not a live cluster trace."
        ),
        "steps": steps,
        "outcome": (
            "render_security emitted runAsNonRoot true with no runAsUser, so kubelet treated mill harvest as image USER root. "
            "A first patch that set runAsUser 0 still failed test_run_as_non_root_has_numeric_uid (got runAsUser=0). "
            "The helper now emits runAsUser 65532; pytest 5 passed. "
            "Applying Deployment/skuasec-harvest remains blocked by gate-cli freeze SK-60; live spec still has no runAsUser. "
            "SK-83 opened. Overall: incomplete; prod apply unresolved."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "nonroot_uid_fix": 0.10,
            "canonical_uid_test": 0.08,
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
            codebase_type="CLI / Kubernetes pod renderer (Python 3.12)",
            bug_class="schema mismatch: runAsNonRoot true without runAsUser uses image USER root; first fix used runAsUser 0 instead of 65532",
            test_harness="pytest + kubectl + gate-cli",
            noise_steps={"502": 3, "429": 6},
            noise_recovery_steps={"502": 4, "429": 7},
            plan_change_step=8,
            debug_loop_steps=[10, 11, 12, 13, 14, 15],
            tags=[
                "runAsNonRoot",
                "runAsUser",
                "CreateContainerConfigError",
                "non-root-uid",
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
    return """# ACTF r36 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r36-uuid5-dns-vs-uuid3-murreuid-a4d81c`, `act-r36-runasnonroot-uid0-skuasec-b8e205` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`kubectl`/`gate-cli`/`aws`/`jq`/`refuse`). meta.round=36 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Never wrote outputs/raw/. Distinct from staged r10-r35 (r34 dir is an r32 gen.py stub with no batch; r24 os.path.commonprefix /bin vs /binaries / preStop sleep>grace, r32 os.path.join absolute / hostNetwork ClusterFirst, r33 quoteplus mill-space HMAC / cpu Quantity bare int cores, r35 urlsafe_b64decode padding / readOnlyRootFilesystem no emptyDir /tmp). Invented repos `git.murrefen.internal/pkg/murreuid-lots.git` and `git.skuaquay.internal/k8s/skuasec-pod.git`. Beads create failed (Dolt events id default); Linear RM-793 remains the rights tracker.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r36-uuid5-dns-vs-uuid3-murreuid-a4d81c | Python 3.12 mill lot UUID helper + lot-uuids fixtures / pytest + aws s3api + jq | schema mismatch: `uuid.uuid5` DNS `str()` is hyphenated SHA-1; first fix used uuid5 `.hex` and still missed mill uuid3 MD5 hex | success; 6/6; PR 361 | 0.58 |
| act-r36-runasnonroot-uid0-skuasec-b8e205 | Python 3.12 pod renderer / pytest + kubectl + gate-cli | schema mismatch: `runAsNonRoot` true without `runAsUser` uses image USER root; first fix used `runAsUser` 0 instead of 65532 | incomplete HIL/prod apply; SK-83; freeze SK-60 | 0.28 |

## Step counts, noise, plan change
- act-r36-uuid5-dns-vs-uuid3-murreuid-a4d81c: 15 steps. 429 at step 4 (`gh api` cpython uuid.rst, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/uuid3-dns.md`). 502 at step 6 (`aws s3api get-object` murrefen-specs lot-uuids ELB) -> recovery step 7 (`jq` committed `fixtures/lot-uuids.json`). Plan change at step 8: jq join shows want already uuid3 DNS hex and got is hyphenated uuid5; abandon rotating UUID namespace. Debug loop: 9 edit uuid5 `.hex` -> 10 write mixed-key pytest -> 11 FAIL got uuid5 hex -> 12 re-read encode_lot -> 13 uuid3 `.hex` patch -> 14 6 passed.
- act-r36-runasnonroot-uid0-skuasec-b8e205: 17 steps. 502 at step 3 (`kubectl get deploy` kind ingress) -> recovery step 4 (`--request-timeout=30s` writes /tmp/skuasec-deploy.json). 429 at step 6 (`gh api` kubernetes/website security-context.md, retry-after 7) -> recovery step 7 (read vendored `docs/runasnonroot.md`). Plan change at step 8: jq runAsNonRoot true vs runAsUser null while harvest CreateContainerConfigError; abandon rebuilding mill images. Debug loop: 10 edit runAsUser 0 -> 11 write 65532 pytest -> 12 FAIL got runAsUser=0 -> 13 re-read helper -> 14 65532 patch -> 15 5 passed. `refuse` at step 9 blocks `kubectl delete deploy`. gate-cli REJECT at 16; SK-83 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. uuid5-dns-vs-uuid3: 0.40+0.12+0.08-0.02=0.58. runasnonroot-uid0: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: `uuid.uuid5` plus `str()` is a real stdlib footgun (SHA-1 and hyphens); uuid5 `.hex` is the equally tempting hyphen-shaped wrong fix and the mixed-key test names the contract (mill catalog is uuid3 MD5 32-hex, including space mill lot `WB 440.csv`). `runAsNonRoot` without `runAsUser` is the usual silent CreateContainerConfigError on a root image; `runAsUser` 0 is numeric root and still fails mill gate 65532. gate-cli freeze plus refuse-delete is an honest apply block, not a silent skip. Weak: mill-inventory 502 fallback is availability (committed fixture is not a stale dest whose uuid3 hex disagrees with a second document); kubectl json dump is one object; no reviewer asking to keep uuid5 "so RFC-4122 hyphen form still joins mill HTTPS". Next densification: a 502 whose local lot-uuids fixture is stale (`want` uuid3 hex vs a second file still on hyphenated uuid5), or a reviewer asking to keep `runAsUser` 0 "so the mill harvest can bind privileged ports".

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
    batch = OUT / "batch-r36.jsonl"
    with batch.open("w", encoding="utf-8") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    notes_path = OUT / "NOTES-r36.md"
    notes_path.write_text(notes(), encoding="utf-8")
    errors, warnings, kinds, n = check_jsonl(
        batch, "batch-r36.jsonl", staging=FactoryStaging(enabled=True)
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
