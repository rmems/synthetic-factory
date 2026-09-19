#!/usr/bin/env python3
"""End-to-end tests for the oracle-grounded CLIs and the committed fixtures.

The golden run under tests/fixtures/oracle-grounded/golden-r01/ is regenerated
here and compared byte for byte. That single check covers determinism,
reproducibility, and the identity of the implementation at once: if a simulator
changes, `oracle.module_digest` changes and this test fails loudly rather than
letting a fixture quietly stop describing the code that produced it.
"""

import copy
import errno
import hashlib
import io
import json
import os
import re
import shutil
import subprocess  # nosec B404 -- the CLI test harness executes fixed local scripts
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from oracle_grounded import canon, families, oracles, record  # noqa: E402
import oracle_generate  # noqa: E402
import oracle_validate  # noqa: E402
from oracle_fixture_replay import replay_diagnostic_fixture  # noqa: E402

GENERATE = REPO / "pipelines" / "oracle_generate.py"
VALIDATE = REPO / "pipelines" / "oracle_validate.py"
FIXTURES = REPO / "tests" / "fixtures" / "oracle-grounded"
GOLDEN = FIXTURES / "golden-r01"
INVALID = FIXTURES / "invalid"
PINNED_COMMIT = oracles.resolve_commit(REPO)[0]

__all__ = (
    "FIXTURES", "GENERATE", "GOLDEN", "INVALID", "PINNED_COMMIT", "Path", "REPO",
    "VALIDATE", "build", "canon", "errno", "families", "io", "json", "mock",
    "oracle_generate", "oracle_validate", "oracles", "os", "read_jsonl", "record",
    "relabel_as_named_runtime", "replay_diagnostic_fixture", "run_cli", "shutil", "sys",
    "tempfile", "unittest", "write_test_manifest",
)


def clean_env(**updates):
    env = dict(os.environ)
    for runtime in families.ALL_RUNTIMES:
        env.pop(oracles.env_key(runtime), None)
    env.update(updates)
    return env


def run_cli(script, *args, env=None):
    if env is None:
        env = clean_env()
    return subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603 -- argv is explicit test input, never a shell command
        [sys.executable, str(script), *[str(arg) for arg in args]],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _ensure_jsonl_counterparts(run_dir):
    # Scratch runs must have the same two-file family layout as production,
    # including an empty accepted or rejected side when every proposal lands
    # in the other verdict.
    for path in sorted(run_dir.rglob("*.jsonl")):
        match = re.fullmatch(r"(accepted|rejected)-r(\d+)\.jsonl", path.name)
        if match is None:
            continue
        other = "rejected" if match.group(1) == "accepted" else "accepted"
        counterpart = path.with_name(f"{other}-r{match.group(2)}.jsonl")
        if not counterpart.exists():
            counterpart.write_text("", encoding="utf-8")


def _runtime_probe(probe):
    return isinstance(probe, dict) and isinstance(probe.get("runtime"), str)


def _bound_runtime_probe(probe):
    return _runtime_probe(probe) and isinstance(probe.get("bound"), bool)


def _oracle_availability_shape(oracle):
    if not isinstance(oracle, dict) or not isinstance(oracle.get("implementation"), str):
        return False
    availability = oracle.get("availability")
    if not isinstance(availability, dict):
        return False
    probes = availability.get("runtimes")
    return isinstance(probes, list) and all(
        _bound_runtime_probe(probe) for probe in probes
    )


def _parsed_record(line):
    if not line.strip():
        return None
    try:
        item = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(item, dict) or not isinstance(item.get("family"), str):
        return None
    if not _oracle_availability_shape(item.get("oracle")):
        return None
    return item


def _scan_jsonl(run_dir):
    files = {}
    parsed = []
    for path in sorted(run_dir.rglob("*.jsonl")):
        body = path.read_bytes()
        lines = body.decode().splitlines()
        files[path.relative_to(run_dir).as_posix()] = {
            "sha256": hashlib.sha256(body).hexdigest(),
            "records": sum(1 for line in lines if line.strip()),
        }
        for line in lines:
            if (item := _parsed_record(line)) is not None:
                parsed.append((path, item))
    return files, parsed


def _family_records(parsed, family, verdict):
    prefix = f"{verdict}-"
    return [
        item
        for path, item in parsed
        if item["family"] == family and path.name.startswith(prefix)
    ]


