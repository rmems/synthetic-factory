"""Import-form probe for the rights sidecar verifier, run in a fresh interpreter.

Follows ``parity_import_probe``: :func:`split_twins` runs in a child process
started with the ``spawn`` method, forgets any repository module the child
inherited, imports ``verify_hf_release`` in one form and then in the other, and
reports the modules whose bare and ``pipelines.`` names are two objects. No code
string crosses the process boundary and nothing is imported by computed name.
The module preludes alone must bind the twins; none of these names is
registered in ``pipelines._PACKAGE_SIBLING_NAMES``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"

TWINS = (
    "verify_hf_release",
    "verify_hf_release_rights",
    "rights_document",
    "rights_document_procedural",
    "rights_document_support",
)


def _from_repository(module: object) -> bool:
    return (getattr(module, "__file__", None) or "").startswith(str(REPO))


def _drop_loaded_repository_modules() -> None:
    stale = [
        name for name, module in sys.modules.items()
        if name != __name__ and _from_repository(module)
    ]
    for name in stale:
        del sys.modules[name]


def _drop_repository_paths() -> None:
    keep = (REPO, PIPELINES)
    sys.path[:] = [entry for entry in sys.path if Path(entry or ".").resolve() not in keep]


def _forget_repository_modules() -> None:
    """Drop every module and path entry this child inherited from the repository."""

    _drop_loaded_repository_modules()
    _drop_repository_paths()


def _cli_form() -> ModuleType:
    """``python3 pipelines/verify_hf_release.py`` puts ``pipelines/`` first."""

    sys.path.insert(0, str(PIPELINES))
    import verify_hf_release

    return verify_hf_release


def _package_form() -> ModuleType:
    """``from pipelines import verify_hf_release`` from the repository root."""

    sys.path.insert(0, str(REPO))
    from pipelines import verify_hf_release

    return verify_hf_release


def _is_one_object(name: str) -> bool:
    module = sys.modules.get(name)
    return module is not None and module is sys.modules.get(f"pipelines.{name}")


def split_twins(first: str) -> list[str]:
    """Import ``first`` (``cli`` or ``package``), then the other form; list split twins."""

    _forget_repository_modules()
    loaders = (_cli_form, _package_form) if first == "cli" else (_package_form, _cli_form)
    loaded = [load() for load in loaders]
    if loaded[0] is not loaded[1]:
        return ["verify_hf_release"]
    return [name for name in TWINS if not _is_one_object(name)]
