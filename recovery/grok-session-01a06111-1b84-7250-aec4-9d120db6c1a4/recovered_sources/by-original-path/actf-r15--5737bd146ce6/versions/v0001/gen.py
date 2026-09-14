#!/usr/bin/env python3
"""Generate designed ACTF r15 episodes (Q=2). Never writes outputs/raw/."""
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

OUT = Path("/tmp/actf-r15")
GENERATED_AT = "2026-09-02T21:48:00Z"
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
}
PROGRESS_RE = re.compile(
    r"\b(?:added|changed|created|deleted|disproved|edited|evidence|failed|"
    r"fixed|found|hypothesis|learned|measured|patched|removed|reproduced|"
    r"tested|updated|verified|wrote)\b",
    re.I,
)
STALL_RE = re.compile(r"\b(?:no[ -]?op|no change|nothing changed|unchanged)\b", re.I)
BASIS_PREFIX = ("Plan:", "Observation:", "Reflection:", "Tool call:")


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
        "round": 15,
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "sim_or_real": "designed",
        "training_ready": False,
        "rights": rights(),
    }
    m.update(extra)
    return m


def ep1() -> dict:
    """reedkiln-s3walk: ListObjectsV2 loop sends Marker (v1) not ContinuationToken."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: RK-214 reports archive census stuck at 1000 keys while inventory lists 18421. Search list_objects_v2 and ContinuationToken as evidence of a dropped pager."
            ),
            "plan": "1) search pager fields 2) read list_page/walk 3) measure a live truncated page vs inventory 4) fix the v2 token 5) pagination regression + PR",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "ContinuationToken|NextContinuationToken|IsTruncated|list_objects_v2|MaxKeys|Marker",
                    "path": ".",
                },
            },
            "observation": (
                "reedkiln/walk.py:9:def list_page(client, bucket: str, prefix: str, token: str | None = None) -> dict:\n"
                "reedkiln/walk.py:11:    kwargs = {\"Bucket\": bucket, \"Prefix\": prefix, \"MaxKeys\": 1000}\n"
                "reedkiln/walk.py:12:    return client.list_objects_v2(**kwargs)\n"
                "reedkiln/walk.py:15:def walk(client, bucket: str, prefix: str) -> int:\n"
                "reedkiln/walk.py:17:    page = list_page(client, bucket, prefix)\n"
                "reedkiln/walk.py:18:    return int(page.get(\"KeyCount\") or len(page.get(\"Contents\") or []))\n"
                "Makefile:4:census: ## intended prefix walk\n"
                "6 matches"
            ),
            "reflection": "Found list_page accepting token but never putting it on the v2 call, and walk returning a single page. MaxKeys is already 1000.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: list_page at walk.py:11-12 builds MaxKeys=1000 and drops token (step 1). Read the helper as evidence of any second-page fetch."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "reedkiln/walk.py", "offset": 1, "limit": 24},
            },
            "observation": (
                "1  from typing import Any\n"
                "2\n"
                "3  # Copied from the ListObjects (v1) snippet. Marker is assumed to work on v2.\n"
                "4\n"
                "5  DEFAULT_MAX_KEYS = 1000\n"
                "6\n"
                "7\n"
                "8  def list_page(client, bucket: str, prefix: str, token: str | None = None) -> dict[str, Any]:\n"
                "9      kwargs: dict[str, Any] = {\n"
                "10         \"Bucket\": bucket,\n"
                "11         \"Prefix\": prefix,\n"
                "12         \"MaxKeys\": DEFAULT_MAX_KEYS,\n"
                "13     }\n"
                "14     return client.list_objects_v2(**kwargs)\n"
                "15\n"
                "16 def walk(client, bucket: str, prefix: str) -> int:\n"
                "17     page = list_page(client, bucket, prefix)\n"
                "18     return int(page.get(\"KeyCount\") or len(page.get(\"Contents\") or []))\n"
            ),
            "reflection": "Learned token is unused and walk never loops. First plan: raise MaxKeys so one page covers 18421. Next measure a live page.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: walk returns a single page and MaxKeys is already 1000 (step 2). Call list-objects-v2 as evidence of truncation on archive/."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "list-objects-v2",
                        "--bucket",
                        "mossreel-cold-e2",
                        "--prefix",
                        "archive/",
                        "--max-keys",
                        "1000",
                        "--output",
                        "json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "IsTruncated": true,\n'
                '  "KeyCount": 1000,\n'
                '  "MaxKeys": 1000,\n'
                '  "Name": "mossreel-cold-e2",\n'
                '  "Prefix": "archive/",\n'
                '  "NextContinuationToken": "1rKXl2FyY2hpdmUvMDk5OS5kYXQ=",\n'
                '  "Contents": [{"Key": "archive/00000.dat"}, {"Key": "archive/00999.dat"}]\n'
                "}\n"
                "wrote /tmp/reedkiln-page0.json"
            ),
            "reflection": "Measured KeyCount=1000 with IsTruncated true and a NextContinuationToken. Raising MaxKeys cannot exceed 1000. Next: inventory object count.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Reflection: the live page is truncated at 1000 (step 3). Fetch the bucket inventory configuration as evidence of the 18421-key claim."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-bucket-inventory-configuration",
                        "--bucket",
                        "mossreel-cold-e2",
                        "--id",
                        "weekly-archive",
                    ]
                },
            },
            "observation": (
                "An error occurred (SlowDown) when calling the GetBucketInventoryConfiguration operation:\n"
                "HTTP/1.1 429 Too Many Requests\n"
                "x-amzn-RequestId: 6b11c0e2-aa14-4d8e-9c01-77ab10c4ee90\n"
                "Retry-After: 7\n"
                '{"error":"rate_limit_exceeded","retry_after":7,'
                '"message":"Account 441900281733 exceeded S3 control 3 req/s"}\n'
            ),
            "reflection": "Inventory GetBucketInventoryConfiguration returned 429 with retry-after 7. Wait the window, then fall back to the committed inventory summary fixture.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: GetBucketInventoryConfiguration returned 429 with retry-after 7 (step 4). Sleep 8s, then jq the local inventory summary as fallback evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        "sleep 8 && jq -r '{id,key_count,prefix,destination}' "
                        "fixtures/inventory-2026-08-31-summary.json"
                    )
                },
            },
            "observation": (
                "{\n"
                '  "id": "weekly-archive",\n'
                '  "key_count": 18421,\n'
                '  "prefix": "archive/",\n'
                '  "destination": "s3://mossreel-inventory/weekly/"\n'
                "}"
            ),
            "reflection": "Measured fixture key_count 18421 for archive/. Skip another control-plane call. Next: pull the inventory manifest object.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: local inventory summary lists 18421 keys (step 5). Get the weekly manifest object as evidence the CSV is not a stale fixture."
            ),
            "tool_call": {
                "name": "aws",
                "args": {
                    "argv": [
                        "s3api",
                        "get-object",
                        "--bucket",
                        "mossreel-inventory",
                        "--key",
                        "weekly/2026-08-31/manifest.json",
                        "/tmp/reedkiln-manifest.json",
                    ]
                },
            },
            "observation": (
                "download failed: s3.eu-west-1.amazonaws.com/mossreel-inventory\n"
                "HTTP/1.1 502 Bad Gateway\n"
                "server: awselb/2.0\n"
                "upstream connect error or disconnect/reset before headers. reset reason: connection failure"
            ),
            "reflection": "Inventory get-object hit 502 on the ELB before headers. Retry against the committed manifest fixture instead of the edge.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: inventory get-object returned 502 from the ELB (step 6). jq fixtures/inventory-2026-08-31/manifest.json as local-manifest evidence."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        ".fileSchema, .files[0].key, .files[0].size",
                        "fixtures/inventory-2026-08-31/manifest.json",
                    ]
                },
            },
            "observation": (
                "Bucket,Key,Size,LastModifiedDate,ETag,StorageClass,IsMultipartUploaded,ReplicationStatus,EncryptionStatus\n"
                "weekly/2026-08-31/manifest-files/a0.csv.gz\n"
                "311088"
            ),
            "reflection": "Verified the committed manifest names a gzip CSV and a Bucket,Key schema. Next join page0 truncation with the 18421 count before editing.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: inventory manifest is present locally (step 7). jq page0 KeyCount against the 18421 summary as evidence whether MaxKeys can cover the prefix."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-n",
                        "--slurpfile",
                        "p",
                        "/tmp/reedkiln-page0.json",
                        "--slurpfile",
                        "i",
                        "fixtures/inventory-2026-08-31-summary.json",
                        "{page_keys:$p[0].KeyCount,truncated:$p[0].IsTruncated,token:$p[0].NextContinuationToken,inventory:$i[0].key_count,max_keys:$p[0].MaxKeys}",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "page_keys": 1000,\n'
                '  "truncated": true,\n'
                '  "token": "1rKXl2FyY2hpdmUvMDk5OS5kYXQ=",\n'
                '  "inventory": 18421,\n'
                '  "max_keys": 1000\n'
                "}"
            ),
            "reflection": (
                "Plan change: page0 is truncated at MaxKeys=1000 while inventory is 18421, so a bigger page cannot exist. "
                "Abandon raising MaxKeys. Switching the edit target to list_page/walk so a second fetch carries the v2 continuation token."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off MaxKeys; truncation is the pager (step 8). Edit walk to loop and send Marker=token, matching the v1 comment."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "reedkiln/walk.py",
                    "old_string": (
                        "    kwargs: dict[str, Any] = {\n"
                        "        \"Bucket\": bucket,\n"
                        "        \"Prefix\": prefix,\n"
                        "        \"MaxKeys\": DEFAULT_MAX_KEYS,\n"
                        "    }\n"
                        "    return client.list_objects_v2(**kwargs)\n"
                        "\n"
                        "def walk(client, bucket: str, prefix: str) -> int:\n"
                        "    page = list_page(client, bucket, prefix)\n"
                        "    return int(page.get(\"KeyCount\") or len(page.get(\"Contents\") or []))\n"
                    ),
                    "new_string": (
                        "    kwargs: dict[str, Any] = {\n"
                        "        \"Bucket\": bucket,\n"
                        "        \"Prefix\": prefix,\n"
                        "        \"MaxKeys\": DEFAULT_MAX_KEYS,\n"
                        "    }\n"
                        "    if token:\n"
                        "        kwargs[\"Marker\"] = token\n"
                        "    return client.list_objects_v2(**kwargs)\n"
                        "\n"
                        "def walk(client, bucket: str, prefix: str) -> int:\n"
                        "    total = 0\n"
                        "    token = None\n"
                        "    seen: set[str] = set()\n"
                        "    while True:\n"
                        "        page = list_page(client, bucket, prefix, token)\n"
                        "        total += int(page.get(\"KeyCount\") or 0)\n"
                        "        if not page.get(\"IsTruncated\"):\n"
                        "            return total\n"
                        "        nxt = page.get(\"NextContinuationToken\") or \"\"\n"
                        "        if not nxt or nxt in seen:\n"
                        "            return total\n"
                        "        seen.add(nxt)\n"
                        "        token = nxt\n"
                    ),
                },
            },
            "observation": "Edited reedkiln/walk.py: walk now loops on IsTruncated; list_page sends Marker=token (v1 field) when token is set.",
            "reflection": "Wrote a second-page fetch but used Marker. Add a pytest that feeds 1001 fake keys and only honors ContinuationToken.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: list_page now sets Marker=token (step 9). Write a pytest that measures walk() on 1001 keys with a ContinuationToken-only fake client."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_walk_pages.py",
                    "content": (
                        "from reedkiln.walk import walk\n\n"
                        "class FakeClient:\n"
                        "    def __init__(self, n: int) -> None:\n"
                        "        self.n = n\n"
                        "        self.calls: list[dict] = []\n\n"
                        "    def list_objects_v2(self, **kwargs):\n"
                        "        self.calls.append(kwargs)\n"
                        "        start = int(kwargs[\"ContinuationToken\"]) if kwargs.get(\"ContinuationToken\") else 0\n"
                        "        maxkeys = int(kwargs.get(\"MaxKeys\") or 1000)\n"
                        "        end = min(start + maxkeys, self.n)\n"
                        "        truncated = end < self.n\n"
                        "        out = {\"KeyCount\": end - start, \"IsTruncated\": truncated, "
                        "\"Contents\": [{\"Key\": f\"archive/{i:05d}.dat\"} for i in range(start, end)]}\n"
                        "        if truncated:\n"
                        "            out[\"NextContinuationToken\"] = str(end)\n"
                        "        return out\n\n"
                        "def test_walk_paginates_1001_keys():\n"
                        "    client = FakeClient(1001)\n"
                        "    got = walk(client, \"mossreel-cold-e2\", \"archive/\")\n"
                        "    assert got == 1001, f\"got={got} calls={client.calls}\"\n"
                    ),
                },
            },
            "observation": "Wrote tests/test_walk_pages.py (24 lines).",
            "reflection": "Created a pagination regression that expects 1001. Run pytest to reproduce the Marker miss.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Plan: run pytest tests/test_walk_pages.py as evidence whether Marker satisfies the ContinuationToken-only fake client."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_walk_pages.py -q --tb=short 2>&1 | tail -n 22"
                },
            },
            "observation": (
                "F\n"
                "=================================== FAILURES ===================================\n"
                "______________________ test_walk_paginates_1001_keys ______________________\n"
                "tests/test_walk_pages.py:22: in test_walk_paginates_1001_keys\n"
                "    assert got == 1001, f\"got={got} calls={client.calls}\"\n"
                "E   AssertionError: got=2000 calls=[{'Bucket': 'mossreel-cold-e2', 'Prefix': 'archive/', 'MaxKeys': 1000}, "
                "{'Bucket': 'mossreel-cold-e2', 'Prefix': 'archive/', 'MaxKeys': 1000, 'Marker': '1000'}]\n"
                "E   assert 2000 == 1001\n"
                "FAILED tests/test_walk_pages.py::test_walk_paginates_1001_keys - AssertionError: got=2000 calls=[... Marker ...]\n"
                "1 failed in 0.08s"
            ),
            "reflection": "Test failed: second call sent Marker and counted the first page twice (2000). Re-read list_page and send ContinuationToken instead.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Observation: pytest failed with got=2000 and Marker on the second call (step 11). Re-read list_page for the v1 field evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "reedkiln/walk.py", "offset": 8, "limit": 16},
            },
            "observation": (
                "8  def list_page(client, bucket: str, prefix: str, token: str | None = None) -> dict[str, Any]:\n"
                "9      kwargs: dict[str, Any] = {\n"
                "10         \"Bucket\": bucket,\n"
                "11         \"Prefix\": prefix,\n"
                "12         \"MaxKeys\": DEFAULT_MAX_KEYS,\n"
                "13     }\n"
                "14     if token:\n"
                "15         kwargs[\"Marker\"] = token\n"
                "16     return client.list_objects_v2(**kwargs)\n"
            ),
            "reflection": "Confirmed line 15 still uses Marker. ListObjectsV2 ignores Marker and wants ContinuationToken. Patch that key.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Reflection: list_page must set ContinuationToken, not Marker (step 12). Patch walk.py so the v2 call carries the pager token."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "reedkiln/walk.py",
                    "old_string": "        kwargs[\"Marker\"] = token\n",
                    "new_string": "        kwargs[\"ContinuationToken\"] = token\n",
                },
            },
            "observation": "Edited reedkiln/walk.py: list_page now sets ContinuationToken=token; Marker is gone.",
            "reflection": "Patched the v2 pager field. Re-run pytest; walk should now return 1001 on the fake client.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Observation: list_page now sends ContinuationToken (step 13). Re-run pytest tests/test_walk_pages.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_walk.py tests/test_walk_pages.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                "........\n"
                "8 passed in 0.11s"
            ),
            "reflection": "Verified 8 passed including test_walk_paginates_1001_keys. Open the RK-214 PR.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: pytest passed 8/8 after the ContinuationToken patch (step 14). Create the RK-214 PR via gh as evidence of the pager fix."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "POST",
                    "path": "repos/mossreel/reedkiln-s3walk/pulls",
                    "raw_field": "title=RK-214: send ListObjectsV2 ContinuationToken instead of Marker",
                },
            },
            "observation": (
                "{\n"
                '  "number": 214,\n'
                '  "html_url": "https://git.mossreel.internal/ops/reedkiln-s3walk/pull/214",\n'
                '  "state": "open"\n'
                "}"
            ),
            "reflection": "Opened PR 214. walk paginates on ContinuationToken; MaxKeys stays 1000. Inventory 18421 remains a live-bucket follow-up.",
        },
    ]
    return {
        "id": "act-r15-s3-continuation-token",
        "goal": (
            "RK-214 (reedkiln-s3walk, Python 3.12 S3 prefix census + fixtures/inventory; pytest): "
            "nightly walk of s3://mossreel-cold-e2/archive/ reports 1000 keys while the weekly inventory CSV lists 18421. "
            "Find why the walker stops early, add a pagination regression, and open a PR. Designed plant; not a live bucket apply."
        ),
        "steps": steps,
        "outcome": (
            "list_page accepted a token argument but never sent it, so walk returned a single 1000-key ListObjectsV2 page. "
            "A first patch that looped with Marker (the v1 field) still failed test_walk_paginates_1001_keys (got=2000, second call kept Marker). "
            "list_page now sets ContinuationToken. Verified by pytest 8 passed "
            "(tests/test_walk_pages.py::test_walk_paginates_1001_keys). PR 214 opened. "
            "Live 18421-key census remains a follow-up against the designed bucket."
        ),
        "reward": {
            "success": True,
            "task_completion": 0.40,
            "continuation_token": 0.12,
            "pagination_test": 0.08,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.58,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 8,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 2,
                "duration_min": 31,
            },
        },
        "meta": meta_common(
            codebase_type="CLI / data pipeline (Python 3.12 S3 prefix census)",
            bug_class="silent truncation: ListObjectsV2 pager used v1 Marker; first fix still ignored ContinuationToken",
            test_harness="pytest + aws s3api + jq",
            noise_steps={"429": 4, "502": 6},
            noise_recovery_steps={"429": 5, "502": 7},
            plan_change_step=8,
            debug_loop_steps=[9, 10, 11, 12, 13, 14],
            tags=[
                "s3",
                "list-objects-v2",
                "continuation-token",
                "marker-vs-token",
                "pagination",
                "inventory",
            ],
        ),
    }


def ep2() -> dict:
    """lockfold-cron: startingDeadlineSeconds uses window minutes as seconds."""
    steps = [
        {
            "n": 1,
            "decision_basis": db(
                "Plan: PW-77 reports lockfold-nightly skipped after the 02:00 window. Search startingDeadlineSeconds and window_minutes as evidence of a too-small deadline."
            ),
            "plan": "1) search deadline renderer 2) read starting_deadline_seconds 3) measure live CronJob 4) fix units 5) regression 6) apply or hand off",
            "tool_call": {
                "name": "search",
                "args": {
                    "pattern": "startingDeadlineSeconds|window_minutes|Europe/Dublin|schedule",
                    "path": ".",
                },
            },
            "observation": (
                "lockfold/deadline.py:4:def starting_deadline_seconds(window_minutes: int) -> int:\n"
                "lockfold/deadline.py:7:    return window_minutes\n"
                "lockfold/render.py:22:    spec[\"startingDeadlineSeconds\"] = starting_deadline_seconds(window_minutes)\n"
                "lockfold/render.py:18:    spec[\"schedule\"] = \"0 2 * * *\"\n"
                "deploy/cronjob.yaml:11:  startingDeadlineSeconds: 15\n"
                "deploy/cronjob.yaml:9:  schedule: \"0 2 * * *\"\n"
                "7 matches"
            ),
            "reflection": "Found starting_deadline_seconds returning window_minutes unchanged, and the live YAML already has startingDeadlineSeconds: 15 with a 02:00 schedule.",
        },
        {
            "n": 2,
            "decision_basis": db(
                "Observation: deadline.py:7 returns window_minutes as the seconds field (step 1). Read the helper as evidence of any * 60 conversion."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "lockfold/deadline.py", "offset": 1, "limit": 20},
            },
            "observation": (
                "1  # Window is configured in minutes so operators can say \"15 minutes after 02:00\".\n"
                "2  # CronJob spec wants seconds. The first cut assumed the names already matched.\n"
                "3\n"
                "4  def starting_deadline_seconds(window_minutes: int) -> int:\n"
                "5      if window_minutes < 0:\n"
                "6          raise ValueError(\"window_minutes must be >= 0\")\n"
                "7      return window_minutes\n"
                "8\n"
                "9  DEFAULT_WINDOW_MINUTES = 15\n"
            ),
            "reflection": "Learned there is no minute-to-second conversion. First plan: the 02:00 CronJob is IST vs UTC. Next measure the live object.",
        },
        {
            "n": 3,
            "decision_basis": db(
                "Observation: DEFAULT_WINDOW_MINUTES is 15 and the helper returns 15 (step 2). kubectl get the CronJob as evidence of lastScheduleTime vs deadline."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-peatwharf",
                    "namespace": "peatwharf",
                    "argv": [
                        "get",
                        "cronjob",
                        "lockfold-nightly",
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
                ") occurred attempting to list CronJob.batch/lockfold-nightly"
            ),
            "reflection": "kind apiserver ingress returned 502 before headers. Retry with a longer request timeout and write the object locally.",
        },
        {
            "n": 4,
            "decision_basis": db(
                "Observation: kubectl get cronjob returned 502 from the kind ingress (step 3). Retry --request-timeout=30s and write /tmp/lockfold-cj.json as evidence."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-peatwharf",
                    "namespace": "peatwharf",
                    "argv": [
                        "get",
                        "cronjob",
                        "lockfold-nightly",
                        "-o",
                        "json",
                        "--request-timeout=30s",
                    ],
                },
            },
            "observation": (
                "{\n"
                '  "metadata": {"name": "lockfold-nightly", "namespace": "peatwharf"},\n'
                '  "spec": {\n'
                '    "schedule": "0 2 * * *",\n'
                '    "startingDeadlineSeconds": 15,\n'
                '    "concurrencyPolicy": "Forbid",\n'
                '    "timeZone": "Etc/UTC"\n'
                "  },\n"
                '  "status": {\n'
                '    "lastScheduleTime": "2026-09-01T02:00:00Z",\n'
                '    "lastSuccessfulTime": "2026-09-01T02:04:11Z"\n'
                "  }\n"
                "}\n"
                "wrote /tmp/lockfold-cj.json"
            ),
            "reflection": "Measured startingDeadlineSeconds=15, timeZone Etc/UTC, last success yesterday 02:04Z. Tonight's run is missing. Next inspect events.",
        },
        {
            "n": 5,
            "decision_basis": db(
                "Observation: CronJob lastScheduleTime is yesterday 02:00Z with deadline 15 (step 4). kubectl events as evidence of a missed starting window."
            ),
            "tool_call": {
                "name": "kubectl",
                "args": {
                    "context": "kind-peatwharf",
                    "namespace": "peatwharf",
                    "argv": [
                        "get",
                        "events",
                        "--field-selector",
                        "involvedObject.name=lockfold-nightly",
                        "--sort-by=.lastTimestamp",
                    ],
                },
            },
            "observation": (
                "LAST SEEN   TYPE      REASON              OBJECT                      MESSAGE\n"
                "47m         Warning   SawCompletedJob     cronjob/lockfold-nightly    Saw completed job lockfold-nightly-29800160, can be anything but an active job\n"
                "11m         Warning   MissedSchedule      cronjob/lockfold-nightly    Cannot determine if job needs to be started: too late: starting deadline (15s) exceeded"
            ),
            "reflection": "Found MissedSchedule: starting deadline (15s) exceeded. That is seconds, not a timezone miss. Confirm against the Kubernetes docs next.",
        },
        {
            "n": 6,
            "decision_basis": db(
                "Observation: events say starting deadline (15s) exceeded (step 5). Fetch the CronJob deadline docs via gh as evidence of the unit contract."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "api",
                    "method": "GET",
                    "path": "repos/kubernetes/website/contents/content/en/docs/concepts/workloads/controllers/cron-jobs.md",
                },
            },
            "observation": (
                "HTTP/2 429\n"
                "retry-after: 6\n"
                "x-ratelimit-limit: 60\n"
                "x-ratelimit-remaining: 0\n"
                '{"message":"API rate limit exceeded for user ci-runner (60 req/h GitHub); retry_after=6",'
                '"documentation_url":"https://docs.github.com/rest/overview/rate-limits"}'
            ),
            "reflection": "GitHub returned 429 with retry-after 6 while fetching CronJob docs. Wait, then use the vendored docs/cronjob-starting-deadline.md fixture.",
        },
        {
            "n": 7,
            "decision_basis": db(
                "Observation: gh api returned 429 with retry_after 6 (step 6). Sleep 7s, then read docs/cronjob-starting-deadline.md as local-docs evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "docs/cronjob-starting-deadline.md", "offset": 1, "limit": 18},
            },
            "observation": (
                "1  startingDeadlineSeconds is an optional *seconds* deadline.\n"
                "2  If a CronJob misses its scheduled time for any reason (controller down, job still running under Forbid),\n"
                "3  the controller counts missed starts. If the deadline is exceeded, it does not start the Job and emits MissedSchedule.\n"
                "4  A 15-minute operator window must be 15 * 60 = 900 seconds.\n"
                "5  15 seconds will miss any start delayed more than 15s.\n"
                "6  timeZone on the CronJob is independent of this field.\n"
            ),
            "reflection": "Verified the field is seconds and 15 minutes must be 900. timeZone is independent. Next join that with the helper return.",
        },
        {
            "n": 8,
            "decision_basis": db(
                "Observation: docs require 900 seconds for a 15-minute window (step 7). jq spec.startingDeadlineSeconds from the saved CronJob as evidence of the live unit."
            ),
            "tool_call": {
                "name": "jq",
                "args": {
                    "argv": [
                        "-r",
                        "{schedule:.spec.schedule,tz:.spec.timeZone,deadline:.spec.startingDeadlineSeconds,last:.status.lastScheduleTime}",
                        "/tmp/lockfold-cj.json",
                    ]
                },
            },
            "observation": (
                "{\n"
                '  "schedule": "0 2 * * *",\n'
                '  "tz": "Etc/UTC",\n'
                '  "deadline": 15,\n'
                '  "last": "2026-09-01T02:00:00Z"\n'
                "}"
            ),
            "reflection": (
                "Plan change: live deadline is 15 seconds with timeZone already UTC, so the IST conversion plan is false. "
                "Abandon timezone edits. Switching the edit target to starting_deadline_seconds so 15 minutes become 900 seconds."
            ),
        },
        {
            "n": 9,
            "decision_basis": db(
                "Reflection: pivoting off timezone; deadline 15s is the miss (step 8). Refuse deleting the CronJob to 'unstick' tonight's skip."
            ),
            "tool_call": {
                "name": "refuse",
                "args": {
                    "action": "kubectl delete cronjob/lockfold-nightly so a freshly created object picks a new deadline tonight",
                    "policy": "SCHED-CRON-02",
                    "incident": "PW-77",
                },
            },
            "observation": (
                "refused: SCHED-CRON-02 forbids deleting CronJob/lockfold-nightly to skip a MissedSchedule. "
                "Delete would drop history and can fail-open the lockfold window. "
                "Safe alternative: patch startingDeadlineSeconds to minutes*60 and keep Forbid concurrency."
            ),
            "reflection": "Denied the delete. Next patch starting_deadline_seconds; keep the CronJob object.",
        },
        {
            "n": 10,
            "decision_basis": db(
                "Observation: delete is refused; edit target is starting_deadline_seconds (step 9). First patch: add 1 minute as an off-by-one on the returned seconds."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "lockfold/deadline.py",
                    "old_string": (
                        "def starting_deadline_seconds(window_minutes: int) -> int:\n"
                        "    if window_minutes < 0:\n"
                        "        raise ValueError(\"window_minutes must be >= 0\")\n"
                        "    return window_minutes\n"
                    ),
                    "new_string": (
                        "def starting_deadline_seconds(window_minutes: int) -> int:\n"
                        "    if window_minutes < 0:\n"
                        "        raise ValueError(\"window_minutes must be >= 0\")\n"
                        "    return window_minutes + 1\n"
                    ),
                },
            },
            "observation": "Edited lockfold/deadline.py: helper now returns window_minutes + 1 (16 for the default 15-minute window).",
            "reflection": "Wrote a +1 off-by-one instead of a minute-to-second conversion. Add a pytest that requires 15 minutes == 900 seconds.",
        },
        {
            "n": 11,
            "decision_basis": db(
                "Observation: helper now returns window_minutes+1 (step 10). Write a pytest that measures starting_deadline_seconds(15) == 900."
            ),
            "tool_call": {
                "name": "write_file",
                "args": {
                    "path": "tests/test_deadline.py",
                    "content": (
                        "from lockfold.deadline import starting_deadline_seconds\n\n"
                        "def test_starting_deadline_seconds_is_minutes_times_60():\n"
                        "    got = starting_deadline_seconds(15)\n"
                        "    assert got == 900, f\"got={got} want=900 (15*60)\"\n"
                    ),
                },
            },
            "observation": "Wrote tests/test_deadline.py (6 lines).",
            "reflection": "Created a unit conversion regression. Run pytest to reproduce the +1 miss.",
        },
        {
            "n": 12,
            "decision_basis": db(
                "Plan: run pytest tests/test_deadline.py as evidence whether window_minutes+1 satisfies the 900-second contract."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_deadline.py -q --tb=short 2>&1 | tail -n 20"
                },
            },
            "observation": (
                "F\n"
                "=================================== FAILURES ===================================\n"
                "__________ test_starting_deadline_seconds_is_minutes_times_60 __________\n"
                "tests/test_deadline.py:5: in test_starting_deadline_seconds_is_minutes_times_60\n"
                "    assert got == 900, f\"got={got} want=900 (15*60)\"\n"
                "E   AssertionError: got=16 want=900 (15*60)\n"
                "E   assert 16 == 900\n"
                "FAILED tests/test_deadline.py::test_starting_deadline_seconds_is_minutes_times_60 - AssertionError: got=16 want=900 (15*60)\n"
                "1 failed in 0.04s"
            ),
            "reflection": "Test failed: got=16, not 900. Re-read starting_deadline_seconds and multiply minutes by 60.",
        },
        {
            "n": 13,
            "decision_basis": db(
                "Observation: pytest failed with got=16 want=900 (step 12). Re-read deadline.py for the +1 return evidence."
            ),
            "tool_call": {
                "name": "read_file",
                "args": {"path": "lockfold/deadline.py", "offset": 1, "limit": 12},
            },
            "observation": (
                "1  # Window is configured in minutes so operators can say \"15 minutes after 02:00\".\n"
                "2  # CronJob spec wants seconds. The first cut assumed the names already matched.\n"
                "3\n"
                "4  def starting_deadline_seconds(window_minutes: int) -> int:\n"
                "5      if window_minutes < 0:\n"
                "6          raise ValueError(\"window_minutes must be >= 0\")\n"
                "7      return window_minutes + 1\n"
                "8\n"
                "9  DEFAULT_WINDOW_MINUTES = 15\n"
            ),
            "reflection": "Confirmed line 7 is still minutes plus one. The CronJob field is seconds. Patch to window_minutes * 60.",
        },
        {
            "n": 14,
            "decision_basis": db(
                "Reflection: helper must return minutes*60, not minutes+1 (step 13). Patch starting_deadline_seconds to the second conversion."
            ),
            "tool_call": {
                "name": "edit_file",
                "args": {
                    "path": "lockfold/deadline.py",
                    "old_string": "    return window_minutes + 1\n",
                    "new_string": "    return window_minutes * 60\n",
                },
            },
            "observation": "Edited lockfold/deadline.py: starting_deadline_seconds now returns window_minutes * 60 (900 for the default 15).",
            "reflection": "Patched the unit conversion. Re-run pytest; 15 minutes should now be 900 seconds.",
        },
        {
            "n": 15,
            "decision_basis": db(
                "Observation: helper now returns minutes*60 (step 14). Re-run pytest tests/test_deadline.py as verification evidence."
            ),
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": "pytest tests/test_deadline.py tests/test_render.py -q --tb=short 2>&1 | tail -n 12"
                },
            },
            "observation": (
                "......\n"
                "6 passed in 0.09s"
            ),
            "reflection": "Verified 6 passed including test_starting_deadline_seconds_is_minutes_times_60. Check gate-cli before applying the CronJob.",
        },
        {
            "n": 16,
            "decision_basis": db(
                "Observation: pytest passed 6/6 after the *60 patch (step 15). Run gate-cli check apply as evidence whether prod CronJob mutation is allowed."
            ),
            "tool_call": {
                "name": "gate-cli",
                "args": {
                    "argv": [
                        "check",
                        "apply",
                        "--change",
                        "lockfold-cron-deadline",
                        "--resource",
                        "cronjob/lockfold-nightly",
                    ]
                },
            },
            "observation": (
                "gate-cli check apply --change lockfold-cron-deadline\n"
                "status: REJECT\n"
                "policy: prod-batch-freeze\n"
                "ticket: PW-88\n"
                "until: 2026-09-09T00:00:00Z\n"
                "evidence: change mutates CronJob/lockfold-nightly (nightly lockfold window)\n"
                "found 0 waivers"
            ),
            "reflection": "Measured REJECT under PW-88 freeze through 2026-09-09. Do not kubectl apply. Open a handoff issue attaching the unit fix.",
        },
        {
            "n": 17,
            "decision_basis": db(
                "Observation: gate-cli REJECT'd the CronJob apply under freeze PW-88 (step 16). Open a handoff issue as evidence the live deadline is still 15s."
            ),
            "tool_call": {
                "name": "gh",
                "args": {
                    "subcommand": "issue",
                    "verb": "create",
                    "title": "PW-91: apply lockfold startingDeadlineSeconds=900 after PW-88 freeze (blocks PW-77 close)",
                    "body": "starting_deadline_seconds now returns minutes*60; pytest 6 passed. Live CronJob still has startingDeadlineSeconds: 15. gate-cli freeze PW-88 until 2026-09-09. Do not kubectl delete the CronJob.",
                },
            },
            "observation": "https://git.peatwharf.internal/sched/lockfold-cron/issues/91",
            "reflection": "Opened PW-91. Renderer is green; prod apply remains blocked. Handoff, not close.",
        },
    ]
    return {
        "id": "act-r15-cron-deadline-seconds",
        "goal": (
            "PW-77 (lockfold-cron, Python 3.12 CronJob renderer + kind peatwharf; pytest + kubectl): "
            "lockfold-nightly did not start after the 02:00 UTC window; events mention a missed starting deadline. "
            "Find why the job is skipped, fix the renderer, and apply or hand off. Designed plant; not a live cluster trace."
        ),
        "steps": steps,
        "outcome": (
            "starting_deadline_seconds returned window_minutes as CronJob startingDeadlineSeconds, so a 15-minute operator window became 15 seconds. "
            "A first patch that added 1 still failed test_starting_deadline_seconds_is_minutes_times_60 (got=16 want=900). "
            "The helper now returns minutes*60; pytest 6 passed. "
            "Applying CronJob/lockfold-nightly remains blocked by gate-cli freeze PW-88; live startingDeadlineSeconds is still 15. "
            "PW-91 opened. Overall: incomplete; prod apply unresolved."
        ),
        "reward": {
            "success": False,
            "task_completion": 0.24,
            "deadline_unit_fix": 0.10,
            "minutes_times_60_test": 0.08,
            "prod_apply_blocked_penalty": -0.12,
            "noise_retry_overhead_penalty": -0.02,
            "total": 0.28,
            "aggregation": "unweighted sum of the numeric components above (success is a boolean label, not a summand); rounding_decimals 2",
            "cost": {
                "tests_passed": 6,
                "tests_failed_final": 0,
                "wasted_calls": 2,
                "retries": 3,
                "duration_min": 37,
                "prod_apply": 0,
            },
        },
        "meta": meta_common(
            codebase_type="CLI / Kubernetes CronJob renderer (Python 3.12)",
            bug_class="off-by-unit: startingDeadlineSeconds used minutes as seconds; first fix was +1 not *60",
            test_harness="pytest + kubectl + gate-cli",
            noise_steps={"502": 3, "429": 6},
            noise_recovery_steps={"502": 4, "429": 7},
            plan_change_step=8,
            debug_loop_steps=[10, 11, 12, 13, 14, 15],
            tags=[
                "cronjob",
                "startingDeadlineSeconds",
                "unit-conversion",
                "missed-schedule",
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
    return """# ACTF r15 — 2026-09-02-final-heavy (grok-4.6)

