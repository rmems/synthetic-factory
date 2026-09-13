#!/usr/bin/env python3
"""Shared helpers for the rights-policy test modules."""

from __future__ import annotations


class SpoofedString(str):
    """A ``str`` whose equality, hashing and ``__class__`` claim another value.

    ``emitted`` is what the instance serialises as; ``expected`` is what ``==``,
    ``!=`` and ``hash`` report, and ``__class__`` answers plain ``str``. The
    rights tests hand these to the validators to prove that closed vocabularies
    and fixed fields are checked on the exact bytes, not through ``==`` or
    ``isinstance``.
    """

    def __new__(cls, emitted: str, expected: str):
        instance = super().__new__(cls, emitted)
        instance.expected = expected
        return instance

    def __eq__(self, other):
        return other == self.expected

    @property
    def __class__(self):
        return str

    def __ne__(self, other):
        return other != self.expected

    def __hash__(self):
        return hash(self.expected)
