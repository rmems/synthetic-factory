"""Tiny hop plant for OBS catalog extract tests. Not a mill."""

from __future__ import annotations


def P(**k):
    kind = k["kind"]
    k.setdefault("panel", f"{k['svc'].split('-')[0]} {kind}")
    k.setdefault("lpanel", f"{k['lsvc'].split('-')[0]} leftover")
    k.setdefault("file", f"{kind}/{k['dash']}.yaml")
    k.setdefault("lfile", f"{kind}/{k['ldash']}.yaml")
    k.setdefault("false_file", f"{kind}/{k['dash']}.false.yaml")
    k.setdefault("lfalse_file", f"{kind}/{k['ldash']}.false.yaml")
    k.setdefault("novel", 73)
    return k


PAIRS = [
    P(
        slug="tiny-mimir-cap",
        lslug="tiny-mimir-handoff",
        svc="tiny-hinge-svc",
        lsvc="tiny-flap-svc",
        dash="tiny-mimir",
        ldash="tiny-handoff",
        kind="mimir",
        lie="tiny leftover series cap",
        llie="tiny leftover handoff does not lift the cap",
        fail_val="10",
        fix_val="100000",
        query='tiny_total{job="tiny-hinge-svc"}',
        lquery='tiny_total{job="tiny-flap-svc"}',
        new_vs="tiny Mimir leftover, not Loki max_concurrent",
    ),
]
