"""Stage CSV replay files and publish their directory without overwriting."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from ._contract import CsvRefusal, FINDING_DESTINATION_EXISTS, FINDING_DESTINATION_INVALID, bind_import_twin

if __name__.startswith("pipelines."):
    from ..compose_destination_rename import rename_noreplace
else:
    from compose_destination_rename import rename_noreplace

__all__ = ["write_run_files"]


def _publish(parent: Path, staged: Path, destination: Path) -> None:
    descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        rename_noreplace(descriptor, staged.name, destination.name)
    except FileExistsError as exc:
        raise CsvRefusal(
            FINDING_DESTINATION_EXISTS, f"{destination} already exists"
        ) from exc
    finally:
        os.close(descriptor)


def write_run_files(destination: Path, files: dict[str, str]) -> None:
    """Expose only complete runs; clean the private stage on write failure."""
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise CsvRefusal(FINDING_DESTINATION_INVALID, f"cannot create output parent {destination.parent}: {exc}") from exc
    with tempfile.TemporaryDirectory(prefix=".csv-stage-", dir=destination.parent) as temp:
        staged = Path(temp)
        for name, payload in files.items():
            (staged / name).write_text(payload, encoding="utf-8")
        _publish(destination.parent, staged, destination)


bind_import_twin(__name__)
