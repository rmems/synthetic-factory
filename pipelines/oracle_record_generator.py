"""Deterministic generator proposal and request integrity checks."""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_record_generator")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_record_generator"
    )


class GeneratorChecks:
    """Check generator evidence through the record facade's live dependencies."""

    def __init__(self, api):
        self.api = api

    def validate(self, record):
        findings = []
        generator = record["generator"]
        if not isinstance(generator, dict):
            return ["generator must be an object"]
        if generator.get("authoritative") is not False:
            findings.append("generator.authoritative must be false")
        family = record["family"]
        self._identity_findings(record, generator, family, findings)
        self._metadata_findings(record, family, findings)
        self._proposal_shape_findings(record, findings)
        self._proposal_integrity_findings(record, findings)
        self._configuration_findings(record, findings)
        return findings

    def _identity_findings(self, record, generator, family, findings):
        identifier = record["id"]
        match = self.api.re.fullmatch(rf"{self.api.re.escape(family)}-r([0-9]+)-([0-9]+)", identifier)
        if match is None:
            findings.append("id does not encode the record family, round, and index")
        else:
            round_number, index = int(match.group(1)), int(match.group(2))
            if record["meta"]["round"] != round_number:
                findings.append("meta.round does not match the round encoded in id")
            if identifier != f"{family}-r{round_number:02d}-{index:04d}":
                findings.append("id is not in canonical family-round-index form")
            if generator.get("label") != f"{family}#{index}":
                findings.append("generator.label does not match the family and index in id")
            self._seed_findings(record, generator, (family, index), findings)

    def _seed_findings(self, record, generator, identity, findings):
        family, index = identity
        record_seed = generator.get("seed")
        if not isinstance(record_seed, int) or isinstance(record_seed, bool):
            findings.append("generator.seed must be an integer")
            return
        if not 0 <= record_seed <= self.api.MAX_SEED:
            findings.append("generator.seed must be an unsigned 64-bit integer")
            return
        expected_generator = self.api.generators.generator_block(
            record_seed,
            f"{family}#{index}",
            model=generator.get("name"),
        )
        if generator != expected_generator:
            findings.append("generator does not match the deterministic generator contract")
        oracle_seed = record["oracle"].get("seed")
        if oracle_seed != record_seed:
            findings.append(
                "oracle.seed does not match the generator seed that produced this record"
            )
        self._reproduce_proposal(record, family, record_seed, findings)

    def _reproduce_proposal(self, record, family, record_seed, findings):
        try:
            expected_scenario, expected_intervention, expected_candidate = self.api.families.spec_for_record(record).propose(self.api.Rng(record_seed))
            expected_proposal = {
                "scenario": self.api.canon.normalize(expected_scenario),
                "intervention": self.api.canon.normalize(expected_intervention),
                "candidate_prediction": self.api.canon.normalize(expected_candidate),
            }
            retained_proposal = {
                key: record[key] for key in ("scenario", "intervention", "candidate_prediction")
            }
            if retained_proposal != expected_proposal:
                findings.append(
                    "generator.seed does not reproduce the stored scenario, "
                    "intervention, and candidate prediction"
                )
        except Exception as exc:
            findings.append(
                "generator proposal could not be reproduced from generator.seed: "
                f"{type(exc).__name__}"
            )

    def _metadata_findings(self, record, family, findings):
        expected_tags = ["oracle-grounded", family, record["oracle"]["implementation"]]
        if record["meta"].get("tags") != expected_tags:
            findings.append("meta.tags do not match the record family and oracle implementation")
        unknown_meta = sorted(key for key in record["meta"] if key not in self.api.META_ALLOWED_KEYS)
        if unknown_meta:
            findings.append("meta carries unauthenticated sibling keys: " + ", ".join(unknown_meta))

    def _proposal_shape_findings(self, record, findings):
        if not isinstance(record["scenario"], dict) or not record["scenario"]:
            findings.append("scenario must be a non-empty object")
        candidate = record["candidate_prediction"]
        if candidate is not None:
            if not isinstance(candidate, dict):
                findings.append("candidate_prediction must be an object or null")
            elif candidate.get("kind") != "non_authoritative_guess":
                findings.append("candidate_prediction.kind must be 'non_authoritative_guess'")

    def _proposal_integrity_findings(self, record, findings):
        reserved = self.api._reserved_key_hits(record)
        if reserved:
            findings.append(
                "generator sections carry oracle-reserved keys: " + self.api._reserved_key_listing(reserved)
            )
        expected = self.api.canon.digest(self.api.proposal_of(record))
        if record["proposal_hash"] != expected:
            findings.append(
                "proposal_hash does not cover the stored generator sections "
                "(the scenario or the prediction was edited after the oracle ran)"
            )

    def _configuration_findings(self, record, findings):
        try:
            request = self.api.families.spec_for_record(record).build_request(
                record["scenario"], record["intervention"]
            )
            rebuilt = self.api.canon.normalize(request.get("configuration"))
            retained = self.api.canon.normalize(record["oracle"].get("configuration"))
            if retained != rebuilt:
                findings.append(
                    "oracle.configuration does not match the configuration rebuilt "
                    "from scenario and intervention"
                )
        except Exception as exc:
            findings.append(
                "oracle request could not be rebuilt from scenario and intervention: "
                f"{type(exc).__name__}"
            )


if __package__:
    _expose_package_sibling(__name__)