Quota Q=2 designed coding episodes (FACTORY_QUOTAS=2). IDs `act-r15-s3-continuation-token`, `act-r15-cron-deadline-seconds` (mill prefix `act`, unused in-repo). Envelope: id/goal/steps/outcome/reward/meta. Tools restricted to verify_execution KNOWN_TOOLS (`bash`/`read_file`/`edit_file`/`write_file`/`search`/`gh`/`kubectl`/`gate-cli`/`aws`/`jq`/`refuse`). meta.round=15 factory=agentic-coding-trajectory-factory generator=grok-4.6 run_label=2026-09-02-final-heavy sim_or_real=designed. meta.rights RM-793 research_only; training_ready false. Never wrote outputs/raw/. r13/r14 staging dirs were empty; novelty is vs staged r10–r12 plus committed mill (meterflow/hubgate/shardup/tollgate/feedloom/tallyhouse). Invented repos `git.mossreel.internal/ops/reedkiln-s3walk.git` and `git.peatwharf.internal/sched/lockfold-cron.git`.

| id | codebase / harness | bug class | result | reward.total |
|----|--------------------|-----------|--------|--------------|
| act-r15-s3-continuation-token | Python 3.12 S3 prefix census + inventory fixtures / pytest + aws s3api + jq | silent truncation: ListObjectsV2 pager sent v1 `Marker`; first loop still ignored `ContinuationToken` | success; 8/8; PR 214 | 0.58 |
| act-r15-cron-deadline-seconds | Python 3.12 CronJob renderer / pytest + kubectl + gate-cli | off-by-unit: `startingDeadlineSeconds` used minutes as seconds; first fix was +1 not *60 | incomplete HIL/prod apply; PW-91; freeze PW-88 | 0.28 |

