"""Pure RUN2 metadata and candidate completeness checks shared by trusted consumers."""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from . import catalog as cat, catalog_check, executor, generate, mutate, records as assembly, vocabulary as cv
from . import planning
from ._contract import ExactJSONFloat, bind_import_twin, exact_fraction, oc, vocab

# Bind the loaded implementation once; validate_run itself performs no I/O.
_HARNESS_SHA256 = executor.harness_sha256()


def run_identity(run: dict, candidates_sha256: str) -> dict:
    """All RUN fields are replay provenance; the captured byte digest is independent input."""
    return {'candidates_sha256': candidates_sha256, 'run_sha256':
            cat.sha256_text(oc.canonical_json(run)),
            **{key: run[key] for key in ('seed', 'produced_at', 'catalog', 'harness_sha256')}}


def _counts(value, expected=None):
    if not isinstance(value, dict):
        return False
    for count in value.values():
        if type(count) is not int:
            return False
        if count < 0:
            return False
    return expected is None or Counter(value) == Counter(expected)


def _integer_in_domain(value, minimum, maximum):
    if type(value) is not int:
        return False
    return minimum <= value <= maximum


def _draw_identity_matches(record, run, catalog):
    index = record['intervention']['draw_index']
    identity = cat.sha256_text(oc.canonical_json([catalog.catalog_id, catalog.programs_sha256]))
    if not _integer_in_domain(index, 0, run['count'] - 1):
        return False
    expected = f'{cv.RECORD_ID_PREFIX}-{identity}-{run["seed"]}-{index:05d}'
    return record['id'] == expected


def _generator_identity_matches(record, run):
    actual = (
        record['generator']['seed'],
        record['generator']['name'],
        record['generator']['version'],
        record['provenance']['produced_at'],
    )
    expected = (run['seed'], cv.GENERATOR_NAME, cv.GENERATOR_VERSION, run['produced_at'])
    return actual == expected


def _oracle_identity_matches(record, run):
    index = record['intervention']['draw_index']
    program_id = record['scenario']['source']['program_id']
    expected_seed = assembly.candidate_seed(run['seed'], program_id, index)
    configuration = record['oracle']['configuration']
    expected_limits = {
        'cpu_s': int(run['timeout_s']) + 2,
        'address_space_mib': cv.ADDRESS_SPACE_MIB,
        'file_size_kib': cv.FILE_SIZE_KIB,
    }
    actual = (
        record['oracle']['seed'],
        record['oracle']['fingerprint']['harness_sha256'],
        exact_fraction(configuration['timeout_s']),
        configuration['limits'],
    )
    expected = (expected_seed, run['harness_sha256'], exact_fraction(run['timeout_s']), expected_limits)
    return actual == expected


def record_identity_matches(record, catalog):
    """Derivable per-record identity only; authentic timestamps and draws need RUN."""
    run = {'seed': record['generator']['seed'], 'count': cv.MAX_COUNT,
           'harness_sha256': _HARNESS_SHA256,
           'timeout_s': record['oracle']['configuration']['timeout_s']}
    checks = (
        lambda: _integer_in_domain(run['seed'], 0, cv.MAX_SEED),
        lambda: _draw_identity_matches(record, run, catalog),
        lambda: _oracle_identity_matches(record, run),
    )
    return all(check() for check in checks)


def _record_identity(record, run, catalog):
    checks = (
        lambda: _draw_identity_matches(record, run, catalog),
        lambda: _generator_identity_matches(record, run),
        lambda: _oracle_identity_matches(record, run),
        lambda: record_identity_matches(record, catalog),
    )
    return all(check() for check in checks)


def _record_totals_match(run, records):
    if type(run['records']) is not int:
        return False
    if run['records'] != len(records):
        return False
    for key, field in (('outcomes', 'outcome'), ('oracle_statuses', 'oracle_status')):
        expected = Counter(record['result'][field] for record in records)
        if not _counts(run[key], expected):
            return False
    reasons = Counter(code for record in records for code in record['result']['reason_codes'])
    return _counts(run['reasons'], reasons)


def _skips_match(run):
    skips = run['skips']
    if not _counts(skips):
        return False
    return set(skips) <= cv.SKIP_CODE_SET


def _program_counts_match(run, expected):
    programs = run['programs']
    if not isinstance(programs, dict):
        return False
    return all(_counts(counts) for counts in programs.values()) and programs == expected


def _program_cap_matches(run, per_program):
    return all(count <= run['per_program_cap'] for count in per_program.values())


def _program_summary_matches(run, records, catalog):
    sites = {program.program_id: len(mutate.sites(
        program.text, program.function, program.want_kind,
    )) for program in catalog.programs}
    per_program = Counter(record['scenario']['source']['program_id'] for record in records)
    expected = {
        program_id: {'sites': count, 'records': per_program[program_id]}
        for program_id, count in sites.items()
    }
    inventory = sum(count == 0 for count in sites.values())
    checks = (
        lambda: _program_counts_match(run, expected),
        lambda: _program_cap_matches(run, per_program),
        lambda: run['skips'].get(cv.SKIP_MUTATION_NO_SITES, 0) == inventory,
    )
    return all(check() for check in checks)


