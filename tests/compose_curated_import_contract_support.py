"""Fresh-interpreter support for package/direct module identity contracts."""

from __future__ import annotations

import importlib
import multiprocessing
import sys
from pathlib import Path
from typing import Iterable


_PROCESS_TIMEOUT_SECONDS = 30.0
_TERMINATION_TIMEOUT_SECONDS = 5.0


def _assert_module_identities(
    repo_text: str,
    names: tuple[str, ...],
    first_prefix: str,
    second_prefix: str,
) -> None:
    repo = Path(repo_text)
    sys.path.insert(0, str(repo / "pipelines"))
    sys.path.insert(0, str(repo))
    first = [importlib.import_module(first_prefix + name) for name in names]
    second = [importlib.import_module(second_prefix + name) for name in names]
    if not all(left is right for left, right in zip(first, second)):
        raise AssertionError("package and direct module identities diverged")


def clean_process_identity_exit_code(
    repo: Path,
    names: Iterable[str],
    *,
    package_first: bool,
) -> int | None:
    """Check import-order identity in a spawned, uncontaminated interpreter."""

    first_prefix, second_prefix = ("pipelines.", "") if package_first else ("", "pipelines.")
    process = multiprocessing.get_context("spawn").Process(
        target=_assert_module_identities,
        args=(str(repo), tuple(names), first_prefix, second_prefix),
    )
    process.start()
    process.join(_PROCESS_TIMEOUT_SECONDS)
    if process.is_alive():
        process.terminate()
        process.join(_TERMINATION_TIMEOUT_SECONDS)
        if process.is_alive():
            process.kill()
            process.join(_TERMINATION_TIMEOUT_SECONDS)
        raise TimeoutError(
            "clean-process module identity check timed out after "
            f"{_PROCESS_TIMEOUT_SECONDS:g} seconds"
        )
    return process.exitcode
