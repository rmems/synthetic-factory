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
import hashlib
import json
import re
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from urllib.parse import urlparse
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

HUB_BASE_URL = "https://huggingface.co"
APACHE_2_NORMALIZED_SHA256 = "b9a1a37910c6451f5e6892324a5f52878114219b593a9f48eb8054f45e24d33c"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")

REQUIRED_CARD_MARKERS = (
    "> **Release status:**",
    "raw, uncurated",
    "Claude Fable 5",
    "Meta Muse Spark 1.2",
    "Codex (GPT-5.6-Sol(max))",
    "Grok Build (Grok 4.6(xhigh))",
    "research, quality-audit",
    "curation-review",
    "curation design, validation, and release engineering",
    "not training-ready",
    "## Intended model target",
    "## Generation attribution",
    "## Published raw payload",
    "## Links",
    "## License",
    "[Synthetic Data Factory](https://github.com/rmems/synthetic-factory)",
    "data/viewer/records.parquet",
    "name: source_file",
    "name: source_line",
    "name: record_json",
)

REQUIRED_PURPOSE_TEXT = {
    "rmems/thalamic-relay-trajectories": "relay-gated state assessment",
    "rmems/neuromorphic-event-language-bridge": "event streams to structured language views",
    "rmems/multi-agent-ouroboros-swarm": "delegation, critique, conflict resolution",
    "rmems/failure-as-fuel-preference-cascade": "chosen/rejected comparisons",
    "rmems/agentic-coding-trajectories": "planning, tool use, observation",
}

REQUIRED_TARGET_TEXT = {
    "rmems/thalamic-relay-trajectories": "designed as one component of **Spikenaut** training",
    "rmems/neuromorphic-event-language-bridge": "designed as one component of **Spikenaut** training",
    "rmems/multi-agent-ouroboros-swarm": "not labeled as Spikenaut training data",
    "rmems/failure-as-fuel-preference-cascade": "not labeled as Spikenaut training data",
    "rmems/agentic-coding-trajectories": "not labeled as Spikenaut training data",
}


@dataclass(frozen=True)
class CheckResult:
    """Read-only verification outcome for one Hub dataset repository."""

    repo: str
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def public_url(
    repo: str,
    path: str,
    base_url: str,
    revision: str = "main",
    *,
    resolve: bool = False,
) -> str:
    """Return a fixed-host, public Hub file URL for a safe repository path."""

    if not repo.startswith("rmems/") or repo.count("/") != 1:
        raise ValueError(f"expected an rmems dataset repo, got {repo!r}")
    if base_url.rstrip("/") != HUB_BASE_URL:
        raise ValueError(f"expected Hugging Face base URL, got {base_url!r}")
    if not path or path.startswith("/") or any(
        part in {"", ".", ".."} for part in path.split("/")
    ):
        raise ValueError(f"unsafe repository path: {path!r}")
    if revision != "main" and not REVISION_RE.fullmatch(revision):
        raise ValueError(f"expected main or immutable revision, got {revision!r}")
    endpoint = "resolve" if resolve else "raw"
    return f"{HUB_BASE_URL}/datasets/{repo}/{endpoint}/{revision}/{path}"


