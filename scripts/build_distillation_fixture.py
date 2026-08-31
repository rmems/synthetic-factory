#!/usr/bin/env python3
"""Rebuild the committed distillation fixture run (issue #78).

Writes a small, real end-to-end run for the three families under
``tests/fixtures/distillation-run/`` plus a MANIFEST that records which oracles
actually ran, which were unavailable, and the conventional-baseline report.

The run is small on purpose. It proves the shape end to end; it is not a
corpus. ``MANIFEST.json`` says so in ``training_ready``.

Usage::

    python3 scripts/build_distillation_fixture.py [--out <dir>] [--force]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
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
import oracle_contract as oc  # noqa: E402
import router_baseline  # noqa: E402
import validate_distill  # noqa: E402

DEFAULT_OUT = REPO / "tests" / "fixtures" / "distillation-run"

FAULT_SEED = 20260823
FAULT_COUNT = 18
ENERGY_SEED = 20260823
ENERGY_COUNT = 4
ROUTER_SEED = 11
ROUTER_COUNT = 80


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# The identity this script writes into every manifest it produces. --force
# authenticates against it before deleting anything.
MANIFEST_PRODUCER = "scripts/build_distillation_fixture.py"

# The only names a distillation run contains beside its manifest.
RUN_LAYOUT = frozenset(
    {"MANIFEST.json", "fault-recovery", "energy-preferences", "moe-router"}
)


def _is_own_manifest(path: Path) -> bool:
    """True when ``path`` is a manifest this script itself wrote."""

    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return (
        isinstance(manifest, dict)
        and manifest.get("generated_by") == MANIFEST_PRODUCER
    )


def can_rebuild(out: Path) -> bool:
    """True when ``out`` is safe for ``--force`` to delete and rewrite.

    ``build()`` hands this directory to ``shutil.rmtree``, so "looks vaguely
    like a run" is not enough: a dataset or project directory that happens to
    contain an unrelated file named ``MANIFEST.json`` would be irreversibly
    deleted. A rebuildable target is empty, or is a distillation run this
    script wrote — its manifest names this script as the producer and nothing
    unexpected sits beside it.
    """

    if not out.is_dir():
        return False
    entries = list(out.iterdir())
    if not entries:
        return True
    if any(entry.name not in RUN_LAYOUT for entry in entries):
        return False
    manifest = out / "MANIFEST.json"
    return manifest.is_file() and _is_own_manifest(manifest)


def assert_rebuildable(out: Path) -> None:
    """Refuse ``--force`` unless ``out`` looks like a distillation run."""

    if out.is_dir():
        if can_rebuild(out):
            return
        raise SystemExit(
            f"{out} is not a distillation run this script wrote (expected an "
            f"empty directory, or a MANIFEST.json naming {MANIFEST_PRODUCER} "
            "beside the family directories); refusing to delete it"
        )
    raise SystemExit(f"{out} exists but is not a directory; refusing to delete it")


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
        "oracle_contract.curation_eligible; the energy records are "
        f"denominated in {meter.cost_quantity} "
        + (
            f"as measured by {meter.name}."
            if meter.measures_energy
            else "because no energy meter was readable on this host."
        )
    )


def _refuse_raw_tree(out: Path) -> None:
    """``outputs/raw`` is the immutable evidence tree; never touch it.

    ``--force`` hands ``out`` to ``shutil.rmtree`` — pointed beneath the raw
    root, that deletes published evidence, and even without ``--force`` the
    build would write fixture files into it. Refuse before any filesystem
    mutation, resolved so relative paths and symlinks cannot dodge the check.
    """

    resolved = out.resolve()
    raw_root = (REPO / "outputs" / "raw").resolve()
    if resolved == raw_root or raw_root in resolved.parents:
        raise SystemExit(
            f"refusing to build the fixture at {out}: outputs/raw is the "
            "immutable evidence tree (AGENTS.md) and may never be deleted "
            "or written to"
        )


def build(out: Path, force: bool = False) -> dict[str, Any]:
    _refuse_raw_tree(out)
    if out.exists():
        if not force:
            raise SystemExit(f"{out} exists; pass --force to rebuild it")
        assert_rebuildable(out)
        shutil.rmtree(out)

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
        # The constant, not a twin literal: `--force` authenticates manifests
        # against MANIFEST_PRODUCER in `_is_own_manifest`, so a divergence
        # here would make every manifest this script writes refuse its own
        # documented rebuild.
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
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    manifest = build(Path(args.out), force=args.force)
    print(json.dumps(manifest["validation"], indent=2, sort_keys=True))
    print(json.dumps(manifest["baseline"]["escalation"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
