#!/usr/bin/env python3
"""Emit TTF r42 window JSONL (ttf-r42-701..705) into /tmp/ttf-r42w/. Never writes outputs/raw/."""

from __future__ import annotations

import json
import math
import random
import re
import subprocess
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-r42w")
BATCH_PATH = OUT_DIR / "batch-r42.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r42.md"
REPO = Path("/home/raulmc/rmems/synthetic-factory")
PIPELINES = REPO / "pipelines"
WINDOW_FACTORY = (
    REPO
    / "outputs"
    / "raw"
    / "2026-09-02-final-heavy"
    / "thalamic-trajectory-factory"
)

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T19:20:00Z"),
        ("intended_use", "research_only"),
        ("project_training_policy", "blocked"),
        ("research_retention_status", "allowed"),
        ("research_evaluation_status", "allowed"),
        ("redistribution_status", "unresolved"),
        ("provider_training_status", "unresolved"),
        ("weight_publication_status", "blocked"),
        ("status_basis", "RM-793 project policy: xAI hosted outputs are research-only"),
        ("linear_issue", "RM-793"),
    ]
)
AGG = "total = task_progress + safety + efficiency + coherence + exploration"
CHANNEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,31}$")

THIS_DOMAINS = (
    "potassium-perchlorate-crystallizer",
    "holmium-chloride-still",
    "gadolinium-gallium-garnet-puller",
    "erbium-oxide-calciner",
    "thulium-metal-distiller",
)
THIS_PLANTS = (
    "Perchlor-Beck",
    "Holmia-Knap",
    "Garnet-Wold",
    "Erbia-Clough",
    "Thulia-Fen",
)
IDS = [f"ttf-r42-{n}" for n in range(701, 706)]
NOVEL_COVERAGE_LINE = "Novel coverage: 19.0%"
PLANT_RE = re.compile(r"\b([A-Z][A-Za-z]+(?:-[A-Z][A-Za-z0-9]+)+)\b")
THOUGHT_KEYS = {
    "thought",
    "reasoning",
    "chain_of_thought",
    "hidden_reasoning",
    "inner_monologue",
    "scratch",
    "internal_reasoning",
    "internal_reasoning_verbatim",
    "thinking",
    "cot",
    "thoughts",
}
SITOUT_DOMAINS = {
    "warehouse-amr",
    "aerial-swarm",
    "underwater-rov",
    "grid-inspection",
    "humanoid-locomotion",
    "surgical-assist",
    "industrial-assembly",
    "autonomous-driving",
    "brick-tunnel-kiln",
    "steam-methane-reformer",
    "Bayer-digester",
    "polyethylene-loop-reactor",
    "copper-electrorefining",
    "beryllium-fluoride-reducer",
    "molybdenum-disulfide-roaster",
    "gallium-trichloride-still",
    "tantalum-ethoxide-hydrolyzer",
    "silicon-carbide-cvd-reactor",
    "methanol-synthesis-loop",
    "twin-roll-caster",
    "electrolytic-tinning-line",
    "heap-leach-pad",
    "grain-oriented-anneal",
    "niobium-pentachloride-chlorinator",
    "sulfur-hexafluoride-reactor",
    "cadmium-telluride-bridgman",
    "neodymium-fluoride-electrolyzer",
    "tungsten-carbide-carburizer",
}

