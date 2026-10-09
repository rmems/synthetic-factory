#!/usr/bin/env python3
"""Shared helpers for the tool-world core test modules.

The committed ``counter-workspace`` pack's constants, fault rows and specs,
an environment with its fault menu removed, and a sandbox that copies the
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


def sandbox(case: unittest.TestCase, prefix: str = "tool-world-core-") -> Path:
    """A temporary root removed when ``case`` finishes; packs are copied into it to be corrupted."""
    root = Path(tempfile.mkdtemp(prefix=prefix))
    case.addCleanup(shutil.rmtree, root, True)
    return root


def copy_pack(root: Path, name: str = PACK) -> Path:
    """A fresh copy of the committed pack under ``root``, one copy per corruption."""
    destination = Path(tempfile.mkdtemp(dir=root)) / name
    shutil.copytree(support.CATALOG_DIR / PACK, destination)
    return destination


def corrupted(root: Path, mutate) -> Path:
    directory = copy_pack(root)
    mutate(directory)
    return directory
