"""Leak-checked text training views for the five oracle-grounded neuromorphic families.

``oracle_generate.py run -> oracle_views -> sft / chat / choice rows``. A pure
projection of accepted, publishable, simulated oracle measurements into text:
the prompt is rendered from an allowlist of ``scenario`` and ``intervention``
keys, the completion is re-derived from ``result.measured``, and every row is
re-checked against its record before it is returned or written. The view makes
no training-readiness claim.

The package sits beside ``oracle_grounded`` rather than inside it on purpose:
``source_policy.catalog_digest`` seals every ``pipelines/oracle_grounded/*.py``
into the reviewed procedural authority, and a text projection is not part of
what produces or validates a measurement. Every module imports only its
siblings and ``_contract`` and ends with ``bind_import_twin(__name__)`` so both
import spellings are one object.
"""

__all__ = [
    "_contract",
    "cli",
    "findings",
    "gate",
    "labels",
    "leaks",
    "output",
    "public",
    "render",
    "rows",
    "vocabulary",
]

from ._contract import bind_import_twin

bind_import_twin(__name__)
