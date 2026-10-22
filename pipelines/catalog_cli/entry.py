"""Install one package CLI's public names from the shared subcommand layer.

:func:`install_generate` and :func:`install_extract` bind ``build_parser`` and
``run``. Generate-shape ``--help`` text is ``_GENERATE_DOC``; extract-shape
CLIs still carry their own module docstring.
"""

from __future__ import annotations

import functools
import importlib
from pathlib import Path
from types import ModuleType
from typing import Any

if __name__.startswith("pipelines."):
    from ..oracle_grounded.import_twins import bind_import_twin
    from . import subcommands
else:
    from catalog_cli import subcommands
    from oracle_grounded.import_twins import bind_import_twin

__all__ = ["install_extract", "install_generate"]

_REFUSAL_ATTRIBUTE = {
    "flk": "FlkRefusal",
    "gql": "GqlRefusal",
    "msd": "MsdRefusal",
    "rag": "RagRefusal",
    "saf": "SafRefusal",
}
# The generate CLIs share one source shape, so the ``--help`` description lives
# here. It is the module docstring each package CLI had before the shared layer.
_GENERATE_DOC = """{title} mill commands: catalog-check and generate.

Exit codes: 0 on success, 2 on a coded refusal or usage error. ``--json``
prints one object so an agent never parses prose.
"""
_SAF_GENERATE = {
    "generate_help": "safety-case pairs into a new directory",
    "unit": "pair",
}


def _package_key(module_globals: dict[str, Any]) -> str:
    package = module_globals.get("__package__") or ""
    if package:
        return package.rpartition(".")[2]
    return Path(module_globals["__file__"]).parent.name


def _anchor_package(module_globals: dict[str, Any]) -> str:
    """Package the CLI was loaded as, or its directory name in script mode.

    Script mode (``python3 pipelines/<pkg>/cli.py``) has an empty
    ``__package__``. The directory name is the flat package (``flk``), and
    the CLI has already put ``pipelines/`` on ``sys.path``.
    """

    package = module_globals.get("__package__") or ""
    if package:
        return package
    return Path(module_globals["__file__"]).parent.name


def _import_sibling(module_globals: dict[str, Any], name: str) -> ModuleType:
    """Import ``name`` relative to the CLI package.

    The module name passed to ``import_module`` is one of three literals.
    The anchor package comes from the caller, so this file never names a
    mill path.
    """

    package = _anchor_package(module_globals)
    if name == "catalog":
        return importlib.import_module(".catalog", package)
    if name == "generate":
        return importlib.import_module(".generate", package)
    if name == "_contract":
        return importlib.import_module("._contract", package)
    raise ImportError(f"unknown mill module {name}")


def _module_level(module_globals: dict[str, Any], name: str, function: Any) -> Any:
    """Name ``function`` as ``<module>.<name>`` so pickle finds it by reference."""

    function.__module__ = module_globals["__name__"]
    function.__name__ = name
    function.__qualname__ = name
    module_globals[name] = function
    return function


def _publish(module_globals: dict[str, Any], commands: Any) -> None:
    """Bind ``build_parser`` and ``run`` as module-level forwards to ``commands``.

    Forwards, not bound methods: a bound method carries the commands object,
    which holds module references and so cannot be pickled for a worker pool.
    ``__wrapped__`` still names the bound method.
    """

    @functools.wraps(commands.build_parser)
    def build_parser() -> Any:
        return commands.build_parser()

    @functools.wraps(commands.run)
    def run(argv: list[str] | None = None) -> int:
        return commands.run(argv)

    module_globals["__all__"] = ["build_parser", "run"]
    _module_level(module_globals, "build_parser", build_parser)
    _module_level(module_globals, "run", run)


def install_generate(module_globals: dict[str, Any]) -> None:
    """Bind the generate-shape CLI (``flk``, ``gql``, ``msd``, ``rag``, ``saf``)."""

    key = _package_key(module_globals)
    module_globals["__doc__"] = _GENERATE_DOC.format(title=key.upper())
    catalog = _import_sibling(module_globals, "catalog")
    generate = _import_sibling(module_globals, "generate")
    commands = subcommands.GenerateCommands(
        prog=f"{key}.cli",
        description=module_globals.get("__doc__"),
        catalog=catalog,
        generate=generate,
        refusal=getattr(catalog, _REFUSAL_ATTRIBUTE[key]),
        **(_SAF_GENERATE if key == "saf" else {}),
    )
    _publish(module_globals, commands)

    def main() -> None:
        # Resolve ``run`` at call time so a replaced ``cli.run`` controls ``main``.
        raise SystemExit(module_globals["run"]())

    _module_level(module_globals, "main", main)
    if module_globals.get("__name__") == "__main__":
        main()
    elif module_globals.get("__package__"):
        catalog.bind_import_twin(module_globals["__name__"])


def install_extract(module_globals: dict[str, Any], catalog: ModuleType) -> None:
    """Bind the extract-shape CLI (``mac``, ``sbox``)."""

    key = _package_key(module_globals)
    generate = _import_sibling(module_globals, "generate")
    contract = _import_sibling(module_globals, "_contract")
    commands = subcommands.ExtractCommands(
        prog=f"{key}.cli",
        description=module_globals.get("__doc__"),
        catalog=catalog,
        generate=generate,
        refusal=contract.envelope.ContractError,
    )
    _publish(module_globals, commands)
    catalog.bind_import_twin(module_globals["__name__"])
    if module_globals.get("__name__") == "__main__":
        raise SystemExit(module_globals["run"]())


bind_import_twin(__name__)
