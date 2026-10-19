#!/usr/bin/env python3
"""Resolve repository names through the GitHub API into a new alias cache (#494).

Compose never touches the network: it canonicalizes source repositories from
the committed ``config/eval-exclusion/repo-aliases.json``. This operator script
is the only place that asks GitHub. For each name it runs
``gh api repos/<owner>/<name>``, which follows the redirects GitHub serves for
renamed and transferred repositories, and records the canonical ``full_name``
(lowercased), the stable numeric ``id``, and the UTC resolution time. The
canonical target gets its own self-entry, so the cache stays closed.

A name that would follow another to a new target (a moved former target, or a
sibling alias) is re-resolved first and must land on the same repository id;
otherwise nothing is written. The result is validated with the same loader
compose uses and published at a brand-new ``--out`` path inside this checkout
or the temporary directory (an existing path, a symlink, anything under
``outputs/raw/``, or a path that resolves elsewhere is refused). Review the
diff, then replace the committed cache with it in a pull request.

  python3 scripts/refresh_repo_aliases.py \
      --out config/eval-exclusion/repo-aliases.refreshed.json kbknapp/clap-rs
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B404 -- one fixed `gh api` argv below, never a shell
import sys
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Iterable

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import eval_exclusion_aliases as aliases  # noqa: E402
import eval_exclusion_lists as lists  # noqa: E402
import eval_exclusion_policy as policy  # noqa: E402
import raw_tree_guard  # noqa: E402
import repo_identity  # noqa: E402

Fetch = Callable[[str], Any]


class RefreshError(RuntimeError):
    """A name could not be resolved, so no cache is written."""


GH = "gh"


def _is_executable_file(path: str) -> bool:
    return os.path.isfile(path) and os.access(path, os.X_OK)


def _gh_executable() -> str:
    """Absolute ``gh`` from the PATH directories; a bare name would be a partial-path launch."""

    for directory in os.get_exec_path():
        candidate = os.path.join(os.path.abspath(directory), GH)
        if _is_executable_file(candidate):
            return candidate
    raise RefreshError("gh is not on PATH")


def gh_api_repo(name: str) -> Any:
    """Return the decoded ``gh api repos/<name>`` document, failing closed."""

    try:
        repo = repo_identity.canonical_repo(name)
    except repo_identity.RepoNameError as exc:
        raise RefreshError(str(exc)) from exc
    argv = [_gh_executable(), "api", f"repos/{repo}"]
    try:
        # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
        completed = subprocess.run(  # nosec B603 -- absolute gh, fixed argv, validated owner/name, no shell
            argv, capture_output=True, check=False, text=True, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RefreshError(f"gh api repos/{repo} could not run: {exc}") from exc
    if completed.returncode != 0:
        raise RefreshError(f"gh api repos/{repo} failed: {completed.stderr.strip()}")
    try:
        return json.loads(completed.stdout)
    except ValueError as exc:
        raise RefreshError(f"gh api repos/{repo} returned invalid JSON: {exc}") from exc


def _repository_object(name: str, document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise RefreshError(f"{name}: GitHub returned no repository object")
    return document


def _repository_id(name: str, repository: dict[str, Any]) -> int:
    github_id = repository.get("id")
    if not aliases.is_positive_id(github_id):
        raise RefreshError(f"{name}: GitHub returned no repository id")
    return github_id


def _repository_canonical(name: str, repository: dict[str, Any]) -> str:
    try:
        return repo_identity.canonical_repo(repository.get("full_name"))
    except repo_identity.RepoNameError as exc:
        raise RefreshError(f"{name}: GitHub returned an unusable full_name: {exc}") from exc


def _resolved(name: str, document: Any) -> tuple[str, int]:
    """Classify one ``gh api`` answer as ``(canonical owner/name, github_id)`` or refuse it.

    ``gh`` has already followed GitHub's rename and transfer redirects, so the
    answer describes the repository the name points at today.
    """

    repository = _repository_object(name, document)
    github_id = _repository_id(name, repository)
    return _repository_canonical(name, repository), github_id


def _api_entry(name: str, canonical: str, github_id: int, stamp: str) -> dict[str, Any]:
    return {
        "name": name, "canonical": canonical, "method": aliases.METHOD_GITHUB_API,
        "github_id": github_id, "resolved_at": stamp,
    }


def _cached_api_id(cached: dict[str, Any] | None) -> int | None:
    """The GitHub id a cached entry was resolved to, or ``None`` when it has none."""

    return None if cached is None else cached.get("github_id")


def _require_cached_identity(
    entries: dict[str, dict[str, Any]], names: Iterable[str], github_id: int
) -> None:
    """Refuse a refresh that would silently swap one repository for another.

    GitHub ends a rename redirect once the old name is reused, so the same name
    can start returning a different repository. A cached ``github_api`` entry
    whose id differs from the fetched id is that case, and the cache is left
    unchanged.
    """

    for name in names:
        cached = entries.get(name)
        if _cached_api_id(cached) not in (None, github_id):
            raise RefreshError(
                f"{name}: repository identity changed (cached github_id {cached['github_id']}, "
                f"GitHub now returns {github_id}); the cache is left unchanged"
            )


def _former_target(entries: dict[str, dict[str, Any]], name: str, canonical: str) -> str | None:
    """The other repository ``name`` resolved to before this refresh, if it moved."""

    former = entries.get(name, {}).get("canonical")
    return None if former in (None, name, canonical) else former


def _require_same_target(mover: str, fetch: Fetch, expected: tuple[str, int]) -> None:
    """A name must itself resolve to the new repository before it is repointed there."""

    if _resolved(mover, fetch(mover)) != expected:
        raise RefreshError(
            f"{mover}: no longer resolves to {expected[0]} (github_id {expected[1]}), so its "
            "other aliases cannot be repointed consistently; the cache is left unchanged"
        )


def _movers(entries: dict[str, dict[str, Any]], name: str, canonical: str) -> list[str]:
    """Every other cached name that would follow ``name`` to ``canonical``.

    That is the former target of ``name`` (when it changed) and every alias of
    ``name`` or of that former target. Each one is re-resolved before it moves,
    because a sibling name may since have been reused for another repository.
    """

    former = _former_target(entries, name, canonical)
    moved = {name, former} - {None, canonical}
    followers = {entry["name"] for entry in entries.values() if entry["canonical"] in moved}
    return sorted((followers | {former}) - {None, name, canonical})


def _apply_resolution(
    entries: dict[str, dict[str, Any]], name: str, fetch: Fetch, stamp: str
) -> None:
    """Resolve ``name`` and everything that follows it, or change nothing at all."""

    expected = _resolved(name, fetch(name))
    canonical, github_id = expected
    _require_cached_identity(entries, (name, canonical), github_id)
    movers = _movers(entries, name, canonical)
    for mover in movers:
        _require_same_target(mover, fetch, expected)
        _require_cached_identity(entries, (mover,), github_id)
    for resolved in (*movers, name, canonical):
        entries[resolved] = _api_entry(resolved, canonical, github_id, stamp)


def refreshed_document(
    cache_document: dict[str, Any], names: Iterable[str], fetch: Fetch, now: datetime
) -> dict[str, Any]:
    """Return a new cache document with every name freshly resolved through ``fetch``."""

    stamp = aliases.format_timestamp(now)
    entries = {entry["name"]: dict(entry) for entry in cache_document["entries"]}
    for raw in names:
        try:
            name = repo_identity.canonical_repo(raw)
        except repo_identity.RepoNameError as exc:
            raise RefreshError(str(exc)) from exc
        _apply_resolution(entries, name, fetch, stamp)
    document = {
        "schema_version": aliases.CACHE_SCHEMA_VERSION,
        "updated_at": stamp,
        "entries": [entries[name] for name in sorted(entries)],
    }
    payload = lists.canonical_bytes(document)
    aliases.validate_cache_document(document, lists.sha256_hex(payload), "refreshed cache")
    return document


def _allowed_output_roots() -> tuple[str, ...]:
    """Where a refreshed cache may be written: this checkout, or the temporary directory."""

    return tuple(os.path.realpath(root) for root in (REPO, tempfile.gettempdir()))


def _is_within(path: str, root: str) -> bool:
    return os.path.commonpath((path, root)) == root


def confined_output(path: Path) -> Path:
    """Resolve ``--out`` and refuse anything outside the allowed roots or in the raw tree.

    The final component may not be a symlink; every parent symlink is resolved
    with ``realpath`` before the containment check, so ``..`` segments and
    symlinked directories cannot carry the write elsewhere.
    """

    supplied = os.fspath(path)
    if os.path.islink(supplied):
        raise RefreshError(f"--out {supplied} is a symlink")
    resolved = os.path.realpath(supplied)
    if raw_tree_guard.is_under_raw(Path(resolved)):
        raise RefreshError(f"--out {supplied} names or aliases outputs/raw/, which is immutable")
    parent = os.path.dirname(resolved)
    if not os.path.isdir(parent):
        raise RefreshError(f"--out {supplied}: parent {parent} is not an existing directory")
    if not any(_is_within(parent, root) for root in _allowed_output_roots()):
        raise RefreshError(
            f"--out {supplied} resolves outside the repository and the temporary directory"
        )
    return Path(resolved)


def publish_new_file(path: Path, payload: bytes) -> None:
    """Publish ``payload`` at a new ``path`` atomically; no partial file is ever visible.

    The bytes go to an exclusive temporary sibling, are fsynced, then hard-linked
    into place (``os.link`` refuses an existing destination). The temporary is
    removed on every path, so a failed write leaves neither it nor ``path``.
    """

    path = confined_output(path)
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.publishing"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path, follow_symlinks=False)
    finally:
        temporary.unlink(missing_ok=True)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("names", nargs="+", help="owner/name values to resolve")
    parser.add_argument("--cache", type=Path, default=policy.ALIAS_CACHE_PATH)
    parser.add_argument("--out", type=Path, required=True, help="new file; must not exist")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, fetch: Fetch = gh_api_repo,
         now: Callable[[], datetime] = lambda: datetime.now(UTC)) -> int:
    args = parse_args(argv)
    try:
        document, payload = lists.read_canonical_document(args.cache, "repo alias cache")
        current = aliases.validate_cache_document(
            document, lists.sha256_hex(payload), str(args.cache)
        )
        refreshed = refreshed_document(document, args.names, fetch, now())
        publish_new_file(args.out, lists.canonical_bytes(refreshed))
    except (RefreshError, lists.ExclusionPolicyError, OSError) as exc:
        print(f"refresh_repo_aliases: {exc}", file=sys.stderr)
        return 1
    resolved = {entry["name"]: entry["canonical"] for entry in refreshed["entries"]}
    print(json.dumps({
        "out": str(args.out), "previous_sha256": current.sha256,
        "resolved": {name: resolved[repo_identity.canonical_repo(name)] for name in args.names},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
