#!/usr/bin/env python3
"""Resolve repository names through the GitHub API into a new alias cache (#494).

Compose never touches the network: it canonicalizes source repositories from
the committed ``config/eval-exclusion/repo-aliases.json``. This operator script
is the only place that asks GitHub. For each name it runs
``gh api repos/<owner>/<name>``, which follows the redirects GitHub serves for
renamed and transferred repositories, and records the canonical ``full_name``
(lowercased), the stable numeric ``id``, and the UTC resolution time. The
canonical target gets its own self-entry, so the cache stays closed.

The result is validated with the same loader compose uses and written to a
brand-new ``--out`` path (an existing path is refused). Review the diff, then
replace the committed cache with it in a pull request.

  python3 scripts/refresh_repo_aliases.py --out /tmp/repo-aliases.json kbknapp/clap-rs
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess  # nosec B404 -- one fixed `gh api` argv below, never a shell
import sys
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
import repo_identity  # noqa: E402

Fetch = Callable[[str], Any]


class RefreshError(RuntimeError):
    """A name could not be resolved, so no cache is written."""


def _gh_executable() -> str:
    """Absolute ``gh`` on PATH; a bare name would be a partial-path launch."""

    found = shutil.which("gh")
    if found is None:
        raise RefreshError("gh is not on PATH")
    return found


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


def _resolved(name: str, document: Any) -> tuple[str, int]:
    if not isinstance(document, dict):
        raise RefreshError(f"{name}: GitHub returned no repository object")
    full_name, github_id = document.get("full_name"), document.get("id")
    if isinstance(github_id, bool) or not isinstance(github_id, int) or github_id < 1:
        raise RefreshError(f"{name}: GitHub returned no repository id")
    try:
        return repo_identity.canonical_repo(full_name), github_id
    except repo_identity.RepoNameError as exc:
        raise RefreshError(f"{name}: GitHub returned an unusable full_name: {exc}") from exc


def _api_entry(name: str, canonical: str, github_id: int, stamp: str) -> dict[str, Any]:
    return {
        "name": name, "canonical": canonical, "method": aliases.METHOD_GITHUB_API,
        "github_id": github_id, "resolved_at": stamp,
    }


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
        if cached is None or cached["method"] != aliases.METHOD_GITHUB_API:
            continue
        if cached["github_id"] != github_id:
            raise RefreshError(
                f"{name}: repository identity changed (cached github_id {cached['github_id']}, "
                f"GitHub now returns {github_id}); the cache is left unchanged"
            )


def _former_target(entries: dict[str, dict[str, Any]], name: str, canonical: str) -> str | None:
    cached = entries.get(name)
    former = None if cached is None else cached["canonical"]
    return None if former in (None, name, canonical) else former


def _require_same_target(former: str, fetch: Fetch, expected: tuple[str, int]) -> None:
    """A moved target must itself resolve to the new repository before its aliases follow."""

    if _resolved(former, fetch(former)) != expected:
        raise RefreshError(
            f"{former}: no longer resolves to {expected[0]} (github_id {expected[1]}), so its "
            "other aliases cannot be repointed consistently; the cache is left unchanged"
        )


def _repoint(
    entries: dict[str, dict[str, Any]], moved: set[str], canonical: str, stamp: str
) -> None:
    """Send every alias of a moved name to its new canonical target."""

    for entry in entries.values():
        if entry["canonical"] in moved:
            entry["canonical"] = canonical
            entry["resolved_at"] = stamp


def _apply_resolution(
    entries: dict[str, dict[str, Any]], name: str, fetch: Fetch, stamp: str
) -> None:
    canonical, github_id = _resolved(name, fetch(name))
    _require_cached_identity(entries, (name, canonical), github_id)
    former = _former_target(entries, name, canonical)
    if former is not None:
        _require_same_target(former, fetch, (canonical, github_id))
        _require_cached_identity(entries, (former,), github_id)
        entries[former] = _api_entry(former, canonical, github_id, stamp)
    _repoint(entries, {name, former} - {None, canonical}, canonical, stamp)
    entries[name] = _api_entry(name, canonical, github_id, stamp)
    entries[canonical] = _api_entry(canonical, canonical, github_id, stamp)


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


def publish_new_file(path: Path, payload: bytes) -> None:
    """Publish ``payload`` at a new ``path`` atomically; no partial file is ever visible.

    The bytes go to an exclusive temporary sibling, are fsynced, then hard-linked
    into place (``os.link`` refuses an existing destination). The temporary is
    removed on every path, so a failed write leaves neither it nor ``path``.
    """

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
