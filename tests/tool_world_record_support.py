#!/usr/bin/env python3
"""Shared helpers for the record, scripted-policy, replay and generation test modules.

Every episode runs the scripted policy on a task of the committed
``counter-workspace`` pack and assembles its record; a generated run lives
in a private catalog under a temporary directory, so the committed pins
are never read or edited.
"""

from __future__ import annotations

import dataclasses
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tool_world_test_support as support

# The support module goes first: it puts pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import catalog as catalog_mod
from tool_world import env as env_mod
from tool_world import generate, records
from tool_world import pack as pack_mod
from tool_world import vocabulary as cv
from tool_world._contract import check_episode, load_strict_json, sha256_bytes
from tool_world.policies import scripted

PACK = "counter-workspace"
ADD_SUB = "counter.add-sub"
DELETE_LOCK = "counter.delete-stale-lock"
FACTORY = "tool-world-workspace-factory"
SEEDS = (1, 2, 3, 7)
HEX64 = "0" * 64
RECORD_ID = re.compile(r"^twd-[0-9a-f]{16}-[0-9a-f]{16}-\d+-\d{5}$")
TRANSIENT = "EAGAIN temporary failure"
refusal = support.refusal


def call(name: str, **args) -> dict:
    return {"name": name, "args": args}


def action(intent: str, tool_call: dict, captures: dict | None = None, **flags) -> pack_mod.Action:
    return pack_mod.Action(
        intent=intent,
        tool_call=tool_call,
        captures=captures or {},
        verification=flags.get("verification", False),
        confirmation=flags.get("confirmation", False),
    )


def task_variant(task_id: str, **replace) -> tuple[pack_mod.Pack, pack_mod.Task]:
    pack = support.load_pack(PACK)
    return pack, dataclasses.replace(pack.task(task_id), **replace)


def build(env, trajectory) -> dict:
    run = records.RunContext(HEX64, "twd-run-test", scripted.policy_sha256())
    return records.build_record(env, trajectory, run, 1)


def episode(task_id: str, seed: int = 1, variant: str = cv.VARIANT_GOLD, **replace):
    """Run the scripted policy on one task and assemble its record."""
    pack, task = task_variant(task_id, **replace)
    env = env_mod.Environment(pack, task, seed)
    trajectory = scripted.run(env, variant)
    return env, trajectory, build(env, trajectory)


def gate(view: dict) -> list[str]:
    return check_episode(
        view, "training_view", forbid_hidden_thought=True, enforce_terminal_outcome=True
    )


def read_candidates(run_dir: Path) -> list[dict]:
    lines = (run_dir / generate.CANDIDATES_FILENAME).read_text(encoding="utf-8").splitlines()
    return [load_strict_json(line) for line in lines if line.strip()]


def resign_bytes(run_dir: Path, payload: bytes) -> None:
    """Write raw candidate bytes and keep RUN.json's digest consistent with them."""
    (run_dir / generate.CANDIDATES_FILENAME).write_bytes(payload)
    run_file = run_dir / generate.RUN_FILENAME
    summary = json.loads(run_file.read_text(encoding="utf-8"))
    summary["candidates_sha256"] = sha256_bytes(payload)
    run_file.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def resign_run(run_dir: Path, candidates: list[dict]) -> None:
    """Rewrite the candidates and keep RUN.json's digest consistent with them."""
    payload = "\n".join(json.dumps(record, sort_keys=True) for record in candidates) + "\n"
    resign_bytes(run_dir, payload.encode("utf-8"))


class RunCase(unittest.TestCase):
    """A private catalog holding the workspace pack, and run requests into its temporary root."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="tool-world-replay-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.catalog_dir = support.private_catalog(self.root / "catalog", (PACK,))
        self.catalog = catalog_mod.load_catalog(self.catalog_dir)

    def request(self, **overrides) -> generate.RunRequest:
        fields = {
            "catalog_dir": self.catalog_dir,
            "out_dir": self.root / "run",
            "seed": 1,
            "count": 2,
            "factory": FACTORY,
            "variants": "all",
            "produced_at": support.PRODUCED_AT,
        }
        fields.update(overrides)
        return generate.RunRequest(**fields)
