#!/usr/bin/env python3
"""Regenerate the derived pins in the VSET test fixtures.

Several fixture values are hashes of live repository bytes, so an
ordinary edit to ``config/FACTORY-REGISTRY.json`` or to the counter repo
pack invalidates them and the VSET tests fail with no stated remedy:

* ``environment.repo_snapshot_hash`` -- ``pack_snapshot_hash`` over the
  repo pack's ``src/`` and ``tests/`` bytes.
* ``factory_contract_version`` / ``factory_registry_sha256`` -- the
  reviewed ``config/FACTORY-REGISTRY.json`` pin.
* ``counts`` and ``manifest_hash`` -- derived from the manifest entries.

This script restates those pins from the very functions
``pipelines/validate_vset.py`` validates against, so it can never relax a
check: it only removes the guesswork from a legitimate regeneration.
Deliberately broken reject fixtures keep every other field untouched.

  python3 scripts/refresh_vset_fixture_pins.py --check   # CI / tests
  python3 scripts/refresh_vset_fixture_pins.py           # rewrite
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

from vset_constants import (  # noqa: E402
    CURATION_DECISIONS,
    ORACLE_STATUSES,
    RECORD_KINDS,
    pack_snapshot_hash,
    registry_pin,
)
from vset_manifest import (  # noqa: E402
    _count_map,
    _is_invalid_or_impossible,
    manifest_body_hash,
)

FIXTURES = REPO / "tests" / "fixtures" / "vset"
PACK = FIXTURES / "repo-pack-counter"
MANIFEST = FIXTURES / "manifests" / "pilot-v1.json"
RECORD_DIRS = (FIXTURES / "records" / "accept", FIXTURES / "records" / "reject")


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _serialize(document: Any) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def _ordered(existing: Any, computed: dict[str, int]) -> dict[str, int]:
    """Keep the fixture's own key order; append new keys deterministically."""

    order = list(existing) if isinstance(existing, dict) else []
    keys = [key for key in order if key in computed]
    keys += sorted(key for key in computed if key not in keys)
    return {key: computed[key] for key in keys}


def _pin_record(record: Any, digest: str) -> None:
    environment = record.get("environment") if isinstance(record, dict) else None
    if isinstance(environment, dict) and "repo_snapshot_hash" in environment:
        environment["repo_snapshot_hash"] = digest


def _pin_counts(manifest: dict[str, Any], entries: list[Any]) -> None:
    counts = manifest.get("counts")
    if not isinstance(counts, dict):
        return
    counts["records"] = len(entries)
    for key, path, allowed in (
        ("by_record_kind", ("record_kind",), RECORD_KINDS),
        ("by_oracle_status", ("oracle", "status"), ORACLE_STATUSES),
        ("by_curation_decision", ("curation", "decision"), CURATION_DECISIONS),
    ):
        counts[key] = _ordered(counts.get(key), _count_map(entries, path, allowed))
    counts["invalid_or_impossible"] = sum(
        1 for entry in entries if _is_invalid_or_impossible(entry)
    )


def _pin_release(release: Any, pin: dict[str, str]) -> None:
    if not isinstance(release, dict):
        return
    if "factory_contract_version" in release:
        release["factory_contract_version"] = pin["schema_version"]
    if "factory_registry_sha256" in release:
        release["factory_registry_sha256"] = pin["sha256"]


def _pin_manifest(manifest: dict[str, Any], digest: str, pin: dict[str, str]) -> None:
    manifest["factory_contract_version"] = pin["schema_version"]
    manifest["factory_registry_sha256"] = pin["sha256"]
    entries = manifest.get("entries")
    entries = entries if isinstance(entries, list) else []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        _pin_record(entry, digest)
        _pin_release(entry.get("release"), pin)
    _pin_counts(manifest, entries)
    # manifest_hash covers the body above, so it is always stamped last.
    manifest["manifest_hash"] = manifest_body_hash(manifest)


def _refreshed() -> dict[Path, str]:
    digest = pack_snapshot_hash(PACK)
    pin = registry_pin()
    wanted: dict[Path, str] = {}
    for directory in RECORD_DIRS:
        for path in sorted(directory.glob("*.json")):
            record = _read(path)
            _pin_record(record, digest)
            wanted[path] = _serialize(record)
    manifest = _read(MANIFEST)
    _pin_manifest(manifest, digest, pin)
    wanted[MANIFEST] = _serialize(manifest)
    return wanted


def _stale(wanted: dict[Path, str]) -> list[Path]:
    return [
        path for path, text in wanted.items() if path.read_text(encoding="utf-8") != text
    ]


def stale_fixtures() -> list[Path]:
    """Fixture paths whose pinned bytes no longer match the live repository."""

    return _stale(_refreshed())


def _report(paths: list[Path], verb: str) -> None:
    for path in paths:
        print(f"{verb}: {path.relative_to(REPO)}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="report stale fixtures without writing (exit 1 when any drift)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    wanted = _refreshed()
    stale = _stale(wanted)
    if not stale:
        print("VSET fixture pins already match the live repository.")
        return 0
    if args.check:
        _report(stale, "stale")
        return 1
    for path in stale:
        path.write_text(wanted[path], encoding="utf-8")
    _report(stale, "rewrote")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
