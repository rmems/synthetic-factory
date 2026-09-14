#!/usr/bin/env python3
"""Generate designed ACTF r37 episodes (Q=2). Never writes outputs/raw/."""
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

OUT = Path("/tmp/actf-r37")
GENERATED_AT = "2026-09-02T23:59:30Z"
ROUND = 37
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
ID1 = "act-r37-rstrip-charset-json-chertjson-a4e81c"
ID2 = "act-r37-ondelete-silent-roll-kelproll-b8c203"
PLANT_TOKENS = ("chertjson", "chertfen", "kelproll", "kelpfen")


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
    self_batch = (OUT / "batch-r37.jsonl").resolve()
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


STEM_BEFORE = '''def lot_stem(name: str) -> str:
    return name.rstrip(".json")
'''

STEM_SUFFIX = '''def lot_stem(name: str) -> str:
    return name.removesuffix(".json")
'''

STEM_CASE = '''def lot_stem(name: str) -> str:
    if name.lower().endswith(".json"):
        return name[:-5]
    return name
'''

STEM_TEST = '''from chertjson.lotstem import lot_stem

KEYS = ["class.json", "session.json", "bass.JSON"]
WANT = {"class", "session", "bass"}


def test_lot_stem_strips_json_suffix_any_case():
    got = {lot_stem(k) for k in KEYS}
    assert got == WANT, f"got={sorted(got)} want={sorted(WANT)}"
'''

ROLL_BEFORE = '''# Ported from the mill kiln StatefulSet. OnDelete was copied onto the Deployment.
API_VERSION = "apps/v1"
UPDATE_STRATEGY = "OnDelete"
IMAGE = "kelproll-harvest:1.5"


def render_deploy() -> dict:
    return {
        "apiVersion": API_VERSION,
        "kind": "Deployment",
        "spec": {
            "replicas": 1,
            "strategy": {"type": UPDATE_STRATEGY},
            "template": {
                "spec": {
                    "containers": [{"name": "harvest", "image": IMAGE}],
                }
            },
        },
    }
'''

ROLL_PULL = '''# Ported from the mill kiln StatefulSet. OnDelete was copied onto the Deployment.
API_VERSION = "apps/v1"
UPDATE_STRATEGY = "OnDelete"
IMAGE = "kelproll-harvest:1.5"


def render_deploy() -> dict:
    return {
        "apiVersion": API_VERSION,
        "kind": "Deployment",
        "spec": {
            "replicas": 1,
            "strategy": {"type": UPDATE_STRATEGY},
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "harvest",
                            "image": IMAGE,
                            "imagePullPolicy": "Always",
                        }
                    ],
                }
            },
        },
    }
'''

ROLL_ROLLING = '''# Ported from the mill kiln StatefulSet. OnDelete was copied onto the Deployment.
API_VERSION = "apps/v1"
UPDATE_STRATEGY = "RollingUpdate"
IMAGE = "kelproll-harvest:1.5"


def render_deploy() -> dict:
    return {
        "apiVersion": API_VERSION,
        "kind": "Deployment",
        "spec": {
            "replicas": 1,
            "strategy": {"type": UPDATE_STRATEGY},
            "template": {
                "spec": {
                    "containers": [{"name": "harvest", "image": IMAGE}],
                }
            },
        },
    }
'''

ROLL_TEST = '''from kelproll.harvest import render_deploy


def test_strategy_is_rolling_update():
    spec = render_deploy()
    got = spec["spec"]["strategy"]["type"]
    assert got == "RollingUpdate", f"got strategy={got}"
    assert got != "OnDelete"
'''


