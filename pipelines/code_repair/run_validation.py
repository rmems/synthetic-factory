"""Pure RUN2 metadata and candidate completeness checks shared by trusted consumers."""
from __future__ import annotations

import math
from collections import Counter

from . import catalog as cat, catalog_check, executor, generate, mutate, records as assembly, vocabulary as cv
from ._contract import bind_import_twin, oc, vocab

# Bind the loaded implementation once; validate_run itself performs no I/O.
_HARNESS_SHA256 = executor.harness_sha256()


def run_identity(run: dict, candidates_sha256: str) -> dict:
    """All RUN fields are replay provenance; the captured byte digest is independent input."""
    return {'candidates_sha256': candidates_sha256, 'run_sha256':
            cat.sha256_text(oc.canonical_json(run)),
            **{key: run[key] for key in ('seed', 'produced_at', 'catalog', 'harness_sha256')}}


def _counts(value, expected=None):
    if not isinstance(value, dict) or any(type(n) is not int or n < 0 for n in value.values()):
        return False
    return expected is None or Counter(value) == Counter(expected)


def _record_identity(record, run, catalog):
    index = record['intervention']['draw_index']
    program_id = record['scenario']['source']['program_id']
    identity = cat.sha256_text(oc.canonical_json([catalog.catalog_id, catalog.programs_sha256]))
    if type(index) is not int or not 0 <= index < run['count']:
        return False
    configuration = record['oracle']['configuration']
    return (record['id'] == f'{cv.RECORD_ID_PREFIX}-{identity}-{run["seed"]}-{index:05d}'
            and record['generator']['seed'] == run['seed']
            and record['generator']['name'] == cv.GENERATOR_NAME
            and record['generator']['version'] == cv.GENERATOR_VERSION
            and record['provenance']['produced_at'] == run['produced_at']
            and record['oracle']['seed'] == assembly.candidate_seed(run['seed'], program_id, index)
            and record['oracle']['fingerprint']['harness_sha256'] == run['harness_sha256']
            and configuration['timeout_s'] == run['timeout_s']
            and configuration['limits'] == {'cpu_s': int(run['timeout_s']) + 2,
                 'address_space_mib': cv.ADDRESS_SPACE_MIB, 'file_size_kib': cv.FILE_SIZE_KIB})


def _summary_matches(run, records, catalog):
    if type(run['records']) is not int or run['records'] != len(records):
        return False
    for key, field in (('outcomes', 'outcome'), ('oracle_statuses', 'oracle_status')):
        if not _counts(run[key], Counter(r['result'][field] for r in records)):
            return False
    if not _counts(run['reasons'], Counter(c for r in records for c in r['result']['reason_codes'])):
        return False
    skips = run['skips']
    if not _counts(skips) or not set(skips) <= cv.SKIP_CODE_SET:
        return False
    sites = {p.program_id: len(mutate.sites(p.text, p.function, p.want_kind)) for p in catalog.programs}
    per_program = Counter(r['scenario']['source']['program_id'] for r in records)
    expected = {p: {'sites': n, 'records': per_program[p]} for p, n in sites.items()}
    if not isinstance(run['programs'], dict) or any(
            not _counts(counts) for counts in run['programs'].values()):
        return False
    if run['programs'] != expected or any(n > run['per_program_cap'] for n in per_program.values()):
        return False
    inventory = sum(n == 0 for n in sites.values())
    if skips.get(cv.SKIP_MUTATION_NO_SITES, 0) != inventory:
        return False
    return run['count'] == len(records) + sum(v for k, v in skips.items() if k != cv.SKIP_MUTATION_NO_SITES)


def validate_run(run, records, *, catalog, candidates_sha256) -> list[str]:
    from .validation import validate_record
    try:
        if not isinstance(run, dict) or not isinstance(records, list):
            return [cv.EXPORT_RUN_SUMMARY_MISMATCH]
        if (run['format'] != generate.RUN_FORMAT or run['family'] != cv.FAMILY
                or run['generator'] != {'name': cv.GENERATOR_NAME, 'version': cv.GENERATOR_VERSION}
                or type(run['seed']) is not int or not 0 <= run['seed'] <= cv.MAX_SEED
                or type(run['count']) is not int or not 1 <= run['count'] <= cv.MAX_COUNT
                or not vocab.is_timestamp(run['produced_at'])
                or type(run['per_program_cap']) is not int or not 1 <= run['per_program_cap'] <= cv.MAX_PER_PROGRAM_CAP
                or type(run['timeout_s']) not in (int, float) or not math.isfinite(run['timeout_s'])
                or not 0 < run['timeout_s'] <= cv.MAX_TIMEOUT_S
                or run['harness_sha256'] != _HARNESS_SHA256
                or run['candidates_sha256'] != candidates_sha256):
            return [cv.EXPORT_RUN_SUMMARY_MISMATCH]
        pinned = {'catalog_id': catalog.catalog_id, 'programs_sha256': catalog.programs_sha256,
                  'program_count': len(catalog.programs)}
        policy = None if catalog.split_policy is None else catalog.split_policy.as_json()
        if run['catalog'] != pinned or run['split_policy'] != policy or catalog_check.catalog_structure_findings(catalog):
            return [cv.EXPORT_CATALOG_MISMATCH]
        for record in records:
            findings = validate_record(record, catalog=catalog)
            if findings:
                return findings
            if not _record_identity(record, run, catalog):
                return [cv.EXPORT_RUN_SUMMARY_MISMATCH]
        if len({r['id'] for r in records}) != len(records) or not _summary_matches(run, records, catalog):
            return [cv.EXPORT_RUN_SUMMARY_MISMATCH]
        return []
    except (cv.RepairRefusal, KeyError, TypeError, ValueError, AttributeError, RecursionError, OverflowError):
        return [cv.EXPORT_RUN_SUMMARY_MISMATCH]


bind_import_twin(__name__)
