"""Tiny leftover3 pair for OBS catalog extract tests. Not a mill."""

from __future__ import annotations

PAIRS: list[dict] = [
    {
        "slug": "tiny-dd-env-drop-leftover",
        "lslug": "tiny-nr-span-drop-leftover",
        "svc": "tiny-gate-svc",
        "lsvc": "tiny-jetway-svc",
        "lie": "tiny Datadog env tag leftover drops the APM panel",
        "llie": "tiny NR span leftover is not the Datadog bind",
        "file": "/etc/datadog-agent/datadog.yaml",
        "lfile": "/etc/newrelic-infra.yml",
        "fail_val": "true",
        "fix_val": "false",
        "query": "avg:trace.http.request{service:tiny-gate-svc}",
        "lquery": "SELECT average(duration) FROM Span",
    },
]
