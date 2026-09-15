#!/usr/bin/env python3
"""Rebuild the committed distillation fixture run (issue #78).

Writes a small, real end-to-end run for the three families under
``tests/fixtures/distillation-run/`` plus a MANIFEST that records which oracles
actually ran, which were unavailable, and the conventional-baseline report.

The run is small on purpose. It proves the shape end to end; it is not a
corpus. ``MANIFEST.json`` says so in ``training_ready``.

Usage::

    python3 scripts/build_distillation_fixture.py [--out <dir>] [--force]

``--out`` must not exist yet. The script never deletes or overwrites: a
rebuild of the committed fixture is written to a fresh directory and swapped
into ``tests/fixtures/distillation-run/`` by hand. ``--force`` is still
accepted, but in-place rebuilds are refused until a rebuild can preserve the
previous fixture, and anything else beside it, when a generator fails.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import energy_preferences  # noqa: E402
import fault_recovery  # noqa: E402
import moe_router  # noqa: E402
from oracle_grounded import distill_contract as oc  # noqa: E402
import router_baseline  # noqa: E402
import validate_distill  # noqa: E402
from raw_tree_guard import is_under_raw  # noqa: E402

DEFAULT_OUT = REPO / "tests" / "fixtures" / "distillation-run"

FAULT_SEED = 20260823
FAULT_COUNT = 18
ENERGY_SEED = 20260823
ENERGY_COUNT = 4
ROUTER_SEED = 11
ROUTER_COUNT = 80


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# The identity this script writes into every manifest it produces.
MANIFEST_PRODUCER = "scripts/build_distillation_fixture.py"


def _write_records(out: Path, written: dict[str, Any]) -> dict[str, Any]:
    """Write each batch and record its size and digest for the manifest."""

    files: dict[str, Any] = {}
    for relative, records in written.items():
        destination = out / relative
        oc.write_jsonl(destination, records)
        files[relative] = {"records": len(records), "sha256": _sha256(destination)}
    return files


def _baseline_summary(router_records: list[Any]) -> dict[str, Any]:
    """The student baseline the router records are scored against."""

    samples = router_baseline.dataset_from_records(router_records)
    baseline = router_baseline.evaluate_baselines(samples)
    baseline["target"] = router_baseline.TARGET_TOP1
    baseline["escalation"] = router_baseline.escalation_gate(baseline)
    return baseline


def _validation_summary(out: Path) -> dict[str, Any]:
    """Re-validate what was just written, refusing to publish a blocked run."""

    report = validate_distill.validate_path(out)
    report.pop("_stamped", None)
    if report["blocked"]:
        # A generator regression must fail the rebuild, not ship. The invalid
        # records are left in place for inspection, but no MANIFEST.json is
        # written and the exit code is nonzero, so nothing downstream can
        # mistake this for the documented rebuild having succeeded.
        first = [finding["error"] for finding in report["findings"][:3]]
        raise SystemExit(
            f"{out} does not validate; refusing to publish MANIFEST.json "
            f"over an invalid run: {first}"
        )
    return {
        key: report[key]
        for key in (
            "records",
            "valid",
            "invalid",
            "curation_eligible",
            "curation_ineligible_reasons",
            "families",
            "fault_outcomes",
            "preferred_policies",
        )
    }


def _oracles_block(
    meter: Any, meter_probe: dict[str, Any], router_oracle: Any, router_probe: dict[str, Any]
) -> dict[str, Any]:
    """An audit of which oracle actually ran, and what was unavailable here."""

    return {
        fault_recovery.FAMILY: {
            "ran": fault_recovery.ORACLE_NAME,
            "type": "deterministic_simulator",
            "authority": oc.AUTHORITY_AUTHORITATIVE,
            "unavailable": ["hardware_replay (no neuromorphic board present)"],
        },
        energy_preferences.FAMILY: {
            "ran": meter.name,
            "cost_quantity": meter.cost_quantity,
            "cost_is_energy": meter.measures_energy,
            "meter_probe": meter_probe,
            "unavailable": [
                entry["meter"]
                for entry in meter_probe["probed"]
                if not entry["available"]
            ],
        },
        moe_router.FAMILY: {
            "ran": router_oracle.name,
            "authority": router_oracle.authority,
            "is_llm_teacher": router_oracle.is_llm_teacher,
            "oracle_probe": router_probe,
            # Probed on this host, not hard-coded. The manifest is an audit
            # of what was available where the fixture was built, so a
            # rebuild on a host with transformers installed must say so
            # rather than repeat the original machine's answer.
            "unavailable": [
                f"{entry['name']} ({entry['detail']})"
                for entry in router_probe["oracles"]
                if not entry["available"]
            ],
        },
    }


def _training_ready_note(meter: Any, router_oracle: Any) -> str:
    """Why structural validity here is still not training-readiness."""

    return (
        "Structural validity is not training-readiness. The router records "
        f"come from a {router_oracle.authority} oracle and are excluded by "
        "distill_contract.curation_eligible; the energy records are "
        f"denominated in {meter.cost_quantity} "
        + (
            f"as measured by {meter.name}."
            if meter.measures_energy
            else "because no energy meter was readable on this host."
        )
    )


def _refuse_raw_tree(out: Path) -> None:
    """``outputs/raw`` is the immutable evidence tree; never touch it.

    The build would write fixture files into it. Refuse before any filesystem
    mutation through ``raw_tree_guard``, the repository's one raw-path
    detector: unlike a comparison against this checkout's resolved raw root,
    it also recognises another checkout's ``outputs/raw``, a symlink alias of
    the raw root and a bind mount of it.
    """

    if is_under_raw(out):
        raise SystemExit(
            f"refusing to build the fixture at {out}: outputs/raw is the "
            "immutable evidence tree (AGENTS.md) and may never be deleted "
            "or written to"
        )


def _refuse_existing(out: Path, force: bool) -> None:
    """Never build in place: an existing ``out`` is refused before any mutation.

    Deleting the previous fixture ahead of the generators cannot preserve it,
    or unrelated files beside it, when a generator fails, so ``--force`` is
    refused as well until a rebuild can. A fresh directory costs nothing and
    leaves the previous fixture exactly as it was.
    """

    if not out.exists():
        return
    reason = (
        "in-place --force rebuilds are refused" if force else "it would be overwritten"
    )
    raise SystemExit(
        f"{out} exists and {reason}: build into a fresh --out directory and swap "
        "it into place by hand, so a failed build never touches the previous fixture"
    )


def build(out: Path, force: bool = False) -> dict[str, Any]:
    _refuse_raw_tree(out)
    _refuse_existing(out, force)

    fault_records = fault_recovery.build_records(FAULT_SEED, FAULT_COUNT)

    meter, meter_probe = energy_preferences.select_meter(prefer_energy=True)
    energy_records = energy_preferences.build_records(
        ENERGY_SEED, ENERGY_COUNT, meter=meter, meter_probe=meter_probe, repeats=5
    )

    router_probe = moe_router.oracles_report()
    router_oracle = moe_router.ReferenceMoERouter()
    router_records = moe_router.build_records(
        ROUTER_SEED, ROUTER_COUNT, oracle=router_oracle
    )

    written = {
        "fault-recovery/batch-r01.jsonl": fault_records,
        "energy-preferences/batch-r01.jsonl": energy_records,
        "moe-router/batch-r01.jsonl": router_records,
    }
    files = _write_records(out, written)
    baseline = _baseline_summary(router_records)

    manifest = {
        "issue": "rmems/synthetic-factory#78",
        "generated_by": MANIFEST_PRODUCER,
        "schema_version": oc.SCHEMA_VERSION,
        "seeds": {
            fault_recovery.FAMILY: FAULT_SEED,
            energy_preferences.FAMILY: ENERGY_SEED,
            moe_router.FAMILY: ROUTER_SEED,
        },
        "files": files,
        "validation": _validation_summary(out),
        "oracles": _oracles_block(meter, meter_probe, router_oracle, router_probe),
        "baseline": baseline,
        "training_ready": False,
        "training_ready_note": _training_ready_note(meter, router_oracle),
    }
    (out / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument(
        "--force",
        action="store_true",
        help="accepted for compatibility; in-place rebuilds are refused, use a fresh --out",
    )
    args = parser.parse_args(argv)
    manifest = build(Path(args.out), force=args.force)
    print(json.dumps(manifest["validation"], indent=2, sort_keys=True))
    print(json.dumps(manifest["baseline"]["escalation"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
