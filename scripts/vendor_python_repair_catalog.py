#!/usr/bin/env python3
"""Build the code-repair catalog from TheAlgorithms/Python at a pinned commit (one-time, network).

Fetches the recursive git tree at the commit, keeps the small files of the
chosen families, applies the file-level rules the builder cannot see (stdlib
imports only, none of the IO or randomness modules), selects the target
functions with ``code_repair.catalog_build.select_targets``, and writes a
brand-new catalog directory through the builder, so the catalog is the
builder's output byte for byte and every later run is offline. The reviewed
reference table (``references.json``: ``"path::function" -> {kind, function,
source}``) is an input; programs without an entry become ``original_self``.
Raw fetched bytes are cached under ``--cache-dir`` for reruns.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import http.client
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

_PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from code_repair import catalog_build as cb  # noqa: E402
from code_repair import executor as ex  # noqa: E402
from code_repair import lineage  # noqa: E402

REPOSITORY = "TheAlgorithms/Python"
API = "https://api.github.com/repos/{repository}/git/trees/{commit}?recursive=1"
COMMIT_API = "https://api.github.com/repos/{repository}/commits/{commit}"
RAW = "https://raw.githubusercontent.com/{repository}/{commit}/{path}"
FAMILIES = (
    "maths", "sorts", "searches", "strings", "bit_manipulation", "conversions",
    "dynamic_programming",
)
MAX_FILE_BYTES = 3072
# An explicit allow-list, inspected across the whole file (CodeAnt, Greptile and Codex on
# #203): pure computation modules plus ``doctest`` (the upstream files run their own doctests
# under ``__main__``). Deliberately independent of the interpreter's stdlib inventory, which
# admits ``ctypes``, ``importlib``, ``pickle`` and other routes to the host.
ALLOWED_MODULES = frozenset({
    "__future__", "bisect", "cmath", "collections", "copy", "dataclasses", "decimal",
    "doctest", "enum", "fractions", "functools", "heapq", "itertools", "math", "operator",
    "re", "string", "struct", "typing",
})
DEFAULT_POLICY = {
    "algorithm": lineage.SPLIT_ALGORITHM, "seed": 20260908, "salt": "python-repair-v1",
    "weights": {"train": 80, "validation": 10, "held_out": 10},
}


def _fetch(url: str, cache: Path) -> bytes:
    key = cache / hashlib.sha256(url.encode("utf-8")).hexdigest()
    if key.is_file():
        return key.read_bytes()
    data = _https_get(url)
    cache.mkdir(parents=True, exist_ok=True)
    key.write_bytes(data)
    return data


def _https_get(url: str) -> bytes:
    """One HTTPS GET of a pinned GitHub URL; anything but 200 refuses the build."""

    parts = urlsplit(url)
    if parts.scheme != "https":
        raise SystemExit(f"refusing a non-https URL: {url}")
    connection = http.client.HTTPSConnection(parts.netloc, timeout=60)
    try:
        target = parts.path + (f"?{parts.query}" if parts.query else "")
        connection.request("GET", target, headers={"User-Agent": "synthetic-factory-vendor"})
        response = connection.getresponse()
        if response.status != 200:
            raise SystemExit(f"{url}: HTTP {response.status}")
        return response.read()
    finally:
        connection.close()


def _tree(commit: str, cache: Path) -> list[dict]:
    """The pinned commit's tree, fetched by the tree's own sha so the listing is bound to it.

    A tree fetched by commit sha echoes the commit's sha, so the commit is read first and the
    tree by ``commit.tree.sha`` (CodeAnt on #203).
    """

    commit_meta = json.loads(_fetch(
        COMMIT_API.format(repository=REPOSITORY, commit=commit), cache
    ))
    expected = commit_meta["commit"]["tree"]["sha"]
    payload = json.loads(_fetch(API.format(repository=REPOSITORY, commit=expected), cache))
    if payload.get("sha") != expected:
        raise SystemExit("tree sha differs from the pinned commit tree sha")
    if payload.get("truncated"):
        raise SystemExit("the tree listing was truncated; refusing an incomplete catalog")
    return [entry for entry in payload["tree"] if entry["type"] == "blob"]


def _is_candidate(entry: dict) -> bool:
    """A small ``<family>/<module>.py`` file, not a package marker."""

    path = entry["path"]
    family, _slash, name = path.partition("/")
    in_family = family in FAMILIES and name.endswith(".py") and "/" not in name
    return in_family and name != "__init__.py" and entry.get("size", 0) < MAX_FILE_BYTES


def _candidate_paths(tree: list[dict]) -> list[str]:
    return sorted(entry["path"] for entry in tree if _is_candidate(entry))


def _import_roots(node: ast.stmt) -> set[str] | None:
    """The top-level modules one import statement binds; None for a non-import."""

    if isinstance(node, ast.Import):
        return {alias.name.split(".")[0] for alias in node.names}
    if isinstance(node, ast.ImportFrom):
        return {""} if node.level else {(node.module or "").split(".")[0]}
    return None


def _imports_admissible(module: ast.Module) -> bool:
    return all(
        roots.issubset(ALLOWED_MODULES)
        for roots in map(_import_roots, ast.walk(module)) if roots is not None
    )


def _file_admissible(text: str) -> bool:
    """Parses, imports only the standard library and none of the IO or randomness modules."""

    try:
        module = ast.parse(text)
    except (SyntaxError, ValueError):
        return False
    return _imports_admissible(module) and "```" not in text


def _lf_framed(text: str) -> bool:
    return "\r" not in text and text.endswith("\n")


def _commit(value: str) -> str:
    if re.fullmatch(r"[0-9a-fA-F]{40}", value) is None:
        raise argparse.ArgumentTypeError("commit must be exactly 40 hex characters")
    return value


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commit", type=_commit, required=True, help="the pinned upstream commit (40 hex)"
    )
    parser.add_argument("--out", type=Path, required=True, help="a brand-new catalog directory")
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument(
        "--references", type=Path, required=True, help="the reviewed reference table"
    )
    parser.add_argument("--catalog-id", default="python-repair-v1")
    parser.add_argument(
        "--limit", type=int, default=None, help="keep only the first N files (smoke)"
    )
    parser.add_argument("--timeout-s", type=float, default=2.0)
    return parser.parse_args(argv)


def _blob(entry: dict, commit: str, cache: Path) -> bytes:
    url = RAW.format(repository=REPOSITORY, commit=commit, path=entry["path"])
    data = _fetch(url, cache)
    framed = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    digest = hashlib.sha1(framed, usedforsecurity=False).hexdigest()
    if digest != entry.get("sha"):
        raise SystemExit("raw file blob sha mismatch: " + str(entry["path"])[:160])
    return data


def _admissible_sources(
    entries: list[dict], commit: str, cache: Path
) -> tuple[dict[str, str], dict]:
    """The LF-framed, UTF-8, admissible files by path, and the file counts."""

    sources: dict[str, str] = {}
    rejected = {"unreadable": 0, "not_admissible": 0}
    for entry in entries:
        path = entry["path"]
        data = _blob(entry, commit, cache)
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            rejected["unreadable"] += 1
            continue
        if not (_lf_framed(text) and _file_admissible(text)):
            rejected["not_admissible"] += 1
            continue
        sources[path] = text
    files = {
        "candidate_files": len(entries), "admissible_files": len(sources),
        "rejected_files": rejected,
    }
    return sources, files


def _summary(files: dict, build: cb.Build, rows: list) -> dict:
    return {
        **files,
        "programs": len(rows), "dropped_by_code": dict(Counter(n["code"] for n in build.notes)),
        "per_family": {f: sum(1 for r in rows if r["family"] == f) for f in FAMILIES},
        "references": {k: sum(1 for r in rows if r["hidden"]["reference"]["kind"] == k)
                       for k in ("sibling_same_file", "reviewed_expression", "original_self")},
        "splits": {s: sum(1 for r in rows if r["split"] == s) for s in lineage.SPLITS},
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    cache = Path(args.cache_dir)
    tree = _tree(args.commit, cache)
    entries = sorted((e for e in tree if _is_candidate(e)), key=lambda e: e["path"])
    if args.limit is not None:
        entries = entries[: args.limit]
    sources, files = _admissible_sources(entries, args.commit, cache)
    targets = [
        (path, function)
        for path, text in sources.items() for function in cb.select_targets(text)
    ]
    license_entry = next((e for e in tree if e["path"] == "LICENSE.md"), None)
    if license_entry is None:
        raise SystemExit("pinned tree has no LICENSE.md blob")
    license_text = _blob(license_entry, args.commit, cache)
    upstream = cb.Upstream(REPOSITORY, args.commit, "MIT", license_text.decode("utf-8"))
    references = json.loads(Path(args.references).read_text(encoding="utf-8"))
    build = cb.Build(upstream, sources, references, lineage.SplitPolicy.from_json(DEFAULT_POLICY))
    rows = cb.build_rows(build, targets, ex.Executor(timeout_s=args.timeout_s))
    cb.write_catalog(Path(args.out), args.catalog_id, build, rows)
    print(json.dumps(_summary(files, build, rows), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
