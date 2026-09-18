"""Manifest header, layout, and availability validation.

The caller supplies its live facade so callback and limit overrides remain visible.
"""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_validate_manifest")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_validate_manifest"
    )


if __package__:
    from .oracle_validate_manifest_part1 import ManifestChecksPart1
    from .oracle_validate_manifest_part2 import ManifestChecksPart2
    from .oracle_validate_manifest_part3 import ManifestChecksPart3
else:
    from oracle_validate_manifest_part1 import ManifestChecksPart1
    from oracle_validate_manifest_part2 import ManifestChecksPart2
    from oracle_validate_manifest_part3 import ManifestChecksPart3


class ManifestChecks(ManifestChecksPart1, ManifestChecksPart2, ManifestChecksPart3):
    """Compose the focused validation concerns behind one facade."""

    def __init__(self, api):
        self.api = api


if __package__:
    _expose_package_sibling(__name__)
