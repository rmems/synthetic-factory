"""Public gate. Measurement runs in a child process; this module does not judge."""

from __future__ import annotations

from ._contract import bind_import_twin, dumps_exact_json
from .harness import GateReport, run_gate

__all__ = ["GateReport", "check_bytes", "check_record"]


def check_bytes(payload: bytes) -> GateReport:
    """Judge the raw record bytes in a subprocess."""

    return run_gate(payload)


def check_record(record: dict) -> GateReport:
    """Serialize ``record`` and :func:`check_bytes` it."""

    return check_bytes(dumps_exact_json(record).encode("utf-8"))


bind_import_twin(__name__)
