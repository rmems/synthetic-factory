"""Tiny leftover-spec row for OBS catalog extract tests. Not a mill."""

from pathlib import Path

OUT = Path("scripts/observability_debug_mill/mill_plants_ab.py")

SPECS = [
    dict(
        vendor="Tiny Broker",
        ok_slug="tiny-metrics-off-leftover",
        bad_slug="tiny-met-raise-q-not-enable",
        noun="keel",
        panel="Tiny metrics",
        needle="tiny_up",
        lie_core="prometheus leftover scrape path /missing",
        false_lead="Tiny smp leftover",
        avoided="; leftover8 Kong prometheus",
        knob=".prometheus.path",
        old="path: /missing",
        new="path: /metrics",
        wrong_knob=".smp",
        wrong_old="smp: 1",
        wrong_new="smp: 4",
        wrong2_old="name: sandbox",
        wrong2_new="name: hangar",
        prefix="tinyb",
    ),
]
