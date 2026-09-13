"""Pure integrity checks for every code-repair evidence row, including exclusions."""
from __future__ import annotations

from dataclasses import dataclass

from . import catalog as cat, mutate, record_validation, row_validation, views, vocabulary as cv
from ._contract import bind_import_twin, oc


def _catalog_expectations(program, catalog):
    source = {
        'program_id': program.program_id,
        'family': program.family,
        'upstream': program.upstream,
        'module_sha256': program.sha256,
    }
    public = {'kind': 'doctest', 'examples': [
        {'example_id': example.example_id, 'source': example.source, 'want': example.want}
        for example in program.examples
    ]}
    hidden = {
        'kind': program.reference.kind,
        'reference_function': program.reference.function,
        'reference_sha256': program.reference.sha256,
        'cases': list(program.cases),
    }
    split = {
        'lineage_id': program.program_id,
        'group_id': program.group_id,
        'split': program.split,
        'policy_sha256': None if catalog.split_policy is None else catalog.split_policy.sha256,
    }
    return source, public, hidden, split


def _catalog_shape_finding(record, expected):
    source, public, hidden, split = expected
    if record['provenance']['split_lineage'] != split:
        return cv.EXPORT_SPLIT_REDERIVATION_MISMATCH
    actual = (
        record['scenario']['source'],
        record['scenario']['public_tests'],
        record['oracle']['configuration']['hidden_check'],
    )
    return None if actual == (source, public, hidden) else cv.EXPORT_CATALOG_MISMATCH


def _site_matches(site, intervention):
    actual = (site.as_json(), site.operator, site.variant)
    expected = (
        intervention.get('site'),
        intervention.get('operator'),
        intervention.get('variant'),
    )
    return actual == expected


def _mutation_matches(record, program):
    intervention = record['intervention']
    if intervention.get('kind') != 'ast_mutation':
        return False
    sites = [
        site for site in mutate.sites(program.text, program.function, program.want_kind)
        if _site_matches(site, intervention)
    ]
    if len(sites) != 1:
        return False
    site = sites[0]
    broken = record['scenario']['broken_program']['files'][cv.PROGRAM_FILENAME]
    checks = (
        lambda: mutate.apply(program.text, site) == broken,
        lambda: views.completion_of(record) == program.text,
        lambda: mutate.verify(program.text, broken, site, program.function) is None,
    )
    return all(check() for check in checks)


def catalog_bindings(record: dict, catalog: cat.Catalog) -> list[str]:
    """Bind public and hidden inputs and the mutation to an independently loaded catalog."""
    source = record['scenario']['source']
    program = next((p for p in catalog.programs if p.program_id == source['program_id']), None)
    if program is None:
        return [cv.EXPORT_CATALOG_MISMATCH]
    finding = _catalog_shape_finding(record, _catalog_expectations(program, catalog))
    if finding is not None:
        return [finding]
    if not _mutation_matches(record, program):
        return [cv.EXPORT_RECORD_FAILS_CONTRACT]
    return []


@dataclass(frozen=True)
class _RecordInputs:
    record: dict
    where: str
    catalog: cat.Catalog | None


def _shape_finding(inputs):
    record = inputs.record
    if not isinstance(record, dict):
        return cv.EXPORT_RECORD_FAILS_CONTRACT
    if oc.check_digest(record, inputs.where):
        return cv.EXPORT_EVIDENCE_DIGEST_MISMATCH
    record_validation.validate_shape(record)
    return None


def _evidence_finding(inputs):
    record = inputs.record
    checks = (
        (lambda: oc.check_oracle_label_leak(record, inputs.where),
         cv.EXPORT_RECORD_FAILS_CONTRACT),
        (lambda: not record_validation.verdict_matches(record),
         cv.EXPORT_EVIDENCE_VERDICT_MISMATCH),
        (lambda: not row_validation.outcomes_match(record),
         cv.EXPORT_EVIDENCE_VERDICT_MISMATCH),
        (lambda: bool(views.evidence_findings(record)),
         cv.EXPORT_RECORD_FAILS_CONTRACT),
    )
    for check, finding in checks:
        if check():
            return finding
    return None


def _catalog_finding(inputs):
    if inputs.catalog is None:
        return None
    findings = catalog_bindings(inputs.record, inputs.catalog)
    return findings[0] if findings else None


def _positive_view_finding(inputs):
    if not views.is_positive(inputs.record):
        return None
    findings = views.view_findings(inputs.record, views.sft_row(inputs.record))
    return cv.EXPORT_RECORD_FAILS_CONTRACT if findings else None


def _validate_record(inputs):
    for stage in (_shape_finding, _evidence_finding, _catalog_finding, _positive_view_finding):
        finding = stage(inputs)
        if finding is not None:
            return finding
    return None


def validate_record(record, where='record', *, catalog=None) -> list[str]:
    """Return coded findings without executing source or treating natural exclusions as errors."""
    try:
        finding = _validate_record(_RecordInputs(record, where, catalog))
    except (cv.RepairRefusal, KeyError, TypeError, ValueError, AttributeError, RecursionError):
        finding = cv.EXPORT_RECORD_FAILS_CONTRACT
    return [finding] if finding is not None else []


def validate_run(run, records, *, catalog, candidates_sha256) -> list[str]:
    """Validate the run and its captured records without execution."""
    from .run_validation import validate_run as check
    return check(run, records, catalog=catalog, candidates_sha256=candidates_sha256)


bind_import_twin(__name__)
