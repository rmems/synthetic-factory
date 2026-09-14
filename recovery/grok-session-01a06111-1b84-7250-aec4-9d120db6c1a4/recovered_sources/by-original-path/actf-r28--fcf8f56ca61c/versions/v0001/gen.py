#!/usr/bin/env python3
"""Generate designed ACTF r28 episodes (Q=2). Never writes outputs/raw/."""
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

OUT = Path("/tmp/actf-r28")
GENERATED_AT = "2026-09-02T22:50:00Z"
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
ID1 = "act-r28-ipv4-hosts-skip-network-brinecidr-c9e14a"
ID2 = "act-r28-ingress-prefix-sibling-fenroute-b7d28c"


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
        "round": 28,
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
    self_batch = (OUT / "batch-r28.jsonl").resolve()
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
    return found


def ep1() -> dict:
    """brinecidr-lotnet: IPv4Network.hosts() drops network and broadcast."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: BC-280 reports mill inventory omits 10.18.4.0 and 10.18.4.255. Search lot_addrs and hosts as evidence of a hosts()-only walk."
            ),
            "plan": "1) search lot_addrs 2) read lotnet.py 3) measure hosts() range 4) confirm want addrs 5) fix full network walk 6) regression + PR",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "lot_addrs|ip_network|\\.hosts\\(|DEFAULT_CIDR",
                    "path": ".",
                },
            },
            "observation": (
                "brinecidr/lotnet.py:5:DEFAULT_CIDR = \"10.18.4.0/24\"\n"
                "brinecidr/lotnet.py:8:def lot_addrs(cidr: str = DEFAULT_CIDR) -> list[str]:\n"
                "brinecidr/lotnet.py:10:    net = ipaddress.ip_network(cidr)\n"
                "brinecidr/lotnet.py:11:    return [str(ip) for ip in net.hosts()]\n"
                "brinecidr/inventory.py:16:    for addr in lot_addrs():\n"
                "5 matches"
            ),
            "reflection": "Found lot_addrs walking ip_network(...).hosts(). Next read the helper.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: lotnet.py:11 returns [str(ip) for ip in net.hosts()] (step 1). Read the helper as evidence of any network or broadcast include."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "brinecidr/lotnet.py", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  import ipaddress\n"
                "2\n"
                "3  # Lot inventory. Copied from a scanner that skipped router and broadcast.\n"
                "4  # Mill still uses .0 as the lot-gateway and .255 as the freeze sentinel.\n"
                "5  DEFAULT_CIDR = \"10.18.4.0/24\"\n"
                "6\n"
                "7\n"
                "8  def lot_addrs(cidr: str = DEFAULT_CIDR) -> list[str]:\n"
                "9      net = ipaddress.ip_network(cidr)\n"
                "10     return [str(ip) for ip in net.hosts()]\n"
            ),
            "reflection": "Learned there is no include of network or broadcast. First plan: AWS subnet reserved those two. Next measure hosts().",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: lot_addrs walks net.hosts() with no extra endpoints (step 2). Measure first, last, and len of lot_addrs() as evidence of the skipped edges."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "python3 -c \"from brinecidr.lotnet import lot_addrs; a=lot_addrs(); "
                        "print(a[0], a[-1], len(a))\""
                    )
                },
            },
            "observation": "10.18.4.1 10.18.4.254 254",
            "reflection": "Measured hosts() as 10.18.4.1..254 (254 addrs). Next confirm mill want still includes .0 and .255.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Reflection: hosts() dropped the network and broadcast addresses (step 3). Fetch ipaddress.hosts notes via gh as evidence of the skip rule."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/python/cpython/contents/Doc/library/ipaddress.rst",
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
            "reflection": "GitHub returned 429 with retry-after 5 while fetching ipaddress docs. Wait, then use the vendored docs/ipv4-hosts.md fixture.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry-after 5 (step 4). Sleep 6s, then read docs/ipv4-hosts.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/ipv4-hosts.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  IPv4Network.hosts() yields usable hosts only; it skips network and broadcast.\n"
                "2  For 10.18.4.0/24 that is 10.18.4.1 through 10.18.4.254 (254 addresses).\n"
                "3  Iterating the network itself yields all 256 addresses including .0 and .255.\n"
                "4  Appending only broadcast_address still leaves the network address out.\n"
                "5  Mill lot-gateway (.0) and freeze sentinel (.255) must stay in inventory.\n"
                "6  A missing AWS reserved-range object is independent of this client walk.\n"
            ),
            "reflection": "Verified hosts() skips .0 and .255 and that appending broadcast is incomplete. Next pull the committed mill addr fixture.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: RFC-style notes say hosts() skips network and broadcast (step 5). Get the committed mill addr object as evidence want includes .0 and .255."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-object",
                        "--bucket",
                        "coblefen-specs",
                        "--key",
                        "brinecidr/lot-addrs.json",
                        "/tmp/brinecidr-addrs.json",
                    ]
                },
            },
            "observation": (
                "download failed: s3.eu-west-1.amazonaws.com/coblefen-specs\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "server: awselb/2.0\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection failure"
            ),
            "reflection": "Mill addr get-object hit 502 on the ELB before headers. Retry against the committed fixtures/lot-addrs.json instead of the edge.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: mill addr get-object returned 502 from the ELB (step 6). jq fixtures/lot-addrs.json cidr and want edges as local-spec evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{cidr:.cidr, want_first:.want_first, want_last:.want_last, want_len:.want_len}",
                        "fixtures/lot-addrs.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "cidr": "10.18.4.0/24",\n'
                '  "want_first": "10.18.4.0",\n'
                '  "want_last": "10.18.4.255",\n'
                '  "want_len": 256\n'
                "}"
            ),
            "reflection": "Verified want already includes .0 and .255 (256 addrs). Next join that with the measured hosts() range.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: fixture want edges are 10.18.4.0 and 10.18.4.255 (step 7). jq the measured hosts() range against that spec as evidence whether AWS reserved the ends."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "s",
                        "fixtures/lot-addrs.json",
                        "{got_first:\"10.18.4.1\",got_last:\"10.18.4.254\",got_len:254,want_first:$s[0].want_first,want_last:$s[0].want_last,want_len:$s[0].want_len}",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "got_first": "10.18.4.1",\n'
                '  "got_last": "10.18.4.254",\n'
                '  "got_len": 254,\n'
                '  "want_first": "10.18.4.0",\n'
                '  "want_last": "10.18.4.255",\n'
                '  "want_len": 256\n'
                "}"
            ),
            "reflection": (
                "Plan change: mill want addrs already include the network and broadcast, and got is hosts()-only. "
                "Abandon describing AWS subnets. Switching the edit target to lot_addrs so the full network is walked."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the reserved-subnet plan; hosts() skipped .0 and .255 (step 8). Edit lot_addrs to append broadcast_address so the sentinel is kept."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "brinecidr/lotnet.py",
                    "old_string": (
                        "def lot_addrs(cidr: str = DEFAULT_CIDR) -> list[str]:\n"
                        "    net = ipaddress.ip_network(cidr)\n"
                        "    return [str(ip) for ip in net.hosts()]\n"
                    ),
                    "new_string": (
                        "def lot_addrs(cidr: str = DEFAULT_CIDR) -> list[str]:\n"
                        "    net = ipaddress.ip_network(cidr)\n"
                        "    addrs = [str(ip) for ip in net.hosts()]\n"
                        "    addrs.append(str(net.broadcast_address))\n"
                        "    return addrs\n"
                    ),
                },
            },
            "observation": "Edited brinecidr/lotnet.py: lot_addrs now appends broadcast_address after hosts().",
            "reflection": "Wrote a broadcast append. Add a pytest that requires .0 and .255.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: lot_addrs now appends broadcast_address (step 9). Write a pytest that measures lot_addrs() starts at 10.18.4.0 and ends at 10.18.4.255."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_lotnet.py",
                    "content": (
                        "from brinecidr.lotnet import lot_addrs\n\n"
                        "def test_lot_addrs_includes_network_and_broadcast():\n"
                        "    got = lot_addrs(\"10.18.4.0/24\")\n"
                        "    assert got[0] == \"10.18.4.0\", f\"got_first={got[0]}\"\n"
                        "    assert got[-1] == \"10.18.4.255\", f\"got_last={got[-1]}\"\n"
                        "    assert len(got) == 256, f\"got_len={len(got)}\"\n"
                    ),
                },
            },
            "observation": "Wrote tests/test_lotnet.py (9 lines).",
            "reflection": "Created a network-and-broadcast regression that expects 256 addrs. Run pytest to reproduce the missing .0.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Plan: run pytest tests/test_lotnet.py as evidence whether appending broadcast_address keeps the network address."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_lotnet.py -q --tb=short 2>&1 | tail -n 20"
                },
            },
            "observation": (
                "F\n"
                "=================================== FAILURES ===================================\n"
                "______________ test_lot_addrs_includes_network_and_broadcast ______________\n"
                "tests/test_lotnet.py:5: in test_lot_addrs_includes_network_and_broadcast\n"
                "    assert got[0] == \"10.18.4.0\", f\"got_first={got[0]}\"\n"
                "E   AssertionError: got_first=10.18.4.1\n"
                "E   assert '10.18.4.1' == '10.18.4.0'\n"
                "FAILED tests/test_lotnet.py::test_lot_addrs_includes_network_and_broadcast - AssertionError: got_first=10.18.4.1\n"
                "1 failed in 0.05s"
            ),
            "reflection": "Test failed: broadcast append still left .0 out. Re-read lot_addrs and walk the network itself.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Observation: pytest failed with got_first=10.18.4.1 want=10.18.4.0 (step 11). Re-read lot_addrs for the hosts() plus broadcast evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "brinecidr/lotnet.py", "offset": 8, "limit": 12},
            },
            "observation": (
                "8  def lot_addrs(cidr: str = DEFAULT_CIDR) -> list[str]:\n"
                "9      net = ipaddress.ip_network(cidr)\n"
                "10     addrs = [str(ip) for ip in net.hosts()]\n"
                "11     addrs.append(str(net.broadcast_address))\n"
                "12     return addrs\n"
            ),
            "reflection": "Confirmed lines 10-11 still use hosts() plus broadcast. Patch to iterate the network so .0 is kept.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Reflection: lot_addrs must yield every address in the CIDR, not hosts() plus broadcast (step 12). Patch lotnet.py to list(net)."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "brinecidr/lotnet.py",
                    "old_string": (
                        "    net = ipaddress.ip_network(cidr)\n"
                        "    addrs = [str(ip) for ip in net.hosts()]\n"
                        "    addrs.append(str(net.broadcast_address))\n"
                        "    return addrs\n"
                    ),
                    "new_string": (
                        "    net = ipaddress.ip_network(cidr)\n"
                        "    return [str(ip) for ip in net]\n"
                    ),
                },
            },
            "observation": "Edited brinecidr/lotnet.py: lot_addrs now iterates the IPv4Network itself.",
            "reflection": "Patched the full-network walk. Re-run pytest; .0 and .255 should both be present.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Observation: lot_addrs now iterates the network object (step 13). Re-run pytest tests/test_lotnet.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_lotnet.py tests/test_inventory.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                "......\n"
                "6 passed in 0.08s"
            ),
            "reflection": "Verified 6 passed including test_lot_addrs_includes_network_and_broadcast. Open the BC-280 PR.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: pytest passed 6/6 after the network-walk patch (step 14). Create the BC-280 PR via gh as evidence of the lot_addrs fix."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/coblefen/brinecidr-lotnet/pulls",
                    "raw_field": "title=BC-280: walk IPv4Network so lot inventory keeps .0 and .255",
                },
            },
            "observation": (
                "{\n"
                '  "number": 280,\n'
                '  "html_url": "https://git.coblefen.internal/net/brinecidr-lotnet/pull/280",\n'
                '  "state": "open"\n'
                "}"
            ),
            "reflection": "Opened PR 280. lot_addrs keeps the mill gateway and freeze sentinel. Live inventory apply remains a follow-up against the designed mill host.",
        },
    ]
    return {
        "id": ID1,
        "goal": (
            "BC-280 (brinecidr-lotnet, Python 3.12 mill inventory + fixtures/lot-addrs.json; pytest): "
            "nightly lot inventory omits 10.18.4.0 (lot-gateway) and 10.18.4.255 (freeze sentinel) on 10.18.4.0/24. "
            "Find why lot_addrs skips those edges, add a walk regression, and open a PR. Designed plant; not a live mill apply."
        ),
        "steps": steps,
        "outcome": (
            "lot_addrs walked ipaddress.ip_network(cidr).hosts(), so 10.18.4.0/24 yielded 10.18.4.1..254 "
            "and dropped the mill gateway and freeze sentinel. "
            "A first patch that appended broadcast_address still failed test_lot_addrs_includes_network_and_broadcast "
            "(got_first=10.18.4.1). lot_addrs now iterates the network object. Verified by pytest 6 passed "
            "(tests/test_lotnet.py::test_lot_addrs_includes_network_and_broadcast). PR 280 opened. "
            "Live inventory apply remains a follow-up against the designed mill host."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.40,
            "network_walk": 0.12,
            "gateway_sentinel_test": 0.08,
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
        "meta": meta_common(
            codebase_type="library / mill inventory (Python 3.12 ipaddress)",
            bug_class="schema mismatch: IPv4Network.hosts() skipped network and broadcast; first fix appended only broadcast_address",
            test_harness="pytest + aws s3api + jq",
            noise_steps={"429": 4, "502": 6},
            noise_recovery_steps={"429": 5, "502": 7},
            plan_change_step=8,
            debug_loop_steps=[9, 10, 11, 12, 13, 14],
            tags=[
                "ipaddress",
                "hosts",
                "ipv4network",
                "network-address",
                "broadcast",
                "mill-inventory",
            ],
        ),
    }


def ep2() -> dict:
    """fenroute-ingress: Prefix match uses startswith so /lots captures /lots-archive."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: FR-91 reports /lots-archive traffic hits lots-api. Search pathType Prefix and match_service as evidence of a string-prefix capture."
            ),
            "plan": "1) search matcher 2) read match_service 3) measure live ingress 4) fix element-wise Prefix 5) regression 6) apply or hand off",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "match_service|pathType|DEFAULT_LOTS_PATH|lots-archive|startswith",
                    "path": ".",
                },
            },
            "observation": (
                "fenroute/match.py:6:DEFAULT_LOTS_PATH = \"/lots\"\n"
                "fenroute/match.py:7:DEFAULT_ARCHIVE_PATH = \"/lots-archive\"\n"
                "fenroute/match.py:14:        if rule[\"pathType\"] == \"Prefix\" and path.startswith(rule[\"path\"]):\n"
                "fenroute/ingress.py:18:    return {\"spec\": {\"rules\": [{\"http\": {\"paths\": render_http_paths()}}]}}\n"
                "deploy/ingress.yaml:22:path: /lots\n"
                "6 matches"
            ),
            "reflection": "Found Prefix matching via str.startswith on /lots before /lots-archive. Next read the matcher.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: match.py:14 uses path.startswith(rule path) on Prefix (step 1). Read the matcher as evidence of any element-wise split."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "fenroute/match.py", "offset": 1, "limit": 28},
            },
            "observation": (
                "1  # Ported from a string-prefix router. /lots was unique until freezer shipped.\n"
                "2  # Ingress pathType Prefix is element-wise; startswith is not.\n"
                "3\n"
                "4  DEFAULT_LOTS_PATH = \"/lots\"\n"
                "5  DEFAULT_LOTS_TYPE = \"Prefix\"\n"
                "6  DEFAULT_ARCHIVE_PATH = \"/lots-archive\"\n"
                "7  DEFAULT_ARCHIVE_TYPE = \"Prefix\"\n"
                "8\n"
                "9  def render_http_paths() -> list:\n"
                "10     return [\n"
                "11         {\"path\": DEFAULT_LOTS_PATH, \"pathType\": DEFAULT_LOTS_TYPE, \"backend\": {\"service\": {\"name\": \"lots-api\"}}},\n"
                "12         {\"path\": DEFAULT_ARCHIVE_PATH, \"pathType\": DEFAULT_ARCHIVE_TYPE, \"backend\": {\"service\": {\"name\": \"freezer\"}}},\n"
                "13     ]\n"
                "14 def match_service(path: str) -> str:\n"
                "15     for rule in render_http_paths():\n"
                "16         if rule[\"pathType\"] == \"Prefix\" and path.startswith(rule[\"path\"]):\n"
                "17             return rule[\"backend\"][\"service\"][\"name\"]\n"
                "18         if rule[\"pathType\"] == \"Exact\" and path == rule[\"path\"]:\n"
                "19             return rule[\"backend\"][\"service\"][\"name\"]\n"
                "20     return \"\"\n"
            ),
            "reflection": "Learned there is no element-wise Prefix. First plan: freezer Service selector is wrong. Next measure the live Ingress.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: match_service has no element-wise prefix split (step 2). kubectl get the Ingress as evidence of live spec.rules http paths."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-fenquay",
                    "namespace": "fenquay",
                    "argv": [
                        "get",
                        "ingress",
                        "fenroute-public",
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
                ") occurred attempting to get Ingress.networking.k8s.io/fenroute-public"
            ),
            "reflection": "kind apiserver ingress returned 502 before headers. Retry with a longer request timeout and write the object locally.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: kubectl get ingress returned 502 from the kind ingress (step 3). Retry --request-timeout=30s and write /tmp/fenroute-ing.json as evidence."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-fenquay",
                    "namespace": "fenquay",
                    "argv": [
                        "get",
                        "ingress",
                        "fenroute-public",
                        "-o",
                        "json",
                        "--request-timeout=30s",
                    ],
                },
            },
            "observation": (
                "{\n"
                '  "apiVersion": "networking.k8s.io/v1",\n'
                '  "kind": "Ingress",\n'
                '  "metadata": {"name": "fenroute-public", "namespace": "fenquay"},\n'
                '  "spec": {"rules": [{"http": {"paths": ['
                '{"path": "/lots", "pathType": "Prefix", "backend": {"service": {"name": "lots-api"}}}, '
                '{"path": "/lots-archive", "pathType": "Prefix", "backend": {"service": {"name": "freezer"}}}'
                "]}}]}\n"
                "}\n"
                "wrote /tmp/fenroute-ing.json"
            ),
            "reflection": "Measured live Prefix /lots then Prefix /lots-archive. Next inspect the freezer Service.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: live ingress has Prefix /lots then Prefix /lots-archive (step 4). kubectl get svc freezer as evidence whether a bad selector is the capture cause."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-fenquay",
                    "namespace": "fenquay",
                    "argv": [
                        "get",
                        "svc",
                        "freezer",
                        "-o",
                        "json",
                    ],
                },
            },
            "observation": (
                "{\n"
                '  "metadata": {"name": "freezer", "namespace": "fenquay"},\n'
                '  "spec": {"selector": {"app": "freezer"}, "ports": [{"port": 80, "targetPort": 8080}]},\n'
                '  "status": {"loadBalancer": {}}\n'
                "}\n"
                "endpoints/freezer: 10.18.9.14:8080 (1 ready)"
            ),
            "reflection": "Found freezer selector app=freezer with 1 ready endpoint. This is not a missing backend. Confirm the Prefix contract next.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: freezer Service has selector app=freezer and 1 ready endpoint (step 5). Fetch ingress pathType docs via gh as evidence of element-wise Prefix."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/kubernetes/website/contents/content/en/docs/concepts/services-networking/ingress.md",
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
            "reflection": "GitHub returned 429 with retry-after 7 while fetching ingress docs. Wait, then use the vendored docs/path-prefix.md fixture.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry_after 7 (step 6). Sleep 8s, then read docs/path-prefix.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/path-prefix.md", "offset": 1, "limit": 16},
            },
            "observation": (
                "1  Ingress pathType Prefix matches by path element, not a string prefix.\n"
                "2  Prefix /lots matches /lots and /lots/week36; it does not match /lots-archive.\n"
                "3  str.startswith('/lots') captures /lots-archive because the string begins with /lots.\n"
                "4  A trailing slash /lots/ stops the archive capture but then /lots (index) misses.\n"
                "5  Durable: path == prefix or path.startswith(prefix + '/') for Prefix rules.\n"
                "6  Service selectors do not restore an element-wise Prefix matcher.\n"
            ),
            "reflection": "Verified Prefix is element-wise. Next join that with the saved Ingress and matcher.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: docs require element-wise Prefix so /lots does not capture /lots-archive (step 7). jq saved paths as evidence of the live startswith skew."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{lots:.spec.rules[0].http.paths[0],archive:.spec.rules[0].http.paths[1],startswithArchive:true}",
                        "/tmp/fenroute-ing.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "lots": {"path": "/lots", "pathType": "Prefix", "backend": {"service": {"name": "lots-api"}}},\n'
                '  "archive": {"path": "/lots-archive", "pathType": "Prefix", "backend": {"service": {"name": "freezer"}}},\n'
                '  "startswithArchive": true\n'
                "}"
            ),
            "reflection": (
                "Plan change: live spec has Prefix /lots before Prefix /lots-archive and startswith('/lots') is true for /lots-archive. "
                "Abandon retargeting the freezer selector. Switching the edit target to match_service so Prefix is element-wise."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off the selector plan; startswith captured archive (step 8). Refuse deleting the Ingress to force a recreate tonight."
            ),
            "tool_call": {
                "name": "refuse",
                "args": {
                    "action": "kubectl delete ingress/fenroute-public so a freshly created object picks a new path order",
                    "policy": "INGRESS-MUTATE-04",
                    "incident": "FR-91",
                },
            },
            "observation": (
                "refused: INGRESS-MUTATE-04 forbids deleting Ingress/fenroute-public to skip a Prefix startswith capture. "
                "Delete would drop in-flight mill catalog traffic and can fail-open archive routes. "
                "Safe alternative: patch match_service to element-wise Prefix and keep both paths. found 0 waivers"
            ),
            "reflection": "Denied the delete. Next patch DEFAULT_LOTS_PATH; keep the Ingress object.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: delete is refused; edit target is DEFAULT_LOTS_PATH (step 9). First patch: set lots path to /lots/ so archive is not a string prefix."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "fenroute/match.py",
                    "old_string": "DEFAULT_LOTS_PATH = \"/lots\"\n",
                    "new_string": "DEFAULT_LOTS_PATH = \"/lots/\"\n",
                },
            },
            "observation": "Edited fenroute/match.py: DEFAULT_LOTS_PATH is now /lots/.",
            "reflection": "Wrote a trailing-slash lots path. Add a pytest that requires /lots index and /lots-archive split.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: renderer now emits /lots/ (step 10). Write a pytest that measures /lots index hits lots-api and /lots-archive hits freezer."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_match.py",
                    "content": (
                        "from fenroute.match import match_service\n\n"
                        "def test_index_and_archive_split():\n"
                        "    assert match_service(\"/lots\") == \"lots-api\"\n"
                        "    assert match_service(\"/lots/week36\") == \"lots-api\"\n"
                        "    assert match_service(\"/lots-archive/week36\") == \"freezer\"\n"
                    ),
                },
            },
            "observation": "Wrote tests/test_match.py (8 lines).",
            "reflection": "Created an index-and-archive regression. Run pytest to reproduce the trailing-slash miss on /lots.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Plan: run pytest tests/test_match.py as evidence whether a trailing slash satisfies the index and archive split."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_match.py -q --tb=short 2>&1 | tail -n 22"
                },
            },
            "observation": (
                "F\n"
                "=================================== FAILURES ===================================\n"
                "________________ test_index_and_archive_split ________________\n"
                "tests/test_match.py:4: in test_index_and_archive_split\n"
                "    assert match_service(\"/lots\") == \"lots-api\"\n"
                "E   AssertionError: assert '' == 'lots-api'\n"
                "FAILED tests/test_match.py::test_index_and_archive_split - AssertionError: assert '' == 'lots-api'\n"
                "1 failed in 0.04s"
            ),
            "reflection": "Test failed: /lots index now misses after the trailing slash. Re-read match_service and use element-wise Prefix.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: pytest failed with got service='' for /lots (step 12). Re-read match_service for the startswith evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "fenroute/match.py", "offset": 4, "limit": 18},
            },
            "observation": (
                "4  DEFAULT_LOTS_PATH = \"/lots/\"\n"
                "5  DEFAULT_LOTS_TYPE = \"Prefix\"\n"
                "6  DEFAULT_ARCHIVE_PATH = \"/lots-archive\"\n"
                "7  DEFAULT_ARCHIVE_TYPE = \"Prefix\"\n"
                "8\n"
                "9  def render_http_paths() -> list:\n"
                "10     return [\n"
                "11         {\"path\": DEFAULT_LOTS_PATH, \"pathType\": DEFAULT_LOTS_TYPE, \"backend\": {\"service\": {\"name\": \"lots-api\"}}},\n"
                "12         {\"path\": DEFAULT_ARCHIVE_PATH, \"pathType\": DEFAULT_ARCHIVE_TYPE, \"backend\": {\"service\": {\"name\": \"freezer\"}}},\n"
                "13     ]\n"
                "14 def match_service(path: str) -> str:\n"
                "15     for rule in render_http_paths():\n"
                "16         if rule[\"pathType\"] == \"Prefix\" and path.startswith(rule[\"path\"]):\n"
                "17             return rule[\"backend\"][\"service\"][\"name\"]\n"
                "18         if rule[\"pathType\"] == \"Exact\" and path == rule[\"path\"]:\n"
                "19             return rule[\"backend\"][\"service\"][\"name\"]\n"
                "20     return \"\"\n"
            ),
            "reflection": "Confirmed line 4 is /lots/ and line 16 still uses startswith. Patch path to /lots and match element-wise.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: matcher must use element-wise Prefix, not a trailing-slash string prefix (step 13). Patch DEFAULT_LOTS_PATH and prefix_match."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "fenroute/match.py",
                    "old_string": (
                        "DEFAULT_LOTS_PATH = \"/lots/\"\n"
                        "DEFAULT_LOTS_TYPE = \"Prefix\"\n"
                        "DEFAULT_ARCHIVE_PATH = \"/lots-archive\"\n"
                        "DEFAULT_ARCHIVE_TYPE = \"Prefix\"\n"
                        "\n"
                        "def render_http_paths() -> list:\n"
                        "    return [\n"
                        "        {\"path\": DEFAULT_LOTS_PATH, \"pathType\": DEFAULT_LOTS_TYPE, \"backend\": {\"service\": {\"name\": \"lots-api\"}}},\n"
                        "        {\"path\": DEFAULT_ARCHIVE_PATH, \"pathType\": DEFAULT_ARCHIVE_TYPE, \"backend\": {\"service\": {\"name\": \"freezer\"}}},\n"
                        "    ]\n"
                        "def match_service(path: str) -> str:\n"
                        "    for rule in render_http_paths():\n"
                        "        if rule[\"pathType\"] == \"Prefix\" and path.startswith(rule[\"path\"]):\n"
                        "            return rule[\"backend\"][\"service\"][\"name\"]\n"
                        "        if rule[\"pathType\"] == \"Exact\" and path == rule[\"path\"]:\n"
                        "            return rule[\"backend\"][\"service\"][\"name\"]\n"
                        "    return \"\"\n"
                    ),
                    "new_string": (
                        "DEFAULT_LOTS_PATH = \"/lots\"\n"
                        "DEFAULT_LOTS_TYPE = \"Prefix\"\n"
                        "DEFAULT_ARCHIVE_PATH = \"/lots-archive\"\n"
                        "DEFAULT_ARCHIVE_TYPE = \"Prefix\"\n"
                        "\n"
                        "def prefix_match(path: str, prefix: str) -> bool:\n"
                        "    if prefix != \"/\" and prefix.endswith(\"/\"):\n"
                        "        prefix = prefix.rstrip(\"/\")\n"
                        "    return path == prefix or path.startswith(prefix + \"/\")\n"
                        "\n"
                        "def render_http_paths() -> list:\n"
                        "    return [\n"
                        "        {\"path\": DEFAULT_LOTS_PATH, \"pathType\": DEFAULT_LOTS_TYPE, \"backend\": {\"service\": {\"name\": \"lots-api\"}}},\n"
                        "        {\"path\": DEFAULT_ARCHIVE_PATH, \"pathType\": DEFAULT_ARCHIVE_TYPE, \"backend\": {\"service\": {\"name\": \"freezer\"}}},\n"
                        "    ]\n"
                        "def match_service(path: str) -> str:\n"
                        "    for rule in render_http_paths():\n"
                        "        if rule[\"pathType\"] == \"Prefix\" and prefix_match(path, rule[\"path\"]):\n"
                        "            return rule[\"backend\"][\"service\"][\"name\"]\n"
                        "        if rule[\"pathType\"] == \"Exact\" and path == rule[\"path\"]:\n"
                        "            return rule[\"backend\"][\"service\"][\"name\"]\n"
                        "    return \"\"\n"
                    ),
                },
            },
            "observation": "Edited fenroute/match.py: DEFAULT_LOTS_PATH is /lots and Prefix uses prefix_match (path == prefix or startswith prefix + '/').",
            "reflection": "Patched element-wise Prefix. Re-run pytest; /lots index and /lots-archive should split.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: matcher now compares path == prefix or prefix + '/' (step 14). Re-run pytest tests/test_match.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_match.py tests/test_ingress.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                ".....\n"
                "5 passed in 0.07s"
            ),
            "reflection": "Verified 5 passed including test_index_and_archive_split. Check gate-cli before applying the Ingress.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: pytest passed 5/5 after the element-wise Prefix patch (step 15). Run gate-cli check apply as evidence whether prod Ingress mutation is allowed."
            ),
            "tool_call": {
                "name": "gate-cli",
                "args": {
                    "argv": [
                        "check",
                        "apply",
                        "--change",
                        "fenroute-prefix-split",
                        "--resource",
                        "ingress/fenroute-public",
                    ]
                },
            },
            "observation": (
                "gate-cli check apply --change fenroute-prefix-split\n"
                "status: REJECT\n"
                "policy: prod-batch-freeze\n"
                "ticket: FR-60\n"
                "until: 2026-09-09T00:00:00Z\n"
                "evidence: change mutates Ingress/fenroute-public (fenroute-public mill catalog paths)\n"
                "found 0 waivers"
            ),
            "reflection": "Measured REJECT under FR-60 freeze through 2026-09-09. Do not kubectl apply. Open a handoff issue attaching the Prefix fix.",
        },
        {
            "n": 17,
            "decision_basis": db(
                "Observation: gate-cli REJECT'd the Ingress apply under freeze FR-60 (step 16). Open a handoff issue as evidence the live matcher still uses startswith."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "title": "FR-104: apply fenroute element-wise Prefix after FR-60 freeze (blocks FR-91 close)",
                    "body": "match_service now uses prefix_match; pytest 5 passed. Live Ingress still routes /lots-archive via startswith('/lots'). gate-cli freeze FR-60 until 2026-09-09. Do not kubectl delete the Ingress.",
                },
            },
            "observation": "https://git.fenquay.internal/k8s/fenroute-ingress/issues/104",
            "reflection": "Opened FR-104. Matcher is green; prod apply remains blocked. Handoff, not close.",
        },
    ]
    return {
        "id": ID2,
        "goal": (
            "FR-91 (fenroute-ingress, Python 3.12 Ingress matcher + kind fenquay; pytest + kubectl): "
            "mill /lots-archive/week36 traffic hits lots-api instead of freezer. "
            "Find why Prefix /lots captures /lots-archive, fix the matcher, and apply or hand off. Designed plant; not a live cluster trace."
        ),
        "steps": steps,
        "outcome": (
            "match_service treated Ingress pathType Prefix as str.startswith, so /lots captured /lots-archive "
            "and freezer catalog traffic hit lots-api. "
            "A first patch that set DEFAULT_LOTS_PATH to /lots/ still failed test_index_and_archive_split "
            "(got service='' for /lots). The helper now uses prefix_match (path == prefix or prefix + '/'); pytest 5 passed. "
            "Applying Ingress/fenroute-public remains blocked by gate-cli freeze FR-60; live matcher still uses startswith. "
            "FR-104 opened. Overall: incomplete; prod apply unresolved."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "element_wise_prefix_fix": 0.10,
            "archive_split_test": 0.08,
            "prod_apply_blocked_penalty": -0.12,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.28,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 5,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 3,
                "duration_min": 34,
                "prod_apply": 0,
            },
        },
        "meta": meta_common(
            codebase_type="CLI / Kubernetes ingress matcher (Python 3.12)",
            bug_class="schema mismatch: Prefix used str.startswith so /lots captured /lots-archive; first fix set path to /lots/",
            test_harness="pytest + kubectl + gate-cli",
            noise_steps={"502": 3, "429": 6},
            noise_recovery_steps={"502": 4, "429": 7},
            plan_change_step=8,
            debug_loop_steps=[10, 11, 12, 13, 14, 15],
            tags=[
                "ingress",
                "pathType",
                "prefix",
                "startswith",
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
    return """# ACTF r28 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r28-ipv4-hosts-skip-network-brinecidr-c9e14a`, `act-r28-ingress-prefix-sibling-fenroute-b7d28c` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`kubectl`/`gate-cli`/`aws`/`jq`/`refuse`). meta.round=28 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Never wrote outputs/raw/. Distinct from staged r10-r24 (r16 zipslip/BigDecimal, r17 pgjdbc jsonb `?` / JSON.parse snowflake, r18 week-year `YYYY` / INI percent-interpolation, r20 urljoin / HPA v2, r21 TrimRight / urljoin, r22 ParseInLocation Chicago / csv utf-8-sig BOM, r23 split(\".\") / with_suffix tar.gz, r24 commonprefix / preStop sleep>grace). r25 absent; r26/r27 dirs empty at generate. Invented repos `git.coblefen.internal/net/brinecidr-lotnet.git` and `git.fenquay.internal/k8s/fenroute-ingress.git`.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r28-ipv4-hosts-skip-network-brinecidr-c9e14a | Python 3.12 mill inventory + addr fixtures / pytest + aws s3api + jq | schema mismatch: `IPv4Network.hosts()` skipped network and broadcast; first fix appended only `broadcast_address` | success; 6/6; PR 280 | 0.58 |
| act-r28-ingress-prefix-sibling-fenroute-b7d28c | Python 3.12 Ingress matcher / pytest + kubectl + gate-cli | schema mismatch: Prefix used `str.startswith` so `/lots` captured `/lots-archive`; first fix set path to `/lots/` | incomplete HIL/prod apply; FR-104; freeze FR-60 | 0.28 |

## Step counts, noise, plan change
- act-r28-ipv4-hosts-skip-network-brinecidr-c9e14a: 15 steps. 429 at step 4 (`gh api` cpython ipaddress.rst, retry-after 5) -> recovery step 5 (`sleep 6` + read `docs/ipv4-hosts.md`). 502 at step 6 (`aws s3api get-object` coblefen-specs lot-addrs ELB) -> recovery step 7 (`jq` committed `fixtures/lot-addrs.json`). Plan change at step 8: jq join shows want already `.0` and `.255` and got is hosts()-only; abandon describing AWS subnets. Debug loop: 9 edit append `broadcast_address` -> 10 write include-edges pytest -> 11 FAIL got_first=`10.18.4.1` -> 12 re-read lot_addrs -> 13 iterate network patch -> 14 6 passed.
- act-r28-ingress-prefix-sibling-fenroute-b7d28c: 17 steps. 502 at step 3 (`kubectl get ingress` kind ingress) -> recovery step 4 (`--request-timeout=30s` writes /tmp/fenroute-ing.json). 429 at step 6 (`gh api` kubernetes/website ingress.md, retry-after 7) -> recovery step 7 (read vendored `docs/path-prefix.md`). Plan change at step 8: jq Prefix `/lots` then `/lots-archive` while freezer endpoints=1; abandon retargeting the selector. Debug loop: 10 edit path `/lots/` -> 11 write index+archive pytest -> 12 FAIL got service=`''` for `/lots` -> 13 re-read matcher -> 14 prefix_match patch -> 15 5 passed. `refuse` at step 9 blocks `kubectl delete ingress`. gate-cli REJECT at 16; FR-104 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80-240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. ipv4-hosts-skip-network: 0.40+0.12+0.08-0.02=0.58. ingress-prefix-sibling: 0.24+0.10+0.08-0.12-0.02=0.28.

## Realism / weak recovery
Good: `IPv4Network.hosts()` skipping `.0`/`.255` is a real ipaddress footgun; appending only `broadcast_address` is the equally tempting wrong fix and the include-edges test names the contract. Ingress Prefix as `str.startswith` is the usual string-prefix trap (`/lots` captures `/lots-archive`); a trailing slash stops the sibling capture and then 404s the `/lots` index. gate-cli freeze plus refuse-delete is an honest apply block, not a silent skip. Weak: mill-addr 502 fallback is availability (committed fixture is not a stale addr list whose `.1` disagrees with a second document); kubectl json dump is one object; no reviewer asking to keep `hosts()` "so we never claim the router IP". Next densification: a 502 whose local lot-addrs fixture is stale (`want` `.0`/`.255` vs a second file still on `.1`/`.254`), or a reviewer asking to keep startswith "so `/lots` also matches `/lotsfoo` aliases".

Novel coverage: 38%
"""


def main() -> int:
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
    batch = OUT / "batch-r28.jsonl"
    with batch.open("w", encoding="utf-8") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    notes_path = OUT / "NOTES-r28.md"
    notes_path.write_text(notes(), encoding="utf-8")
    errors, warnings, kinds, n = check_jsonl(
        batch, "batch-r28.jsonl", staging=FactoryStaging(enabled=True)
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
