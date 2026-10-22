#!/usr/bin/env python3
"""The eval-denylist / do-not-train exclusion policy, loaded at import (#494).

Policy is data: the two vendored lists and the repository alias cache under
``config/eval-exclusion/`` are read and strictly validated when this module is
imported, so a missing or invalid file stops compose before any record is
read. ``ACTIVE_POLICY`` is the loaded policy; ``load_policy`` builds another
one from explicit paths (tests and generator-side consumers use it).

``ExclusionPolicy.evaluate`` is the one matching rule. It canonicalizes a
source repository (lowercase, then one offline alias-cache lookup), then looks
up whole values only: the canonical ``owner/name`` against each list's
``repos``, and a ``program_id`` / ``task_id`` against the same-named keys. A
repository that is absent, malformed, or not in the cache is *unresolved* and
reported as such, never passed through.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("eval_exclusion_policy")
    from . import eval_exclusion_aliases as _aliases
    from . import eval_exclusion_lists as _lists
    from . import repo_identity as _repo_identity
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "eval_exclusion_policy"
    )
    import eval_exclusion_aliases as _aliases
    import eval_exclusion_lists as _lists
    import repo_identity as _repo_identity

ExclusionPolicyError = _lists.ExclusionPolicyError
ExclusionList = _lists.ExclusionList
AliasCache = _aliases.AliasCache

REPO_ROOT = Path(__file__).resolve().parent.parent
POLICY_DIR = REPO_ROOT / "config" / "eval-exclusion"
DENYLIST_PATH = POLICY_DIR / "eval-denylist.json"
DO_NOT_TRAIN_PATH = POLICY_DIR / "do-not-train.json"
ALIAS_CACHE_PATH = POLICY_DIR / "repo-aliases.json"

REASON_EVAL_DENYLISTED = "compose.eval_denylisted"
REASON_DO_NOT_TRAIN = "compose.do_not_train_listed"
REASON_REPO_UNRESOLVED = "compose.source_repo_unresolved"
REASON_REPO_INVALID = "compose.source_repo_invalid"
REASON_BY_SLOT = {
    _lists.LIST_EVAL_DENYLIST: REASON_EVAL_DENYLISTED,
    _lists.LIST_DO_NOT_TRAIN: REASON_DO_NOT_TRAIN,
}
REASON_ORDER = (
    REASON_REPO_INVALID, REASON_REPO_UNRESOLVED, REASON_EVAL_DENYLISTED, REASON_DO_NOT_TRAIN,
)
_ID_KEYS = ((_lists.KEY_PROGRAM_IDS, "program_id"), (_lists.KEY_TASK_IDS, "task_id"))


@dataclass(frozen=True)
class SourceIdentity:
    """What a record says about its public source, exactly as the record says it."""

    repo: Any
    program_id: str | None = None
    task_id: str | None = None
    base_commit: str | None = None


@dataclass(frozen=True)
class Evaluation:
    """The deterministic verdict for one source identity."""

    reason_codes: tuple[str, ...]
    canonical_repo: str | None
    matches: tuple[dict[str, str], ...]

    @property
    def excluded(self) -> bool:
        return bool(self.reason_codes)


def _match(listed: ExclusionList, key: str, value: str) -> dict[str, str]:
    return {"list": listed.slot, "key": key, "value": value}


def _repo_matches(listed: ExclusionList, canonical: str | None) -> list[dict[str, str]]:
    """The list's hit on a resolved canonical repository, if any."""

    if canonical is None or canonical not in listed.repos:
        return []
    return [_match(listed, _lists.KEY_REPOS, canonical)]


def _identity_ids(identity: SourceIdentity) -> tuple[tuple[str, str], ...]:
    """The ``(list key, value)`` pairs a record carries as plain strings."""

    pairs = ((key, getattr(identity, attribute)) for key, attribute in _ID_KEYS)
    return tuple((key, value) for key, value in pairs if isinstance(value, str))


def _id_matches(listed: ExclusionList, ids: tuple[tuple[str, str], ...]) -> list[dict[str, str]]:
    """The list's hits on ``program_id`` / ``task_id`` values."""

    return [_match(listed, key, value) for key, value in ids if value in listed.values(key)]


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(resolved)


