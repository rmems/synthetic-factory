"""Ordered validation of oracle stages and declared runtime availability."""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_record_stages")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_record_stages"
    )


if __package__:
    from .oracle_record_stages_part1 import StageChecksPart1
    from .oracle_record_stages_part2 import StageChecksPart2
    from .oracle_record_stages_part3 import StageChecksPart3
else:
    from oracle_record_stages_part1 import StageChecksPart1
    from oracle_record_stages_part2 import StageChecksPart2
    from oracle_record_stages_part3 import StageChecksPart3


class StageChecks(StageChecksPart1, StageChecksPart2, StageChecksPart3):
    """Compose the focused validation concerns behind one facade."""

    def __init__(self, api):
        self.api = api


if __package__:
    _expose_package_sibling(__name__)
