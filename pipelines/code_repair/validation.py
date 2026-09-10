"""Pure integrity checks for every code-repair evidence row, including exclusions."""
from __future__ import annotations

from . import catalog as cat, mutate, record_validation, views, vocabulary as cv
from ._contract import bind_import_twin, oc


def catalog_bindings(record: dict, catalog: cat.Catalog) -> list[str]:
    """Bind public and hidden inputs and the mutation to an independently loaded catalog."""
    source = record['scenario']['source']
    program = next((p for p in catalog.programs if p.program_id == source['program_id']), None)
    if program is None:
        return [cv.EXPORT_CATALOG_MISMATCH]
    expected_source = {'program_id': program.program_id, 'family': program.family,
                       'upstream': program.upstream, 'module_sha256': program.sha256}
    public = {'kind': 'doctest', 'examples': [
        {'example_id': e.example_id, 'source': e.source, 'want': e.want} for e in program.examples]}
    hidden = {'kind': program.reference.kind, 'reference_function': program.reference.function,
              'reference_sha256': program.reference.sha256, 'cases': list(program.cases)}
    split = {'lineage_id': program.program_id, 'group_id': program.group_id,
             'split': program.split,
             'policy_sha256': None if catalog.split_policy is None else catalog.split_policy.sha256}
    if record['provenance']['split_lineage'] != split:
        return [cv.EXPORT_SPLIT_REDERIVATION_MISMATCH]
    if (source != expected_source or record['scenario']['public_tests'] != public
            or record['oracle']['configuration']['hidden_check'] != hidden
            or record['provenance']['split_lineage'] != split):
        return [cv.EXPORT_CATALOG_MISMATCH]
    intervention = record['intervention']
    sites = [s for s in mutate.sites(program.text, program.function, program.want_kind)
             if s.as_json() == intervention.get('site')
             and s.operator == intervention.get('operator') and s.variant == intervention.get('variant')]
    if intervention.get('kind') != 'ast_mutation' or len(sites) != 1:
        return [cv.EXPORT_RECORD_FAILS_CONTRACT]
    broken = record['scenario']['broken_program']['files'][cv.PROGRAM_FILENAME]
    if (mutate.apply(program.text, sites[0]) != broken
            or views.completion_of(record) != program.text
            or mutate.verify(program.text, broken, sites[0], program.function) is not None):
        return [cv.EXPORT_RECORD_FAILS_CONTRACT]
    return []


def validate_record(record, where='record', *, catalog=None) -> list[str]:
    """Return coded findings without executing source or treating natural exclusions as errors."""
    try:
        if not isinstance(record, dict):
            return [cv.EXPORT_RECORD_FAILS_CONTRACT]
        if oc.check_digest(record, where):
            return [cv.EXPORT_EVIDENCE_DIGEST_MISMATCH]
        record_validation.validate_shape(record)
        if oc.check_oracle_label_leak(record, where):
            return [cv.EXPORT_RECORD_FAILS_CONTRACT]
        if not record_validation.verdict_matches(record):
            return [cv.EXPORT_EVIDENCE_VERDICT_MISMATCH]
        if views.evidence_findings(record):
            return [cv.EXPORT_RECORD_FAILS_CONTRACT]
        if catalog is not None:
            findings = catalog_bindings(record, catalog)
            if findings:
                return findings
        if views.is_positive(record):
            findings = views.view_findings(record, views.sft_row(record))
            if findings:
                return [cv.EXPORT_RECORD_FAILS_CONTRACT]
        return []
    except (cv.RepairRefusal, KeyError, TypeError, ValueError, AttributeError, RecursionError):
        return [cv.EXPORT_RECORD_FAILS_CONTRACT]


def validate_run(run, records, *, catalog, candidates_sha256) -> list[str]:
    """Validate the run and its captured records without execution."""
    from .run_validation import validate_run as check
    return check(run, records, catalog=catalog, candidates_sha256=candidates_sha256)


bind_import_twin(__name__)