## Step counts, noise, plan change
- act-r15-s3-continuation-token: 15 steps. 429 at step 4 (`aws s3api get-bucket-inventory-configuration`, retry-after 7) → recovery step 5 (`sleep 8` + jq `fixtures/inventory-2026-08-31-summary.json` key_count 18421). 502 at step 6 (`aws s3api get-object` inventory manifest ELB) → recovery step 7 (`jq` committed manifest schema). Plan change at step 8: jq join shows page0 MaxKeys=1000 truncated vs inventory 18421; abandon raising MaxKeys. Debug loop: 9 edit Marker+loop → 10 write ContinuationToken-only pytest → 11 FAIL got=2000 Marker on second call → 12 re-read list_page → 13 ContinuationToken patch → 14 8 passed.
- act-r15-cron-deadline-seconds: 17 steps. 502 at step 3 (`kubectl get cronjob` kind ingress) → recovery step 4 (`--request-timeout=30s` writes /tmp/lockfold-cj.json). 429 at step 6 (`gh api` kubernetes/website cron-jobs.md, retry-after 6) → recovery step 7 (read vendored `docs/cronjob-starting-deadline.md`). Plan change at step 8: jq deadline=15 with timeZone already UTC plus MissedSchedule 15s; abandon IST conversion. Debug loop: 10 edit +1 → 11 write 900s pytest → 12 FAIL got=16 → 13 re-read helper → 14 *60 patch → 15 6 passed. `refuse` at step 9 blocks `kubectl delete cronjob`. gate-cli REJECT at 16; PW-91 at 17.