def fetch_bytes(url: str, timeout: float = 30.0) -> bytes:
    """Fetch one public release file with a stable, explicit user agent."""

    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "huggingface.co":
        raise ValueError(f"refusing non-Hub URL: {url!r}")
    request = Request(url, headers={"User-Agent": "synthetic-factory-release-ci/1"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed Hub URL
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


def _normalized_text(value: str) -> str:
    return " ".join(value.split()).casefold()


def _normalized_sha256(value: str) -> str:
    normalized = "\n".join(value.splitlines()) + "\n"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _snapshot_entries(
    provenance: dict, errors: list[str]
) -> tuple[tuple[str, str], ...]:
    """Validate immutable raw-payload declarations and return their paths."""

    snapshot = provenance.get("raw_snapshot")
    if not isinstance(snapshot, dict):
        errors.append("provenance missing raw_snapshot")
        return ()
    revision = snapshot.get("revision")
    files = snapshot.get("files")
    if not isinstance(revision, str) or not REVISION_RE.fullmatch(revision):
        errors.append("raw_snapshot must declare a 40-character immutable revision")
        return ()
    if not isinstance(files, list) or not files:
        errors.append("raw_snapshot must declare at least one raw payload file")
        return ()

    entries: list[tuple[str, str]] = []
    for entry in files:
        if not isinstance(entry, dict):
            errors.append("raw_snapshot file declaration must be an object")
            continue
        path = entry.get("path")
        digest = entry.get("sha256")
        if (
            not isinstance(path, str)
            or not path.startswith("data/raw/")
            or not path.endswith(".jsonl")
            or any(part in {"", ".", ".."} for part in path.split("/"))
        ):
            errors.append(f"raw_snapshot has unsafe payload path: {path!r}")
            continue
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            errors.append(f"raw_snapshot has invalid sha256 for {path}")
            continue
        entries.append((path, digest))
    if len(entries) != len({path for path, _digest in entries}):
        errors.append("raw_snapshot repeats a payload path")
    return tuple(entries)


def _viewer_errors(card: str, viewer_bytes: bytes) -> tuple[str, ...]:
    """Validate the stdlib-verifiable framing and declared lossless schema."""

    errors = []
    if not re.search(r"(?m)^\s+num_examples:\s+[1-9][0-9]*\s*$", card):
        errors.append("README must declare a positive viewer num_examples value")
    if len(viewer_bytes) < 12 or not viewer_bytes.startswith(b"PAR1"):
        errors.append("viewer projection is not Parquet-framed")
        return tuple(errors)
    if not viewer_bytes.endswith(b"PAR1"):
        errors.append("viewer projection is missing the Parquet footer magic")
        return tuple(errors)
    footer_size = int.from_bytes(viewer_bytes[-8:-4], "little")
    if footer_size <= 0 or footer_size > len(viewer_bytes) - 8:
        errors.append("viewer projection has an invalid Parquet footer length")
    return tuple(errors)


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
            public_url(
                repo, "data/viewer/records.parquet", base_url, resolve=True
            ),
            timeout,
        )
    except Exception as error:  # network exceptions differ across Hub backends
        return CheckResult(repo, (f"public fetch failed: {error}",))

    if _front_matter(card).get("license") != "apache-2.0":
        errors.append("README front matter must declare license: apache-2.0")
    normalized_card = _normalized_text(card)
    for marker in REQUIRED_CARD_MARKERS:
        if _normalized_text(marker) not in normalized_card:
            errors.append(f"README missing required card marker: {marker}")
    purpose = REQUIRED_PURPOSE_TEXT[repo]
    if _normalized_text(purpose) not in normalized_card:
        errors.append(f"README missing repository purpose marker: {purpose}")
    target = REQUIRED_TARGET_TEXT[repo]
    if _normalized_text(target) not in normalized_card:
        errors.append(f"README missing Spikenaut classification: {target}")
    if _normalized_sha256(license_text) != APACHE_2_NORMALIZED_SHA256:
        errors.append("LICENSE does not match the complete Apache License 2.0 text")
    errors.extend(_viewer_errors(card, viewer_bytes))

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
        snapshot_entries = _snapshot_entries(provenance, errors)
        snapshot = provenance.get("raw_snapshot")
        revision = snapshot.get("revision") if isinstance(snapshot, dict) else None
        if isinstance(revision, str):
            for path, expected_digest in snapshot_entries:
                try:
                    payload = bytes_fetcher(
                        public_url(repo, path, base_url, revision), timeout
                    )
                except Exception as error:  # network exceptions differ by Hub backend
                    errors.append(f"immutable raw payload fetch failed for {path}: {error}")
                    continue
                actual_digest = hashlib.sha256(payload).hexdigest()
                if actual_digest != expected_digest:
                    errors.append(f"raw payload digest mismatch for {path}")

    return CheckResult(repo, tuple(errors))


def verify_repositories(
    repos: Iterable[str], *, timeout: float = 30.0
) -> tuple[CheckResult, ...]:
    return tuple(verify_dataset(repo, timeout=timeout) for repo in repos)


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
