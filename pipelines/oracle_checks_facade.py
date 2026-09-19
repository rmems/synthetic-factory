"""Shared composition for the focused-check facades."""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_checks_facade")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_checks_facade"
    )


class ApiChecks:
    """Bind one focused-check composition to its live caller facade."""

    def __init__(self, api):
        self.api = api


if __package__:
    _expose_package_sibling(__name__)
