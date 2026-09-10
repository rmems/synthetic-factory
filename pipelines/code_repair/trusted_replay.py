"""Fresh execution at export/admission boundaries; stored verdicts never grant authority."""
from __future__ import annotations

from collections import Counter
import platform

from . import executor, replay, vocabulary as cv
from .run_validation import run_identity
from .validation import validate_run
from ._contract import bind_import_twin


def replay_records(run, records, *, catalog, candidates_sha256) -> dict:
    """Validate captured inputs, then freshly execute every positive using the pinned timeout."""
    findings = validate_run(run, records, catalog=catalog, candidates_sha256=candidates_sha256)
    cv.refuse_when(bool(findings), cv.FINDING_EXPORT_INTEGRITY, ', '.join(findings))
    engine = executor.Executor(timeout_s=run['timeout_s'])
    entries = sorted((replay.replay_record(r, catalog, engine) for r in records),
                     key=lambda e: str(e['record_id']))
    active = [e for e in entries if e['status'] == 'replayed']
    codes = Counter(e['code'] for e in active)
    failed = sum(n for code, n in codes.items() if code != cv.REPLAY_PASSED)
    return {'run_identity': run_identity(run, candidates_sha256),
            'catalog': {'catalog_id': catalog.catalog_id, 'programs_sha256': catalog.programs_sha256},
            'harness_sha256': engine.harness_sha256,
            'interpreter': '.'.join(platform.python_version().split('.')[:2]),
            'status': 'failed' if failed else ('passed' if active else 'nothing_to_replay'),
            'records': entries, 'counts': {'records': len(entries), 'positives': len(active),
                'passed': codes[cv.REPLAY_PASSED], 'failed': failed,
                'not_replayed': len(entries) - len(active),
                'failed_by_code': {c: n for c, n in sorted(codes.items()) if c != cv.REPLAY_PASSED}}}


bind_import_twin(__name__)
