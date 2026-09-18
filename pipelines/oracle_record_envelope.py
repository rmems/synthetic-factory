"""Ordered oracle envelope, measurement result and provenance validation."""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_record_envelope")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_record_envelope"
    )


def _nonempty_object(value):
    return isinstance(value, dict) and bool(value)


if __package__:
    from .oracle_record_envelope_part1 import EnvelopeChecksPart1
    from .oracle_record_envelope_part2 import EnvelopeChecksPart2
else:
    from oracle_record_envelope_part1 import EnvelopeChecksPart1
    from oracle_record_envelope_part2 import EnvelopeChecksPart2


class EnvelopeChecks(EnvelopeChecksPart1, EnvelopeChecksPart2):
    """Compose the focused validation concerns behind one facade."""

    def __init__(self, api):
        self.api = api

if __package__:
    _expose_package_sibling(__name__)
