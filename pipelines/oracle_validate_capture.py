"""Authenticate the manifest-declared run snapshot against captured bytes.

The caller supplies its live facade so callback and limit overrides remain visible.
"""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_validate_capture")
    from .oracle_checks_facade import ApiChecks
    from .oracle_validate_capture_part1 import CaptureChecksPart1
    from .oracle_validate_capture_part2 import CaptureChecksPart2
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_validate_capture"
    )
    from oracle_checks_facade import ApiChecks
    from oracle_validate_capture_part1 import CaptureChecksPart1
    from oracle_validate_capture_part2 import CaptureChecksPart2


class CaptureChecks(ApiChecks, CaptureChecksPart1, CaptureChecksPart2):
    """Bind manifest declarations to pinned bytes through live facade seams."""

    def __init__(self, api):
        super().__init__(api)


if __package__:
    _expose_package_sibling(__name__)