@dataclass(frozen=True)
class ExclusionPolicy:
    """Both lists plus the alias cache, cross-validated against each other."""

    denylist: ExclusionList
    do_not_train: ExclusionList
    aliases: AliasCache
    paths: tuple[str, str, str]

    def lists(self) -> tuple[ExclusionList, ExclusionList]:
        return self.denylist, self.do_not_train

    def resolve_repo(self, raw: Any) -> tuple[str | None, str | None]:
        """Return ``(canonical, None)`` or ``(None, reason)`` for one raw repository value."""

        if raw is None:
            return None, REASON_REPO_UNRESOLVED
        try:
            spelled = _repo_identity.canonical_repo(raw)
        except _repo_identity.RepoNameError:
            return None, REASON_REPO_INVALID
        canonical = self.aliases.resolve(spelled)
        return (canonical, None) if canonical is not None else (None, REASON_REPO_UNRESOLVED)

    def _matches(self, canonical: str | None, identity: SourceIdentity) -> list[dict[str, str]]:
        """Every whole-value hit, list by list: the repository first, then the ids."""

        ids = _identity_ids(identity)
        return [
            match
            for listed in self.lists()
            for match in (*_repo_matches(listed, canonical), *_id_matches(listed, ids))
        ]

    def evaluate(self, identity: SourceIdentity, *, require_repo: bool = True) -> Evaluation:
        """Match one source identity on whole canonical values; never on substrings."""

        if identity.repo is None and not require_repo:
            canonical, unresolved = None, None
        else:
            canonical, unresolved = self.resolve_repo(identity.repo)
            if unresolved is not None and not require_repo:
                unresolved = None
        matches = self._matches(canonical, identity)
        reasons = {REASON_BY_SLOT[match["list"]] for match in matches}
        if unresolved is not None:
            reasons.add(unresolved)
        ordered = tuple(reason for reason in REASON_ORDER if reason in reasons)
        return Evaluation(ordered, canonical, tuple(matches))

    def descriptor(self) -> dict[str, Any]:
        """The exact block every compose summary records for this policy."""

        denylist_path, do_not_train_path, alias_path = self.paths
        return {
            _lists.LIST_EVAL_DENYLIST: _list_descriptor(self.denylist, denylist_path),
            _lists.LIST_DO_NOT_TRAIN: _list_descriptor(self.do_not_train, do_not_train_path),
            "repo_aliases": {
                "path": alias_path,
                "sha256": self.aliases.sha256,
                "updated_at": self.aliases.updated_at,
            },
        }


def _list_descriptor(listed: ExclusionList, path: str) -> dict[str, Any]:
    return {"path": path, "sha256": listed.sha256, "status": listed.status}


def _require_canonical_list_names(listed: ExclusionList, aliases: AliasCache) -> None:
    stale = sorted(repo for repo in listed.repos if aliases.is_alias(repo))
    if stale:
        canonical = {repo: aliases.resolve(repo) for repo in stale}
        raise ExclusionPolicyError(
            f"{listed.slot} list names renamed repositories by their old names: {canonical}"
        )


def load_policy(
    denylist_path: Path = DENYLIST_PATH,
    do_not_train_path: Path = DO_NOT_TRAIN_PATH,
    alias_cache_path: Path = ALIAS_CACHE_PATH,
) -> ExclusionPolicy:
    """Load and cross-validate both lists and the alias cache, failing closed."""

    denylist = _lists.load_list(Path(denylist_path), _lists.LIST_EVAL_DENYLIST)
    do_not_train = _lists.load_list(Path(do_not_train_path), _lists.LIST_DO_NOT_TRAIN)
    aliases = _aliases.load_cache(Path(alias_cache_path))
    for listed in (denylist, do_not_train):
        _require_canonical_list_names(listed, aliases)
    paths = (
        _display_path(Path(denylist_path)),
        _display_path(Path(do_not_train_path)),
        _display_path(Path(alias_cache_path)),
    )
    return ExclusionPolicy(denylist, do_not_train, aliases, paths)


ACTIVE_POLICY = load_policy()


if __package__:
    _expose_package_sibling(__name__)
