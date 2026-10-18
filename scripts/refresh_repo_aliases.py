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
import subprocess
import sys
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


def gh_api_repo(name: str) -> Any:
    """Return the decoded ``gh api repos/<name>`` document, failing closed."""

    try:
        completed = subprocess.run(
            ["gh", "api", f"repos/{name}"], capture_output=True, check=False, text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RefreshError(f"gh api repos/{name} could not run: {exc}") from exc
    if completed.returncode != 0:
        raise RefreshError(f"gh api repos/{name} failed: {completed.stderr.strip()}")
    try:
        return json.loads(completed.stdout)
    except ValueError as exc:
        raise RefreshError(f"gh api repos/{name} returned invalid JSON: {exc}") from exc


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


def _repoint(entries: dict[str, dict[str, Any]], name: str, canonical: str) -> None:
    """Keep the cache closed when a former canonical name has itself moved."""

    for entry in entries.values():
        if entry["canonical"] == name and entry["name"] != name:
            entry["canonical"] = canonical


def refreshed_document(
    cache_document: dict[str, Any], names: Iterable[str], fetch: Fetch, now: datetime
) -> dict[str, Any]:
    """Return a new cache document with every name freshly resolved through ``fetch``."""

    stamp = now.astimezone(UTC).strftime(aliases.TIMESTAMP_FORMAT)
    entries = {entry["name"]: entry for entry in cache_document["entries"]}
    for raw in names:
        try:
            name = repo_identity.canonical_repo(raw)
        except repo_identity.RepoNameError as exc:
            raise RefreshError(str(exc)) from exc
        canonical, github_id = _resolved(name, fetch(name))
        _repoint(entries, name, canonical)
        entries[name] = _api_entry(name, canonical, github_id, stamp)
        entries[canonical] = _api_entry(canonical, canonical, github_id, stamp)
    document = {
        "schema_version": aliases.CACHE_SCHEMA_VERSION,
        "updated_at": stamp,
        "entries": [entries[name] for name in sorted(entries)],
    }
    payload = lists.canonical_bytes(document)
    aliases.validate_cache_document(document, lists.sha256_hex(payload), "refreshed cache")
    return document


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
        with args.out.open("xb") as handle:
            handle.write(lists.canonical_bytes(refreshed))
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
