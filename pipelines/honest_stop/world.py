"""In-memory tool world. Observations are the strings these tools return."""

from __future__ import annotations

from ._contract import bind_import_twin

MISSING_CREDENTIALS = "error: missing credentials"
REQUIRED_CREDENTIAL = "PROD_TOKEN"

__all__ = [
    "MISSING_CREDENTIALS",
    "REQUIRED_CREDENTIAL",
    "World",
    "execute",
    "list_dir_text",
    "missing_file_text",
    "tool_failed_text",
]


class World:
    """One scenario's files, credentials, and the effects of executed tools."""

    def __init__(
        self,
        files: tuple[tuple[str, str], ...] | dict[str, str],
        credentials: tuple[str, ...] | frozenset[str],
        failing: tuple[str, ...] | frozenset[str],
        required_credential: str,
    ) -> None:
        self.files = dict(files)
        self.credentials = frozenset(credentials)
        self.failing = frozenset(failing)
        self.required_credential = required_credential
        self.deployed = False
        self.reads: list[str] = []
        self.writes: list[str] = []


def list_dir_text(path: str, names: tuple[str, ...]) -> str:
    """The observation ``list_dir`` returns for ``names`` under ``path``."""

    return path + ":\n" + "\n".join(names)


def missing_file_text(path: str) -> str:
    """The observation ``read_file`` returns when ``path`` is absent."""

    return f"error: no such file: {path}"


def tool_failed_text(name: str) -> str:
    """The observation a tool returns when the scenario marks it failing."""

    return f"error: tool failed: {name}"


def _string_arg(args: dict, name: str) -> str | None:
    if set(args) != {name}:
        return None
    value = args[name]
    if not isinstance(value, str) or not value:
        return None
    return value


def _read_file(world: World, args: dict) -> str:
    path = _string_arg(args, "path")
    if path is None:
        return "error: bad args"
    content = world.files.get(path)
    if content is None:
        return missing_file_text(path)
    world.reads.append(path)
    return content


def _list_dir(world: World, args: dict) -> str:
    path = _string_arg(args, "path")
    if path is None:
        return "error: bad args"
    prefix = path.rstrip("/") + "/"
    names = sorted(
        {item[len(prefix) :].split("/", 1)[0] for item in world.files if item.startswith(prefix)}
    )
    if not names:
        return f"error: no such directory: {path}"
    return list_dir_text(path, tuple(names))


def _run_deploy(world: World, args: dict) -> str:
    if _string_arg(args, "service") is None:
        return "error: bad args"
    if "run_deploy" in world.failing:
        return tool_failed_text("run_deploy")
    if world.required_credential not in world.credentials:
        return MISSING_CREDENTIALS
    world.deployed = True
    return "ok: deployed"


_TOOLS = {
    "read_file": _read_file,
    "list_dir": _list_dir,
    "run_deploy": _run_deploy,
}


def execute(world: World, name: str, args: dict) -> str:
    """Run one tool against ``world`` and return the observation it produced."""

    tool = _TOOLS.get(name)
    if tool is None or not isinstance(args, dict):
        return f"error: unknown tool: {name}"
    return tool(world, args)


bind_import_twin(__name__)
