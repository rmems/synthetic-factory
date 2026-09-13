#!/usr/bin/env python3
"""Unicode and spacing spellings must not walk a payload past the bridge.

The bounded diagnosis document is the only channel from Session A to
Session B, so every check that recognizes a rejected-trajectory mapping has
to see the same text an operator sees. These regressions cover the three
ways an equivalent spelling used to read as ordinary prose: a space between
the words of a key, a cross-script homoglyph inside one word, and
compatibility punctuation standing in for ASCII delimiters.
"""

import unittest

from preference_arms_support import diagnosis_document  # noqa: E402
import preference_arms  # noqa: E402
from preference_arms_text import (  # noqa: E402
    _is_rejected_trajectory_key,
    _text_contains_rejected_trajectory_mapping,
)


def _document_with_root_cause(root_cause):
    return diagnosis_document(1, root_cause=root_cause).encode("utf-8")


class SpaceSeparatedKeysAreRejected(unittest.TestCase):
    """``executed action:`` is the same label as ``executed_action:``."""

    SPACED_LABELS = (
        "executed action",
        "future outcome",
        "reward components",
        "safety decision",
        "spike events",
        "reward delta",
        "internal reasoning",
    )

    def test_spaced_labels_read_as_trajectory_mappings(self):
        for label in self.SPACED_LABELS:
            with self.subTest(label=label):
                self.assertTrue(
                    _text_contains_rejected_trajectory_mapping(f"{label}: energize"),
                )

    def test_prose_prefix_does_not_hide_the_label(self):
        self.assertTrue(
            _text_contains_rejected_trajectory_mapping(
                "The supervisor logged the executed action: energize the coil."
            )
        )

    def test_spaced_payload_is_refused_by_the_document_contract(self):
        payload = _document_with_root_cause(
            "executed action: energize\nfuture outcome: worker injured"
        )
        with self.assertRaises(preference_arms.PreferenceArmsError) as caught:
            preference_arms.validate_diagnosis_document(payload, label="diagnosis-01-r11.md")
        self.assertIn("serialized payload", str(caught.exception))

    def test_ordinary_narrative_prose_still_passes(self):
        payload = _document_with_root_cause(
            "The gate accepted a plan it should have refused; the supervisor "
            "caught it one step later, after the arm had already committed."
        )
        result = preference_arms.validate_diagnosis_document(
            payload, label="diagnosis-01-r11.md"
        )
        self.assertIn("shared_context", result)


class CrossScriptWordsAreRefused(unittest.TestCase):
    """A hand-maintained homoglyph table can never be complete."""

    # U+0501 CYRILLIC SMALL LETTER KOMI DE is absent from the folding table,
    # so the key has to be refused for mixing scripts rather than normalized.
    KOMI_DE = "ԁ"

    def test_unlisted_homoglyph_is_still_a_trajectory_key(self):
        self.assertTrue(_is_rejected_trajectory_key(f"execute{self.KOMI_DE}_action"))

    def test_unlisted_homoglyph_mapping_is_refused(self):
        payload = _document_with_root_cause(
            f"execute{self.KOMI_DE}_action: energize the coil"
        )
        with self.assertRaises(preference_arms.PreferenceArmsError) as caught:
            preference_arms.validate_diagnosis_document(payload, label="diagnosis-01-r11.md")
        self.assertIn("serialized payload", str(caught.exception))

    def test_single_script_words_are_unaffected(self):
        for word in ("rationale", "причина", "原因"):
            with self.subTest(word=word):
                self.assertFalse(_is_rejected_trajectory_key(word))


class CompatibilityPunctuationIsFolded(unittest.TestCase):
    """Fullwidth delimiters are the ASCII delimiters they render as."""

    FULLWIDTH_OBJECT = (
        "｛\"safety_decision\"：\"ACCEPT\"，"
        "\"executed_action\"：\"energize\"，"
        "\"future_outcome\"：\"worker injured\"｝"
    )

    def test_fullwidth_object_is_refused(self):
        payload = _document_with_root_cause(self.FULLWIDTH_OBJECT)
        with self.assertRaises(preference_arms.PreferenceArmsError) as caught:
            preference_arms.validate_diagnosis_document(payload, label="diagnosis-01-r11.md")
        self.assertIn("object syntax", str(caught.exception))

    def test_fullwidth_mapping_without_braces_is_refused(self):
        payload = _document_with_root_cause(
            "\"executed_action\"：\"energize\" was the recorded step"
        )
        with self.assertRaises(preference_arms.PreferenceArmsError) as caught:
            preference_arms.validate_diagnosis_document(payload, label="diagnosis-01-r11.md")
        self.assertIn("serialized payload", str(caught.exception))

    def test_fullwidth_code_fence_is_refused(self):
        payload = _document_with_root_cause("｀｀｀json payload elided")
        with self.assertRaises(preference_arms.PreferenceArmsError) as caught:
            preference_arms.validate_diagnosis_document(payload, label="diagnosis-01-r11.md")
        self.assertIn("code fence", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
