"""Manifest header, layout, and availability validation.

The caller supplies its live facade so callback and limit overrides remain visible.
"""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_validate_manifest")
    from .oracle_checks_facade import ApiChecks
    from .oracle_validate_manifest_part1 import ManifestChecksPart1
    from .oracle_validate_manifest_part2 import ManifestChecksPart2
    from .oracle_validate_manifest_part3 import ManifestChecksPart3
    from .oracle_validate_manifest_part4 import ManifestChecksPart4
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_validate_manifest"
    )
    from oracle_checks_facade import ApiChecks
    from oracle_validate_manifest_part1 import ManifestChecksPart1
    from oracle_validate_manifest_part2 import ManifestChecksPart2
    from oracle_validate_manifest_part3 import ManifestChecksPart3
    from oracle_validate_manifest_part4 import ManifestChecksPart4


class ManifestChecks(
    ApiChecks,
    ManifestChecksPart1,
    ManifestChecksPart2,
    ManifestChecksPart3,
    ManifestChecksPart4,
):
    """Compose the focused validation concerns behind one facade."""

    def __init__(self, api):
        ApiChecks.__init__(self, api)


if __package__:
    _expose_package_sibling(__name__)