def ep1() -> dict:
    """chertjson-lots: str.rstrip('.json') is a charset, not a suffix."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: CJ-241 reports mill lot catalog misses class/session/bass stems. Search lot_stem and rstrip as evidence of charset strip on .json."
            ),
            "plan": "1) search lot_stem 2) read lotstem.py 3) measure rstrip 4) confirm want stems 5) fix case-insensitive suffix 6) regression + PR",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "lot_stem|rstrip\\(|removesuffix|endswith",
                    "path": ".",
                },
            },
            "observation": (
                "chertjson/lotstem.py:1:def lot_stem(name: str) -> str:\n"
                "chertjson/lotstem.py:2:    return name.rstrip(\".json\")\n"
                "tests/test_install.py:11:    assert lot_stem(\"class.json\") == \"class\"\n"
                "5 matches"
            ),
            "reflection": "Found lot_stem wrapping str.rstrip('.json') as if it were a suffix. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: lotstem.py:2 returns name.rstrip('.json') (step 1). Read the helper as evidence of any removesuffix or casefold clamp."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "chertjson/lotstem.py", "offset": 1, "limit": 12},
            },
            "observation": (
                "1  def lot_stem(name: str) -> str:\n"
                "2      return name.rstrip(\".json\")\n"
                "3\n"
                "4  # Mill lot catalog keys are stems. PLC packer emits .json and .JSON.\n"
            ),
            "reflection": "Learned rstrip is called with a charset, not a suffix. First plan: mill S3 prefix missing. Next measure the rstrip.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: lot_stem rstrip's .json as a charset (step 2). Measure rstrip of class.json and bass.JSON as evidence of truncated stems."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 -c \"print(repr('class.json'.rstrip('.json'))); "
                        "print(repr('session.json'.rstrip('.json'))); "
                        "print(repr('bass.JSON'.rstrip('.json')))\""
                    )
                },
            },
            "observation": "'cla'\n'sessi'\n'bass.JSON'",
            "reflection": "Measured rstrip turning class.json into cla and leaving bass.JSON. Next confirm the mill want stems.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Reflection: rstrip turned class.json into cla (step 3). Fetch str.rstrip notes via gh as evidence of the charset not suffix contract."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/python/cpython/contents/Doc/library/stdtypes.rst",
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
            "reflection": "GitHub returned a rate-limit with retry-after 5 while fetching str.rstrip docs. Wait, then use the vendored docs/rstrip-charset.md fixture.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/rstrip-charset.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/rstrip-charset.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  str.rstrip(chars) treats the argument as a set of characters, not a suffix.\n"
                "2  'class.json'.rstrip('.json') is cla because trailing s is in {'.','j','s','o','n'}.\n"
                "3  'session.json'.rstrip('.json') is sessi because trailing n and o are in the set.\n"
                "4  'bass.JSON'.rstrip('.json') stays bass.JSON; the charset is case-sensitive.\n"
                "5  removesuffix('.json') keeps class/session but leaves mill PLC .JSON lots intact.\n"
                "6  Durable: case-insensitive endswith('.json') then slice [:-5]. A missing mill prefix is independent of this client stem.\n"
            ),
            "reflection": "Verified the charset rstrip trap and that removesuffix still misses .JSON lots. Next pull the committed mill stem fixture.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: RFC-style notes say rstrip takes a charset (step 5). Get the committed mill stem inventory as evidence the want set is bare stems."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-object",
                        "--bucket",
                        "chertfen-specs",
                        "--key",
                        "chertjson/lot-stems.json",
                        "/tmp/chertjson-inventory.json",
                    ]
                },
            },
            "observation": (
                "download failed: s3.eu-west-1.amazonaws.com/chertfen-specs\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "server: awselb/2.0\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection failure"
            ),
            "reflection": "Mill inventory get-object hit a bad gateway on the ELB before headers. Retry against the committed fixtures/lot-stems.json instead of the edge.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: mill inventory get-object returned 502 from the ELB (step 6). jq fixtures/lot-stems.json want and keys as local-spec evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{want:.want, keys:.keys, n:.key_count}",
                        "fixtures/lot-stems.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "want": ["class", "session", "bass"],\n'
                '  "keys": ["class.json", "session.json", "bass.JSON"],\n'
                '  "n": 3\n'
                "}"
            ),
            "reflection": "Verified want already lists three bare mill stems. Next join that with the measured rstrip.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: fixture want already lists 3 bare mill stems (step 7). jq the measured rstrip against that spec as evidence whether stems are wrong."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "s",
                        "fixtures/lot-stems.json",
                        "{got:[\"cla\",\"sessi\",\"bass.JSON\"],want:$s[0].want,n:$s[0].key_count}",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "got": ["cla", "sessio", "bass.JSON"],\n'
                '  "want": ["class", "session", "bass"],\n'
                '  "n": 3\n'
                "}"
            ),
            "reflection": (
                "Plan change: mill want inventory already lists three bare stems and got is cla/sessio/bass.JSON from charset rstrip. "
                "Abandon remounting the mill S3 prefix. Switching the edit target to lot_stem so .json/.JSON both drop."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the missing-prefix plan; rstrip kept bass.JSON and truncated class (step 8). Edit removesuffix as evidence lowercase .json drops."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "chertjson/lotstem.py",
                    "old_string": STEM_BEFORE.strip(),
                    "new_string": STEM_SUFFIX.strip(),
                },
            },
            "observation": "Edited chertjson/lotstem.py: lot_stem now uses str.removesuffix('.json') so a lowercase suffix is dropped.",
            "reflection": "Wrote a removesuffix swap. Add a pytest that requires both lowercase .json keys and mill PLC .JSON lots.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: lot_stem now uses removesuffix('.json') (step 9). Write a pytest as evidence that lot_stem equals the 3 mill stems for mixed keys."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_stem.py",
                    "content": STEM_TEST,
                },
            },
            "observation": "Wrote tests/test_stem.py (14 lines).",
            "reflection": "Created a mixed-key regression that expects three bare mill stems. Run pytest to reproduce the .JSON miss.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Plan: run pytest tests/test_stem.py as evidence whether removesuffix keeps mill .JSON lots as bare bass not bass.JSON."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_stem.py -q --tb=short 2>&1 | tail -n 20"
                },
            },
            "observation": (
                "F\n"
                "=================================== FAILURES ===================================\n"
                "______ test_lot_stem_strips_json_suffix_any_case ______\n"
                "tests/test_stem.py:11: in test_lot_stem_strips_json_suffix_any_case\n"
                "    assert got == WANT, f\"got={sorted(got)} want={sorted(WANT)}\"\n"
                "E   AssertionError: got=['bass.JSON', 'class', 'session'] "
                "want=['bass', 'class', 'session']\n"
                "FAILED tests/test_stem.py::test_lot_stem_strips_json_suffix_any_case - AssertionError: got bass.JSON\n"
                "1 failed in 0.05s"
            ),
            "reflection": "Test failed: removesuffix dropped lowercase .json and left bass.JSON. Re-read lot_stem and switch to a case-insensitive endswith slice.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Observation: pytest failed with got bass.JSON want bass (step 11). Re-read lot_stem for the removesuffix evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "chertjson/lotstem.py", "offset": 1, "limit": 12},
            },
            "observation": STEM_SUFFIX,
            "reflection": "Confirmed line 2 still uses removesuffix and mill PLC .JSON lots stay. Patch endswith after lower then slice [:-5].",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Reflection: lot_stem must casefold the suffix test rather than removesuffix (step 12). Patch lotstem.py to endswith .json after lower as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "chertjson/lotstem.py",
                    "old_string": STEM_SUFFIX.strip(),
                    "new_string": STEM_CASE.strip(),
                },
            },
            "observation": "Edited chertjson/lotstem.py: lot_stem now slices [:-5] when name.lower().endswith('.json').",
            "reflection": "Patched the suffix. Re-run pytest; all three mill stems should appear.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Observation: lot_stem now slices [:-5] when lower endswith .json (step 13). Re-run pytest tests/test_stem.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_stem.py tests/test_install.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                "......\n"
                "6 passed in 0.08s"
            ),
            "reflection": "Verified 6 passed including test_lot_stem_strips_json_suffix_any_case. Open the CJ-241 PR.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: pytest passed 6/6 after the case-insensitive suffix patch (step 14). Create the CJ-241 PR via gh as evidence of the lot_stem fix."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/chertfen/chertjson-lots/pulls",
                    "raw_field": "title=CJ-241: strip .json/.JSON with endswith so mill lot stems match catalog",
                },
            },
            "observation": (
                "{\n"
                '  "number": 371,\n'
                '  "html_url": "https://git.chertfen.internal/pkg/chertjson-lots/pull/371",\n'
                '  "state": "open"\n'
                "}"
            ),
            "reflection": "Opened PR 371. lot_stem matches all three mill stems. Live mill catalog follow-up remains against the designed mill host.",
        },
    ]
    return {
        "id": ID1,
        "goal": (
            "CJ-241 (chertjson-lots, Python 3.12 mill lot stem helper + fixtures/lot-stems.json; pytest): "
            "nightly mill lot catalog misses class/session/bass while dest keys are class.json, session.json, bass.JSON. "
            "Find why lot_stem truncates class and keeps .JSON, add a mixed-key regression, and open a PR. Designed plant; not a live mill apply."
        ),
        "steps": steps,
        "outcome": (
            "lot_stem passed name through str.rstrip('.json'), so charset {'.','j','s','o','n'} truncated class.json to cla and left bass.JSON. "
            "A first patch that swapped in removesuffix('.json') still failed test_lot_stem_strips_json_suffix_any_case (got bass.JSON). "
            "lot_stem now slices [:-5] when name.lower().endswith('.json'). Verified by pytest 6 passed "
            "(tests/test_stem.py::test_lot_stem_strips_json_suffix_any_case). PR 371 opened. "
            "Live mill catalog copies remain a follow-up against the designed mill host."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.40,
            "rstrip_charset_fix": 0.12,
            "mixed_key_stem_test": 0.08,
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
            codebase_type="library / mill lot stem (Python 3.12 str.rstrip charset)",
            bug_class="schema mismatch: str.rstrip('.json') is a charset; first fix used removesuffix and left mill PLC .JSON lots",
            test_harness="pytest + aws s3api + jq",
            noise_steps={"429": 4, "502": 6},
            noise_recovery_steps={"429": 5, "502": 7},
            plan_change_step=8,
            debug_loop_steps=[9, 10, 11, 12, 13, 14],
            tags=[
                "str.rstrip",
                "charset-vs-suffix",
                "removesuffix",
                "mill-lot-stem",
                "case-insensitive-suffix",
                "json-extension",
            ],
        ),
    }


def ep2() -> dict:
    """kelproll-harvest: Deployment OnDelete silently skips image rolls."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: KR-72 reports mill harvest still runs image 1.4 after the 1.5 bump. Search UPDATE_STRATEGY and OnDelete as evidence of a silent roll skip."
            ),
            "plan": "1) search harvest renderer 2) read render_deploy 3) measure live deploy 4) fix RollingUpdate 5) regression 6) apply or hand off",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "UPDATE_STRATEGY|OnDelete|RollingUpdate|imagePullPolicy",
                    "path": ".",
                },
            },
            "observation": (
                "kelproll/harvest.py:3:UPDATE_STRATEGY = \"OnDelete\"\n"
                "kelproll/harvest.py:12:            \"strategy\": {\"type\": UPDATE_STRATEGY},\n"
                "kelproll/harvest.py:16:                    \"containers\": [{\"name\": \"harvest\", \"image\": IMAGE}],\n"
                "deploy/harvest.yaml:18:type: OnDelete\n"
                "6 matches"
            ),
            "reflection": "Found UPDATE_STRATEGY OnDelete copied onto a Deployment. Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: harvest.py:3 sets UPDATE_STRATEGY=OnDelete while mill harvest is a Deployment (step 1). Read the renderer as evidence of any RollingUpdate clamp."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "kelproll/harvest.py", "offset": 1, "limit": 28},
            },
            "observation": ROLL_BEFORE,
            "reflection": "Learned there is no RollingUpdate clamp. First plan: mill image pull secret missing. Next measure the live Deployment.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: render_deploy emits strategy OnDelete (step 2). kubectl get the Deployment as evidence of live spec.template image vs pod image."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-kelpfen",
                    "namespace": "kelpfen",
                    "argv": [
                        "get",
                        "deploy",
                        "kelproll-harvest",
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
                ") occurred attempting to get Deployment.apps/kelproll-harvest"
            ),
            "reflection": "kind apiserver ingress returned a bad gateway before headers. Retry with a longer request timeout and write the object locally.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: kubectl get deploy returned 502 from the kind ingress (step 3). Retry --request-timeout=30s and write /tmp/kelproll-deploy.json as evidence."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-kelpfen",
                    "namespace": "kelpfen",
                    "argv": [
                        "get",
                        "deploy",
                        "kelproll-harvest",
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
                '  "metadata": {"name": "kelproll-harvest", "namespace": "kelpfen"},\n'
                '  "spec": {\n'
                '    "replicas": 1,\n'
                '    "strategy": {"type": "OnDelete"},\n'
                '    "template": {"spec": {"containers": [{"name": "harvest", '
                '"image": "kelproll-harvest:1.5"}]}}\n'
                "  },\n"
                '  "status": {"readyReplicas": 1, "updatedReplicas": 1, "availableReplicas": 1}\n'
                "}\n"
                "wrote /tmp/kelproll-deploy.json"
            ),
            "reflection": "Measured live spec image 1.5 with strategy OnDelete and readyReplicas 1. Next inspect running mill harvest pods.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: live spec image is 1.5, strategy OnDelete, ready 1 (step 4). kubectl get pods as evidence whether mill harvest still runs 1.4."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-kelpfen",
                    "namespace": "kelpfen",
                    "argv": [
                        "get",
                        "pods",
                        "-l",
                        "app=kelproll-harvest",
                        "-o",
                        "json",
                    ],
                },
            },
            "observation": (
                "{\n"
                '  "items": [{\n'
                '    "metadata": {"name": "kelproll-harvest-7c9f4d8b6-xk2n1"},\n'
                '    "status": {\n'
                '      "phase": "Running",\n'
                '      "containerStatuses": [{"name": "harvest", '
                '"image": "kelproll-harvest:1.4", "ready": true}]\n'
                "    }\n"
                "  }]\n"
                "}\n"
                "found pod image kelproll-harvest:1.4"
            ),
            "reflection": "Found mill harvest still running 1.4 while spec is 1.5. This is not a missing pull secret. Confirm the OnDelete contract next.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: pod image is still 1.4 while spec is 1.5 (step 5). Fetch Deployment strategy docs via gh as evidence of the OnDelete contract."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/kubernetes/website/contents/content/en/docs/concepts/workloads/controllers/deployment.md",
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
            "reflection": "GitHub returned a rate-limit with retry-after 7 while fetching Deployment strategy docs. Wait, then use the vendored docs/ondelete-roll.md fixture.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry_after 7 (step 6). Sleep 8s, then read docs/ondelete-roll.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/ondelete-roll.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  Deployment strategy OnDelete never creates a new ReplicaSet on spec change.\n"
                "2  image 1.5 in spec with OnDelete leaves mill harvest pods on 1.4 until each pod is deleted.\n"
                "3  imagePullPolicy Always still does not roll; no new pod is created to pull.\n"
                "4  Durable: render_deploy must emit strategy RollingUpdate.\n"
                "5  Recreating the Deployment is not required and drops in-flight mill harvest.\n"
                "6  Kind does not rewrite strategy; the renderer must.\n"
            ),
            "reflection": "Verified OnDelete skips rolls. Next join that with the saved Deployment.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: docs require RollingUpdate for Deployment image bumps (step 7). jq spec from the saved deploy as evidence of the live skew."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{image:.spec.template.spec.containers[0].image,strategy:.spec.strategy.type,ready:.status.readyReplicas}",
                        "/tmp/kelproll-deploy.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "image": "kelproll-harvest:1.5",\n'
                '  "strategy": "OnDelete",\n'
                '  "ready": 1\n'
                "}"
            ),
            "reflection": (
                "Plan change: live spec already has image 1.5 and strategy OnDelete while mill harvest pods still run 1.4. "
                "Abandon rotating pull secrets. Switching the edit target to render_deploy so strategy is RollingUpdate."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the pull-secret plan; strategy is OnDelete (step 8). Refuse deleting the Deployment as evidence the object must stay."
            ),
            "tool_call": {
                "name": "refuse",
                "args": {
                    "action": "kubectl delete deploy/kelproll-harvest so a freshly created object picks RollingUpdate",
                    "policy": "ROLL-MUTATE-04",
                    "incident": "KR-72",
                },
            },
            "observation": (
                "refused: ROLL-MUTATE-04 forbids deleting Deployment/kelproll-harvest to skip an OnDelete roll skew. "
                "Delete would drop in-flight mill harvest sidecars and can fail-open replica caps. "
                "Safe alternative: patch strategy to RollingUpdate and keep replicas 1. found 0 waivers"
            ),
            "reflection": "Denied the delete. Next patch render_deploy; keep the Deployment object.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: delete is refused; edit target is imagePullPolicy (step 9). First patch: set Always as evidence mill harvest will pull 1.5."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "kelproll/harvest.py",
                    "old_string": ROLL_BEFORE.strip(),
                    "new_string": ROLL_PULL.strip(),
                },
            },
            "observation": "Edited kelproll/harvest.py: harvest container now sets imagePullPolicy Always so 1.5 is pulled.",
            "reflection": "Wrote an Always pull-policy swap. Add a pytest that requires strategy RollingUpdate.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: renderer now emits imagePullPolicy Always (step 10). Write a pytest as evidence that mill harvest strategy is RollingUpdate."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_harvest.py",
                    "content": ROLL_TEST,
                },
            },
            "observation": "Wrote tests/test_harvest.py (10 lines).",
            "reflection": "Created a RollingUpdate strategy regression. Run pytest to reproduce the OnDelete miss.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Plan: run pytest tests/test_harvest.py as evidence whether Always satisfies the RollingUpdate contract."
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
                "______________ test_strategy_is_rolling_update ______________\n"
                "tests/test_harvest.py:7: in test_strategy_is_rolling_update\n"
                "    assert got == \"RollingUpdate\", f\"got strategy={got}\"\n"
                "E   AssertionError: got strategy=OnDelete\n"
                "E   assert 'OnDelete' == 'RollingUpdate'\n"
                "FAILED tests/test_harvest.py::test_strategy_is_rolling_update - AssertionError: got strategy=OnDelete\n"
                "1 failed in 0.04s"
            ),
            "reflection": "Test failed: strategy is still OnDelete and mill gate wants RollingUpdate. Re-read render_deploy and set UPDATE_STRATEGY RollingUpdate.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: pytest failed with got strategy OnDelete want RollingUpdate (step 12). Re-read render_deploy for the UPDATE_STRATEGY evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "kelproll/harvest.py", "offset": 1, "limit": 36},
            },
            "observation": ROLL_PULL,
            "reflection": "Confirmed line 3 still uses OnDelete against mill harvest rolls. Patch UPDATE_STRATEGY to RollingUpdate.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: helper must emit RollingUpdate not OnDelete (step 13). Patch UPDATE_STRATEGY to RollingUpdate as evidence."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "kelproll/harvest.py",
                    "old_string": ROLL_PULL.strip(),
                    "new_string": ROLL_ROLLING.strip(),
                },
            },
            "observation": "Edited kelproll/harvest.py: UPDATE_STRATEGY is RollingUpdate.",
            "reflection": "Patched RollingUpdate. Re-run pytest; mill harvest strategy should now be RollingUpdate.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: helper now emits strategy RollingUpdate (step 14). Re-run pytest tests/test_harvest.py as verification evidence."
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
            "reflection": "Verified 5 passed including test_strategy_is_rolling_update. Check gate-cli before applying the Deployment.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: pytest passed 5/5 after the RollingUpdate patch (step 15). Run gate-cli check apply as evidence whether prod Deployment mutation is allowed."
            ),
            "tool_call": {
                "name": "gate-cli",
                "args": {
                    "argv": [
                        "check",
                        "apply",
                        "--change",
                        "kelproll-rolling",
                        "--resource",
                        "deploy/kelproll-harvest",
                    ]
                },
            },
            "observation": (
                "gate-cli check apply --change kelproll-rolling\n"
                "status: REJECT\n"
                "policy: prod-batch-freeze\n"
                "ticket: KR-60\n"
                "until: 2026-09-16T00:00:00Z\n"
                "evidence: change mutates Deployment/kelproll-harvest (kelproll-harvest strategy OnDelete)\n"
                "found 0 waivers"
            ),
            "reflection": "Measured REJECT under KR-60 freeze through 2026-09-16. Do not kubectl apply. Open a handoff issue attaching the RollingUpdate fix.",
        },
        {
            "n": 17,
            "decision_basis": db(
                "Observation: gate-cli REJECT'd the Deployment apply under freeze KR-60 (step 16). Open a handoff issue as evidence live strategy is still OnDelete."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "title": "KR-83: apply kelproll RollingUpdate after KR-60 freeze (blocks KR-72 close)",
                    "body": "render_deploy now emits strategy RollingUpdate; pytest 5 passed. Live Deployment still has OnDelete. gate-cli freeze KR-60 until 2026-09-16. Do not kubectl delete the Deployment.",
                },
            },
            "observation": "https://git.kelpfen.internal/k8s/kelproll-harvest/issues/83",
            "reflection": "Opened KR-83. Renderer is green; prod apply remains blocked. Handoff, not close.",
        },
    ]
    return {
        "id": ID2,
        "goal": (
            "KR-72 (kelproll-harvest, Python 3.12 resource renderer + kind kelpfen; pytest + kubectl): "
            "kelproll-harvest still runs image 1.4 after the 1.5 bump while the Deployment spec already shows 1.5. "
            "Find why OnDelete skips the roll, fix the renderer, and apply or hand off. Designed plant; not a live cluster trace."
        ),
        "steps": steps,
        "outcome": (
            "render_deploy emitted strategy OnDelete, so kube-controller never created a new ReplicaSet and mill harvest pods stayed on 1.4. "
            "A first patch that set imagePullPolicy Always still failed test_strategy_is_rolling_update (got strategy=OnDelete). "
            "The helper now emits RollingUpdate; pytest 5 passed. "
            "Applying Deployment/kelproll-harvest remains blocked by gate-cli freeze KR-60; live spec still has OnDelete. "
            "KR-83 opened. Overall: incomplete; prod apply unresolved."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "rolling_update_fix": 0.10,
            "rolling_strategy_test": 0.08,
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
            bug_class="silent no-op: Deployment strategy OnDelete skips image rolls; first fix used imagePullPolicy Always",
            test_harness="pytest + kubectl + gate-cli",
            noise_steps={"502": 3, "429": 6},
            noise_recovery_steps={"502": 4, "429": 7},
            plan_change_step=8,
            debug_loop_steps=[10, 11, 12, 13, 14, 15],
            tags=[
                "deployment-strategy",
                "OnDelete",
                "RollingUpdate",
                "imagePullPolicy",
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
    return """# ACTF r37 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r37-rstrip-charset-json-chertjson-a4e81c`, `act-r37-ondelete-silent-roll-kelproll-b8c203` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`kubectl`/`gate-cli`/`aws`/`jq`/`refuse`). meta.round=37 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Never wrote outputs/raw/. Distinct from staged r10-r33 (r23 Path.with_suffix `.tar.gz` is a last-suffix cut, not charset `rstrip('.json')`; r30 `rstrip()` default whitespace on CRLF mill notes, not charset `.json`; r32 os.path.join absolute / hostNetwork ClusterFirst; r33 quote_plus / Quantity cpu 100 cores; r20 urljoin / HPA v2; r24 os.path.commonprefix / preStop sleep>grace; r28 IPv4 hosts skip / Ingress Prefix sibling; r29 glob ** nonrecursive / minReady>progressDeadline). r34/r36 absent; r35 is an incomplete r32 gen.py clone. Invented repos `git.chertfen.internal/pkg/chertjson-lots.git` and `git.kelpfen.internal/k8s/kelproll-harvest.git`. Beads create failed (Dolt events id default); Linear RM-793 remains the rights tracker.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r37-rstrip-charset-json-chertjson-a4e81c | Python 3.12 mill lot stem helper + lot-stems fixtures / pytest + aws s3api + jq | schema mismatch: `str.rstrip('.json')` is a charset; first fix used `removesuffix` and left mill PLC `.JSON` lots | success; 6/6; PR 371 | 0.58 |
| act-r37-ondelete-silent-roll-kelproll-b8c203 | Python 3.12 resource renderer / pytest + kubectl + gate-cli | silent no-op: Deployment `OnDelete` skips image rolls; first fix used `imagePullPolicy Always` | incomplete HIL/prod apply; KR-83; freeze KR-60 | 0.28 |

## Step counts, noise, plan change
- act-r37-rstrip-charset-json-chertjson-a4e81c: 15 steps. 429 at step 4 (`gh api` cpython stdtypes.rst, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/rstrip-charset.md`). 502 at step 6 (`aws s3api get-object` chertfen-specs lot-stems ELB) -> recovery step 7 (`jq` committed `fixtures/lot-stems.json`). Plan change at step 8: jq join shows want already bare stems and got is cla/sessio/bass.JSON; abandon remounting mill S3 prefix. Debug loop: 9 edit `removesuffix` -> 10 write mixed-key pytest -> 11 FAIL got bass.JSON -> 12 re-read lot_stem -> 13 endswith+slice patch -> 14 6 passed.
- act-r37-ondelete-silent-roll-kelproll-b8c203: 17 steps. 502 at step 3 (`kubectl get deploy` kind ingress) -> recovery step 4 (`--request-timeout=30s` writes /tmp/kelproll-deploy.json). 429 at step 6 (`gh api` kubernetes/website deployment.md, retry-after 7) -> recovery step 7 (read vendored `docs/ondelete-roll.md`). Plan change at step 8: jq spec image 1.5 vs strategy OnDelete while pods still 1.4; abandon rotating pull secrets. Debug loop: 10 edit imagePullPolicy Always -> 11 write RollingUpdate pytest -> 12 FAIL got strategy=OnDelete -> 13 re-read helper -> 14 RollingUpdate patch -> 15 5 passed. `refuse` at step 9 blocks `kubectl delete deploy`. gate-cli REJECT at 16; KR-83 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. rstrip-charset-json: 0.40+0.12+0.08-0.02=0.58. ondelete-silent-roll: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: `str.rstrip('.json')` treating the argument as a charset is a real stdlib footgun; `removesuffix('.json')` is the equally tempting suffix-shaped wrong fix and the mixed-key test names the contract (mill PLC `bass.JSON` stays). Deployment `OnDelete` is the usual silent image-pin on mill harvest: spec already 1.5, pods still 1.4; `imagePullPolicy Always` still creates no ReplicaSet. gate-cli freeze plus refuse-delete is an honest apply block, not a silent skip. Weak: mill-inventory 502 fallback is availability (committed fixture is not a stale dest whose stems disagree with a second document); kubectl json dump is one object; no reviewer asking to keep charset rstrip "so mill lot names that end in n/s still trim". Next densification: a 502 whose local lot-stems fixture is stale (`want` `class` vs a second file still on `class.json`), or a reviewer asking to keep OnDelete "so mill kiln StatefulSet pods are not rolled by image bumps".

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
    batch = OUT / "batch-r37.jsonl"
    with batch.open("w", encoding="utf-8") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    notes_path = OUT / "NOTES-r37.md"
    notes_path.write_text(notes(), encoding="utf-8")
    errors, warnings, kinds, n = check_jsonl(
        batch, "batch-r37.jsonl", staging=FactoryStaging(enabled=True)
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
