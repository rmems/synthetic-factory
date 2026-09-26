"""Check CSV mill import identity and standard-library safety in a spawned process."""

import sys
from pathlib import Path

PACKAGED_NAME = "pipelines.csv_mill"

MODULES = (
    "_contract",
    "catalog",
    "catalog_extract",
    "catalog_io",
    "catalog_models",
    "catalog_source",
    "catalog_validation",
    "cli",
    "generate",
    "generate_io",
    "generate_parent",
    "steps",
    "steps_templates",
)


def _forget_family() -> None:
    for name in tuple(sys.modules):
        family = name.removeprefix("pipelines.").split(".")[0]
        if family in ("csv", "csv_mill"):
            del sys.modules[name]


def _direct_family():
    import csv_mill as package
    from csv_mill import _contract, catalog, catalog_extract, catalog_io, catalog_models, catalog_source, catalog_validation, cli, generate, generate_io, generate_parent, steps, steps_templates
    return package, (_contract, catalog, catalog_extract, catalog_io, catalog_models, catalog_source, catalog_validation, cli, generate, generate_io, generate_parent, steps, steps_templates)


def _packaged_family():
    import pipelines.csv_mill as package
    from pipelines.csv_mill import _contract, catalog, catalog_extract, catalog_io, catalog_models, catalog_source, catalog_validation, cli, generate, generate_io, generate_parent, steps, steps_templates
    return package, (_contract, catalog, catalog_extract, catalog_io, catalog_models, catalog_source, catalog_validation, cli, generate, generate_io, generate_parent, steps, steps_templates)


def _stdlib_csv():
    import csv
    return csv


def probe(first: str, preload_stdlib: bool = False) -> dict:
    repo = Path(__file__).resolve().parents[1]
    _forget_family()
    original_csv = _stdlib_csv() if preload_stdlib else None
    sys.path[:0] = [str(repo / "pipelines"), str(repo)]
    loaders = {"csv_mill": _direct_family, PACKAGED_NAME: _packaged_family}
    second = "csv_mill" if first == PACKAGED_NAME else PACKAGED_NAME
    first_package, first_modules = loaders[first]()
    second_package, second_modules = loaders[second]()
    split = [name for name, left, right in zip(MODULES, first_modules, second_modules, strict=True) if left is not right]
    csv = _stdlib_csv()
    return {
        "same_stdlib": original_csv is None or csv is original_csv,
        "rows": list(csv.reader(["a,b"])),
        "split_modules": split,
        "same_package": first_package is second_package,
        "exports": sorted(first_package.__all__),
    }
