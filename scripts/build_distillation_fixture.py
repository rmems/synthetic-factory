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


def build(out: Path, force: bool = False) -> dict[str, Any]:
    if out.exists():
        if not force:
            raise SystemExit(f"{out} exists; pass --force to rebuild it")
        shutil.rmtree(out)

    fault_records = fault_recovery.build_records(FAULT_SEED, FAULT_COUNT)

    meter, meter_probe = energy_preferences.select_meter(prefer_energy=True)
    energy_records = energy_preferences.build_records(
        ENERGY_SEED, ENERGY_COUNT, meter=meter, repeats=5
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
    files: dict[str, Any] = {}
    for relative, records in written.items():
        destination = out / relative
        oc.write_jsonl(destination, records)
        files[relative] = {"records": len(records), "sha256": _sha256(destination)}

    samples = router_baseline.dataset_from_records(router_records)
    baseline = router_baseline.evaluate_baselines(samples)
    baseline["target"] = router_baseline.TARGET_TOP1
    baseline["escalation"] = router_baseline.escalation_gate(baseline)

    report = validate_distill.validate_path(out)
    report.pop("_stamped", None)

    manifest = {
        "issue": "rmems/synthetic-factory#78",
        "generated_by": "scripts/build_distillation_fixture.py",
        "schema_version": oc.SCHEMA_VERSION,
        "seeds": {
            fault_recovery.FAMILY: FAULT_SEED,
            energy_preferences.FAMILY: ENERGY_SEED,
            moe_router.FAMILY: ROUTER_SEED,
        },
        "files": files,
        "validation": {
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
        },
        "oracles": {
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
        },
        "baseline": baseline,
        "training_ready": False,
        "training_ready_note": (
            "Structural validity is not training-readiness. The router records "
            f"come from a {router_oracle.authority} oracle and are excluded by "
            "oracle_contract.curation_eligible; the energy records are "
            f"denominated in {meter.cost_quantity} "
            + (
                f"as measured by {meter.name}."
                if meter.measures_energy
                else "because no energy meter was readable on this host."
            )
        ),
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
