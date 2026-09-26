"""Manifest record bindings and family summaries.

The caller supplies its live facade so callback and limit overrides remain visible.
"""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_validate_manifest_records")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_validate_manifest_records"
    )


if __package__:
    from .oracle_validate_manifest_records_part1 import ManifestRecordChecksPart1
    from .oracle_validate_manifest_records_part2 import FamilyEvidence, ManifestRecordChecksPart2
    from .oracle_validate_manifest_records_part3 import ManifestRecordChecksPart3
else:
    from oracle_validate_manifest_records_part1 import ManifestRecordChecksPart1
    from oracle_validate_manifest_records_part2 import FamilyEvidence, ManifestRecordChecksPart2
    from oracle_validate_manifest_records_part3 import ManifestRecordChecksPart3

__all__ = ("FamilyEvidence", "ManifestRecordChecks")


class ManifestRecordChecks(
    ManifestRecordChecksPart1, ManifestRecordChecksPart2, ManifestRecordChecksPart3
):
    """Compose the focused validation concerns behind one facade."""

    def __init__(self, api):
        self.api = api


if __package__:
    _expose_package_sibling(__name__)
