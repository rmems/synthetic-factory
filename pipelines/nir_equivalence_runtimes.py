#!/usr/bin/env python3
"""The two in-repo interpreters, the upstream adapters, and the availability probe.

The reference runtimes differ from each other by documented convention, not by
accident: that difference is the instrument this family measures with. The
upstream adapters execute only where their runtime is actually present and
say so with a reason code where it is not: `nir_rs` is backed by the real
`nir-rs` crate through this workspace's `nir-rs` binary, probed on PATH (or
via `NIR_RS_EXECUTABLE`); the others have no fallback path.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess  # nosec B404 -- subprocess drives the env/PATH-gated adapter binaries
import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_runtimes")
    from .nir_equivalence_graph import (  # noqa: E402
        GraphError,
        _roundtrip_with_codec,
    )
    from .nir_equivalence_interpreter import (  # noqa: E402,F401  # pylint: disable=unused-import
        NirReferenceRuntime,
        RuntimeConventions,
        UnsupportedConstruct,
        _integrate_membrane,
        _step_affine,
        _step_delay,
    )
    from .nir_equivalence_observation import (  # noqa: E402
        OutputObservation,
        final_membrane,
    )
    from .nir_equivalence_terms import (  # noqa: E402
        ALL_KNOWN_TYPES,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_runtimes"
    )
    from nir_equivalence_graph import (  # noqa: E402
        GraphError,
        _roundtrip_with_codec,
    )
    from nir_equivalence_interpreter import (  # noqa: E402,F401  # pylint: disable=unused-import
        NirReferenceRuntime,
        RuntimeConventions,
        UnsupportedConstruct,
        _integrate_membrane,
        _step_affine,
        _step_delay,
    )
    from nir_equivalence_observation import (  # noqa: E402
        OutputObservation,
        final_membrane,
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


NIR_RS_NOT_INSTALLED_DETAIL = (
    "nir_rs is not installed in this environment; "
    "the authority-contract oracle for this family"
)
NIR_RS_PROBE_FAILED_DETAIL = (
    "a nir_rs executable was found but its availability handshake failed; "
    "the authority-contract oracle for this family"
)
NIR_RS_CONTRACT_MISMATCH_DETAIL = (
    "a nir_rs executable was found but declares conventions or coverage "
    "outside the documented adapter contract; "
    "the authority-contract oracle for this family"
)


class NirRsRuntime:
    """The ``nir-rs`` crate driven through this workspace's ``nir-rs`` binary.

    The binary (``rust/nir-rs``, crate ``nir-rs =0.4.4``) is the authority
    contract: it builds real ``NirGraph``/``NirNode``/``Tensor`` values, runs
    the crate's serde codec for the roundtrip claim, and executes under this
    family's declared ``subtract``/``steps``/``insertion`` conventions so both
    sides of a comparison ran under explicit semantics. When no binary is
    reachable the probe reports the same ``RUNTIME_NOT_INSTALLED`` diagnostic
    the unimplemented stub carried -- there is no substitute path.
    """

    name = "nir_rs"
    runtime_class = "upstream_runtime"
    executable = "nir-rs"
    executable_env = "NIR_RS_EXECUTABLE"
    conventions = {"reset": "subtract", "delay_unit": "steps", "cycle_break_order": "insertion"}
    supported_types = tuple(sorted(ALL_KNOWN_TYPES))

    def availability(self):
        binary = self._binary()
        if binary is None:
            return {
                "available": False,
                "reason_code": "RUNTIME_NOT_INSTALLED",
                "detail": NIR_RS_NOT_INSTALLED_DETAIL,
            }
        try:
            probe = self._request("availability", None)
        except (RuntimeUnavailable, GraphError, UnsupportedConstruct):
            # The diagnostic carries stable text so a recorded observation can
            # be re-authenticated after the generating host's environment
            # changes; the specific subprocess failure is host-local.
            return {
                "available": False,
                "reason_code": "RUNTIME_PROBE_FAILED",
                "detail": NIR_RS_PROBE_FAILED_DETAIL,
            }
        if not self._contract_ok(probe):
            return {
                "available": False,
                "reason_code": "RUNTIME_CONTRACT_MISMATCH",
                "detail": NIR_RS_CONTRACT_MISMATCH_DETAIL,
            }
        return {
            "available": True,
            "reason_code": None,
            "detail": f"nir-rs adapter at {binary} (crate nir-rs 0.4.4)",
        }

    def serialize_graph(self, graph):
        """Serialize through the crate's serde codec, via the binary."""
        return self._request("serialize", graph)

    def parse_graph(self, text):
        """Parse wire text back into an in-repo graph, via the binary."""
        return self._request("parse", text)

    def roundtrip_graph(self, graph):
        # `_roundtrip_with_codec` does not catch UnsupportedConstruct -- the
        # in-repo codec accepts every construct shape. This adapter's codec is
        # the crate's real serde boundary, and it refuses constructs outside
        # its declared coverage; the honest report for that is a parse failure.
        try:
            report = _roundtrip_with_codec(
                graph, self.serialize_graph, self.parse_graph
            )
        except UnsupportedConstruct as exc:
            report = {
                "parse_ok": False,
                "canonical_stable": False,
                "structure_stable": False,
                "reason_code": "ROUNDTRIP_PARSE_FAILURE",
                "detail": str(exc),
                "structure_digest": None,
            }
        report["runtime"] = self.name
        report["adapter"] = f"{self.name}.nir_rs_serde"
        return report

    def execute(self, graph, stimulus):
        """Run the graph on the crate's types; observation shaping stays here.

        The binary reports raw per-step output values and final membrane
        state; rounding, spike-event extraction, and the record-facing output
        shape are applied by the same observation helpers the in-repo runtimes
        use, so a `nir_rs` row is shaped identically to a reference row.
        """
        measured = self._request("execute", {"graph": graph, "stimulus": stimulus})
        observation = OutputObservation(graph, measured["output_node"])
        for values in measured["outputs"]:
            observation.append(values)
        state = {
            name: {"v": list(v)}
            for name, v in (measured.get("membrane") or {}).items()
        }
        return {
            "steps": measured["steps"],
            "output_node": measured["output_node"],
            "output_trace": observation.trace,
            "spike_events": observation.events,
            "spike_count": len(observation.events),
            "final_membrane": final_membrane(state),
            "evaluation_order": list(measured["evaluation_order"]),
            "recurrent_edges": sorted(
                [list(edge) for edge in measured["recurrent_edges"]]
            ),
        }

    def _contract_ok(self, probe):
        """The probe's declared conventions and coverage match this adapter."""
        if not isinstance(probe, dict):
            return False
        types_ok = tuple(probe.get("supported_types") or ()) == self.supported_types
        return probe.get("conventions") == self.conventions and types_ok

    def _binary(self):
        """The ``nir-rs`` adapter binary this run would drive, or None.

        A declared override must resolve to an executable file; one that does
        not is the same outcome as no binary at all.
        """
        override = os.environ.get(self.executable_env)
        if override:
            path = Path(override)
            if path.is_file() and os.access(path, os.X_OK):
                return override
            return None
        return shutil.which(self.executable)

    def _request(self, command, payload):
        """One subprocess round-trip against the ``nir-rs`` adapter binary."""
        binary = self._binary()
        if binary is None:
            raise RuntimeUnavailable(
                self.name, "RUNTIME_NOT_INSTALLED", NIR_RS_NOT_INSTALLED_DETAIL
            )
        envelope, returncode = self._read_envelope(binary, command, payload)
        return self._raise_for_envelope(binary, envelope, returncode)

    def _read_envelope(self, binary, command, payload):
        """The ``(envelope, returncode)`` the adapter answered, or a refusal."""
        try:
            # argv-array launch of the env/PATH-resolved adapter binary: the
            # environment is the documented trust boundary choosing which
            # ``nir-rs`` to drive, and no shell is involved.
            proc = subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit, python.lang.security.audit.dangerous-subprocess-use-tainted-env-args  # nosec B603
                [binary, command],
                input=None if payload is None else json.dumps(payload),
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeUnavailable(
                self.name,
                "RUNTIME_PROBE_FAILED",
                f"{binary!r} could not be executed: {exc}",
            ) from exc
        try:
            return json.loads(proc.stdout or ""), proc.returncode
        except ValueError as exc:
            raise RuntimeUnavailable(
                self.name,
                "RUNTIME_PROBE_FAILED",
                f"{binary!r} answered with unparseable output: {exc}",
            ) from exc

    def _raise_for_envelope(self, binary, envelope, returncode):
        """The ``result`` payload, or the typed failure the envelope names."""
        if returncode == 0 and isinstance(envelope, dict) and envelope.get("ok") is True:
            return envelope["result"]
        error = envelope.get("error") if isinstance(envelope, dict) else None
        error = error if isinstance(error, dict) else {}
        raise self._envelope_failure(binary, error)

    def _envelope_failure(self, binary, error):
        """The typed exception the envelope's error block names."""
        kind = error.get("kind")
        detail = error.get("detail") or f"{binary!r} failed without a diagnostic"
        if kind == "unsupported":
            return UnsupportedConstruct(
                error.get("node"), error.get("node_type"), detail
            )
        if kind == "graph":
            return GraphError(detail)
        return RuntimeUnavailable(self.name, "RUNTIME_PROBE_FAILED", detail)


REFERENCE_V1 = NirReferenceRuntime(
    name="nir_reference_v1",
    conventions=RuntimeConventions("subtract", "steps", "insertion"),
    supported_types=ALL_KNOWN_TYPES,
)
REFERENCE_ALT = NirReferenceRuntime(
    name="nir_reference_v1_altorder",
    conventions=RuntimeConventions("zero", "steps_minus_one", "reverse_name"),
    supported_types=ALL_KNOWN_TYPES - {"LI"},
)
NIR_RS = NirRsRuntime()
UPSTREAM_RUNTIMES = (
    NIR_RS,
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
# `nir_rs` joins the re-executable set: records may mark it `executed` and
# validation replays it, but only while the probe can reach the binary --
# `_reexecutable_runtime` gates on a live probe so an unavailable entry in an
# environment without the binary is still authenticated, not re-run.
_RUNTIME_BY_NAME = {
    runtime.name: runtime for runtime in (*IN_REPO_RUNTIMES, NIR_RS)
}
_ALL_RUNTIME_BY_NAME = {runtime.name: runtime for runtime in ALL_RUNTIMES}


if __package__:
    _expose_package_sibling(__name__)
