#!/usr/bin/env python3
"""The two in-repo interpreters, the upstream adapters, and the availability probe.

The reference runtimes differ from each other by documented convention, not by
accident: that difference is the instrument this family measures with. The
upstream adapters cannot execute here and say so with a reason code.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_runtimes")
    from .nir_equivalence_interpreter import (  # noqa: E402,F401
        NirReferenceRuntime,
        UnsupportedConstruct,
        _integrate_membrane,
        _step_affine,
        _step_delay,
    )
    from .nir_equivalence_terms import (  # noqa: E402
        ALL_KNOWN_TYPES,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_runtimes"
    )
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from nir_equivalence_interpreter import (  # noqa: E402,F401
        NirReferenceRuntime,
        UnsupportedConstruct,
        _integrate_membrane,
        _step_affine,
        _step_delay,
    )
    from nir_equivalence_terms import (  # noqa: E402
        ALL_KNOWN_TYPES,
    )

class UnavailableRuntime:
    """An upstream runtime that is not present. It has no fallback path."""

    runtime_class = "upstream_runtime"

    def __init__(self, name, module=None, executable=None, detail=""):
        self.name = name
        self.module = module
        self.executable = executable
        self.detail = detail

    def availability(self):
        if self.module and importlib.util.find_spec(self.module) is not None:
            return {
                "available": False,
                "reason_code": "RUNTIME_ADAPTER_NOT_IMPLEMENTED",
                "detail": (
                    f"the {self.module!r} package is importable but this repository "
                    f"ships no adapter for it; {self.detail}"
                ),
            }
        if self.executable and shutil.which(self.executable):
            return {
                "available": False,
                "reason_code": "RUNTIME_ADAPTER_NOT_IMPLEMENTED",
                "detail": (
                    f"{self.executable!r} is on PATH but this repository ships no "
                    f"adapter for it; {self.detail}"
                ),
            }
        return {
            "available": False,
            "reason_code": "RUNTIME_NOT_INSTALLED",
            "detail": f"{self.name} is not installed in this environment; {self.detail}",
        }

    def execute(self, _graph, _stimulus):
        """Refuse, with the probe's reason code. Signature mirrors the runtime protocol."""
        status = self.availability()
        raise RuntimeUnavailable(self.name, status["reason_code"], status["detail"])


class RuntimeUnavailable(Exception):
    def __init__(self, runtime, reason_code, detail):
        super().__init__(f"{runtime}: {reason_code}: {detail}")
        self.runtime = runtime
        self.reason_code = reason_code
        self.detail = detail


REFERENCE_V1 = NirReferenceRuntime(
    name="nir_reference_v1",
    reset="subtract",
    delay_unit="steps",
    cycle_break_order="insertion",
    supported_types=ALL_KNOWN_TYPES,
)
REFERENCE_ALT = NirReferenceRuntime(
    name="nir_reference_v1_altorder",
    reset="zero",
    delay_unit="steps_minus_one",
    cycle_break_order="reverse_name",
    supported_types=ALL_KNOWN_TYPES - {"LI"},
)
UPSTREAM_RUNTIMES = (
    UnavailableRuntime(
        "nir_rs",
        executable="nir-rs",
        detail="the authority-contract oracle for this family",
    ),
    UnavailableRuntime(
        "nir_python",
        module="nir",
        detail="reference NIR serialization library",
    ),
    UnavailableRuntime(
        "nirtorch_snntorch",
        module="snntorch",
        detail="upstream-compatible execution backend",
    ),
)
IN_REPO_RUNTIMES = (REFERENCE_V1, REFERENCE_ALT)


def availability_report():
    report = {}
    for runtime in (*IN_REPO_RUNTIMES, *UPSTREAM_RUNTIMES):
        status = dict(runtime.availability())
        status["runtime_class"] = runtime.runtime_class
        report[runtime.name] = status
    return report


def _runtime_capability(runtime_name):
    runtime = (
        _ALL_RUNTIME_BY_NAME.get(runtime_name)
        if isinstance(runtime_name, str)
        else None
    )
    if runtime is None:
        return {"available": None, "reason_code": None}
    try:
        availability = runtime.availability()
    except Exception:  # noqa: BLE001 - validation reports the probe failure separately
        return {"available": None, "reason_code": None}
    if not isinstance(availability, dict):
        return {"available": None, "reason_code": None}
    available = availability.get("available")
    if available is not True and available is not False:
        available = None
    return {
        "available": available,
        "reason_code": availability.get("reason_code"),
    }


ALL_RUNTIMES = (*IN_REPO_RUNTIMES, *UPSTREAM_RUNTIMES)
EXPECTED_RUNTIME_NAMES = tuple(runtime.name for runtime in ALL_RUNTIMES)
_RUNTIME_BY_NAME = {runtime.name: runtime for runtime in IN_REPO_RUNTIMES}
_ALL_RUNTIME_BY_NAME = {runtime.name: runtime for runtime in ALL_RUNTIMES}


if __package__:
    _expose_package_sibling(__name__)
