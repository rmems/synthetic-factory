"""Editing one oracle identity field cannot disable teacher evidence checks."""

import copy
import unittest

from test_moe_router import mr, oc


def teacher_record():
    record = mr.build_records(11, 1, oracle=mr.ReferenceMoERouter())[0]
    record["oracle"].update(
        name="transformers_moe_router", type="real_model_router",
        implementation=mr.TRANSFORMERS_MOE_IMPLEMENTATION,
        authority=oc.AUTHORITY_AUTHORITATIVE,
    )
    record["oracle"]["fingerprint"].update(
        model="test/unsealed-teacher", revision_or_checkpoint="a" * 40,
        is_llm_teacher=True,
    )
    record["result"].update(is_llm_teacher=True, teacher_grounded=True)
    return record


class TeacherIdentity(unittest.TestCase):
    def test_implementation_rename_cannot_remove_required_logits(self):
        record = teacher_record()
        record["oracle"]["implementation"] = "foreign.module:OtherRouter"
        for layer in record["result"]["routing"]["layers"]:
            layer["router_logits"] = None
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        errors = mr.check_family(record, "test")
        self.assertTrue(any("TEACHER_ROUTER_LOGITS_REQUIRED" in e for e in errors), errors)

    def test_known_teacher_identity_fields_must_agree(self):
        original = teacher_record()
        for field, value in (("implementation", "foreign.module:OtherRouter"), ("type", "other")):
            with self.subTest(field=field):
                record = copy.deepcopy(original)
                record["oracle"][field] = value
                record["provenance"]["record_sha256"] = oc.record_digest(record)
                errors = mr.check_family(record, "test")
                self.assertTrue(any("TRANSFORMERS_IDENTITY_MISMATCH" in e for e in errors), errors)
