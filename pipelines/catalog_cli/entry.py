"""Install one package CLI's public names from the shared subcommand layer.

:func:`install_generate` and :func:`install_extract` bind ``build_parser`` and
``run``. Generate-shape ``--help`` text is ``_GENERATE_DOC``; extract-shape
CLIs still carry their own module docstring.
"""

from __future__ import annotations

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


# ``(pipelines-form, flat-form)``. ``import_module`` receives one of these literals.
_MODULES = {
    ("flk", "catalog"): ("pipelines.flk.catalog", "flk.catalog"),
    ("flk", "generate"): ("pipelines.flk.generate", "flk.generate"),
    ("gql", "catalog"): ("pipelines.gql.catalog", "gql.catalog"),
    ("gql", "generate"): ("pipelines.gql.generate", "gql.generate"),
    ("msd", "catalog"): ("pipelines.msd.catalog", "msd.catalog"),
    ("msd", "generate"): ("pipelines.msd.generate", "msd.generate"),
    ("rag", "catalog"): ("pipelines.rag.catalog", "rag.catalog"),
    ("rag", "generate"): ("pipelines.rag.generate", "rag.generate"),
    ("saf", "catalog"): ("pipelines.saf.catalog", "saf.catalog"),
    ("saf", "generate"): ("pipelines.saf.generate", "saf.generate"),
    ("mac", "generate"): ("pipelines.mac.generate", "mac.generate"),
    ("mac", "_contract"): ("pipelines.mac._contract", "mac._contract"),
    ("sbox", "generate"): ("pipelines.sbox.generate", "sbox.generate"),
    ("sbox", "_contract"): ("pipelines.sbox._contract", "sbox._contract"),
}


def _import_sibling(module_globals: dict[str, Any], name: str) -> ModuleType:
    """Import ``name`` the same way the CLI module itself was imported."""

    package = module_globals.get("__package__") or ""
    pair = _MODULES.get((_package_key(module_globals), name))
    if pair is None:
        raise ImportError(f"unknown mill module {name}")
    qualified = pair[0] if package.startswith("pipelines.") else pair[1]
    return importlib.import_module(qualified)


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
    module_globals["__all__"] = ["build_parser", "run"]
    module_globals["build_parser"] = commands.build_parser
    module_globals["run"] = commands.run

    def main() -> None:
        raise SystemExit(commands.run())

    module_globals["main"] = main
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
    module_globals["__all__"] = ["build_parser", "run"]
    module_globals["build_parser"] = commands.build_parser
    module_globals["run"] = commands.run
    catalog.bind_import_twin(module_globals["__name__"])
    if module_globals.get("__name__") == "__main__":
        raise SystemExit(commands.run())


bind_import_twin(__name__)
