"""Check CSV mill import identity and standard-library safety in a spawned process."""

import importlib
import sys
from pathlib import Path

MODULES = (
    "_contract",
    "catalog",
    "catalog_extract",
    "catalog_io",
    "catalog_models",
    "catalog_validation",
    "cli",
    "generate",
    "steps",
    "steps_templates",
)


def _forget_family() -> None:
    for name in tuple(sys.modules):
        family = name.removeprefix("pipelines.").split(".")[0]
        if family in ("csv", "csv_mill"):
            del sys.modules[name]


def probe(first: str) -> dict:
    repo = Path(__file__).resolve().parents[1]
    _forget_family()
    sys.path[:0] = [str(repo / "pipelines"), str(repo)]
    second = "csv_mill" if first == "pipelines.csv_mill" else "pipelines.csv_mill"
    packages = [importlib.import_module(prefix) for prefix in (first, second)]
    split = [
        name
        for name in MODULES
        if importlib.import_module(f"{first}.{name}")
        is not importlib.import_module(f"{second}.{name}")
    ]
    csv = importlib.import_module("csv")
    return {
        "rows": list(csv.reader(["a,b"])),
        "split_modules": split,
        "same_package": packages[0] is packages[1],
        "exports": sorted(packages[0].__all__),
    }
