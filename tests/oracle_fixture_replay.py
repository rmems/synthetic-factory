"""Trusted deterministic replay of diagnostic historical oracle fixtures.

This is a test helper, not a publication entry point. The historical commit
is retained as fixture data, while unresolved dirty state makes every record
nonpublishable. Public CLI generation independently authenticates actual HEAD.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import oracle_generate
from oracle_grounded import canon, families, oracles


def replay_diagnostic_fixture(manifest, destination):
    if manifest["oracle_dirty"] is not None:
        raise ValueError("historical fixture replay requires unresolved provenance")
    args = SimpleNamespace(
        count=manifest["count_per_family"], seed=manifest["seed"],
        round_number=manifest["round"],
    )
    selected = list(manifest["families"])
    generated = {}
    files = {}
    job = oracle_generate.FamilyJob(
        count=args.count,
        seed=args.seed,
        round_number=args.round_number,
        commit=manifest["oracle_commit"],
        dirty=None,
        require_runtime=False,
        environ={},
    )
    for family in selected:
        accepted, rejected, errors = oracle_generate.generate_family(family, job)
        _require_diagnostic_records(accepted, rejected, errors)
        generated[family] = accepted, rejected, errors
        files.update(_write_family(destination, family, args.round_number, (accepted, rejected)))
    runtimes = tuple(dict.fromkeys(
        runtime for family in selected for runtime in families.spec_for(family).runtimes
    ))
    replayed = oracle_generate.build_manifest(
        job,
        oracle_generate.RunOutputs(
            selected,
            oracles.availability_report(runtimes, environ={}),
            generated,
            files,
        ),
    )
    (destination / "manifest.json").write_text(
        json.dumps(canon.normalize(replayed), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _require_diagnostic_records(accepted, rejected, errors):
    if errors or any(item["validation"]["publishable"] for item in accepted + rejected):
        raise AssertionError("diagnostic replay produced errors or publishable records")


def _write_family(destination, family, round_number, records_by_verdict):
    files = {}
    for verdict, records in zip(("accepted", "rejected"), records_by_verdict, strict=True):
        relative = Path(family) / f"{verdict}-r{round_number:02d}.jsonl"
        digest, _size = oracle_generate.write_jsonl(destination / relative, records)
        files[relative.as_posix()] = {"sha256": digest, "records": len(records)}
    return files