def _family_summary(parsed, family, count_per_family):
    accepted = _family_records(parsed, family, "accepted")
    rejected = _family_records(parsed, family, "rejected")
    first = (accepted or rejected)[0]
    reasons = {
        reason
        for item in rejected
        for reason in item.get("validation", {}).get("reasons", [])
        if isinstance(reason, str)
    }
    return {
        "proposed": count_per_family,
        "accepted": oracle_generate.summarize(accepted),
        "rejected": {"records": len(rejected), "reasons": sorted(reasons)},
        "oracle": {
            "requested_runtime": list(families.spec_for(family).runtimes),
            "implementation": first["oracle"]["implementation"],
        },
    }


def _requested_runtime_order(family_names):
    return [
        runtime
        for family in families.FAMILY_NAMES
        if family in family_names
        for runtime in families.spec_for(family).runtimes
    ]


def _observed_probes(parsed):
    probes = {}
    for _path, item in parsed:
        availability = item.get("oracle", {}).get("availability", {})
        for probe in availability.get("runtimes", []):
            if _runtime_probe(probe):
                probes.setdefault(probe["runtime"], probe)
    return probes


def _availability(parsed, family_names):
    probes = _observed_probes(parsed)
    ordered = [
        probes[runtime]
        for runtime in _requested_runtime_order(family_names)
        if runtime in probes
    ]
    unbound = [probe["runtime"] for probe in ordered if not probe["bound"]]
    return {
        "protocol": oracles.PROTOCOL,
        "runtimes": ordered,
        "all_bound": not unbound,
        "unbound": unbound,
    }


def _manifest_note(parsed):
    # The validator recomputes this note from record publishability.
    any_publishable = any(
        isinstance(item.get("validation"), dict)
        and item["validation"].get("publishable") is True
        for _path, item in parsed
    )
    if any_publishable:
        return oracle_validate.MANIFEST_NOTE_PUBLISHABLE
    return oracle_validate.MANIFEST_NOTE_UNPUBLISHABLE


def _new_test_manifest(parsed, files):
    round_number = next(
        (
            item.get("meta", {}).get("round")
            for _path, item in parsed
            if isinstance(item.get("meta"), dict)
        ),
        1,
    )
    family_names = sorted({item["family"] for _path, item in parsed})
    counts = Counter(item["family"] for _path, item in parsed)
    count_per_family = max(counts.values(), default=1)
    family_summaries = {
        family: _family_summary(parsed, family, count_per_family)
        for family in family_names
    }
    first = parsed[0][1] if parsed else {}
    first_oracle = first.get("oracle", {}) if isinstance(first, dict) else {}
    return {
        "schema": record.SCHEMA_ID,
        "round": round_number,
        "seed": 20260823,
        "count_per_family": count_per_family,
        "families": family_summaries,
        "oracle_commit": first_oracle.get("commit", "0" * 40),
        "oracle_dirty": first_oracle.get("dirty", False),
        "module_digest": first_oracle.get("module_digest", oracles.module_digest()),
        "oracle_availability": _availability(parsed, family_names),
        "files": files,
        "generation_errors": [],
        "note": _manifest_note(parsed),
    }


def write_test_manifest(run_dir):
    run_dir = Path(run_dir)
    manifest_path = run_dir / "manifest.json"
    _ensure_jsonl_counterparts(run_dir)
    files, parsed = _scan_jsonl(run_dir)
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        manifest["files"] = files
    else:
        manifest = _new_test_manifest(parsed, files)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def build(family, index=0):
    return record.build_record(
        family,
        index,
        seed=20260823,
        run=record.RecordRunContext(commit=PINNED_COMMIT, dirty=False, environ={}),
    )


def relabel_as_named_runtime(item):
    item = copy.deepcopy(item)
    oracle = item["oracle"]
    oracle["implementation"] = "named-runtime"
    oracle["authority"] = "measured-runtime"
    item["provenance"]["claimed"] = "measured-runtime"
    item["meta"]["tags"][-1] = "named-runtime"
    oracle["runtime_bound"] = True
    oracle["availability"]["all_bound"] = True
    oracle["availability"]["unbound"] = []
    for probe in oracle["availability"]["runtimes"]:
        probe["bound"] = True
    stage_ids = []
    for stage, runtime in zip(oracle["stages"], oracle["requested_runtime"], strict=True):
        stage["implementation"] = "named-runtime"
        stage["oracle_id"] = runtime
        stage["version"] = "0.0.0-double"
        stage["runtime_commit"] = "a" * 40
        stage["executable"] = runtime
        stage.pop("module_digest", None)
        stage_ids.append(runtime)
    oracle["id"] = "+".join(stage_ids)
    item["result"]["produced_by"] = oracle["id"]
    item["result_hash"] = canon.digest(item["result"])
    item["validation"] = record.assess(item)
    return item
