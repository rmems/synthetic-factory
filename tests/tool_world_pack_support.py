#!/usr/bin/env python3
"""Shared helpers for the tool-world core test modules.

The committed ``counter-workspace`` pack's constants, fault rows and specs,
an environment with its fault menu removed, and a test case that copies the
pack into a temporary directory so a test can corrupt it without reading or
editing the committed catalog pins.
"""

from __future__ import annotations

import dataclasses
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tool_world_test_support as support

# The support module goes first: it puts pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import env as env_mod
from tool_world import faults as faults_mod

PACK = "counter-workspace"
ADD_SUB = "counter.add-sub"
DELETE_LOCK = "counter.delete-stale-lock"
RENAME = "counter.rename-config-key"
COMMITTED_TASKS = (ADD_SUB, DELETE_LOCK, RENAME)
FACTORY = "tool-world-workspace-factory"
SEEDS = (0, 1, 2, 3, 7)
refusal = support.refusal


def call(name: str, **args) -> dict:
    return {"name": name, "args": args}


def plain_env(task_id: str, seed: int = 0, **replace) -> env_mod.Environment:
    """An environment on the task with its fault menu removed unless ``replace`` says otherwise."""
    pack = support.load_pack(PACK)
    fields = {"faults": ()}
    fields.update(replace)
    return env_mod.Environment(pack, dataclasses.replace(pack.task(task_id), **fields), seed)


def fault_row(**overrides) -> dict:
    row = {
        "id": "f",
        "surface": "workspace",
        "kind": "transient_error",
        "tool": "run_tests",
        "marker": "EAGAIN",
    }
    row.update(overrides)
    return row


def spec(**overrides) -> faults_mod.FaultSpec:
    return faults_mod.fault_spec_from_row(fault_row(**overrides), "t")


RECOVERY_ROW = {"intent": "read the file again", "tool_call": call("read_file", path="x")}


def armed(entry: faults_mod.FaultSpec, occurrence: int = 1) -> faults_mod.ScheduledFault:
    return faults_mod.ScheduledFault(entry, True, occurrence)


def rewrite_json(path: Path, mutate) -> None:
    """Load the JSON file, apply ``mutate`` to the payload in place, and write it back."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutate(payload)
    path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")


def set_key(key, value):
    def mutate(payload):
        payload[key] = value

    return mutate


def drop_key(key):
    def mutate(payload):
        del payload[key]

    return mutate


class PackCase(unittest.TestCase):
    """A temporary root the committed pack is copied into, one copy per corruption."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="tool-world-core-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def copy_pack(self, name: str = PACK) -> Path:
        destination = Path(tempfile.mkdtemp(dir=self.root)) / name
        shutil.copytree(support.CATALOG_DIR / PACK, destination)
        return destination

    def corrupted(self, mutate) -> Path:
        directory = self.copy_pack()
        mutate(directory)
        return directory
