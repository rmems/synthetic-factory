"""Ordered validation of oracle stages and declared runtime availability."""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_record_stages")
    from .oracle_checks_facade import ApiChecks
    from .oracle_record_stages_part1 import StageChecksPart1
    from .oracle_record_stages_part2 import StageChecksPart2
    from .oracle_record_stages_part3 import StageChecksPart3
    from .oracle_record_stages_part4 import StageChecksPart4
    from .oracle_record_stages_part5 import StageChecksPart5
    from .oracle_record_stages_part6 import StageChecksPart6
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_record_stages"
    )
    from oracle_checks_facade import ApiChecks
    from oracle_record_stages_part1 import StageChecksPart1
    from oracle_record_stages_part2 import StageChecksPart2
    from oracle_record_stages_part3 import StageChecksPart3
    from oracle_record_stages_part4 import StageChecksPart4
    from oracle_record_stages_part5 import StageChecksPart5
    from oracle_record_stages_part6 import StageChecksPart6


class StageChecks(
    ApiChecks,
    StageChecksPart1,
    StageChecksPart2,
    StageChecksPart3,
    StageChecksPart4,
    StageChecksPart5,
    StageChecksPart6,
):
    """Ordered stage-kind, alignment, and availability checks for one record."""

    def __init__(self, api):
        super().__init__(api)


if __package__:
    _expose_package_sibling(__name__)