## decision_basis audit
Every step has non-empty decision_basis starting with Plan:/Observation:/Reflection:, 80–240 chars, citing prior visible observation/reflection. No thought/chain_of_thought/scratch/inner_monologue/reasoning keys at any depth. Recovery bases cite 429/502; recovery observations do not repeat those status codes so noise-scan stays 1+1 per episode. Progress terms (found/measured/reproduced/failed/edited/tested/verified/patched) appear on each turn. Word "hypothesis" kept out of observations.

## Reward
Unweighted numeric sum; success is a label. Cost sits under reward.cost. s3-continuation-token: 0.40+0.12+0.08−0.02=0.58. cron-deadline-seconds: 0.24+0.10+0.08−0.12−0.02=0.28.

## Realism / weak recovery
Good: Marker vs ContinuationToken is a real boto/ListObjects v1→v2 footgun; the first loop still double-counts because the fake client only honors ContinuationToken. startingDeadlineSeconds minutes-as-seconds is the usual CronJob silent skip; +1 is the equally tempting off-by-one and the 900s test names the contract. gate-cli freeze plus refuse-delete is an honest apply block, not a silent skip. Weak: inventory 502 fallback is availability (committed manifest is not a stale CSV whose key_count disagrees with a second fixture); kubectl json dump is one object; no reviewer asking to keep Marker "for v1 clients". Next densification: a 502 whose local inventory fixture is stale (summary 18421, CSV 1000, SKI-style mismatch), or a reviewer asking to set startingDeadlineSeconds: 0 "to disable skips".

Novel coverage: 40%
"""


def main() -> int:
    recs = [ep1(), ep2()]
    for rec in recs:
        validate_record(rec)
    OUT.mkdir(parents=True, exist_ok=True)
    batch = OUT / "batch-r15.jsonl"
    with batch.open("w", encoding="utf-8") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    notes_path = OUT / "NOTES-r15.md"
    notes_path.write_text(notes(), encoding="utf-8")
    errors, warnings, kinds, n = check_jsonl(
        batch, "batch-r15.jsonl", staging=FactoryStaging(enabled=True)
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
