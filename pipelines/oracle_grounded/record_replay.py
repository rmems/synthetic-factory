"""Bounded replay of stored oracle measurements."""

from . import canon, families, oracles


def _rebuild(record):
    stored_oracle = record["oracle"]
    stored_commit = stored_oracle.get("commit")
    if oracles.resolve_source_commit(stored_commit) != stored_commit:
        return None, ("invalid", "stored oracle.commit is not a resolved source commit")
    if stored_oracle.get("module_digest") != oracles.module_digest():
        return None, ("mismatch", "stored oracle module digest is not current")
    implementation = stored_oracle["implementation"]
    if (
        implementation in ("reference", "mixed")
        and stored_oracle.get("module") != oracles.MODULE_PATH
    ):
        return None, ("mismatch", "stored reference module identity is not current")
    spec = families.spec_for(record["family"])
    request = spec.build_request(record["scenario"], record["intervention"])
    rebuilt = canon.normalize(request.get("configuration"))
    stored = canon.normalize(stored_oracle.get("configuration"))
    if rebuilt != stored:
        detail = (
            "stored oracle.configuration does not match the configuration rebuilt "
            "from scenario and intervention"
        )
        return None, ("mismatch", detail)
    return (stored_oracle, spec, request), None


def _resolve_adapter(record, spec, environ):
    try:
        adapter = spec.oracle(environ)
    except oracles.OracleError as exc:
        return None, ("unavailable", str(exc))
    implementation = record["oracle"]["implementation"]
    if adapter.implementation != implementation:
        detail = (
            f"record was measured by {implementation!r} but this environment "
            f"resolves to {adapter.implementation!r}"
        )
        return None, ("unavailable", detail)
    return adapter, None


def _run_adapter(adapter, family, request):
    try:
        return adapter.run(family, request), None
    except oracles.OracleError as exc:
        return None, ("unavailable", str(exc))


def _stage_result(run, stored_oracle):
    try:
        replay_stages = canon.normalize(run.stages)
        stored_stages = canon.normalize(stored_oracle["stages"])
    except Exception as exc:
        detail = f"stored stage identity is malformed: {type(exc).__name__}"
        return "invalid", detail
    if replay_stages != stored_stages:
        return "mismatch", "stored oracle stage code identity does not match the replay"
    return None


def _digest_result(record, adapter, run):
    replay = {
        "produced_by": adapter.oracle_id,
        "measured": run.measured,
        "units": run.units,
    }
    try:
        replay_digest = canon.digest(replay)
        expected_digest = record["result_hash"]
    except (KeyError, TypeError, ValueError) as exc:
        return "invalid", f"stored result digest is malformed: {type(exc).__name__}"
    if replay_digest == expected_digest:
        return "reproduced", expected_digest
    return "mismatch", f"expected {expected_digest}, recomputed {replay_digest}"


def reproduce(record, environ=None):
    """Re-run a stored measurement, bounding malformed input as invalid."""
    try:
        rebuilt, error = _rebuild(record)
    except Exception as exc:
        detail = f"stored record cannot rebuild an oracle request: {type(exc).__name__}"
        return "invalid", detail
    if error is not None:
        return error
    stored_oracle, spec, request = rebuilt
    adapter, error = _resolve_adapter(record, spec, environ)
    if error is not None:
        return error
    run, error = _run_adapter(adapter, record["family"], request)
    if error is not None:
        return error
    if (error := _stage_result(run, stored_oracle)) is not None:
        return error
    return _digest_result(record, adapter, run)
