#!/usr/bin/env python3
"""Shared primitives for the card-schema declaration modules.

``CardSchemaError`` and ``_require`` are the fail-closed vocabulary every
``card_schema_*`` module raises through. ``DATASET_NAME_RE`` and
``DEFAULT_CONFIG_NAME`` are shared between declaration I/O (``card_schema.py``)
and validation (``card_schema_validate.py``) because a ``config_name`` is
itself validated as a Hub-name-shaped token.
"""

from __future__ import annotations

import re

DATASET_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

DEFAULT_CONFIG_NAME = "default"

__all__ = (
    "CardSchemaError",
    "DATASET_NAME_RE",
    "DEFAULT_CONFIG_NAME",
    "_require",
)


class CardSchemaError(Exception):
    """A declaration file is missing, unreadable, or does not validate."""


def _require(condition: object, message: str) -> None:
    if not condition:
        raise CardSchemaError(message)
