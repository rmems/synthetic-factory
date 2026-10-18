"""Import-form probe for the tag-taxonomy modules, run in a fresh interpreter.

Mirrors ``parity_import_probe``: :func:`run_form` executes in a child process
started with the ``spawn`` method, forgets any repository module the child
inherited, puts ``sys.path`` the way the form under test would, imports in the
order the form names, and reports plain data. Every import below names its
module literally; nothing here imports by computed name.
"""

from __future__ import annotations

import importlib
import multiprocessing
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import ModuleType
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"

# The six modules that were direct-execution only, plus tag_constants, which
# owns the TagTaxonomyError they raise and re-export. Each loader is the
# package-child import a caller outside ``pipelines/`` writes.
PACKAGE_LOADERS = {
    "tag_constants": lambda: importlib.import_module("pipelines.tag_constants"),
    "tag_write": lambda: importlib.import_module("pipelines.tag_write"),
    "tag_io": lambda: importlib.import_module("pipelines.tag_io"),
    "tag_regex": lambda: importlib.import_module("pipelines.tag_regex"),
    "tag_taxonomy": lambda: importlib.import_module("pipelines.tag_taxonomy"),
    "tag_record": lambda: importlib.import_module("pipelines.tag_record"),
    "tag_jsonl": lambda: importlib.import_module("pipelines.tag_jsonl"),
}
MODULES = tuple(PACKAGE_LOADERS)

# (attribute, module in the CLI form, module in the package form): each pair
# must be one object, so an error raised through one import name is caught
# through the other and the CLI re-exports what package callers reach.
SHARED_ATTRIBUTES = (
    ("TagTaxonomyError", "curate_tags", "tag_constants"),
    ("TagTaxonomyError", "curate_tags", "tag_regex"),
    ("TagTaxonomyError", "curate_tags", "tag_taxonomy"),
    ("TagTaxonomyError", "curate_tags", "tag_jsonl"),
    ("UnsafeRegexError", "tag_regex", "tag_regex"),
    ("Taxonomy", "curate_tags", "tag_taxonomy"),
    ("Taxonomy", "tag_record", "tag_jsonl"),
    ("curate_record", "curate_tags", "tag_record"),
    ("curate_jsonl", "curate_tags", "tag_jsonl"),
    ("_write_destinations", "curate_tags", "tag_io"),
    ("_write_new_jsonl", "tag_io", "tag_write"),
)


def _forget_repository_modules() -> None:
    """Drop every module and path entry from this repository, except the probe."""

    for name, module in list(sys.modules.items()):
        location = getattr(module, "__file__", None) or ""
        if name != __name__ and location.startswith(str(REPO)):
            del sys.modules[name]
    sys.path[:] = [
        entry for entry in sys.path if Path(entry or ".").resolve() not in (REPO, PIPELINES)
    ]


def _put_first(directory: Path) -> None:
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))


def cli_form() -> dict[str, ModuleType]:
    """``python3 pipelines/curate_tags.py`` puts ``pipelines/`` first and imports flat."""

    _put_first(PIPELINES)
    import curate_tags
    import tag_constants
    import tag_io
    import tag_jsonl
    import tag_record
    import tag_regex
    import tag_taxonomy
    import tag_write

    return {
        "curate_tags": curate_tags,
        "tag_constants": tag_constants,
        "tag_write": tag_write,
        "tag_io": tag_io,
        "tag_regex": tag_regex,
        "tag_taxonomy": tag_taxonomy,
        "tag_record": tag_record,
        "tag_jsonl": tag_jsonl,
    }


def package_form() -> dict[str, ModuleType]:
    """Every probed module as a package child, from the repository root."""

    _put_first(REPO)
    return {name: load() for name, load in PACKAGE_LOADERS.items()}


def split_modules() -> list[str]:
    """The probed modules whose two spellings are not one module object."""

    return [
        name
        for name in MODULES
        if sys.modules.get(name) is None
        or sys.modules.get(name) is not sys.modules.get(f"pipelines.{name}")
    ]


def unbound_attributes() -> list[str]:
    """The probed modules the ``pipelines`` package does not expose as attributes.

    ``import pipelines.tag_io`` followed by ``pipelines.tag_io.<name>`` needs
    the attribute, not only the ``sys.modules`` entry.
    """

    package = sys.modules.get("pipelines")
    return [
        name
        for name in MODULES
        if getattr(package, name, None) is not sys.modules.get(f"pipelines.{name}")
    ]


def _split_attributes(cli: dict[str, ModuleType], packaged: dict[str, ModuleType]) -> list[str]:
    """The SHARED_ATTRIBUTES pairs that resolved to two different objects."""

    return [
        f"{left}.{attribute} is not pipelines.{right}.{attribute}"
        for attribute, left, right in SHARED_ATTRIBUTES
        if getattr(cli[left], attribute) is not getattr(packaged[right], attribute)
    ]


def _cli_catches_package_error(
    cli: dict[str, ModuleType], packaged: dict[str, ModuleType]
) -> bool:
    """Whether the CLI's ``except TagTaxonomyError`` catches the package loader's error."""

    try:
        packaged["tag_taxonomy"].Taxonomy({}, source="<probe>")
    except cli["curate_tags"].TagTaxonomyError:
        return True
    except ValueError:
        return False
    return False


def _cli_report() -> dict[str, Any]:
    return {"names": {key: module.__name__ for key, module in cli_form().items()}}


def _package_report() -> dict[str, Any]:
    packaged = package_form()
    return {
        "names": {key: module.__name__ for key, module in packaged.items()},
        "pipelines_on_path": str(PIPELINES) in sys.path,
        "split_modules": split_modules(),
        "unbound_attributes": unbound_attributes(),
    }


def _paired_report(cli: dict[str, ModuleType], packaged: dict[str, ModuleType]) -> dict[str, Any]:
    return {
        "split_objects": [name for name in MODULES if cli[name] is not packaged[name]],
        "split_attributes": _split_attributes(cli, packaged),
        "cli_catches_package_error": _cli_catches_package_error(cli, packaged),
        "split_modules": split_modules(),
        "unbound_attributes": unbound_attributes(),
    }


SINGLE_FORMS = {"cli": _cli_report, "package": _package_report}
FORM_LOADERS = {"cli": cli_form, "package": package_form}


def run_form(form: str) -> dict[str, Any]:
    """Load ``form`` ("cli", "package", or "<first>_then_<second>") and report what it bound."""

    _forget_repository_modules()
    if form in SINGLE_FORMS:
        return SINGLE_FORMS[form]()
    first, _then, second = form.partition("_then_")
    bound = {first: FORM_LOADERS[first](), second: FORM_LOADERS[second]()}
    return _paired_report(bound["cli"], bound["package"])


def both_preludes_report() -> dict[str, Any]:
    """Run every module's direct prelude, then its package prelude, and report what bound.

    The bare package loads first, so its init has no flat module to alias.
    The CLI form then runs each direct branch, and the package form runs each
    package branch and finalizer, which rebinds the package name to the direct
    module. Call this with no repository module loaded, for example inside
    ``clean_package_imports``, so both branches really execute in this process.
    """

    _put_first(REPO)
    importlib.import_module("pipelines")
    cli = cli_form()
    return _paired_report(cli, package_form())


def in_fresh_interpreter(form: str) -> dict[str, Any]:
    """Run :func:`run_form` in a spawned interpreter and return its report."""

    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=1, mp_context=context) as pool:
        return pool.submit(run_form, form).result(timeout=180)
