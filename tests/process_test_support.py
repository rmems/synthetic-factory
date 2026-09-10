"""Shared child-process lifecycle support for fresh-interpreter tests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import multiprocessing
from types import ModuleType
from typing import Any


@dataclass(frozen=True)
class ProcessTimeout:
    """Bounded runtime and cleanup policy for a spawned test child."""

    runtime_seconds: float
    termination_seconds: float
    message: str


def spawned_process_exit_code(
    target: Callable[..., None],
    args: tuple[Any, ...] = (),
    *,
    timeout: ProcessTimeout,
    multiprocessing_module: ModuleType = multiprocessing,
) -> int | None:
    """Run ``target`` in a spawned child and return its exit code."""

    process = multiprocessing_module.get_context("spawn").Process(
        target=target,
        args=args,
    )
    process.start()
    process.join(timeout.runtime_seconds)
    if process.is_alive():
        process.terminate()
        process.join(timeout.termination_seconds)
        if process.is_alive():
            process.kill()
            process.join(timeout.termination_seconds)
        raise TimeoutError(timeout.message)
    return process.exitcode
