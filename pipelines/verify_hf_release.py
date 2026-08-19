#!/usr/bin/env python3
"""Verify the public Hugging Face raw-release metadata for this factory.

This is intentionally a read-only stdlib CLI.  Hugging Face dataset repositories
cannot execute GitHub Actions themselves, so this source repository is the
release-verification authority.  The command fetches public, rendered source
files from every configured dataset repository and proves that the release
contract is still present: Apache-2.0 terms, explicit multi-model provenance,
raw/non-training-ready status, and a lossless viewer projection.

Usage:
    python3 pipelines/verify_hf_release.py
    python3 pipelines/verify_hf_release.py --repo rmems/thalamic-relay-trajectories
"""

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Callable, Iterable
from urllib.request import Request, urlopen


DATASET_REPOS = (
    "rmems/thalamic-relay-trajectories",
    "rmems/neuromorphic-event-language-bridge",
    "rmems/multi-agent-ouroboros-swarm",
    "rmems/failure-as-fuel-preference-cascade",
    "rmems/agentic-coding-trajectories",
)

REQUIRED_CONTRIBUTORS = {
    "Claude Fable 5 (Ultracode)": {"synthetic-data-generation"},
    "Meta Muse Spark 1.2": {"research", "quality-audit", "curation-review"},
    "Codex (GPT-5.6-Sol(max))": {
        "research",
        "quality-audit",
        "curation-review",
        "curation-design",
        "validation",
        "release-engineering",
    },
    "Grok Build (Grok 4.6(xhigh))": {
        "research",
        "quality-audit",
        "curation-review",
    },
}

REQUIRED_CARD_TEXT = (
    "Claude Fable 5",
    "Meta Muse Spark 1.2",
    "Codex (GPT-5.6-Sol(max))",
    "Grok Build (Grok 4.6(xhigh))",
    "not training-ready",
    "data/viewer/records.parquet",
)


@dataclass(frozen=True)
class CheckResult:
    """Read-only verification outcome for one Hub dataset repository."""

    repo: str
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def public_url(repo: str, path: str, base_url: str) -> str:
    """Return the public raw-file URL without accepting arbitrary schemes."""

    if not repo.startswith("rmems/") or repo.count("/") != 1:
        raise ValueError(f"expected an rmems dataset repo, got {repo!r}")
    return f"{base_url.rstrip('/')}/datasets/{repo}/raw/main/{path}"


def fetch_bytes(url: str, timeout: float = 30.0) -> bytes:
    """Fetch one public release file with a stable, explicit user agent."""

    request = Request(url, headers={"User-Agent": "synthetic-factory-release-ci/1"})
    with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed Hub URL
        return response.read()


def fetch_text(url: str, timeout: float = 30.0) -> str:
    return fetch_bytes(url, timeout).decode("utf-8")


def _front_matter(text: str) -> dict[str, str]:
    """Parse the scalar front-matter fields this verifier owns.

    Dataset cards use YAML, but this contract only needs scalar top-level
    fields.  Avoiding a YAML dependency keeps the operator and GitHub Action
    stdlib-only.
    """

    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    values = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line.startswith((" ", "-")):
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def _contributor_roles(provenance: dict) -> dict[str, set[str]]:
    roles_by_name: dict[str, set[str]] = {}
    contributors = provenance.get("contributors")
    if not isinstance(contributors, list):
        return roles_by_name
    for contributor in contributors:
        if not isinstance(contributor, dict):
            continue
        name = contributor.get("name")
        roles = contributor.get("roles")
        if isinstance(name, str) and isinstance(roles, list):
            roles_by_name[name] = {role for role in roles if isinstance(role, str)}
    return roles_by_name


def verify_dataset(
    repo: str,
    *,
    base_url: str = "https://huggingface.co",
    timeout: float = 30.0,
    text_fetcher: Callable[[str, float], str] = fetch_text,
    bytes_fetcher: Callable[[str, float], bytes] = fetch_bytes,
) -> CheckResult:
    """Check the public release contract for one repository without writing."""

    errors: list[str] = []
    try:
        card = text_fetcher(public_url(repo, "README.md", base_url), timeout)
        provenance_text = text_fetcher(
            public_url(repo, "provenance.json", base_url), timeout
        )
        license_text = text_fetcher(public_url(repo, "LICENSE", base_url), timeout)
        viewer_bytes = bytes_fetcher(
            public_url(repo, "data/viewer/records.parquet", base_url), timeout
        )
    except Exception as error:  # network exceptions differ across Hub backends
        return CheckResult(repo, (f"public fetch failed: {error}",))

    if _front_matter(card).get("license") != "apache-2.0":
        errors.append("README front matter must declare license: apache-2.0")
    for required_text in REQUIRED_CARD_TEXT:
        if required_text not in card:
            errors.append(f"README missing required text: {required_text}")
    if "Apache License" not in license_text or "Version 2.0" not in license_text:
        errors.append("LICENSE is not recognizably Apache License 2.0")
    if not viewer_bytes:
        errors.append("viewer projection is empty")

    try:
        provenance = json.loads(provenance_text)
    except json.JSONDecodeError as error:
        errors.append(f"provenance.json is invalid JSON: {error.msg}")
    else:
        if provenance.get("payload_published") is not True:
            errors.append("provenance must mark payload_published true")
        if provenance.get("training_ready") is not False:
            errors.append("provenance must mark training_ready false")
        roles_by_name = _contributor_roles(provenance)
        for name, required_roles in REQUIRED_CONTRIBUTORS.items():
            actual_roles = roles_by_name.get(name)
            if actual_roles is None:
                errors.append(f"provenance missing contributor: {name}")
            elif not required_roles.issubset(actual_roles):
                missing = ", ".join(sorted(required_roles - actual_roles))
                errors.append(f"provenance roles missing for {name}: {missing}")

    return CheckResult(repo, tuple(errors))


def verify_repositories(
    repos: Iterable[str], **kwargs
) -> tuple[CheckResult, ...]:
    return tuple(verify_dataset(repo, **kwargs) for repo in repos)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        action="append",
        choices=DATASET_REPOS,
        help="verify only this public rmems dataset repository; repeatable",
    )
    parser.add_argument(
        "--timeout", type=float, default=30.0, help="per-request timeout in seconds"
    )
    args = parser.parse_args(argv)

    results = verify_repositories(args.repo or DATASET_REPOS, timeout=args.timeout)
    for result in results:
        if result.ok:
            print(f"OK {result.repo}")
        else:
            print(f"FAIL {result.repo}", file=sys.stderr)
            for error in result.errors:
                print(f"  - {error}", file=sys.stderr)
    print(
        json.dumps(
            {
                "repositories": len(results),
                "passed": sum(result.ok for result in results),
                "failed": sum(not result.ok for result in results),
            },
            sort_keys=True,
        )
    )
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
