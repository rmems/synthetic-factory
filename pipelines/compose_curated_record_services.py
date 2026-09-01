#!/usr/bin/env python3
"""Call-time service graph for the historical compose-record facade."""

from __future__ import annotations

import sys
from typing import Any

if __package__:
    from . import _expose_package_sibling


def build_record_services(facade: Any) -> Any:
    """Bind stable callbacks that continue resolving live facade seams."""

    return facade.RecordServices(
        lambda record, stages, source: facade._compose_identity_stage(
            record,
            stages,
            source_path=source.path,
            source_line=source.line,
            source_sha256=source.sha256,
        ),
        lambda current, stages, source: facade._compose_bridge_stage(
            current,
            stages,
            source_path=source.path,
            source_line=source.line,
            source_sha256=source.sha256,
            source_file_sha256=source.file_sha256,
        ),
        lambda current, stages, context: facade._compose_preferences_stage(
            current,
            stages,
            source_path=context.source.path,
            source_line=context.source.line,
        ),
        lambda current, kind, stages, context: facade._compose_coding_stage(
            current,
            kind,
            stages,
            source_path=context.source.path,
            source_line=context.source.line,
            source_sha256=context.source.sha256,
        ),
        lambda current, stages, context: facade._compose_rewards_stage(
            current,
            stages,
            source_path=context.source.path,
            source_line=context.source.line,
            calibration=context.calibration,
        ),
    )


if __package__:
    _expose_package_sibling(__name__)
else:
    package = sys.modules.get("pipelines")
    expose = getattr(package, "_expose_package_sibling", None)
    if expose is not None:
        expose(__name__)
