"""Export wiring that writes a manifest stub and refuses Hub publication."""

from __future__ import annotations

from pathlib import Path

from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json, is_under_raw
from .scenarios import catalog
from .splits import load_family

__all__ = ["export_plan", "publish", "write_stub"]


def _rows(family) -> list[dict]:
    rows = []
    for scenario in catalog():
        split = family.splits[scenario.scenario_id]
        excluded = scenario.task_id in family.excluded_task_ids
        rows.append(
            {
                "scenario_id": scenario.scenario_id,
                "task_id": scenario.task_id,
                "split": split,
                "train_export": split != cv.HELD_OUT and not excluded,
            }
        )
    return rows


def export_plan() -> dict:
    """The export contract: zero records, no token, publish left off."""

    family = load_family()
    return {
        "dataset": family.dataset,
        "publish": False,
        "huggingface_token": None,
        "records": 0,
        "config_sha256": family.config_sha256,
        "exclusion_sha256": family.exclusion_sha256,
        "held_out_task_ids": sorted(family.excluded_task_ids),
        "rows": _rows(family),
    }


def publish(*_args: object, **_kwargs: object) -> None:
    """Refuse Hub publication. Tokens are not read."""

    raise cv.FamilyError("export.publish_disabled", "Hugging Face publish is disabled")


def write_stub(out: Path) -> dict:
    """Write ``EXPORT.json`` into a new directory. The file lists zero records."""

    if out.exists():
        raise cv.FamilyError("export.exists", "refusing an existing destination")
    if is_under_raw(out):
        raise cv.FamilyError("export.raw", "refusing outputs/raw")
    plan = export_plan()
    out.mkdir(parents=True)
    target = out / "EXPORT.json"
    target.write_text(dumps_exact_json(plan, indent=2) + "\n", encoding="utf-8")
    return plan


bind_import_twin(__name__)
