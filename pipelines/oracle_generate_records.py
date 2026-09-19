"""Record generation and manifest summaries behind the live CLI facade."""

import sys
from dataclasses import dataclass

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_generate_records")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_generate_records"
    )


@dataclass
class FamilyJob:
    """The run-level inputs every family's generation pass shares."""

    count: int
    seed: int
    round_number: int
    commit: object
    dirty: object
    require_runtime: bool
    environ: object = None
    backend: str = "reference"
    byte_budget: object = None


@dataclass
class RunOutputs:
    """What one generation run produced that the manifest reports."""

    selected: list
    availability: dict
    generated: dict
    files: dict


class GenerationRecords:

    def __init__(self, api):
        self.api = api

    def generate_family(self, family, job):
        """Build records by verdict, stopping at the first fatal generation error."""
        accepted = []
        rejected = []
        errors = []
        byte_budget = job.byte_budget if job.byte_budget is not None else [0]
        file_bytes = {'accepted': 0, 'rejected': 0}
        run = self.api.record.RecordRunContext(
            round_number=job.round_number,
            commit=job.commit,
            dirty=job.dirty,
            environ=job.environ,
            backend=job.backend,
        )
        for index in range(job.count):
            try:
                item = self.api.record.build_record(family, index, seed=job.seed, run=run)
            except (self.api.oracles.OracleError, self.api.record.GenerationError) as exc:
                errors.append(f'{family}#{index}: {type(exc).__name__}: {exc}')
                break
            layers = self.api.record.classify(item, require_named_runtime=job.require_runtime)
            fatal = layers['envelope'] + layers['status']
            if fatal:
                errors.append(f'{family}#{index}: generated record failed its envelope: ' + '; '.join(fatal))
                break
            if item['validation']['status'] == 'accepted' and (not layers['family']):
                self.api._charge_record(item, 'accepted', file_bytes, byte_budget)
                accepted.append(item)
            else:
                self.api._charge_record(item, 'rejected', file_bytes, byte_budget)
                rejected.append(item)
        return (accepted, rejected, errors)

    def _charge_record(self, item, verdict, file_bytes, byte_budget):
        size = len((self.api.canon.dumps_record(item) + '\n').encode('utf-8'))
        file_bytes[verdict] += size
        byte_budget[0] += size
        if file_bytes[verdict] > self.api.MAX_JSONL_BYTES:
            raise ValueError(f"{verdict} payload is exceeding the validator's per-file limit")
        if byte_budget[0] > self.api.MAX_RUN_BYTES:
            raise ValueError("generated payloads are exceeding the validator's per-run limit")

    def summarize(self, records):
        scored = [item['validation']['candidate_prediction_correct'] for item in records if item['validation']['candidate_prediction_correct'] is not None]
        return {'records': len(records), 'candidate_scored': len(scored), 'candidate_correct': sum((1 for value in scored if value))}

    def build_manifest(self, job, outputs):
        per_family = {}
        all_errors = []
        any_publishable = False
        for family in outputs.selected:
            accepted, rejected, errors = outputs.generated[family]
            all_errors.extend(errors)
            if any((item['validation']['publishable'] for item in accepted + rejected)):
                any_publishable = True
            implementation = self.api._generated_implementation(accepted, rejected)
            per_family[family] = {'proposed': job.count, 'accepted': self.api.summarize(accepted), 'rejected': {'records': len(rejected), 'reasons': sorted({reason for item in rejected for reason in item['validation']['reasons']})}, 'oracle': {'requested_runtime': list(self.api.families.spec_for(family).runtimes), 'implementation': implementation}}
        if any_publishable:
            note = "Counts describe this run only. Some records are publishable: they were measured by the in-repo reference simulator at the current module digest (#171) or through the named-runtime protocol; check each record's own validation.publishable and validation.publishable_reason for the authoritative per-record determination."
        else:
            note = "Counts describe this run only; no record here is publishable. Each record's own validation.publishable_reason states why: a validation failure, a module digest the current sources cannot reproduce, or unresolved commit or dirty state."
        return {'schema': self.api.record.SCHEMA_ID, 'round': job.round_number, 'seed': job.seed, 'count_per_family': job.count, 'families': per_family, 'oracle_commit': job.commit, 'oracle_dirty': job.dirty, 'module_digest': self.api.oracles.module_digest(), 'oracle_availability': outputs.availability, 'files': outputs.files, 'generation_errors': all_errors, 'note': note}

    def _generated_implementation(self, accepted, rejected):
        if accepted:
            return accepted[0]['oracle']['implementation']
        if rejected:
            return rejected[0]['oracle']['implementation']
        return None


if __package__:
    _expose_package_sibling(__name__)
