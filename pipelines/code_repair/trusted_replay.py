"""Fresh execution at export/admission boundaries; stored verdicts never grant authority."""
from __future__ import annotations

from collections import Counter
import platform

from . import executor, replay, vocabulary as cv
from .run_validation import run_identity
from .validation import validate_run
from ._contract import bind_import_twin


def _fresh_entries(records, catalog, engine):
    entries = (replay.replay_record(record, catalog, engine) for record in records)
    return sorted(entries, key=lambda entry: str(entry['record_id']))


def _active_codes(entries):
    active = [entry for entry in entries if entry['status'] == 'replayed']
    return active, Counter(entry['code'] for entry in active)


def _failed_count(codes):
    return sum(count for code, count in codes.items() if code != cv.REPLAY_PASSED)


def _replay_status(active, failed):
    if failed:
        return 'failed'
    if active:
        return 'passed'
    return 'nothing_to_replay'


def _replay_counts(entries, active, codes, failed):
    return {
        'records': len(entries),
        'positives': len(active),
        'passed': codes[cv.REPLAY_PASSED],
        'failed': failed,
        'not_replayed': len(entries) - len(active),
        'failed_by_code': {
            code: count for code, count in sorted(codes.items()) if code != cv.REPLAY_PASSED
        },
    }


def _replay_summary(entries):
    active, codes = _active_codes(entries)
    failed = _failed_count(codes)
    return _replay_status(active, failed), _replay_counts(entries, active, codes, failed)


def replay_records(run, records, *, catalog, candidates_sha256) -> dict:
    """Validate captured inputs, then freshly execute every positive using the pinned timeout."""
    findings = validate_run(run, records, catalog=catalog, candidates_sha256=candidates_sha256)
    cv.refuse_when(bool(findings), cv.FINDING_EXPORT_INTEGRITY, ', '.join(findings))
    engine = executor.Executor(timeout_s=run['timeout_s'])
    entries = _fresh_entries(records, catalog, engine)
    status, counts = _replay_summary(entries)
    return {'run_identity': run_identity(run, candidates_sha256),
            'catalog': {'catalog_id': catalog.catalog_id, 'programs_sha256': catalog.programs_sha256},
            'harness_sha256': engine.harness_sha256,
            'interpreter': '.'.join(platform.python_version().split('.')[:2]),
            'status': status, 'records': entries, 'counts': counts}


bind_import_twin(__name__)
