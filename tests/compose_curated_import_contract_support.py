"""Fresh-interpreter support for package/direct module identity contracts."""

from __future__ import annotations

import multiprocessing
import sys
from pathlib import Path
from typing import Iterable

if __package__:
    from . import pipeline_import_catalog
    from .process_test_support import ProcessTimeout, spawned_process_exit_code
else:
    import pipeline_import_catalog
    from process_test_support import ProcessTimeout, spawned_process_exit_code


_PROCESS_TIMEOUT_SECONDS = 30.0
_TERMINATION_TIMEOUT_SECONDS = 5.0


def _assert_module_identities(
    repo_text: str,
    names: tuple[str, ...],
    package_first: bool,
) -> None:
    repo = Path(repo_text)
    sys.path.insert(0, str(repo / "pipelines"))
    sys.path.insert(0, str(repo))
    if package_first:
        first_loader = pipeline_import_catalog.load_package
        second_loader = pipeline_import_catalog.load_direct
    else:
        first_loader = pipeline_import_catalog.load_direct
        second_loader = pipeline_import_catalog.load_package
    first = [first_loader(name) for name in names]
    second = [second_loader(name) for name in names]
    if not all(left is right for left, right in zip(first, second)):
        raise AssertionError("package and direct module identities diverged")


def clean_process_identity_exit_code(
    repo: Path,
    names: Iterable[str],
    *,
    package_first: bool,
) -> int | None:
    """Check import-order identity in a spawned, uncontaminated interpreter."""

    return spawned_process_exit_code(
        _assert_module_identities,
        (str(repo), tuple(names), package_first),
        timeout=ProcessTimeout(
            _PROCESS_TIMEOUT_SECONDS,
            _TERMINATION_TIMEOUT_SECONDS,
            (
                "clean-process module identity check timed out after "
                f"{_PROCESS_TIMEOUT_SECONDS:g} seconds"
            ),
        ),
        multiprocessing_module=multiprocessing,
    )
