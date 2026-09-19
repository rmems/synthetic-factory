"""Pinned, alias-free capture of manifest-declared run files.

The caller supplies its live facade so callback and limit overrides remain visible.
"""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_validate_snapshot")
    from .oracle_checks_facade import ApiChecks
    from .oracle_validate_snapshot_part1 import SnapshotChecksPart1
    from .oracle_validate_snapshot_part2 import SnapshotChecksPart2
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_validate_snapshot"
    )
    from oracle_checks_facade import ApiChecks
    from oracle_validate_snapshot_part1 import SnapshotChecksPart1
    from oracle_validate_snapshot_part2 import SnapshotChecksPart2


class SnapshotChecks(SnapshotChecksPart1, SnapshotChecksPart2, ApiChecks):
    """Capture pinned run files while preserving live facade seams."""

    def __init__(self, api):
        ApiChecks.__init__(self, api)


if __package__:
    _expose_package_sibling(__name__)