def _attempt_count_matches(run, records):
    attempted_skips = sum(
        count for code, count in run['skips'].items() if code != cv.SKIP_MUTATION_NO_SITES
    )
    return run['count'] == len(records) + attempted_skips


def _summary_matches(run, records, catalog):
    checks = (
        lambda: _record_totals_match(run, records),
        lambda: _skips_match(run),
        lambda: _program_summary_matches(run, records, catalog),
        lambda: _attempt_count_matches(run, records),
    )
    return all(check() for check in checks)


@dataclass(frozen=True)
class _RunInputs:
    run: dict
    records: list
    catalog: cat.Catalog
    candidates_sha256: str


def _run_header_matches(run):
    expected_generator = {'name': cv.GENERATOR_NAME, 'version': cv.GENERATOR_VERSION}
    checks = (
        lambda: run['format'] == generate.RUN_FORMAT,
        lambda: run['family'] == cv.FAMILY,
        lambda: run['generator'] == expected_generator,
        lambda: _integer_in_domain(run['seed'], 0, cv.MAX_SEED),
        lambda: _integer_in_domain(run['count'], 1, cv.MAX_COUNT),
    )
    return all(check() for check in checks)


def _valid_timeout(value):
    if type(value) not in (int, float, ExactJSONFloat):
        return False
    if not math.isfinite(value):
        return False
    return 0 < exact_fraction(value) <= exact_fraction(cv.MAX_TIMEOUT_S)


def _run_execution_matches(inputs):
    run = inputs.run
    checks = (
        lambda: vocab.is_timestamp(run['produced_at']),
        lambda: _integer_in_domain(run['per_program_cap'], 1, cv.MAX_PER_PROGRAM_CAP),
        lambda: _valid_timeout(run['timeout_s']),
        lambda: run['harness_sha256'] == _HARNESS_SHA256,
        lambda: run['candidates_sha256'] == inputs.candidates_sha256,
    )
    return all(check() for check in checks)


def _metadata_findings(inputs):
    if not isinstance(inputs.run, dict):
        return [cv.EXPORT_RUN_SUMMARY_MISMATCH]
    if not isinstance(inputs.records, list):
        return [cv.EXPORT_RUN_SUMMARY_MISMATCH]
    if not _run_header_matches(inputs.run):
        return [cv.EXPORT_RUN_SUMMARY_MISMATCH]
    if not _run_execution_matches(inputs):
        return [cv.EXPORT_RUN_SUMMARY_MISMATCH]
    return []


def _catalog_findings(inputs):
    run, catalog = inputs.run, inputs.catalog
    pinned = {
        'catalog_id': catalog.catalog_id,
        'programs_sha256': catalog.programs_sha256,
        'program_count': len(catalog.programs),
    }
    if run['catalog'] != pinned:
        return [cv.EXPORT_CATALOG_MISMATCH]
    policy = None if catalog.split_policy is None else catalog.split_policy.as_json()
    if run['split_policy'] != policy:
        return [cv.EXPORT_CATALOG_MISMATCH]
    if catalog_check.catalog_structure_findings(catalog):
        return [cv.EXPORT_CATALOG_MISMATCH]
    return []


def _record_findings(inputs):
    from .validation import validate_record
    for record in inputs.records:
        findings = validate_record(record, catalog=inputs.catalog)
        if findings:
            return findings
        if not _record_identity(record, inputs.run, inputs.catalog):
            return [cv.EXPORT_RUN_SUMMARY_MISMATCH]
    return []


def _summary_findings(inputs):
    ids = {record['id'] for record in inputs.records}
    if len(ids) != len(inputs.records):
        return [cv.EXPORT_RUN_SUMMARY_MISMATCH]
    if not _summary_matches(inputs.run, inputs.records, inputs.catalog):
        return [cv.EXPORT_RUN_SUMMARY_MISMATCH]
    return []


def _planned_findings(inputs):
    run = inputs.run
    plan = planning.ProposalPlan(inputs.catalog, run['seed'], run['per_program_cap'])
    expected = [proposal.binding() for proposal in plan.proposals(run['count'])]
    actual = [
        (record['scenario']['source']['program_id'], record['intervention']['draw_index'],
         record['intervention']['operator'], record['intervention']['site'],
         record['intervention']['variant'])
        for record in inputs.records
    ]
    if actual != expected or run['skips'] != dict(plan.skips):
        return [cv.EXPORT_RUN_SUMMARY_MISMATCH]
    return []


def _validate_run(inputs):
    for stage in (_metadata_findings, _catalog_findings, _record_findings, _summary_findings,
                  _planned_findings):
        findings = stage(inputs)
        if findings:
            return findings
    return []


def validate_run(run, records, *, catalog, candidates_sha256) -> list[str]:
    try:
        return _validate_run(_RunInputs(run, records, catalog, candidates_sha256))
    except (cv.RepairRefusal, KeyError, TypeError, ValueError, AttributeError, RecursionError, OverflowError):
        return [cv.EXPORT_RUN_SUMMARY_MISMATCH]


bind_import_twin(__name__)
